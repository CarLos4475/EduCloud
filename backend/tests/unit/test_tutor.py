import pytest
from campus.services.academic import DomainError
from test_materials import setup_study, upload_note


class StudyProvider:
    def __init__(self, invented=False):
        self.invented = invented
        self.calls = 0

    def tutor_answer(self, messages, on_progress=None):
        self.calls += 1
        return {
            "answer": "Con corriente fija, V = IR.",
            "citations": [
                {"sourceId": "invented" if self.invented else "S1", "quote": "V = I R"}
            ],
            "insufficientSources": False,
        }, {"total_tokens": 30}


def test_tutor_is_scoped_idempotent_recovers_and_requires_source_consent(tmp_path):
    from campus.services.retrieval import RetrievalService
    from campus.services.tutoring import TutorService

    records, subject, jobs, _, materials, uploads = setup_study(tmp_path)
    ticket, upload = upload_note(uploads, subject)
    materials.ingest(jobs.claim("alice", upload["job"]["id"]))
    provider = StudyProvider()
    tutor = TutorService(records, jobs, RetrievalService(materials), provider)
    conversation = tutor.create(
        "alice",
        {
            "subjectId": subject["id"],
            "title": "Dudas",
            "personalityId": "socratic",
            "assistanceMode": "solution",
            "materialIds": [ticket["materialId"]],
            "sourceMode": "selected_material",
            "preferences": "",
        },
    )
    accepted = tutor.send(
        "alice",
        conversation["id"],
        {"question": "resistencia y corriente V", "allowGeneralForTurn": False},
        "same-turn",
    )
    assert (
        tutor.send(
            "alice",
            conversation["id"],
            {"question": "resistencia y corriente V", "allowGeneralForTurn": False},
            "same-turn",
        )["id"]
        == accepted["id"]
    )
    tutor.run(jobs.claim("alice", accepted["jobId"]))
    restored = tutor.turn("alice", accepted["id"])
    assert (
        restored["status"] == "succeeded"
        and restored["citations"][0]["materialId"] == ticket["materialId"]
    )
    assert provider.calls == 1
    material = materials.get("alice", ticket["materialId"])
    materials.revise(
        "alice",
        material["id"],
        material["revision"],
        [
            {
                "blockId": "block-1",
                "text": "Ley de Ohm: V = I R. Resistencia y corriente.",
            }
        ],
        [],
    )
    assert tutor.turn("alice", accepted["id"])["sourcesChanged"] is True
    with pytest.raises(DomainError):
        tutor.turn("bob", accepted["id"])
    no_source = tutor.send(
        "alice",
        conversation["id"],
        {"question": "mitocondria ADN", "allowGeneralForTurn": False},
        "next-turn",
    )
    tutor.run(jobs.claim("alice", no_source["jobId"]))
    assert tutor.turn("alice", no_source["id"])["needsConsent"] is True
    assert provider.calls == 1


def test_provider_cannot_publish_invented_citations(tmp_path):
    from campus.services.retrieval import RetrievalService
    from campus.services.tutoring import TutorService

    records, subject, jobs, _, materials, uploads = setup_study(tmp_path)
    ticket, uploaded = upload_note(uploads, subject)
    materials.ingest(jobs.claim("alice", uploaded["job"]["id"]))
    tutor = TutorService(
        records, jobs, RetrievalService(materials), StudyProvider(invented=True)
    )
    conversation = tutor.create(
        "alice",
        {
            "subjectId": subject["id"],
            "title": "Duda",
            "materialIds": [ticket["materialId"]],
        },
    )
    turn = tutor.send(
        "alice",
        conversation["id"],
        {"question": "resistencia", "allowGeneralForTurn": False},
        "invented",
    )
    with pytest.raises(DomainError) as invalid:
        tutor.run(jobs.claim("alice", turn["jobId"]))
    assert invalid.value.status == 422
    assert tutor.turn("alice", turn["id"])["citations"] == []


def test_interrupted_provider_requires_explicit_retry_charge_consent(tmp_path):
    from campus.adapters.deepseek import ProviderFailure
    from campus.api.study_runtime import StudyRuntime

    class TimeoutProvider:
        def tutor_answer(self, *args, **kwargs):
            raise ProviderFailure("provider_timeout")

    records, subject, _jobs, objects, _materials, _uploads = setup_study(tmp_path)
    state = StudyRuntime(records, objects, b"test-key", TimeoutProvider())
    ticket, uploaded = upload_note(state.uploads, subject)
    state.run_job(uploaded["job"])
    conv = state.tutor.create(
        "alice", {"subjectId": subject["id"], "materialIds": [ticket["materialId"]]}
    )
    turn = state.tutor.send(
        "alice",
        conv["id"],
        {"question": "resistencia", "allowGeneralForTurn": False},
        "timeout",
    )
    state.run_job(state.jobs.get("alice", turn["jobId"]))
    assert state.tutor.turn("alice", turn["id"])["usageUnknown"] is True
    with pytest.raises(DomainError):
        state.retry("alice", turn["jobId"])
    new_job = state.retry("alice", turn["jobId"], True)
    assert state.tutor.turn("alice", turn["id"])["jobId"] == new_job["id"]
