"""Opt-in live evaluation of the tutor and the generated resources with an own synthetic corpus.

Measures what a student would notice: does the answer use the notes, are citations real,
does the tutor admit when the notes do not cover a question, and do all five resource
kinds come out valid (and how often they needed a repair). Not an academic certification.
"""

import json
import os
import time
import unicodedata
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("CAMPUS_DAILY_TOKEN_BUDGET", "5000000")

from campus.adapters.deepseek import DeepSeekProvider
from campus.adapters.objects import LocalObjects, digest
from campus.adapters.records import MemoryRecords
from campus.api.study_runtime import StudyRuntime
from campus.services.academic import AcademicService

UID = "eval"
CORPORA = {
    "Circuitos": (
        "Ley de Ohm: V = I R. El voltaje V se mide en voltios, la corriente I en amperios "
        "y la resistencia R en ohmios. Si el voltaje es fijo y la resistencia aumenta, la "
        "corriente disminuye. La potencia disipada en una resistencia es P = V I = I^2 R. "
        "Ejemplo: con R = 5 ohmios e I = 2 A, el voltaje es V = 10 V y la potencia es P = 20 W."
    ),
    "Cálculo": (
        "Regla de la potencia: la derivada de x^n es n x^(n-1). Regla del producto: "
        "(f g)' = f' g + f g'. Regla de la cadena: (f(g(x)))' = f'(g(x)) g'(x). "
        "Ejemplo: la derivada de x^3 es 3 x^2. La derivada de una constante es cero. "
        "Un punto crítico ocurre donde la derivada vale cero o no existe."
    ),
}
# (corpus, pregunta, palabras de las que al menos una debe aparecer en la respuesta)
IN_SCOPE = [
    (
        "Circuitos",
        "Si el voltaje es fijo y aumento la resistencia, ¿qué pasa con la corriente?",
        ["disminuy", "baja", "menor"],
    ),
    ("Circuitos", "¿Cuánto vale el voltaje si R = 5 ohmios e I = 2 A?", ["10"]),
    ("Cálculo", "¿Cuál es la derivada de x^3?", ["3x", "3 x", "3x^2", "3x²"]),
    (
        "Cálculo",
        "¿Cómo se deriva un producto de dos funciones?",
        ["f' g", "f'g", "producto"],
    ),
]
# Preguntas cercanas al tema que los apuntes NO cubren: debe reconocer el límite.
OUT_OF_SCOPE = [
    ("Circuitos", "¿Qué dice la ley de Kirchhoff de las mallas?"),
    ("Cálculo", "¿Cómo se calcula una integral por partes?"),
]


def plain(text):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text.lower())
        if unicodedata.category(c) != "Mn"
    )


class Counting:
    """Counts provider calls so repairs and retries show up in the report."""

    def __init__(self, inner):
        self.inner, self.calls, self.model = inner, 0, inner.model

    def structured_answer(self, *args, **kwargs):
        self.calls += 1
        return self.inner.structured_answer(*args, **kwargs)

    def tutor_answer(self, *args, **kwargs):
        return self.inner.tutor_answer(*args, **kwargs)


def sanity(kind, content):
    """Cheap, kind-specific checks of the generated content."""
    if kind == "summary":
        return len(content["sections"]) >= 2 and len(content["overview"]) > 40
    if kind == "concepts":
        return len(content["concepts"]) >= 4
    if kind == "flashcards":
        return len(content["cards"]) >= 6
    if kind == "quiz":
        return (
            all(
                len(set(q["options"])) == len(q["options"])
                and 0 <= q["correctIndex"] < len(q["options"])
                for q in content["questions"]
            )
            and len(content["questions"]) >= 4
        )
    return (
        bool(content["html"])
        and bool(content["javascript"])
        and bool(content["textAlternative"])
    )


