import hashlib
import hmac
import io
import zipfile
from datetime import timedelta

from PIL import Image

from campus.adapters.objects import digest
from campus.services.academic import DomainError
from campus.services.jobs import changed, new_row, now

FORMATS = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/markdown",
    "image/png",
    "image/jpeg",
    "image/webp",
}


def validate_bytes(content, media_type):
    if media_type == "application/pdf":
        if not content.startswith(b"%PDF-"):
            raise DomainError(422, "El archivo no contiene un PDF válido.")
    elif media_type.endswith("presentationml.presentation"):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if (
                    "ppt/presentation.xml" not in archive.namelist()
                    or sum(item.file_size for item in archive.infolist())
                    > 100 * 1024 * 1024
                ):
                    raise ValueError()
        except (ValueError, zipfile.BadZipFile):
            raise DomainError(
                422, "El archivo no es válido o es demasiado grande."
            ) from None
    elif media_type.startswith("image/"):
        try:
            with Image.open(io.BytesIO(content)) as image:
                if (
                    Image.MIME.get(image.format) != media_type
                    or image.width * image.height > 30_000_000
                ):
                    raise ValueError()
                image.verify()
        except (ValueError, OSError, Image.DecompressionBombError):
            raise DomainError(
                422, "La imagen no coincide con el formato declarado."
            ) from None
    else:
        try:
            if b"\0" in content:
                raise ValueError()
            content.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            raise DomainError(422, "La nota debe ser texto UTF-8.") from None


class UploadService:
    # SECURITY-DEBT:
    # What is unsafe: original-byte quota excludes immutable derivatives and orphan checkpoints.
    # Why temporarily accepted: closed local pilot, bounded files; GCS and public deployment are not enabled.
    # Before production: reserve all object bytes and reconcile/delete unreferenced staged versions.
    # Where the real fix belongs: upload/material quota ledger and H6 object-cleanup jobs.
    def __init__(self, records, objects, jobs, secret, clock=now):
        self.records, self.objects, self.jobs, self.secret, self.clock = (
            records,
            objects,
            jobs,
            secret,
            clock,
        )

    def get(self, uid, key):
        row = self.records.get(uid, "uploads", key)
        if not row:
            raise DomainError(404, "No se encontró la carga.")
        return row

    def signature(self, uid, row):
        return hmac.new(
            self.secret,
            f"{uid}:{row['id']}:{row['expiresAt']}".encode(),
            hashlib.sha256,
        ).hexdigest()

    def create(self, uid, subject_id, data):
        self.cleanup_expired(uid)

        def operation():
            if not self.records.get(uid, "subjects", subject_id):
                raise DomainError(404, "No se encontró la materia.")
            media = data["mediaType"]
            maximum = (10 if media.startswith("image/") else 20) * 1024 * 1024
            if media not in FORMATS or not 0 < data["size"] <= maximum:
                raise DomainError(
                    413, "Formato o tamaño fuera de los límites del piloto."
                )
            materials = self.records.list(uid, "materials")
            active = [
                m
                for m in materials
                if m["status"] == "uploading"
                and m.get("expiresAt", "") > self.clock().isoformat()
            ]
            if (
                len(materials) >= 200
                or len(active) >= 2
                or sum(m["size"] for m in materials if m["status"] != "deleted")
                + data["size"]
                > 500 * 1024 * 1024
            ):
                raise DomainError(
                    429,
                    "Llegaste al límite de espacio o de archivos subiéndose a la vez.",
                )
            material = new_row(
                **data,
                subjectId=subject_id,
                status="uploading",
                extractionVersion=None,
                expiresAt=(self.clock() + timedelta(minutes=10)).isoformat(),
                topicIds=[],
            )
            key = f"private/{uid}/materials/{material['id']}/original"
            ticket = new_row(
                materialId=material["id"],
                objectKey=key,
                expiresAt=material["expiresAt"],
                size=data["size"],
                mediaType=media,
                sha256=data["sha256"],
                completed=False,
            )
            self.records.save_many(
                uid,
                [
                    ("materials", material["id"], material, None),
                    ("uploads", ticket["id"], ticket, None),
                ],
            )
            return {
                "uploadId": ticket["id"],
                "materialId": material["id"],
                "signedUrl": f"/uploads/{ticket['id']}/content",
                "requiredHeaders": {"X-Upload-Token": self.signature(uid, ticket)},
                "expiresAt": ticket["expiresAt"],
            }

        return self.records.atomic(operation)

    def put(self, uid, key, token, content):
        row = self.get(uid, key)
        if not hmac.compare_digest(token, self.signature(uid, row)):
            raise DomainError(403, "El ticket de carga no es válido.")
        if row["expiresAt"] <= self.clock().isoformat() or row["completed"]:
            raise DomainError(409, "El ticket caducó o ya se completó.")
        if len(content) != row["size"] or digest(content) != row["sha256"]:
            raise DomainError(422, "El tamaño o hash no coincide con el ticket.")
        validate_bytes(content, row["mediaType"])
        return self.objects.put(row["objectKey"], content, row["mediaType"])

    def complete(self, uid, key, generation, idempotency):
        ticket = self.get(uid, key)
        material = self.records.get(uid, "materials", ticket["materialId"])
        if ticket["completed"]:
            if not ticket.get("jobId"):
                raise DomainError(409, "El ticket caducó y fue retirado.")
            return {"material": material, "job": self.jobs.get(uid, ticket["jobId"])}
        if ticket["expiresAt"] <= self.clock().isoformat():
            raise DomainError(409, "El ticket caducó. Vuelve a cargar el archivo.")
        content = self.objects.get(ticket["objectKey"], generation)
        if len(content) != ticket["size"] or digest(content) != ticket["sha256"]:
            raise DomainError(422, "El objeto no coincide con el ticket.")
        version = hashlib.sha256(f"{uid}:{key}:{generation}".encode()).hexdigest()[:32]

        def additions(job):
            return [
                (
                    "uploads",
                    key,
                    changed(ticket, completed=True, jobId=job["id"]),
                    ticket["revision"],
                ),
                (
                    "materials",
                    material["id"],
                    changed(
                        material,
                        status="queued",
                        jobId=job["id"],
                        objectKey=ticket["objectKey"],
                        generation=generation,
                    ),
                    material["revision"],
                ),
            ]

        job = self.jobs.create(
            uid,
            "ingest",
            material["id"],
            {"version": version},
            idempotency,
            reserve=60000
            if ticket["mediaType"].startswith("image/")
            or ticket["mediaType"] == "application/pdf"
            else 0,
            additions=additions,
        )
        return {
            "material": self.records.get(uid, "materials", material["id"]),
            "job": job,
        }

    def cleanup_expired(self, uid):
        count = 0
        for ticket in self.records.list(uid, "uploads"):
            if ticket["completed"] or ticket["expiresAt"] > self.clock().isoformat():
                continue
            material = self.records.get(uid, "materials", ticket["materialId"])
            if material and material["status"] == "uploading":
                self.records.save_many(
                    uid,
                    [
                        (
                            "uploads",
                            ticket["id"],
                            changed(ticket, completed=True, expired=True),
                            ticket["revision"],
                        ),
                        (
                            "materials",
                            material["id"],
                            changed(
                                material,
                                status="failed",
                                size=0,
                                error="upload_expired",
                            ),
                            material["revision"],
                        ),
                    ],
                )
                try:
                    self.objects.delete(ticket["objectKey"])
                except DomainError as missing:
                    if missing.status != 404:
                        raise
                count += 1
        return count
