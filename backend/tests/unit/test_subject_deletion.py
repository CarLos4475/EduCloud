import pytest
from campus.adapters.testing import TestStudyProvider
from campus.api.study_runtime import StudyRuntime
from campus.services.academic import AcademicService, DomainError
from campus.services.practice import PracticeService
from test_materials import setup_study, upload_note
from test_resources import request


def runtime(tmp_path):
    records, subject, _jobs, objects, _materials, _uploads = setup_study(tmp_path)
    state = StudyRuntime(records, objects, b"test-signature-only", TestStudyProvider())
    ticket, upload = upload_note(state.uploads, subject)
    state.run_job(state.jobs.get("alice", upload["job"]["id"]))
    return state, subject, ticket["materialId"]


def everything(records, uid="alice"):
    names = [
        "materials",
        "materialVersions",
        "uploads",
        "conversations",
        "turns",
        "resources",
        "resourceVersions",
        "attempts",
        "reviews",
        "jobs",
        "topics",
        "agenda",
        "schedule",
    ]
    return {n: len(records.list(uid, n)) for n in names}


def test_deleting_a_subject_removes_everything_built_from_it(tmp_path):
    state, subject, material = runtime(tmp_path)
    academic = AcademicService(state.records)
    academic.create("alice", "topics", {"subjectId": subject["id"], "title": "Ohm"})
    other = academic.create(
        "alice", "subjects", {"name": "Álgebra", "illustrationId": "wave"}
    )
    academic.create("alice", "topics", {"subjectId": other["id"], "title": "Matrices"})
    conversation = state.tutor.create(
        "alice",
        {
            "subjectId": subject["id"],
            "title": "Dudas",
            "personalityId": "patient",
            "assistanceMode": "explain",
            "materialIds": [material],
            "sourceMode": "selected_material",
            "preferences": "",
        },
    )
    turn = state.tutor.send(
        "alice",
        conversation["id"],
        {"question": "resistencia", "allowGeneralForTurn": False},
        "t",
    )
    state.run_job(state.jobs.get("alice", turn["jobId"]))
    detail = state.resources.create("alice", request(subject, material, "quiz"), "q")
    state.run_job(state.jobs.get("alice", detail["versions"][0]["jobId"]))
    version = state.resources.detail("alice", detail["id"])["versions"][0]["id"]
    PracticeService(state.records, state.resources).attempt(
        "alice", version, {"answers": [2]}
    )
    assert all(
        everything(state.records)[n]
        for n in ("materials", "turns", "resources", "attempts")
    )

    state.delete_subject("alice", subject["id"])

    left = everything(state.records)
    assert (
        left["materials"] == left["turns"] == left["resources"] == left["attempts"] == 0
    )
    assert left["resourceVersions"] == left["conversations"] == left["uploads"] == 0
    assert left["materialVersions"] == left["jobs"] == 0
    assert left["topics"] == 1  # the other subject keeps its own data
    with pytest.raises(DomainError):
        academic.get("alice", "subjects", subject["id"])
    assert academic.get("alice", "subjects", other["id"])
    # Original files are removed too, not just their records.
    assert not list(tmp_path.rglob("original"))


def test_deleting_is_private_and_waits_for_running_work(tmp_path):
    state, subject, material = runtime(tmp_path)
    with pytest.raises(DomainError):
        state.delete_subject("bob", subject["id"])
    pending = state.resources.create(
        "alice", request(subject, material, "summary"), "p"
    )
    with pytest.raises(DomainError) as busy:
        state.delete_subject("alice", subject["id"])
    assert busy.value.status == 409
    state.jobs.cancel("alice", pending["versions"][0]["jobId"])
    state.delete_subject("alice", subject["id"])
    assert everything(state.records)["resources"] == 0


def test_deleting_the_account_clears_every_collection_but_only_for_that_student(
    tmp_path,
):
    from campus.api.study_runtime import ACCOUNT_COLLECTIONS

    state, subject, material = runtime(tmp_path)
    academic = AcademicService(state.records)
    academic.create("alice", "periods", {"name": "2026-II"})
    state.records.save("alice", "profiles", "me", {"id": "me", "revision": 1}, None)
    detail = state.resources.create("alice", request(subject, material, "quiz"), "q")
    state.run_job(state.jobs.get("alice", detail["versions"][0]["jobId"]))
    bob = academic.create("bob", "subjects", {"name": "Otra", "illustrationId": "wave"})

    state.delete_account_data("nobody-has-nothing")  # nothing to delete is not an error
    state.delete_account_data("alice")

    assert all(not state.records.list("alice", name) for name in ACCOUNT_COLLECTIONS)
    assert academic.get("bob", "subjects", bob["id"])
    assert not list(tmp_path.rglob("original"))


def test_deleting_the_account_waits_for_running_work(tmp_path):
    state, subject, material = runtime(tmp_path)
    state.resources.create("alice", request(subject, material, "summary"), "p")
    with pytest.raises(DomainError) as busy:
        state.delete_account_data("alice")
    assert busy.value.status == 409
