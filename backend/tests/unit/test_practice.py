import pytest
from campus.services.academic import DomainError
from campus.services.practice import PracticeService
from test_resources import build, request, run_latest


def ready(service, jobs, subject, material, kind, key):
    detail = run_latest(
        service, jobs, service.create("alice", request(subject, material, kind), key)
    )
    return detail, detail["versions"][0]["id"]


def setup(tmp_path):
    service, jobs, _, subject, material = build(tmp_path)
    return PracticeService(service.records, service), service, jobs, subject, material


def test_quiz_attempts_are_graded_by_the_server_and_are_private(tmp_path):
    practice, service, jobs, subject, material = setup(tmp_path)
    _, version = ready(service, jobs, subject, material, "quiz", "q")
    wrong = practice.attempt("alice", version, {"answers": [0]})
    right = practice.attempt("alice", version, {"answers": [2]})
    assert (wrong["score"], right["score"], right["total"]) == (0, 1, 1)
    assert right["results"][0]["correctIndex"] == 2
    for bad in ({"answers": []}, {"answers": [1, 1]}, {"answers": [9]}):
        with pytest.raises((DomainError, ValueError)):
            practice.attempt("alice", version, bad)
    with pytest.raises(DomainError):
        practice.attempt("bob", version, {"answers": [2]})
    # A score can never be supplied by the client.
    with pytest.raises(ValueError):
        practice.attempt("alice", version, {"answers": [2], "score": 99})


def test_practice_needs_a_ready_version_of_the_right_kind(tmp_path):
    practice, service, jobs, subject, material = setup(tmp_path)
    _, summary = ready(service, jobs, subject, material, "summary", "s")
    with pytest.raises(DomainError) as wrong_kind:
        practice.attempt("alice", summary, {"answers": [0]})
    assert wrong_kind.value.status == 422
    pending = service.create("alice", request(subject, material, "quiz"), "pending")
    with pytest.raises(DomainError) as not_ready:
        practice.attempt("alice", pending["versions"][0]["id"], {"answers": [0]})
    assert not_ready.value.status == 409


def test_flashcard_reviews_and_experiment_state_persist_with_revisions(tmp_path):
    practice, service, jobs, subject, material = setup(tmp_path)
    _, cards = ready(service, jobs, subject, material, "flashcards", "f")
    assert practice.get_review("alice", cards)["cards"] == {}
    practice.put_review("alice", cards, {"cards": {"0": "known"}})
    assert (
        practice.put_review("alice", cards, {"cards": {"0": "again"}})["revision"] == 2
    )
    with pytest.raises(DomainError):
        practice.put_review("alice", cards, {"cards": {"5": "known"}})
    _, interactive = ready(service, jobs, subject, material, "interactive", "i")
    first = practice.put_state("alice", interactive, {"state": {"r": 4}})
    second = practice.put_state(
        "alice", interactive, {"state": {"r": 7}, "expectedRevision": first["revision"]}
    )
    assert second["state"] == {"r": 7}
    with pytest.raises(DomainError) as stale:
        practice.put_state(
            "alice",
            interactive,
            {"state": {"r": 1}, "expectedRevision": first["revision"]},
        )
    assert stale.value.status == 409
    with pytest.raises(DomainError) as big:
        practice.put_state("alice", interactive, {"state": {"x": "a" * 60000}})
    assert big.value.status == 413
    practice.delete_state("alice", interactive)
    assert practice.get_state("alice", interactive)["state"] == {}


def test_progress_and_recommendations_follow_the_evidence(tmp_path):
    practice, service, jobs, subject, material = setup(tmp_path)
    start = practice.progress("alice", subject["id"])
    assert start["materialsReady"] == 1 and start["quizAttempts"] == 0
    assert "resumen" in start["recommendations"][0]["text"].lower()
    _, quiz = ready(service, jobs, subject, material, "quiz", "q")
    assert any(
        "cuestionario" in t["text"].lower()
        for t in practice.progress("alice", subject["id"])["recommendations"]
    )
    practice.attempt("alice", quiz, {"answers": [0]})
    low = practice.progress("alice", subject["id"])
    assert low["averageScore"] == 0 and any(
        "Repasa" in t["text"] for t in low["recommendations"]
    )
    practice.attempt("alice", quiz, {"answers": [2]})
    assert practice.progress("alice", subject["id"])["averageScore"] == 50
    _, cards = ready(service, jobs, subject, material, "flashcards", "f")
    practice.put_review("alice", cards, {"cards": {"0": "again"}})
    progress = practice.progress("alice", subject["id"])
    assert (
        progress["cardsToReview"] == 1 and progress["recommendations"][0]["resourceId"]
    )
    with pytest.raises(DomainError):
        practice.progress("bob", subject["id"])


def test_passport_stamps_are_earned_only_from_real_activity(tmp_path):
    practice, service, jobs, subject, material = setup(tmp_path)
    stamps = {s["id"]: s for s in practice.passport("alice")["stamps"]}
    assert stamps["first_material"]["earned"] and not stamps["first_resource"]["earned"]
    _, quiz = ready(service, jobs, subject, material, "quiz", "q")
    practice.attempt("alice", quiz, {"answers": [2]})
    _, interactive = ready(service, jobs, subject, material, "interactive", "i")
    passport = practice.passport("alice")
    stamps = {s["id"]: s for s in passport["stamps"]}
    for earned in ("first_resource", "first_quiz", "perfect_quiz", "explorer"):
        assert stamps[earned]["earned"] and stamps[earned]["earnedAt"]
    assert not stamps["three_subjects"]["earned"]
    assert passport["earned"] == sum(s["earned"] for s in passport["stamps"])
    assert practice.passport("bob")["earned"] == 0
    assert interactive
