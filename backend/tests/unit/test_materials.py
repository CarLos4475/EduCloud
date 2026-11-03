import hashlib

import pytest
from campus.adapters.records import MemoryRecords
from campus.services.academic import AcademicService, DomainError


def setup_study(tmp_path):
    from campus.adapters.objects import LocalObjects
    from campus.services.jobs import JobService
    from campus.services.materials import MaterialService
    from campus.services.uploads import UploadService

    records = MemoryRecords()
    subject = AcademicService(records).create(
        "alice", "subjects", {"name": "Física", "illustrationId": "wave"}
    )
    jobs = JobService(records)
    objects = LocalObjects(tmp_path)
    materials = MaterialService(records, objects, jobs)
    uploads = UploadService(records, objects, jobs, b"test-signature-only")
    return records, subject, jobs, objects, materials, uploads


def upload_note(
    uploads, subject, text="Ley de Ohm: V = I R. La resistencia se mide en ohmios."
):
    content = text.encode()
    ticket = uploads.create(
        "alice",
        subject["id"],
        {
            "name": "Apuntes",
            "mediaType": "text/plain",
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
    )
    version = uploads.put(
        "alice",
        ticket["uploadId"],
        ticket["requiredHeaders"]["X-Upload-Token"],
        content,
    )
    result = uploads.complete(
        "alice", ticket["uploadId"], version["generation"], "complete-1"
    )
    return ticket, result


def test_upload_checks_signature_owner_bytes_and_immutable_generation(tmp_path):
    _, subject, _, _, _, uploads = setup_study(tmp_path)
    content = b"apuntes"
    ticket = uploads.create(
        "alice",
        subject["id"],
        {
            "name": "Notas",
            "mediaType": "text/plain",
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
    )
    token = ticket["requiredHeaders"]["X-Upload-Token"]
    for owner, signature, data, expected in [
        ("bob", token, content, 404),
        ("alice", "forged", content, 403),
        ("alice", token, b"changed", 422),
    ]:
        with pytest.raises(DomainError) as failure:
            uploads.put(owner, ticket["uploadId"], signature, data)
        assert failure.value.status == expected
    version = uploads.put("alice", ticket["uploadId"], token, content)
    with pytest.raises(DomainError):
        uploads.complete("alice", ticket["uploadId"], "substituted-generation", "final")
    assert (
        uploads.complete("alice", ticket["uploadId"], version["generation"], "final")[
            "job"
        ]["status"]
        == "queued"
    )


def test_ingestion_review_history_and_scoped_citations(tmp_path):
    from campus.services.retrieval import RetrievalService

    _records, subject, jobs, _objects, materials, uploads = setup_study(tmp_path)
    ticket, result = upload_note(uploads, subject)
    claimed = jobs.claim("alice", result["job"]["id"])
    materials.ingest(claimed)
    material = materials.get("alice", ticket["materialId"])
    assert material["status"] == "ready"
    retrieval = RetrievalService(materials)
    blocks = retrieval.search(
        "alice", subject["id"], "resistencia ohmios", [material["id"]]
    )
    assert len(blocks) == 1 and blocks[0]["sourceRef"]["locator"] == "section:1"
    old = blocks[0]["sourceRef"]
    updated = materials.revise(
        "alice",
        material["id"],
        material["revision"],
        [
            {
                "blockId": "block-1",
                "text": "Ley de Ohm: V = I R. La resistencia limita la corriente.",
            }
        ],
        [],
    )
    assert updated["extractionVersion"] != old["extractionVersion"]
    assert retrieval.citation("alice", old)["text"].endswith("ohmios.")
    assert (
        retrieval.search("alice", subject["id"], "limita corriente", [material["id"]])[
            0
        ]["sourceRef"]["extractionVersion"]
        == updated["extractionVersion"]
    )
    with pytest.raises(DomainError):
        retrieval.citation("bob", old)
    with pytest.raises(DomainError):
        retrieval.citation("alice", {**old, "quote": "inventado"})
