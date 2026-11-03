"""Local deterministic test adapters; never use as product persistence."""

from __future__ import annotations

from collections import defaultdict
from typing import Generic, TypeVar

from campus.domain.contracts import Actor, JobSpec

T = TypeVar("T")


class InMemoryRepository(Generic[T]):
    def __init__(self) -> None:
        self._records: dict[str, dict[str, T]] = defaultdict(dict)

    async def get(self, actor: Actor, record_id: str) -> T | None:
        return self._records[actor.uid].get(record_id)

    async def put(self, actor: Actor, record_id: str, record: T) -> None:
        self._records[actor.uid][record_id] = record


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._jobs: list[tuple[str, str, str, JobSpec]] = []
        self._dispatch_keys: set[tuple[str, str]] = set()

    async def enqueue(
        self, owner_id: str, job_id: str, dispatch_key: str, job: JobSpec
    ) -> None:
        key = (owner_id, dispatch_key)
        if key not in self._dispatch_keys:
            self._dispatch_keys.add(key)
            self._jobs.append((owner_id, job_id, dispatch_key, job))

    async def pending(self) -> list[tuple[str, str, str, JobSpec]]:
        return list(self._jobs)
