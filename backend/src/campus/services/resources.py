"""Generated resources: immutable versions, verified citations, no server-side execution."""

import hashlib
import json
import re

from pydantic import ValidationError

from campus.adapters.deepseek import ProviderFailure
from campus.domain.contracts import InteractivePackageV1
from campus.domain.resources import (
    KIND_LABELS,
    ConceptsContent,
    FlashcardsContent,
    GeneratedCitation,
    QuizContent,
    ResourceChange,
    ResourceInput,
    ResourceUpdate,
    SummaryContent,
)
from campus.prompts.resources import PROMPT_VERSION, system_prompt
from campus.services.academic import DomainError
from campus.services.jobs import changed, new_row

CONTENT_MODELS = {
    "summary": SummaryContent,
    "concepts": ConceptsContent,
    "flashcards": FlashcardsContent,
    "quiz": QuizContent,
}
RETRYABLE_FAILURES = {
    "provider_interrupted",
    "provider_invalid_output",
    "provider_truncated",
}
MAX_RESOURCES = 100
MAX_VERSIONS = 20
FORBIDDEN_MARKUP = re.compile(
    r"<\s*(script|iframe|object|embed|form|svg|math|link|style|meta|base)\b",
    re.IGNORECASE,
)
FORBIDDEN_JS = re.compile(
    r"\b(window|document|fetch|eval|XMLHttpRequest|WebSocket|importScripts|globalThis|Function|import)\b"
)


def check_interactive(package):
    """Static checks only; the renderer remains the security boundary."""
    if FORBIDDEN_MARKUP.search(package.html) or re.search(
        r"\son\w+\s*=", package.html, re.IGNORECASE
    ):
        raise ValueError("El HTML contiene elementos o atributos no permitidos.")
    if re.search(
        r"(https?:|javascript:|data:|url\s*\(|@import)",
        package.html + package.css,
        re.IGNORECASE,
    ):
        raise ValueError("El recurso no puede cargar contenido externo.")
    if FORBIDDEN_JS.search(package.javascript):
        raise ValueError("El JavaScript usa APIs no disponibles en la VM aislada.")
    if len(json.dumps(package.model_dump(by_alias=True)).encode()) > 300 * 1024:
        raise ValueError("El paquete excede 300 KiB.")


