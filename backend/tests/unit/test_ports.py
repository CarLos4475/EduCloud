import asyncio

from campus.domain.contracts import Actor, JobSpec
from campus.ports.memory import InMemoryJobQueue, InMemoryRepository


def test_memory_repository_scopes_records_to_owner() -> None:
    async def scenario() -> None:
        repository = InMemoryRepository[dict[str, str]]()
        await repository.put(
            Actor(uid="user-a", pilot_enabled=True), "subject-1", {"name": "Álgebra"}
        )

        assert await repository.get(
            Actor(uid="user-a", pilot_enabled=True), "subject-1"
        ) == {"name": "Álgebra"}
        assert (
            await repository.get(Actor(uid="user-b", pilot_enabled=True), "subject-1")
            is None
        )

    asyncio.run(scenario())


def test_memory_queue_deduplicates_dispatch_key() -> None:
    async def scenario() -> None:
        queue = InMemoryJobQueue()
        job = JobSpec(
            kind="material_ingest",
            entity_id="material-1",
            input_version="v1",
            payload={},
        )

        await queue.enqueue("user-a", "job-1", "dispatch-1", job)
        await queue.enqueue("user-a", "job-1", "dispatch-1", job)

        assert await queue.pending() == [("user-a", "job-1", "dispatch-1", job)]

    asyncio.run(scenario())
