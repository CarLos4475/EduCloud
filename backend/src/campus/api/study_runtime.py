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
from campus.services.academic import DomainError
from campus.services.jobs import JobService, changed
from campus.services.materials import MaterialService
from campus.services.retrieval import RetrievalService
from campus.services.tutoring import TutorService
from campus.services.uploads import UploadService


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
                raise DomainError(422, "Tipo de trabajo no admitido.")
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
            raise DomainError(409, "Solo se reintentan trabajos fallidos o cancelados.")
        if previous["usageUnknown"] and not accept_possible_charge:
            raise DomainError(
                409,
                "El consumo anterior es desconocido. Confirma un posible cargo adicional.",
            )
        collection = "turns" if previous["kind"] == "tutor_turn" else "materials"
        entity = self.records.get(uid, collection, previous["entityId"])
        if not entity:
            raise DomainError(404, "El recurso ya no está disponible.")
        if entity.get("jobId") != key:
            current = self.jobs.get(uid, entity["jobId"])
            if current["payload"].get("retryOf") == key:
                return current
            raise DomainError(
                409, "Ese trabajo fue reemplazado por una versión posterior."
            )
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
