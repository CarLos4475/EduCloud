import asyncio
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from campus.api.main import app
from campus.services.academic import DomainError
from campus.services.paging import page_rows
from test_materials import setup_study


def test_json_size_limit_includes_chunked_requests():
    async def body():
        yield b'{"preferences":"'
        for _ in range(24):
            yield b"x" * 100000
        yield b'"}'

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/api/v1/conversations",
                content=body(),
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 413

    asyncio.run(scenario())


def test_cursors_are_tied_to_owner_and_filter():
    rows = [{"id": str(i), "createdAt": "2026-11-02"} for i in range(6)]
    first = page_rows(rows, "alice", "materials:one", 2)
    assert len(first["items"]) == 2 and first["nextCursor"]
    assert (
        len(page_rows(rows, "alice", "materials:one", 2, first["nextCursor"])["items"])
        == 2
    )
    for owner, scope in [("bob", "materials:one"), ("alice", "materials:two")]:
        with pytest.raises(DomainError):
            page_rows(rows, owner, scope, 2, first["nextCursor"])


def test_expired_upload_reservations_are_cleaned_up(tmp_path):
    records, subject, _, _, _, uploads = setup_study(tmp_path)
    current = [datetime(2026, 11, 2, tzinfo=UTC)]
    uploads.clock = lambda: current[0]
    data = {"name": "Nota", "mediaType": "text/plain", "size": 2, "sha256": "a" * 64}
    ticket = uploads.create("alice", subject["id"], data)
    current[0] += timedelta(minutes=11)
    assert uploads.cleanup_expired("alice") == 1
    assert records.get("alice", "materials", ticket["materialId"])["size"] == 0
    with pytest.raises(DomainError):
        uploads.complete("alice", ticket["uploadId"], "invalid", "expired")
