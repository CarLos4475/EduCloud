import hashlib
import os
from functools import lru_cache
from pathlib import Path
from zipfile import BadZipFile

import httpx
from google.api_core.exceptions import GoogleAPIError
from pypdf.errors import PyPdfError

from campus.adapters.deepseek import DeepSeekProvider, ProviderFailure
from campus.adapters.objects import LocalObjects
from campus.adapters.records import RevisionConflict
from campus.api.dependencies import academic_service, settings
from campus.services.academic import AcademicService, DomainError
from campus.services.jobs import JobService, changed
from campus.services.materials import MaterialService
from campus.services.practice import PracticeService
from campus.services.resources import ResourceService
from campus.services.retrieval import RetrievalService
from campus.services.tutoring import TutorService
from campus.services.uploads import UploadService

ACCOUNT_COLLECTIONS = (
    "attempts",
    "reviews",
    "resourceStates",
    "resourceVersions",
    "resources",
    "turns",
    "conversations",
    "materialVersions",
    "uploads",
    "materials",
    "outbox",
    "jobs",
    "idempotency",
    "usage",
    "jobLimits",
    "topics",
    "agenda",
    "schedule",
    "subjects",
    "periods",
    "profiles",
)


class StudyRuntime:
    def __init__(self, records, objects, secret, provider):
        self.records, self.objects, self.provider = records, objects, provider
        self.jobs = JobService(
            records, daily_tokens=int(os.getenv("CAMPUS_DAILY_TOKEN_BUDGET", "100000"))
        )
        self.materials = MaterialService(records, objects, self.jobs, provider)
        self.uploads = UploadService(records, objects, self.jobs, secret)
        self.retrieval = RetrievalService(self.materials)
        self.tutor = TutorService(records, self.jobs, self.retrieval, provider)
        self.resources = ResourceService(records, self.jobs, self.retrieval, provider)
        self.practice = PracticeService(records, self.resources)

    def run_job(self, reference):
        uid, key = reference["ownerId"], reference["id"]
        job = self.jobs.claim(uid, key)
        if not job:
            self.sync_failed_material(self.jobs.get(uid, key))
            return
        try:
            if job["kind"] == "ingest":
                self.materials.ingest(job)
            elif job["kind"] == "tutor_turn":
                self.tutor.run(job)
            elif job["kind"] == "generate_resource":
                self.resources.run(job)
            elif job["kind"] == "index":
                blocks = self.materials.rebuild_index(
                    uid, job["entityId"], job["payload"]["version"]
                )
                self.retrieval.load_index(
                    uid, job["entityId"], job["payload"]["version"]
                )
                material = self.materials.get(uid, job["entityId"])
                additions = []
                if (
                    material["status"] == "queued"
                    and material.get("jobId") == key
                    and material["extractionVersion"] == job["payload"]["version"]
                ):
                    additions = [
                        (
                            "materials",
                            material["id"],
                            changed(material, status=self.materials._status(blocks)),
                            material["revision"],
                        )
                    ]
                self.jobs.finish(
                    uid,
                    key,
                    job["leaseToken"],
                    "succeeded",
                    {"indexedVersion": job["payload"]["version"]},
                    additions=additions,
                )
            else:
                raise DomainError(422, "No pudimos completar esta acción.")
        except (
            DomainError,
            ProviderFailure,
            ValueError,
            OSError,
            httpx.HTTPError,
            RevisionConflict,
            GoogleAPIError,
            PyPdfError,
            BadZipFile,
        ) as error:
            code = (
                error.code
                if isinstance(error, ProviderFailure)
                else "processing_failed"
            )
            additions = []
            if job["kind"] == "ingest":
                material = self.materials.get(uid, job["entityId"])
                if material.get("jobId") == key:
                    additions.append(
                        (
                            "materials",
                            material["id"],
                            changed(material, status="failed"),
                            material["revision"],
                        )
                    )
            self.jobs.finish(
                uid,
                key,
                job["leaseToken"],
                "failed",
                {"error": code},
                additions=additions,
                usage=error.usage if isinstance(error, ProviderFailure) else None,
            )

    def delete_account_data(self, uid):
        """Remove everything stored for a student. Refuses while work is running."""
        if any(
            job["status"] in ("queued", "running", "cancel_requested")
            for job in self.records.list(uid, "jobs")
        ):
            raise DomainError(
                409,
                "Todavía hay tareas en curso. Espera a que terminen o cancélalas.",
            )
        for subject in self.records.list(uid, "subjects"):
            self.delete_subject(uid, subject["id"])
        keys = set()
        for name in ("materials", "uploads"):
            keys.update(
                row["objectKey"]
                for row in self.records.list(uid, name)
                if row.get("objectKey")
            )
        for row in self.records.list(uid, "materialVersions"):
            keys.update(k for k in (row.get("blocksKey"), row.get("indexKey")) if k)
        for key in keys:
            try:
                self.objects.delete(key)
            except (DomainError, OSError, GoogleAPIError, KeyError):
                pass
        for name in ACCOUNT_COLLECTIONS:
            for row in self.records.list(uid, name):
                self.records.remove(uid, name, row["id"])

    def delete_subject(self, uid, subject_id):
        """Remove a subject and everything built from it; refuses while work is running."""
        academic = AcademicService(self.records)
        academic.get(uid, "subjects", subject_id)
        mine = lambda name: [
            r for r in self.records.list(uid, name) if r.get("subjectId") == subject_id
        ]
        materials = mine("materials")
        material_ids = {m["id"] for m in materials}
        uploads = [
            u
            for u in self.records.list(uid, "uploads")
            if u["materialId"] in material_ids
        ]
        turns = [
            t
            for t in self.records.list(uid, "turns")
            if t["conversationId"] in {c["id"] for c in mine("conversations")}
        ]
        versions = [
            v
            for v in self.records.list(uid, "resourceVersions")
            if v["resourceId"] in {r["id"] for r in mine("resources")}
        ]
        entities = material_ids | {t["id"] for t in turns} | {v["id"] for v in versions}
        jobs = [j for j in self.records.list(uid, "jobs") if j["entityId"] in entities]
        if any(j["status"] in ("queued", "running", "cancel_requested") for j in jobs):
            raise DomainError(
                409,
                "Todavía hay tareas en curso en esta materia. Espera a que terminen o cancélalas.",
            )
        keys = set()
        for row in [*materials, *uploads]:
            if row.get("objectKey"):
                keys.add(row["objectKey"])
        for row in self.records.list(uid, "materialVersions"):
            if row["id"].split("_")[0] in material_ids:
                keys.update(k for k in (row.get("blocksKey"), row.get("indexKey")) if k)
        for key in keys:
            try:
                self.objects.delete(key)
            except (DomainError, OSError, GoogleAPIError, KeyError):
                pass  # Already gone; the records below are what matter.
        for name, rows in (
            (
                "materialVersions",
                [
                    r
                    for r in self.records.list(uid, "materialVersions")
                    if r["id"].split("_")[0] in material_ids
                ],
            ),
            ("uploads", uploads),
            ("materials", materials),
            ("turns", turns),
            ("conversations", mine("conversations")),
            ("resourceVersions", versions),
            (
                "resourceStates",
                [
                    r
                    for r in self.records.list(uid, "resourceStates")
                    if r["id"] in {v["id"] for v in versions}
                ],
            ),
            ("attempts", mine("attempts")),
            ("reviews", mine("reviews")),
            ("resources", mine("resources")),
            ("jobs", jobs),
            (
                "outbox",
                [
                    o
                    for o in self.records.list(uid, "outbox")
                    if o["id"] in {j["id"] for j in jobs}
                ],
            ),
        ):
            for row in rows:
                self.records.remove(uid, name, row["id"])
        academic.delete(uid, "subjects", subject_id)

    def sync_failed_material(self, job):
        if job["kind"] != "ingest" or job["status"] not in (
            "failed",
            "canceled",
            "cancel_requested",
        ):
            return
        row = self.records.get(job["ownerId"], "materials", job["entityId"])
        if (
            row
            and row.get("jobId") == job["id"]
            and row["status"] in ("queued", "processing")
        ):
            value = changed(
                row,
                status="failed",
                error="processing_canceled"
                if job["status"] in ("canceled", "cancel_requested")
                else "processing_failed",
            )
            self.records.save(
                job["ownerId"], "materials", row["id"], value, row["revision"]
            )

    def cancel(self, uid, key):
        job = self.jobs.cancel(uid, key)
        self.sync_failed_material(job)
        return job

    def retry(self, uid, key, accept_possible_charge=False):
        previous = self.jobs.get(uid, key)
        if previous["status"] not in ("failed", "canceled"):
            raise DomainError(
                409, "Solo puedes intentar de nuevo lo que no se completó."
            )
        if previous["usageUnknown"] and not accept_possible_charge:
            raise DomainError(
                409,
                "Puede que el intento anterior ya cuente en tu límite de hoy. Confirma que quieres intentarlo de nuevo.",
            )
        collection = {
            "tutor_turn": "turns",
            "generate_resource": "resourceVersions",
        }.get(previous["kind"], "materials")
        entity = self.records.get(uid, collection, previous["entityId"])
        if not entity:
            raise DomainError(404, "Esto ya no está disponible.")
        if entity.get("jobId") != key:
            current = self.jobs.get(uid, entity["jobId"])
            if current["payload"].get("retryOf") == key:
                return current
            raise DomainError(409, "Ya hay una versión más reciente de esto.")
        payload = {**previous["payload"], "retryOf": key}
        if previous["kind"] == "ingest":
            payload["version"] = hashlib.sha256(f"retry:{key}".encode()).hexdigest()[
                :32
            ]
        return self.jobs.create(
            uid,
            previous["kind"],
            previous["entityId"],
            payload,
            f"retry-{key}",
            reserve=previous["reservation"],
            additions=lambda job: [
                (
                    collection,
                    entity["id"],
                    changed(
                        entity,
                        jobId=job["id"],
                        **(
                            {"status": "queued", "error": None}
                            if collection == "materials"
                            else {}
                        ),
                    ),
                    entity["revision"],
                )
            ],
        )


