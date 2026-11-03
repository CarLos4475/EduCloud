import io
from pathlib import Path

from campus.adapters.objects import digest
from campus.adapters.testing import TestStudyProvider
from campus.api.study_runtime import StudyRuntime
from pptx import Presentation
from reportlab.pdfgen.canvas import Canvas
from test_materials import setup_study


def run_file(state, subject, name, media, data):
    ticket = state.uploads.create(
        "alice",
        subject["id"],
        {"name": name, "mediaType": media, "size": len(data), "sha256": digest(data)},
    )
    receipt = state.uploads.put(
        "alice", ticket["uploadId"], ticket["requiredHeaders"]["X-Upload-Token"], data
    )
    accepted = state.uploads.complete(
        "alice", ticket["uploadId"], receipt["generation"], name
    )
    state.run_job(accepted["job"])
    return state.materials.get("alice", ticket["materialId"]), state.jobs.get(
        "alice", accepted["job"]["id"]
    )


def test_pdf_pptx_image_and_corrupt_pdf_states(tmp_path):
    records, subject, _jobs, objects, _materials, _uploads = setup_study(tmp_path)
    state = StudyRuntime(records, objects, b"synthetic-key", TestStudyProvider())
    pdf = io.BytesIO()
    canvas = Canvas(pdf)
    canvas.drawString(50, 760, "Primera pagina: energia E = m c2")
    canvas.showPage()
    canvas.drawString(50, 760, "Segunda pagina: resistencia R")
    canvas.save()
    material, job = run_file(
        state, subject, "two-pages", "application/pdf", pdf.getvalue()
    )
    assert material["status"] == "ready" and job["status"] == "succeeded"
    assert [b["locator"] for b in state.materials.version("alice", material["id"])] == [
        "page:1",
        "page:2",
    ]
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    slide.shapes.add_textbox(0, 0, 1000000, 1000000).text = "Matrices y determinantes"
    pptx = io.BytesIO()
    presentation.save(pptx)
    material, _job = run_file(
        state,
        subject,
        "slides",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        pptx.getvalue(),
    )
    assert state.materials.version("alice", material["id"])[0]["locator"] == "slide:1"
    path = Path(__file__).resolve().parents[3] / "tests/fixtures/materials/ohm.png"
    image, job = run_file(state, subject, "image", "image/png", path.read_bytes())
    assert image["status"] == "needs_review" and job["status"] == "needs_review"
    assert (
        state.retrieval.search("alice", subject["id"], "resistencia", [image["id"]])
        == []
    )
    revised = state.materials.revise(
        "alice",
        image["id"],
        image["revision"],
        [{"blockId": "block-1", "text": "Resistencia R = 5 ohmios."}],
        [],
    )
    assert revised["status"] == "ready" and revised["jobId"] != job["id"]
    version_record = records.get(
        "alice", "materialVersions", f"{image['id']}_{revised['extractionVersion']}"
    )
    objects.delete(version_record["indexKey"])
    state.run_job(state.jobs.get("alice", revised["jobId"]))
    assert state.jobs.get("alice", revised["jobId"])["status"] == "succeeded"
    broken, job = run_file(
        state, subject, "broken", "application/pdf", b"%PDF-1.7\nnot a PDF"
    )
    assert broken["status"] == "failed" and job["status"] == "failed"
    retried = state.retry("alice", job["id"])
    assert state.retry("alice", job["id"])["id"] == retried["id"]
    assert retried["payload"]["version"] != job["payload"]["version"]


def test_partial_page_failure_preserves_good_pages_and_can_be_corrected(
    tmp_path, monkeypatch
):
    import campus.services.materials as module

    records, subject, _jobs, objects, _materials, _uploads = setup_study(tmp_path)
    state = StudyRuntime(records, objects, b"synthetic-key", None)
    pdf = io.BytesIO()
    canvas = Canvas(pdf)
    canvas.drawString(50, 760, "Energia y movimiento")
    canvas.showPage()
    canvas.drawString(50, 760, "Resistencia")
    canvas.save()
    original = module.extract_material
    counter = [0]

    def fail_second(*args, **kwargs):
        counter[0] += 1
        if counter[0] == 2:
            raise ValueError("synthetic page failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "extract_material", fail_second)
    material, _job = run_file(
        state, subject, "partial", "application/pdf", pdf.getvalue()
    )
    assert material["status"] == "partial" and material["failedPages"] == 1
    assert state.retrieval.search("alice", subject["id"], "energia", [material["id"]])
    assert not state.retrieval.search(
        "alice", subject["id"], "resistencia", [material["id"]]
    )
    corrected = state.materials.revise(
        "alice",
        material["id"],
        material["revision"],
        [{"blockId": "block-2", "text": "La resistencia limita la corriente."}],
        [],
    )
    assert corrected["status"] == "ready"
    assert (
        state.materials.version("alice", material["id"], material["extractionVersion"])[
            1
        ]["status"]
        == "failed"
    )


def test_cancelled_material_leaves_queue_and_can_retry(tmp_path):
    from test_materials import upload_note

    records, subject, _jobs, objects, _materials, _uploads = setup_study(tmp_path)
    state = StudyRuntime(records, objects, b"synthetic-key", None)
    ticket, result = upload_note(state.uploads, subject)
    state.cancel("alice", result["job"]["id"])
    assert state.materials.get("alice", ticket["materialId"])["status"] == "failed"
    retried = state.retry("alice", result["job"]["id"])
    state.run_job(retried)
    assert state.materials.get("alice", ticket["materialId"])["status"] == "ready"
