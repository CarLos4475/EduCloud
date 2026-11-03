import asyncio

import httpx
from campus.api.main import app


def test_contract_route_is_explicitly_not_implemented_with_stable_error_shape() -> None:
    async def request() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            return await client.get("/api/v1/contracts")

    response = asyncio.run(request())

    assert response.status_code == 501
    assert response.json() == {
        "code": "not_implemented",
        "message": "Esta operación aún no está implementada.",
        "requestId": "local-request",
        "details": None,
    }
