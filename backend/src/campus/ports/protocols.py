"""Interfaces used by domain services; implementations belong in adapters."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Protocol, TypeVar

from campus.domain.contracts import Actor, JobSpec, SourceRef

T = TypeVar("T")


class Clock(Protocol):
    def now(self) -> datetime: ...


class Repository(Protocol[T]):
    async def get(self, actor: Actor, record_id: str) -> T | None: ...

    async def put(self, actor: Actor, record_id: str, record: T) -> None: ...


class ObjectStore(Protocol):
    async def put(self, key: str, content: bytes, media_type: str) -> str: ...

    async def get(self, key: str) -> bytes: ...

    async def delete(self, key: str) -> None: ...


class JobQueue(Protocol):
    async def enqueue(
        self, owner_id: str, job_id: str, dispatch_key: str, job: JobSpec
    ) -> None: ...


class Retriever(Protocol):
    async def search(
        self,
        actor: Actor,
        subject_id: str,
        query: str,
        material_ids: list[str],
        top_k: int = 8,
    ) -> list[tuple[SourceRef, str, float]]: ...


class TutorProvider(Protocol):
    async def stream_answer(
        self, context: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]: ...

    async def generate_structured(
        self, schema_id: str, context: dict[str, Any]
    ) -> dict[str, Any]: ...
