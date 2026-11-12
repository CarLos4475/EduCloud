"""Practice attempts, flashcard reviews, experiment state, progress and passport stamps."""

import json

from campus.domain.practice import AttemptInput, ReviewInput, StateInput
from campus.services.academic import DomainError
from campus.services.jobs import changed, new_row

MAX_ATTEMPTS = 500
MAX_STATE_BYTES = 50 * 1024
STAMPS = [
    ("first_material", "Primeros apuntes", "Subiste tu primer material y quedó listo."),
    ("first_question", "Primera pregunta", "Le preguntaste algo a tu tutor."),
    ("first_resource", "Primer recurso", "Creaste tu primer recurso de estudio."),
    ("explorer", "Explorador", "Creaste un experimento interactivo."),
    ("first_quiz", "Primer cuestionario", "Contestaste tu primer cuestionario."),
    ("perfect_quiz", "Cuestionario perfecto", "Acertaste todas las preguntas."),
    ("cards_ten", "Tarjetas al día", "Marcaste 10 tarjetas como sabidas."),
    ("three_subjects", "Tres materias", "Tienes tres materias en tu espacio."),
]


class PracticeService:
    def __init__(self, records, resources):
        self.records, self.resources = records, resources

    # --- helpers -------------------------------------------------------------
    def _version(self, uid, version_id, kind=None, ready=True):
        version = self.resources.version(uid, version_id)
        resource = self.resources._resource(uid, version["resourceId"])
        if kind and resource["kind"] != kind:
            raise DomainError(422, "Esta acción no aplica a este tipo de recurso.")
        if ready and (version["status"] != "succeeded" or not version["content"]):
            raise DomainError(409, "Este recurso todavía no está listo.")
        return version, resource

    # --- practice ------------------------------------------------------------
    def attempt(self, uid, version_id, data):
        data = AttemptInput.model_validate(data).model_dump(by_alias=True)
        version, resource = self._version(uid, version_id, "quiz")
        questions = version["content"]["questions"]
        answers = data["answers"]
        if len(answers) != len(questions):
            raise DomainError(422, "Responde todas las preguntas antes de enviar.")
        results = []
        for question, picked in zip(questions, answers, strict=True):
            if picked is not None and not 0 <= picked < len(question["options"]):
                raise DomainError(422, "Una de las respuestas no es válida.")
            results.append(
                {
                    "picked": picked,
                    "correctIndex": question["correctIndex"],
                    "correct": picked == question["correctIndex"],
                }
            )
        if len(self.records.list(uid, "attempts")) >= MAX_ATTEMPTS:
            raise DomainError(429, "Llegaste al límite de intentos guardados.")
        row = new_row(
            resourceId=resource["id"],
            subjectId=resource["subjectId"],
            versionId=version_id,
            score=sum(r["correct"] for r in results),
            total=len(results),
            results=results,
        )
        self.records.save(uid, "attempts", row["id"], row, None)
        return row

    def get_review(self, uid, version_id):
        self._version(uid, version_id, "flashcards")
        return self.records.get(uid, "reviews", version_id) or {
            "versionId": version_id,
            "revision": 0,
            "cards": {},
        }

    def put_review(self, uid, version_id, data):
        data = ReviewInput.model_validate(data).model_dump(by_alias=True)
        version, resource = self._version(uid, version_id, "flashcards")
        count = len(version["content"]["cards"])
        if any(int(key) >= count for key in data["cards"]):
            raise DomainError(422, "Una de las tarjetas no existe.")
        current = self.records.get(uid, "reviews", version_id)
        row = (
            changed(current, cards=data["cards"])
            if current
            else new_row(
                id=version_id,
                versionId=version_id,
                resourceId=resource["id"],
                subjectId=resource["subjectId"],
                cards=data["cards"],
            )
        )
        self.records.save(
            uid, "reviews", version_id, row, current["revision"] if current else None
        )
        return row

    # --- experiment state ----------------------------------------------------
    def get_state(self, uid, version_id):
        self._version(uid, version_id, "interactive")
        return self.records.get(uid, "resourceStates", version_id) or {
            "versionId": version_id,
            "revision": 0,
            "state": {},
        }

    def put_state(self, uid, version_id, data):
        data = StateInput.model_validate(data).model_dump(by_alias=True)
        self._version(uid, version_id, "interactive")
        if len(json.dumps(data["state"]).encode()) > MAX_STATE_BYTES:
            raise DomainError(413, "El avance es demasiado grande para guardarlo.")
        current = self.records.get(uid, "resourceStates", version_id)
        expected = data.get("expectedRevision")
        if expected is not None and (current["revision"] if current else 0) != expected:
            raise DomainError(409, "Este experimento cambió en otra pestaña.")
        row = (
            changed(current, state=data["state"])
            if current
            else new_row(id=version_id, versionId=version_id, state=data["state"])
        )
        self.records.save(
            uid,
            "resourceStates",
            version_id,
            row,
            current["revision"] if current else None,
        )
        return row

    def delete_state(self, uid, version_id):
        self._version(uid, version_id, "interactive")
        self.records.remove(uid, "resourceStates", version_id)

    # --- progress ------------------------------------------------------------
    def progress(self, uid, subject_id):
        resources = self.resources.list(uid, subject_id)  # also checks ownership
        ready = [r for r in resources if r["currentVersionId"]]
        materials = [
            m
            for m in self.records.list(uid, "materials")
            if m["subjectId"] == subject_id and m["status"] in ("ready", "partial")
        ]
        attempts = sorted(
            (
                a
                for a in self.records.list(uid, "attempts")
                if a["subjectId"] == subject_id
            ),
            key=lambda a: a["createdAt"],
        )
        percentages = [round(100 * a["score"] / a["total"]) for a in attempts]
        recent = percentages[-5:]
        reviews = [
            r for r in self.records.list(uid, "reviews") if r["subjectId"] == subject_id
        ]
        known = sum(v == "known" for r in reviews for v in r["cards"].values())
        again = [(r, sum(v == "again" for v in r["cards"].values())) for r in reviews]
        to_review = sum(n for _, n in again)
        quiz = next((r for r in ready if r["kind"] == "quiz"), None)
        tips = []
        if not materials:
            tips.append({"text": "Sube tus primeros apuntes para empezar."})
        elif not ready:
            tips.append(
                {
                    "text": "Crea un resumen de tus apuntes para tener un punto de partida."
                }
            )
        if to_review:
            target = max(again, key=lambda pair: pair[1])[0]
            tips.append(
                {
                    "text": f"Tienes {to_review} tarjetas por repasar.",
                    "resourceId": target["resourceId"],
                }
            )
        if ready and not quiz:
            tips.append({"text": "Crea un cuestionario para ver qué tanto dominas."})
        if quiz and not attempts:
            tips.append(
                {
                    "text": "Prueba el cuestionario para ver cómo vas.",
                    "resourceId": quiz["id"],
                }
            )
        if recent and sum(recent) / len(recent) < 70:
            tips.append(
                {
                    "text": "Repasa tu resumen o tus tarjetas y vuelve a intentar el cuestionario."
                }
            )
        if recent and sum(recent) / len(recent) >= 85 and not to_review:
            tips.append(
                {"text": "¡Vas muy bien! Sube más apuntes o prueba un experimento."}
            )
        return {
            "subjectId": subject_id,
            "materialsReady": len(materials),
            "resourcesReady": len(ready),
            "quizAttempts": len(attempts),
            "averageScore": round(sum(recent) / len(recent)) if recent else None,
            "lastScore": percentages[-1] if percentages else None,
            "cardsKnown": known,
            "cardsToReview": to_review,
            "recommendations": tips[:3],
        }

    # --- passport ------------------------------------------------------------
    def passport(self, uid):
        def first(rows):
            dates = sorted(r["createdAt"] for r in rows)
            return dates[0] if dates else None

        ready_kinds = {}
        for version in self.records.list(uid, "resourceVersions"):
            public = self.resources._public_version(uid, version)
            if public["status"] == "succeeded":
                resource = self.records.get(uid, "resources", version["resourceId"])
                if resource:
                    ready_kinds.setdefault(resource["kind"], []).append(version)
        attempts = self.records.list(uid, "attempts")
        cards = [
            r
            for r in self.records.list(uid, "reviews")
            if sum(v == "known" for v in r["cards"].values())
        ]
        known_total = sum(sum(v == "known" for v in r["cards"].values()) for r in cards)
        subjects = [
            s for s in self.records.list(uid, "subjects") if not s.get("archived")
        ]
        evidence = {
            "first_material": first(
                [
                    m
                    for m in self.records.list(uid, "materials")
                    if m["status"] in ("ready", "partial")
                ]
            ),
            "first_question": first(
                [t for t in self.records.list(uid, "turns") if t.get("text")]
            ),
            "first_resource": first([v for rows in ready_kinds.values() for v in rows]),
            "explorer": first(ready_kinds.get("interactive", [])),
            "first_quiz": first(attempts),
            "perfect_quiz": first([a for a in attempts if a["score"] == a["total"]]),
            "cards_ten": first(cards) if known_total >= 10 else None,
            "three_subjects": first(subjects) if len(subjects) >= 3 else None,
        }
        stamps = [
            {
                "id": key,
                "title": title,
                "description": text,
                "earned": evidence[key] is not None,
                "earnedAt": evidence[key],
            }
            for key, title, text in STAMPS
        ]
        return {
            "earned": sum(s["earned"] for s in stamps),
            "total": len(stamps),
            "stamps": stamps,
        }
