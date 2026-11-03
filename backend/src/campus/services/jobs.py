"""Persistent job state machine. Transport delivers references, never owns state."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from campus.services.academic import DomainError


def now():
    return datetime.now(UTC)


def changed(row, **values):
    return {
        **row,
        **values,
        "revision": row["revision"] + 1,
        "updatedAt": now().isoformat(),
    }


def new_row(**values):
    return {"id": uuid4().hex, "revision": 1, "createdAt": now().isoformat(), **values}


class JobService:
    def __init__(self, records, clock=now, daily_tokens=100000):
        self.records, self.clock, self.daily_tokens = records, clock, daily_tokens

    def get(self, uid, key):
        row = self.records.get(uid, "jobs", key)
        if not row:
            raise DomainError(404, "No se encontró el trabajo.")
        return row

    def create(self, uid, kind, entity, payload, key, reserve=0, additions=()):
        if not key or len(key) > 128:
            raise DomainError(422, "Falta una clave de idempotencia válida.")
        fingerprint = hashlib.sha256(
            json.dumps([kind, entity, payload], sort_keys=True).encode()
        ).hexdigest()
        token = hashlib.sha256(f"{kind}:{key}".encode()).hexdigest()

        def operation():
            previous = self.records.get(uid, "idempotency", token)
            if previous:
                if previous["fingerprint"] != fingerprint:
                    raise DomainError(409, "La clave ya se usó con otro contenido.")
                return self.get(uid, previous["jobId"])
            day = self.clock().date().isoformat()
            usage = self.records.get(uid, "usage", day)
            limits = self.records.get(uid, "jobLimits", "active")
            active_limits = limits or {
                "id": "active",
                "revision": 0,
                "active": 0,
                "requests": [],
            }
            account = usage or {
                "id": day,
                "revision": 0,
                "chargedTokens": 0,
                "active": 0,
                "requests": [],
            }
            recent = [
                t
                for t in active_limits["requests"]
                if t > self.clock().timestamp() - 60
            ]
            if kind == "tutor_turn" and len(recent) >= 20:
                raise DomainError(
                    429, "Se alcanzó el límite de 20 preguntas por minuto."
                )
            if reserve and (
                active_limits["active"] >= 2
                or account["chargedTokens"] + reserve > self.daily_tokens
                or len(recent) >= 20
            ):
                raise DomainError(
                    429, "Se alcanzó la cuota de IA del piloto. Intenta más tarde."
                )
            job = new_row(
                ownerId=uid,
                kind=kind,
                entityId=entity,
                payload=payload,
                status="queued",
                stage="queued",
                progress=0,
                attempts=0,
                leaseToken=None,
                leaseUntil=None,
                reservation=reserve,
                usageDay=day,
                externalStarted=False,
                usageUnknown=False,
                result=None,
                error=None,
            )
            extra = additions(job) if callable(additions) else additions
            changes = [
                ("jobs", job["id"], job, None),
                (
                    "outbox",
                    job["id"],
                    new_row(id=job["id"], status="pending", jobId=job["id"]),
                    None,
                ),
                (
                    "idempotency",
                    token,
                    new_row(id=token, fingerprint=fingerprint, jobId=job["id"]),
                    None,
                ),
                *extra,
            ]
            if reserve:
                usage_next = changed(
                    account,
                    chargedTokens=account["chargedTokens"] + reserve,
                    active=account["active"] + 1,
                    requests=[*recent, self.clock().timestamp()],
                )
                changes.append(
                    ("usage", day, usage_next, usage["revision"] if usage else None)
                )
                changes.append(
                    (
                        "jobLimits",
                        "active",
                        changed(
                            active_limits,
                            active=active_limits["active"] + 1,
                            requests=[*recent, self.clock().timestamp()],
                        ),
                        limits["revision"] if limits else None,
                    )
                )
            if kind == "tutor_turn" and not reserve:
                changes.append(
                    (
                        "jobLimits",
                        "active",
                        changed(
                            active_limits, requests=[*recent, self.clock().timestamp()]
                        ),
                        limits["revision"] if limits else None,
                    )
                )
            self.records.save_many(uid, changes)
            return job

        return self.records.atomic(operation)

    def claim(self, uid, key):
        def operation():
            row = self.get(uid, key)
            if row["status"] == "cancel_requested":
                self._finish(row, None, "canceled", {})
                return None
            expired = (
                row["status"] == "running"
                and datetime.fromisoformat(row["leaseUntil"]) <= self.clock()
            )
            if row["status"] != "queued" and not expired:
                return None
            # Never automatically repeat an external call whose billing is unknown.
            if expired and row["externalStarted"]:
                self._finish(row, None, "failed", {"error": "provider_interrupted"})
                return None
            if row["attempts"] >= 5:
                self._finish(row, None, "failed", {"error": "attempt_limit"})
                return None
            lease = changed(
                row,
                status="running",
                stage="started",
                attempts=row["attempts"] + 1,
                leaseToken=uuid4().hex,
                leaseUntil=(self.clock() + timedelta(minutes=5)).isoformat(),
            )
            self.records.save(uid, "jobs", key, lease, row["revision"])
            return lease

        return self.records.atomic(operation)

    def checkpoint(self, uid, key, token, stage, progress):
        def operation():
            row = self.get(uid, key)
            if (
                row["status"] != "running"
                or row["leaseToken"] != token
                or datetime.fromisoformat(row["leaseUntil"]) <= self.clock()
            ):
                raise DomainError(409, "El trabajo ya no posee su lease.")
            value = changed(
                row,
                stage=stage,
                progress=progress,
                leaseUntil=(self.clock() + timedelta(minutes=5)).isoformat(),
            )
            self.records.save(uid, "jobs", key, value, row["revision"])
            return value

        return self.records.atomic(operation)

    def mark_external_started(self, uid, key, token):
        def operation():
            row = self.get(uid, key)
            if row["status"] != "running" or row["leaseToken"] != token:
                raise DomainError(409, "El trabajo fue cancelado o cambió de ejecutor.")
            self.records.save(
                uid,
                "jobs",
                key,
                changed(row, externalStarted=True, observedUsage=None),
                row["revision"],
            )

        self.records.atomic(operation)

    def observe_usage(self, uid, key, token, usage):
        def operation():
            row = self.get(uid, key)
            if row["leaseToken"] != token or row["status"] not in (
                "running",
                "cancel_requested",
            ):
                raise DomainError(409, "El trabajo cambió de ejecutor.")
            self.records.save(
                uid, "jobs", key, changed(row, observedUsage=usage), row["revision"]
            )

        self.records.atomic(operation)

    def finish(self, uid, key, token, status, result, additions=(), usage=None):
        def operation():
            row = self.get(uid, key)
            if row["status"] == "cancel_requested" and row["leaseToken"] == token:
                self._finish(row, token, "canceled", {}, usage=usage)
                return False
            if (
                row["status"] != "running"
                or row["leaseToken"] != token
                or datetime.fromisoformat(row["leaseUntil"]) <= self.clock()
            ):
                return False
            self._finish(row, token, status, result, additions, usage)
            return True

        return self.records.atomic(operation)

    def _finish(self, row, token, status, result, additions=(), usage=None):
        uid = row["ownerId"]
        if usage is None:
            usage = row.get("observedUsage")
        unknown = bool(row["externalStarted"] and usage is None)
        value = changed(
            row,
            status=status,
            stage=status,
            progress=100 if status == "succeeded" else row["progress"],
            leaseUntil=None,
            leaseToken=None,
            result=result,
            error=result.get("error"),
            usageUnknown=unknown,
            usage=usage,
            usageSettled=True,
        )
        outbox = self.records.get(uid, "outbox", row["id"])
        changes = [("jobs", row["id"], value, row["revision"]), *additions]
        if outbox:
            changes.append(
                (
                    "outbox",
                    row["id"],
                    changed(outbox, status="done"),
                    outbox["revision"],
                )
            )
        if row["reservation"] and not row.get("usageSettled"):
            account = self.records.get(uid, "usage", row["usageDay"])
            limits = self.records.get(uid, "jobLimits", "active")
            actual = (
                int(usage.get("total_tokens", row["reservation"]))
                if usage is not None
                else (row["reservation"] if unknown else 0)
            )
            updated = changed(
                account,
                active=max(0, account["active"] - 1),
                chargedTokens=max(
                    0, account["chargedTokens"] - row["reservation"] + actual
                ),
            )
            changes.append(("usage", account["id"], updated, account["revision"]))
            if limits:
                changes.append(
                    (
                        "jobLimits",
                        "active",
                        changed(limits, active=max(0, limits["active"] - 1)),
                        limits["revision"],
                    )
                )
        self.records.save_many(uid, changes)
        return value

    def cancel(self, uid, key):
        def operation():
            row = self.get(uid, key)
            if row["status"] in ("succeeded", "failed", "canceled"):
                return row
            if row["status"] == "running":
                value = changed(row, status="cancel_requested")
                self.records.save(uid, "jobs", key, value, row["revision"])
                return value
            else:
                return self._finish(row, None, "canceled", {})

        return self.records.atomic(operation)

    def recover_expired(self, uid, key):
        def operation():
            row = self.get(uid, key)
            if row["status"] == "cancel_requested":
                return self._finish(row, None, "canceled", {})
            if (
                row["status"] != "running"
                or datetime.fromisoformat(row["leaseUntil"]) > self.clock()
            ):
                return row
            if row["externalStarted"] or row["attempts"] >= 5:
                return self._finish(
                    row,
                    None,
                    "failed",
                    {
                        "error": "provider_interrupted"
                        if row["externalStarted"]
                        else "attempt_limit"
                    },
                )
            outbox = self.records.get(uid, "outbox", key)
            updated = changed(
                row, status="queued", stage="queued", leaseUntil=None, leaseToken=None
            )
            changes = [("jobs", key, updated, row["revision"])]
            if outbox:
                changes.append(
                    (
                        "outbox",
                        key,
                        changed(outbox, status="pending"),
                        outbox["revision"],
                    )
                )
            self.records.save_many(uid, changes)
            return updated

        return self.records.atomic(operation)
