import asyncio

import httpx


def test_worker_http_rejects_missing_or_forged_identity():
    from campus.worker.main import app

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://worker"
        ) as client:
            for headers in ({}, {"Authorization": "Bearer forged"}):
                response = await client.post(
                    "/internal/jobs",
                    json={"ownerId": "alice", "jobId": "a" * 32},
                    headers=headers,
                )
                assert response.status_code == 403

    asyncio.run(scenario())
