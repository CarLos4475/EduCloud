"""Private immutable object store; local development never serves its directory."""

import hashlib
import re
from pathlib import Path

from campus.services.academic import DomainError


def digest(content):
    return hashlib.sha256(content).hexdigest()


class LocalObjects:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, key):
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*", key) or ".." in key:
            raise ValueError("Invalid internal object key")
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Invalid object path")
        return path

    def put(self, key, content, media_type="application/json"):
        if len(content) > 20 * 1024 * 1024:
            raise DomainError(413, "El archivo excede 20 MiB.")
        path = self.path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as output:
                output.write(content)
        except FileExistsError:
            if path.read_bytes() != content:
                raise DomainError(
                    409, "El objeto ya existe con otra versión."
                ) from None
        return {
            "generation": digest(content),
            "sha256": digest(content),
            "size": len(content),
        }

    def get(self, key, generation=None):
        try:
            content = self.path(key).read_bytes()
        except FileNotFoundError:
            raise DomainError(404, "No se encontró el archivo privado.") from None
        if generation and digest(content) != generation:
            raise DomainError(409, "La versión del archivo cambió.")
        return content

    def delete(self, key, generation=None):
        self.get(key, generation)
        self.path(key).unlink(missing_ok=True)
