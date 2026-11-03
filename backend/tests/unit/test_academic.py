import pytest
from campus.adapters.records import MemoryRecords
from campus.services.academic import AcademicService, DomainError


def test_subject_is_persistent_within_repository_and_isolated_by_owner():
    store = MemoryRecords()
    service = AcademicService(store)
    subject = service.create(
        "alice", "subjects", {"name": "Métodos numéricos II", "illustrationId": "grid"}
    )
    assert (
        AcademicService(store).get("alice", "subjects", subject["id"])["name"]
        == "Métodos numéricos II"
    )
    with pytest.raises(DomainError) as error:
        service.get("bob", "subjects", subject["id"])
    assert error.value.status == 404


def test_revision_conflict_and_cycle_are_rejected():
    service = AcademicService(MemoryRecords())
    subject = service.create(
        "alice", "subjects", {"name": "Álgebra", "illustrationId": "grid"}
    )
    first = service.create(
        "alice", "topics", {"title": "Matrices", "subjectId": subject["id"]}
    )
    second = service.create(
        "alice",
        "topics",
        {
            "title": "Determinantes",
            "subjectId": subject["id"],
            "prerequisiteIds": [first["id"]],
        },
    )
    with pytest.raises(DomainError) as error:
        service.update(
            "alice", "topics", first["id"], {"prerequisiteIds": [second["id"]]}, 1
        )
    assert error.value.status == 422
    service.update("alice", "subjects", subject["id"], {"name": "Álgebra II"}, 1)
    with pytest.raises(DomainError) as error:
        service.update("alice", "subjects", subject["id"], {"name": "Viejo"}, 1)
    assert error.value.status == 409


def test_cross_owner_references_are_rejected_and_archiving_keeps_topics():
    service = AcademicService(MemoryRecords())
    subject = service.create(
        "alice", "subjects", {"name": "Física", "illustrationId": "wave"}
    )
    with pytest.raises(DomainError):
        service.create(
            "bob",
            "agenda",
            {"title": "Tarea", "subjectId": subject["id"], "kind": "task"},
        )
    topic = service.create(
        "alice", "topics", {"title": "Ondas", "subjectId": subject["id"]}
    )
    service.update("alice", "subjects", subject["id"], {"archived": True}, 1)
    assert service.get("alice", "topics", topic["id"])["title"] == "Ondas"


def test_agenda_validates_dates_and_schedule_zone():
    service = AcademicService(MemoryRecords())
    day = service.create(
        "alice", "agenda", {"title": "Examen", "kind": "exam", "dueDate": "2026-11-20"}
    )
    assert day["dueDate"] == "2026-11-20"
    with pytest.raises(DomainError):
        service.create(
            "alice",
            "agenda",
            {"title": "Examen", "kind": "exam", "dueAt": "2026-11-20T12:00:00"},
        )
    with pytest.raises(DomainError):
        service.create(
            "alice",
            "schedule",
            {
                "weekday": 1,
                "localStart": "10:00",
                "localEnd": "09:00",
                "timezone": "America/Mexico_City",
            },
        )


def test_deleting_subject_is_explicitly_deferred():
    service = AcademicService(MemoryRecords())
    subject = service.create(
        "alice", "subjects", {"name": "Física", "illustrationId": "wave"}
    )
    with pytest.raises(DomainError) as error:
        service.delete("alice", "subjects", subject["id"])
    assert error.value.status == 501