def main():
    started = time.monotonic()
    with TemporaryDirectory() as folder:
        provider = Counting(DeepSeekProvider())
        state = StudyRuntime(
            MemoryRecords(), LocalObjects(folder), b"synthetic-evaluation-key", provider
        )
        academic = AcademicService(state.records)
        subjects, materials = {}, {}
        for name, text in CORPORA.items():
            subjects[name] = academic.create(
                UID, "subjects", {"name": name, "illustrationId": "circuit"}
            )
            data = text.encode()
            ticket = state.uploads.create(
                UID,
                subjects[name]["id"],
                {
                    "name": name,
                    "mediaType": "text/plain",
                    "size": len(data),
                    "sha256": digest(data),
                },
            )
            receipt = state.uploads.put(
                UID,
                ticket["uploadId"],
                ticket["requiredHeaders"]["X-Upload-Token"],
                data,
            )
            done = state.uploads.complete(
                UID, ticket["uploadId"], receipt["generation"], name
            )
            state.run_job(done["job"])
            materials[name] = ticket["materialId"]
            assert state.materials.get(UID, materials[name])["status"] == "ready"

        chats = {
            name: state.tutor.create(
                UID,
                {
                    "subjectId": subjects[name]["id"],
                    "title": "Evaluación",
                    "personalityId": "direct",
                    "assistanceMode": "explain",
                    "materialIds": [materials[name]],
                    "sourceMode": "selected_material",
                    "preferences": "",
                },
            )
            for name in CORPORA
        }

        def ask(corpus, question, number):
            turn = state.tutor.send(
                UID,
                chats[corpus]["id"],
                {"question": question, "allowGeneralForTurn": False},
                f"eval-{number}",
            )
            state.run_job(state.jobs.get(UID, turn["jobId"]))
            return state.tutor.turn(UID, turn["id"])

        tutor = []
        for i, (corpus, question, keywords) in enumerate(IN_SCOPE):
            turn = ask(corpus, question, i)
            text = plain(turn["text"])
            tutor.append(
                {
                    "kind": "con_apuntes",
                    "question": question,
                    "status": turn["status"],
                    "cited": len(turn["citations"]) > 0,
                    "answered": any(plain(k) in text for k in keywords),
                    "admitsLimit": turn["needsConsent"],
                }
            )
        for i, (corpus, question) in enumerate(OUT_OF_SCOPE, start=len(IN_SCOPE)):
            turn = ask(corpus, question, i)
            tutor.append(
                {
                    "kind": "fuera_de_apuntes",
                    "question": question,
                    "status": turn["status"],
                    "cited": len(turn["citations"]) > 0,
                    # Correct behaviour: ask for consent instead of inventing support.
                    "admitsLimit": bool(turn["needsConsent"]),
                }
            )

        resources = []
        for corpus in CORPORA:
            for kind in ("summary", "concepts", "flashcards", "quiz", "interactive"):
                before = provider.calls
                begun = time.monotonic()
                detail = state.resources.create(
                    UID,
                    {
                        "subjectId": subjects[corpus]["id"],
                        "kind": kind,
                        "instruction": "",
                        "materialIds": [materials[corpus]],
                    },
                    f"res-{corpus}-{kind}",
                )
                try:
                    state.run_job(state.jobs.get(UID, detail["versions"][0]["jobId"]))
                except Exception as error:  # noqa: BLE001 - the report must record any failure
                    resources.append(
                        {
                            "corpus": corpus,
                            "kind": kind,
                            "ok": False,
                            "error": str(error)[:120],
                        }
                    )
                    continue
                version = state.resources.detail(UID, detail["id"])["versions"][0]
                ok = version["status"] == "succeeded"
                resources.append(
                    {
                        "corpus": corpus,
                        "kind": kind,
                        "ok": ok,
                        "providerCalls": provider.calls - before,
                        "citations": len(version["citations"]) if ok else 0,
                        "sane": bool(ok and sanity(kind, version["content"])),
                        "seconds": round(time.monotonic() - begun, 1),
                    }
                )

    with_notes = [t for t in tutor if t["kind"] == "con_apuntes"]
    outside = [t for t in tutor if t["kind"] == "fuera_de_apuntes"]
    summary = {
        "tutorWithNotes": {
            "cases": len(with_notes),
            "succeeded": sum(t["status"] == "succeeded" for t in with_notes),
            "cited": sum(t["cited"] for t in with_notes),
            "answeredCorrectly": sum(t["answered"] for t in with_notes),
        },
        "tutorOutsideNotes": {
            "cases": len(outside),
            "admittedTheLimit": sum(t["admitsLimit"] for t in outside),
            "inventedCitations": sum(
                t["cited"] and not t["admitsLimit"] for t in outside
            ),
        },
        "resources": {
            "cases": len(resources),
            "valid": sum(r["ok"] for r in resources),
            "sane": sum(r.get("sane", False) for r in resources),
            "withCitations": sum(r.get("citations", 0) > 0 for r in resources),
            "neededRepair": sum(r.get("providerCalls", 1) > 1 for r in resources),
        },
        "model": provider.model,
        "elapsedSeconds": round(time.monotonic() - started, 1),
    }
    report = {"summary": summary, "tutor": tutor, "resources": resources}
    target = (
        Path(__file__).resolve().parents[2]
        / ".superpowers/sdd/2026-11-02-plataforma-estudio/eval-h3/report.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    print(f"Informe completo: {target}")


if __name__ == "__main__":
    main()
