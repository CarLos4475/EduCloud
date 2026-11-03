from google.api_core.exceptions import NotFound, PreconditionFailed
from google.cloud.storage import Client

from campus.adapters.objects import digest
from campus.adapters.operator_credentials import local_operator_credentials
from campus.services.academic import DomainError


class GCSObjects:
    def __init__(self, project, bucket):
        self.bucket = Client(
            project=project, credentials=local_operator_credentials(project)
        ).bucket(bucket)
        self.bucket.reload()
        if (
            not self.bucket.iam_configuration.uniform_bucket_level_access_enabled
            or self.bucket.iam_configuration.public_access_prevention != "enforced"
        ):
            raise ValueError(
                "Cloud Storage requires uniform access and public access prevention."
            )

    def put(self, key, content, media_type="application/json"):
        blob = self.bucket.blob(key)
        try:
            blob.upload_from_string(
                content, content_type=media_type, if_generation_match=0, timeout=60
            )
        except PreconditionFailed:
            if self.get(key) != content:
                raise DomainError(
                    409, "El objeto ya existe con otra versión."
                ) from None
        blob.reload()
        return {
            "generation": str(blob.generation),
            "sha256": digest(content),
            "size": len(content),
        }

    def get(self, key, generation=None):
        blob = self.bucket.blob(key, generation=int(generation) if generation else None)
        try:
            return blob.download_as_bytes(
                if_generation_match=int(generation) if generation else None, timeout=60
            )
        except (NotFound, PreconditionFailed):
            raise DomainError(
                404, "No se encontró esa versión del archivo privado."
            ) from None

    def delete(self, key, generation=None):
        try:
            self.bucket.blob(key).delete(
                if_generation_match=int(generation) if generation else None, timeout=60
            )
        except NotFound:
            raise DomainError(404, "No se encontró el archivo privado.") from None
