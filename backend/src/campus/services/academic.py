from datetime import UTC, date, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from campus.adapters.records import Records, RevisionConflict

ILLUSTRATIONS = [
    {"id": key, "label": label, "symbol": symbol}
    for key, label, symbol in [
        ("grid", "Retícula", "▦"),
        ("wave", "Ondas", "∿"),
        ("orbit", "Órbitas", "◎"),
        ("geometry", "Geometría", "△"),
        ("terminal", "Terminal", ">_"),
        ("circuit", "Circuitos", "⌘"),
        ("blocks", "Bloques", "▧"),
        ("compass", "Brújula", "✧"),
        ("vector", "Vectores", "↗"),
        ("graph", "Gráficas", "⌁"),
        ("cube", "Volumen", "◇"),
        ("nodes", "Conexiones", "∴"),
    ]
]


class DomainError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class AcademicService:
    def __init__(self, records: Records):
        self.records = records

    def get(self, uid, collection, key):
        row = self.records.get(uid, collection, key)
        if not row:
            raise DomainError(404, "El recurso no existe o no está disponible.")
        return row

    def list(self, uid, collection):
        return sorted(self.records.list(uid, collection), key=lambda row: row["id"])

    def validate(self, uid, collection, row):
        for key in ("name", "title"):
            if key in row and (not isinstance(row[key], str) or not row[key].strip()):
                raise DomainError(422, "El nombre o título no puede estar vacío.")
        subject = row.get("subjectId")
        if subject:
            self.get(uid, "subjects", subject)
        if row.get("periodId"):
            self.get(uid, "periods", row["periodId"])
        if collection == "subjects" and row.get("illustrationId") not in {
            i["id"] for i in ILLUSTRATIONS
        }:
            raise DomainError(422, "Selecciona una ilustración del catálogo.")
        if collection == "topics":
            if not subject:
                raise DomainError(422, "El tema necesita una materia.")
            visited = set()

            def visit(key):
                if key == row["id"]:
                    raise DomainError(
                        422, "Los prerrequisitos no pueden formar ciclos."
                    )
                if key in visited:
                    return
                visited.add(key)
                topic = self.get(uid, "topics", key)
                if topic["subjectId"] != subject:
                    raise DomainError(422, "El prerrequisito pertenece a otra materia.")
                for prerequisite in topic.get("prerequisiteIds", []):
                    visit(prerequisite)

            for prerequisite in row.get("prerequisiteIds", []):
                visit(prerequisite)
        if collection == "agenda":
            if row.get("dueDate") and row.get("dueAt"):
                raise DomainError(
                    422, "Usa fecha de día completo o fecha y hora, no ambas."
                )
            if row.get("dueDate"):
                try:
                    date.fromisoformat(row["dueDate"])
                except ValueError:
                    raise DomainError(422, "La fecha no es válida.") from None
            if row.get("dueAt"):
                try:
                    value = datetime.fromisoformat(row["dueAt"])
                    if value.tzinfo is None:
                        raise ValueError()
                except ValueError:
                    raise DomainError(422, "La hora necesita zona horaria.") from None
        if collection == "schedule":
            if row.get("localStart", "") >= row.get("localEnd", ""):
                raise DomainError(422, "La hora final debe ser posterior a la inicial.")
            try:
                ZoneInfo(row.get("timezone", "America/Mexico_City"))
            except ZoneInfoNotFoundError:
                raise DomainError(422, "La zona horaria no es válida.") from None
        if (
            collection == "periods"
            and row.get("startDate")
            and row.get("endDate")
            and row["startDate"] > row["endDate"]
        ):
            raise DomainError(422, "El periodo termina antes de su inicio.")

    def create(self, uid, collection, data):
        return self.records.atomic(lambda: self._create(uid, collection, data))

    def _create(self, uid, collection, data):
        if len(self.list(uid, collection)) >= 200:
            raise DomainError(429, "Se alcanzó el límite de elementos del piloto.")
        now = datetime.now(UTC).isoformat()
        row = {
            **data,
            "id": uuid4().hex,
            "revision": 1,
            "createdAt": now,
            "updatedAt": now,
        }
        self.validate(uid, collection, row)
        self.records.save(uid, collection, row["id"], row, None)
        return row

    def update(self, uid, collection, key, changes, expected):
        return self.records.atomic(
            lambda: self._update(uid, collection, key, changes, expected)
        )

    def _update(self, uid, collection, key, changes, expected):
        row = {
            **self.get(uid, collection, key),
            **changes,
            "revision": expected + 1,
            "updatedAt": datetime.now(UTC).isoformat(),
        }
        self.validate(uid, collection, row)
        try:
            self.records.save(uid, collection, key, row, expected)
        except RevisionConflict:
            raise DomainError(
                409, "El elemento cambió en otra sesión. Recarga y vuelve a intentar."
            ) from None
        return row

    def delete(self, uid, collection, key):
        return self.records.atomic(lambda: self._delete(uid, collection, key))

    def _delete(self, uid, collection, key):
        self.get(uid, collection, key)
        if collection == "subjects":
            # Study data (materials, tutor, resources) is removed first by StudyRuntime.
            for name in ("topics", "agenda", "schedule"):
                for row in self.list(uid, name):
                    if row.get("subjectId") == key:
                        self.records.remove(uid, name, row["id"])
        if collection == "periods" and any(
            s.get("periodId") == key for s in self.list(uid, "subjects")
        ):
            raise DomainError(409, "El periodo tiene materias asociadas.")
        if collection == "topics" and any(
            key in t.get("prerequisiteIds", []) for t in self.list(uid, "topics")
        ):
            raise DomainError(409, "Hay temas que dependen de este tema.")
        self.records.remove(uid, collection, key)
