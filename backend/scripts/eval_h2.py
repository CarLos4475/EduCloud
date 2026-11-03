"""Opt-in live provider evaluation using only synthetic study material."""

import io
import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from campus.adapters.deepseek import DeepSeekProvider
from campus.adapters.objects import LocalObjects, digest
from campus.adapters.records import MemoryRecords
from campus.api.study_runtime import StudyRuntime
from campus.services.academic import AcademicService
from reportlab.pdfgen.canvas import Canvas


def main():
    started = time.monotonic()
    with TemporaryDirectory() as folder:
        state = StudyRuntime(
            MemoryRecords(),
            LocalObjects(folder),
            b"synthetic-evaluation-key",
            DeepSeekProvider(),
        )
        subject = AcademicService(state.records).create(
            "eval",
            "subjects",
            {"name": "Circuitos sintéticos", "illustrationId": "circuit"},
        )

        def upload(name, media, data):
            ticket = state.uploads.create(
                "eval",
                subject["id"],
                {
                    "name": name,
                    "mediaType": media,
                    "size": len(data),
                    "sha256": digest(data),
                },
            )
            receipt = state.uploads.put(
                "eval",
                ticket["uploadId"],
                ticket["requiredHeaders"]["X-Upload-Token"],
                data,
            )
            result = state.uploads.complete(
                "eval", ticket["uploadId"], receipt["generation"], name
            )
            state.run_job(result["job"])
            return state.materials.get("eval", ticket["materialId"]), state.jobs.get(
                "eval", result["job"]["id"]
            )

        pdf = io.BytesIO()
        canvas = Canvas(pdf)
        for i, line in enumerate(
            [
                "Ley de Ohm: V = I R.",
                "La resistencia R = 5 ohmios y la corriente I = 2 A.",
                "El voltaje es V = 10 V.",
            ]
        ):
            canvas.drawString(50, 780 - i * 30, line)
        canvas.save()
        material, _ingest = upload("Apunte PDF", "application/pdf", pdf.getvalue())
        assert material["status"] == "ready"
        image_path = (
            Path(__file__).resolve().parents[2] / "tests/fixtures/materials/ohm.png"
        )
        image, vision = upload("Apunte de imagen", "image/png", image_path.read_bytes())
        assert image["status"] == "needs_review"
        draft = state.materials.version("eval", image["id"])[0]["text"]
        assert all(value in draft for value in ["5", "2", "10"]), (
            "Synthetic OCR did not retain the three expected values"
        )
        conversation = state.tutor.create(
            "eval",
            {
                "subjectId": subject["id"],
                "personalityId": "socratic",
                "assistanceMode": "solution",
                "materialIds": [material["id"]],
            },
        )
        turn = state.tutor.send(
            "eval",
            conversation["id"],
            {
                "question": "Con I = 2 A y R = 5 ohmios, calcula el voltaje usando la ley de Ohm. Dame la solución completa y cita el apunte.",
                "allowGeneralForTurn": False,
            },
            "live-h2",
        )
        state.run_job(state.jobs.get("eval", turn["jobId"]))
        result = state.tutor.turn("eval", turn["id"])
        assert result["status"] == "succeeded", result.get("error")
        assert "10" in result["text"] and result["citations"]
        assert all(citation["locator"] == "page:1" for citation in result["citations"])
        report = {
            "provider": "DeepSeek real",
            "model": state.provider.model,
            "storage": "local synthetic fixture",
            "pdfStatus": material["status"],
            "imageStatus": image["status"],
            "imageDraft": draft,
            "visionUsage": vision.get("usage"),
            "turnStatus": result["status"],
            "answer": result["text"],
            "citations": result["citations"],
            "tutorUsage": result["usage"],
            "elapsedSeconds": round(time.monotonic() - started, 2),
        }
        output = Path(".superpowers/sdd/2026-11-02-plataforma-estudio/eval-h2")
        output.mkdir(parents=True, exist_ok=True)
        (output / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    k: report[k]
                    for k in (
                        "provider",
                        "model",
                        "pdfStatus",
                        "imageStatus",
                        "turnStatus",
                        "visionUsage",
                        "tutorUsage",
                        "elapsedSeconds",
                    )
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