class ResourceService:
    def __init__(self, records, jobs, retrieval, provider):
        self.records, self.jobs, self.retrieval, self.provider = (
            records,
            jobs,
            retrieval,
            provider,
        )

    # --- reading -------------------------------------------------------------
    def _resource(self, uid, key):
        row = self.records.get(uid, "resources", key)
        if not row:
            raise DomainError(404, "No se encontró el recurso.")
        return row

    def _versions(self, uid, resource_id):
        return sorted(
            (
                v
                for v in self.records.list(uid, "resourceVersions")
                if v["resourceId"] == resource_id
            ),
            key=lambda v: v["number"],
        )

    def _public_version(self, uid, row):
        job = self.jobs.get(uid, row["jobId"])
        ready = job["status"] == "succeeded"
        stale = False
        for citation in row["citations"] if ready else []:
            try:
                material = self.retrieval.materials.get(uid, citation["materialId"])
                stale = (
                    stale
                    or material["extractionVersion"] != citation["extractionVersion"]
                )
            except DomainError as missing:
                if missing.status != 404:
                    raise
                stale = True
        return {
            "id": row["id"],
            "resourceId": row["resourceId"],
            "number": row["number"],
            "instruction": row["instruction"],
            "createdAt": row["createdAt"],
            "jobId": row["jobId"],
            "model": row.get("model"),
            "promptVersion": row.get("promptVersion"),
            "status": job["status"],
            "stage": job["stage"],
            "error": job["error"],
            "usageUnknown": job["usageUnknown"],
            "content": row["content"] if ready else None,
            "citations": row["citations"] if ready else [],
            "textAlternative": row.get("textAlternative") if ready else None,
            "sourcesChanged": stale,
        }

    def _summary(self, uid, resource, versions):
        public = [self._public_version(uid, v) for v in versions]
        ready = [v for v in public if v["status"] == "succeeded"]
        return {
            **resource,
            "versionCount": len(public),
            "latestStatus": public[-1]["status"] if public else None,
            "latestVersionId": public[-1]["id"] if public else None,
            "currentVersionId": ready[-1]["id"] if ready else None,
        }, public

    def detail(self, uid, key):
        resource = self._resource(uid, key)
        summary, public = self._summary(uid, resource, self._versions(uid, key))
        return {**summary, "versions": public}

    def list(self, uid, subject_id, archived=False):
        if not self.records.get(uid, "subjects", subject_id):
            raise DomainError(404, "No se encontró la materia.")
        by_resource = {}
        for version in self.records.list(uid, "resourceVersions"):
            by_resource.setdefault(version["resourceId"], []).append(version)
        rows = [
            r
            for r in self.records.list(uid, "resources")
            if r["subjectId"] == subject_id and bool(r["archived"]) == archived
        ]
        rows.sort(key=lambda r: r["createdAt"], reverse=True)
        return [
            self._summary(
                uid, r, sorted(by_resource.get(r["id"], []), key=lambda v: v["number"])
            )[0]
            for r in rows
        ]

    def version(self, uid, key):
        row = self.records.get(uid, "resourceVersions", key)
        if not row:
            raise DomainError(404, "No se encontró la versión.")
        return self._public_version(uid, row)

    # --- writing -------------------------------------------------------------
    def _context(
        self, uid, subject_id, kind, instruction, material_ids, allow_general, previous
    ):
        if len(material_ids) != len(set(material_ids)):
            raise DomainError(422, "No repitas fuentes.")
        for key in material_ids:
            if self.retrieval.materials.get(uid, key)["subjectId"] != subject_id:
                raise DomainError(404, "La fuente no pertenece a esta materia.")
        blocks, seen, budget = [], set(), 18000
        if material_ids:
            found = (
                self.retrieval.search(uid, subject_id, instruction, material_ids)[:4]
                if instruction.strip()
                else []
            )
            for block in [
                *found,
                *self.retrieval.overview(uid, subject_id, material_ids),
            ]:
                ref = block["sourceRef"]
                ident = (ref["materialId"], ref["blockId"])
                if ident in seen:
                    continue
                text = block["text"][: max(0, min(3000, budget))]
                if not text:
                    break
                seen.add(ident)
                budget -= len(text)
                blocks.append({"sourceRef": ref, "text": text})
                if len(blocks) == 8:
                    break
        if not blocks and not allow_general:
            raise DomainError(
                422,
                "Selecciona material con texto listo o autoriza conocimiento general para este recurso.",
            )
        for i, block in enumerate(blocks, 1):
            block["sourceId"] = f"S{i}"
        return {
            "kind": kind,
            "instruction": instruction,
            "sources": blocks,
            "generalKnowledgeAllowed": allow_general,
            "previous": previous,
        }

    def _enqueue(
        self, uid, resource, version, context, fingerprint, idempotency, is_new
    ):
        reserve = len(
            (
                system_prompt(resource["kind"])
                + json.dumps(context, ensure_ascii=False)
            ).encode()
        ) + (14000 if resource["kind"] == "interactive" else 8500)

        def additions(job):
            number = len(self._versions(uid, resource["id"])) + 1
            rows = [
                (
                    "resourceVersions",
                    version["id"],
                    {**version, "number": number, "jobId": job["id"]},
                    None,
                )
            ]
            if is_new:
                rows.insert(0, ("resources", resource["id"], resource, None))
            return rows

        self.jobs.create(
            uid,
            "generate_resource",
            version["id"],
            {"context": context},
            hashlib.sha256(f"{resource['id']}:{idempotency}".encode()).hexdigest(),
            reserve=reserve,
            additions=additions,
        )
        return self.detail(uid, resource["id"])

    def _replay(self, uid, idempotency, fingerprint):
        for version in self.records.list(uid, "resourceVersions"):
            if version.get("idempotencyKey") == idempotency:
                if version["fingerprint"] != fingerprint:
                    raise DomainError(409, "La clave ya se usó con otra petición.")
                return self.detail(uid, version["resourceId"])
        return None

    def _version_row(self, resource_id, instruction, idempotency, fingerprint):
        return new_row(
            resourceId=resource_id,
            number=0,
            instruction=instruction,
            jobId=None,
            content=None,
            citations=[],
            textAlternative=None,
            model=None,
            promptVersion=PROMPT_VERSION,
            idempotencyKey=idempotency,
            fingerprint=fingerprint,
        )

    def create(self, uid, data, idempotency):
        data = ResourceInput.model_validate(data).model_dump(by_alias=True)
        fingerprint = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        replay = self._replay(uid, idempotency, fingerprint)
        if replay:
            return replay
        if not self.records.get(uid, "subjects", data["subjectId"]):
            raise DomainError(404, "No se encontró la materia.")
        if len(self.records.list(uid, "resources")) >= MAX_RESOURCES:
            raise DomainError(429, "Se alcanzó el límite de recursos del piloto.")
        instruction = data["instruction"].strip()
        context = self._context(
            uid,
            data["subjectId"],
            data["kind"],
            instruction,
            data["materialIds"],
            data["allowGeneral"],
            None,
        )
        title = data["title"].strip() or (
            instruction[:1].upper() + instruction[1:60]
            if instruction
            else KIND_LABELS[data["kind"]]
        )
        resource = new_row(
            subjectId=data["subjectId"],
            kind=data["kind"],
            title=title[:120],
            materialIds=data["materialIds"],
            archived=False,
        )
        version = self._version_row(
            resource["id"], instruction, idempotency, fingerprint
        )
        return self._enqueue(
            uid, resource, version, context, fingerprint, idempotency, True
        )

    def change(self, uid, key, data, idempotency):
        data = ResourceChange.model_validate(data).model_dump(by_alias=True)
        fingerprint = hashlib.sha256(
            json.dumps([key, data], sort_keys=True).encode()
        ).hexdigest()
        replay = self._replay(uid, idempotency, fingerprint)
        if replay:
            return replay
        resource = self._resource(uid, key)
        versions = self._versions(uid, key)
        if len(versions) >= MAX_VERSIONS:
            raise DomainError(429, "Se alcanzó el límite de versiones de este recurso.")
        public = [self._public_version(uid, v) for v in versions]
        if public and public[-1]["status"] in ("queued", "running", "cancel_requested"):
            raise DomainError(409, "Ya hay una versión generándose para este recurso.")
        ready = [v for v in public if v["status"] == "succeeded"]
        previous = (
            {
                "number": ready[-1]["number"],
                "content": json.dumps(ready[-1]["content"], ensure_ascii=False)[:8000],
            }
            if ready
            else None
        )
        context = self._context(
            uid,
            resource["subjectId"],
            resource["kind"],
            data["instruction"].strip(),
            resource["materialIds"],
            data["allowGeneral"],
            previous,
        )
        version = self._version_row(
            key, data["instruction"].strip(), idempotency, fingerprint
        )
        return self._enqueue(
            uid, resource, version, context, fingerprint, idempotency, False
        )

    def update(self, uid, key, data):
        data = ResourceUpdate.model_validate(data).model_dump(by_alias=True)
        row = self._resource(uid, key)
        if row["revision"] != data["expectedRevision"]:
            raise DomainError(409, "El recurso cambió. Recarga para continuar.")
        values = {
            name: data[name]
            for name in ("title", "archived")
            if data.get(name) is not None
        }
        self.records.save(
            uid, "resources", key, changed(row, **values), row["revision"]
        )
        return self.detail(uid, key)

    # --- worker --------------------------------------------------------------
    def _validate(self, kind, raw, context):
        if not isinstance(raw, dict):
            raise TypeError("La respuesta debe ser un objeto JSON.")
        raw = dict(raw)
        cites = raw.pop("citations", [])
        if not isinstance(cites, list):
            raise TypeError("citations debe ser una lista.")
        allowed = {b["sourceId"]: b for b in context["sources"]}
        citations = []
        for item in cites:
            citation = GeneratedCitation.model_validate(item)
            block = allowed.get(citation.source_id)
            if block is None or citation.quote not in block["text"]:
                raise ValueError(
                    f"Cita no verificable ({citation.source_id}): copia un extracto literal de esa fuente."
                )
            citations.append({**block["sourceRef"], "quote": citation.quote[:500]})
        if (
            context["sources"]
            and not citations
            and not context["generalKnowledgeAllowed"]
        ):
            raise ValueError("Incluye al menos una cita literal de las fuentes.")
        if kind == "interactive":
            package = InteractivePackageV1.model_validate(
                {
                    **raw,
                    "css": raw.get("css") or "",
                    "sourceRefs": citations,
                }
            )
            check_interactive(package)
            content = package.model_dump(by_alias=True)
            return content, citations, package.text_alternative
        parsed = CONTENT_MODELS[kind].model_validate(raw)
        content = parsed.model_dump(by_alias=True, exclude_none=True)
        if kind == "quiz":
            for question in parsed.questions:
                if question.correct_index >= len(question.options):
                    raise ValueError(
                        "correctIndex debe apuntar a una opción existente."
                    )
        return content, citations, None

    def run(self, job):
        uid, key, token = job["ownerId"], job["entityId"], job["leaseToken"]
        version = self.records.get(uid, "resourceVersions", key)
        resource = self._resource(uid, version["resourceId"])
        context = job["payload"]["context"]
        kind = resource["kind"]
        for block in context["sources"]:
            self.retrieval.citation(uid, block["sourceRef"])
        if self.provider is None:
            raise DomainError(503, "El tutor no está disponible por ahora.")
        self.jobs.mark_external_started(uid, job["id"], token)
        messages = [
            {"role": "system", "content": system_prompt(kind)},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ]
        total, result, last_error, draft = 0, None, "", ""
        for attempt in range(2):  # one bounded repair, never an autonomous loop
            try:
                raw, usage = self.provider.structured_answer(
                    messages,
                    on_progress=lambda: self.jobs.checkpoint(
                        uid, job["id"], token, "receiving", 60
                    ),
                    max_tokens=13000 if kind == "interactive" else 8000,
                )
            except ProviderFailure as failure:
                # A cut-off or unreadable answer is retried once, only when its cost is known.
                if (
                    attempt == 0
                    and failure.code in RETRYABLE_FAILURES
                    and isinstance(failure.usage, dict)
                    and "total_tokens" in failure.usage
                ):
                    total += int(failure.usage["total_tokens"])
                    self.jobs.observe_usage(
                        uid, job["id"], token, {"total_tokens": total}
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": "Tu respuesta anterior se cortó o no era JSON válido. Responde de nuevo con el JSON completo y más breve.",
                        }
                    )
                    self.jobs.checkpoint(uid, job["id"], token, "repairing", 80)
                    continue
                raise
            total += int(usage.get("total_tokens", 0))
            self.jobs.observe_usage(uid, job["id"], token, {"total_tokens": total})
            try:
                result = self._validate(kind, raw, context)
                break
            except (ValueError, TypeError, ValidationError) as error:
                last_error = str(error)[:700]
                draft = json.dumps(raw, ensure_ascii=False)[:20000]
                messages += [
                    {"role": "assistant", "content": draft[:6000]},
                    {
                        "role": "user",
                        "content": "El JSON no es válido: "
                        + last_error
                        + "\nDevuelve el JSON completo corregido, con las mismas reglas.",
                    },
                ]
                self.jobs.checkpoint(uid, job["id"], token, "repairing", 80)
        if result is None:
            # The invalid draft stays on the failed version; it never becomes current.
            self.records.save(
                uid,
                "resourceVersions",
                key,
                changed(version, failedDraft=draft, failureReason=last_error),
                version["revision"],
            )
            raise DomainError(
                422, "No pudimos preparar este recurso. Inténtalo de nuevo."
            )
        content, citations, alternative = result
        self.jobs.finish(
            uid,
            job["id"],
            token,
            "succeeded",
            {"versionId": key},
            additions=[
                (
                    "resourceVersions",
                    key,
                    changed(
                        version,
                        content=content,
                        citations=citations,
                        textAlternative=alternative,
                        model=getattr(self.provider, "model", "test"),
                    ),
                    version["revision"],
                )
            ],
            usage={"total_tokens": total},
        )