@lru_cache
def study_runtime():
    config = settings()
    bucket = os.getenv("CAMPUS_STORAGE_BUCKET")
    if bucket:
        from campus.adapters.gcs import GCSObjects

        objects = GCSObjects(
            os.getenv("CAMPUS_STORAGE_PROJECT", config.project), bucket
        )
    else:
        if os.getenv("K_SERVICE"):
            raise ValueError("Cloud Run requires private object storage.")
        objects = LocalObjects(os.getenv("CAMPUS_LOCAL_DATA_DIR", ".data/objects"))
    secret = os.getenv("CAMPUS_UPLOAD_SIGNING_KEY", "").encode()
    if not secret:
        if os.getenv("K_SERVICE"):
            raise ValueError("Configure a persistent upload signing key.")
        file = Path(".data/keys/upload.key")
        file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with file.open("xb") as output:
                output.write(os.urandom(32))
        except FileExistsError:
            pass
        secret = file.read_bytes()
    provider = DeepSeekProvider() if os.getenv("DEEPSEEK_API_KEY") else None
    if os.getenv("CAMPUS_AI_PROVIDER") == "test":
        if not config.emulators or config.environment != "local":
            raise ValueError("Test provider is only available with local emulators.")
        from campus.adapters.testing import TestStudyProvider

        provider = TestStudyProvider()
    return StudyRuntime(academic_service().records, objects, secret, provider)
