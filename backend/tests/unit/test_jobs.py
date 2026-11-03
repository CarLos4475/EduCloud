from datetime import UTC, datetime, timedelta

import pytest
from campus.adapters.records import MemoryRecords
from campus.services.academic import DomainError


def test_job_outbox_deduplication_leases_and_cancellation():
    from campus.services.jobs import JobService

    current = [datetime(2026, 11, 2, tzinfo=UTC)]
    records = MemoryRecords()
    jobs = JobService(records, clock=lambda: current[0])
    job = jobs.create("alice", "ingest", "material", {}, "upload-1")
    assert records.get("alice", "outbox", job["id"])["status"] == "pending"
    assert jobs.create("alice", "ingest", "material", {}, "upload-1")["id"] == job["id"]
    with pytest.raises(DomainError) as changed:
        jobs.create("alice", "ingest", "different", {}, "upload-1")
    assert changed.value.status == 409
    lease = jobs.claim("alice", job["id"])
    assert lease and jobs.claim("alice", job["id"]) is None
    current[0] += timedelta(minutes=6)
    replacement = jobs.claim("alice", job["id"])
    assert replacement and replacement["leaseToken"] != lease["leaseToken"]
    assert not jobs.finish("alice", job["id"], lease["leaseToken"], "succeeded", {})
    jobs.cancel("alice", job["id"])
    assert not jobs.finish(
        "alice", job["id"], replacement["leaseToken"], "succeeded", {}
    )
    assert jobs.get("alice", job["id"])["status"] == "canceled"
    with pytest.raises(DomainError) as other:
        jobs.get("bob", job["id"])
    assert other.value.status == 404


def test_quota_is_reserved_before_work_and_unknown_usage_is_conservative():
    from campus.services.jobs import JobService

    jobs = JobService(MemoryRecords(), daily_tokens=16000)
    first = jobs.create("alice", "tutor_turn", "chat", {}, "1", reserve=8000)
    jobs.create("alice", "tutor_turn", "chat2", {}, "2", reserve=8000)
    with pytest.raises(DomainError) as quota:
        jobs.create("alice", "tutor_turn", "chat3", {}, "3", reserve=8000)
    assert quota.value.status == 429
    lease = jobs.claim("alice", first["id"])
    jobs.mark_external_started("alice", first["id"], lease["leaseToken"])
    jobs.finish(
        "alice",
        first["id"],
        lease["leaseToken"],
        "failed",
        {"error": "provider_timeout"},
    )
    assert jobs.get("alice", first["id"])["usageUnknown"] is True


def test_active_limit_survives_midnight_and_known_usage_is_not_unknown():
    from campus.services.jobs import JobService

    current = [datetime(2026, 11, 2, 23, 59, tzinfo=UTC)]
    jobs = JobService(MemoryRecords(), clock=lambda: current[0])
    first = jobs.create("alice", "tutor_turn", "one", {}, "one", reserve=8000)
    jobs.create("alice", "tutor_turn", "two", {}, "two", reserve=8000)
    current[0] += timedelta(minutes=2)
    with pytest.raises(DomainError):
        jobs.create("alice", "tutor_turn", "three", {}, "three", reserve=8000)
    lease = jobs.claim("alice", first["id"])
    jobs.mark_external_started("alice", first["id"], lease["leaseToken"])
    jobs.observe_usage("alice", first["id"], lease["leaseToken"], {"total_tokens": 30})
    jobs.finish(
        "alice",
        first["id"],
        lease["leaseToken"],
        "failed",
        {"error": "invalid_citation"},
    )
    assert jobs.get("alice", first["id"])["usageUnknown"] is False
    assert jobs.get("alice", first["id"])["usage"]["total_tokens"] == 30


def test_review_cancellation_does_not_settle_usage_twice():
    from campus.services.jobs import JobService

    records = MemoryRecords()
    jobs = JobService(records)
    job = jobs.create("alice", "ingest", "image", {}, "image", reserve=60000)
    lease = jobs.claim("alice", job["id"])
    jobs.finish(
        "alice",
        job["id"],
        lease["leaseToken"],
        "needs_review",
        {},
        usage={"total_tokens": 30},
    )
    before = records.get("alice", "usage", job["usageDay"])["chargedTokens"]
    jobs.cancel("alice", job["id"])
    assert before == 30
    assert records.get("alice", "usage", job["usageDay"])["chargedTokens"] == before


def test_reconciler_requeues_only_expired_local_work():
    from campus.services.jobs import JobService

    current = [datetime(2026, 11, 2, tzinfo=UTC)]
    jobs = JobService(MemoryRecords(), clock=lambda: current[0])
    job = jobs.create("alice", "ingest", "doc", {}, "dispatch")
    lease = jobs.claim("alice", job["id"])
    assert jobs.recover_expired("alice", job["id"])["status"] == "running"
    current[0] += timedelta(minutes=6)
    assert jobs.recover_expired("alice", job["id"])["status"] == "queued"
    assert jobs.records.get("alice", "outbox", job["id"])["status"] == "pending"
    assert not jobs.finish("alice", job["id"], lease["leaseToken"], "succeeded", {})


def test_turn_rate_limit_applies_even_when_no_provider_is_called():
    from campus.services.jobs import JobService

    jobs = JobService(MemoryRecords())
    for i in range(20):
        jobs.create("alice", "tutor_turn", str(i), {}, str(i))
    with pytest.raises(DomainError):
        jobs.create("alice", "tutor_turn", "21", {}, "21")
