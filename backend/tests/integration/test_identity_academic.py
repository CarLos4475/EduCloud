"""Real Firebase Auth + Firestore emulator integration, no production resources."""

import asyncio
from uuid import uuid4

import httpx
from campus.api.main import app


def account(domain="pcpuma.acatlan.unam.mx"):
    response = httpx.post(
        "http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=demo-key",
        json={
            "email": f"test-{uuid4().hex}@{domain}",
            "password": "Local-study-2026!",
            "returnSecureToken": True,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["idToken"]


def test_firebase_tokens_scope_crud_and_persist_data():
    alice, bob, outside = account(), account(), account("example.test")

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            a = {"Authorization": f"Bearer {alice}"}
            b = {"Authorization": f"Bearer {bob}"}
            assert (
                await client.get(
                    "/api/v1/subjects", headers={"Authorization": f"Bearer {outside}"}
                )
            ).status_code == 403
            async with httpx.AsyncClient(timeout=10) as firestore_client:
                direct = await firestore_client.get(
                    "http://127.0.0.1:8080/v1/projects/demo-campus/databases/(default)/documents/users/synthetic/subjects",
                    headers=a,
                )
            assert direct.status_code == 403
            assert (await client.get("/api/v1/subjects")).status_code == 401
            assert (
                await client.get(
                    "/api/v1/subjects", headers={"Authorization": "Bearer forged"}
                )
            ).status_code == 401
            created = await client.post(
                "/api/v1/subjects",
                json={"name": "Termodinámica propia", "illustrationId": "wave"},
                headers=a,
            )
            assert created.status_code == 201, created.text
            subject = created.json()
            assert (
                await client.get(f"/api/v1/subjects/{subject['id']}", headers=b)
            ).status_code == 404
            assert (
                await client.patch(
                    f"/api/v1/subjects/{subject['id']}",
                    json={"expectedRevision": 1, "name": "Ajena"},
                    headers=b,
                )
            ).status_code == 404
            assert (
                await client.post(
                    "/api/v1/agenda",
                    json={"title": "Referencia ajena", "subjectId": subject["id"]},
                    headers=b,
                )
            ).status_code == 404
            changed = await client.patch(
                f"/api/v1/subjects/{subject['id']}",
                json={
                    "expectedRevision": 1,
                    "name": "Termodinámica II",
                    "illustrationId": "orbit",
                },
                headers=a,
            )
            assert changed.status_code == 200, changed.text
            assert (
                await client.patch(
                    f"/api/v1/subjects/{subject['id']}",
                    json={"expectedRevision": 1, "name": "Obsoleto"},
                    headers=a,
                )
            ).status_code == 409
            assert (
                await client.get(f"/api/v1/subjects/{subject['id']}", headers=a)
            ).json()["name"] == "Termodinámica II"
            assert (
                await client.post(
                    "/api/v1/subjects", json={"name": "x", "ownerId": "bob"}, headers=a
                )
            ).status_code == 422
            profile = await client.put(
                "/api/v1/me",
                json={
                    "displayName": "Estudiante",
                    "timezone": "America/Mexico_City",
                    "expectedRevision": 0,
                },
                headers=a,
            )
            assert profile.status_code == 200, profile.text
            assert (
                await client.put(
                    "/api/v1/me",
                    json={"displayName": "Perfil obsoleto", "expectedRevision": 0},
                    headers=a,
                )
            ).status_code == 409
            schedule = await client.post(
                "/api/v1/schedule",
                json={
                    "subjectId": subject["id"],
                    "weekday": 0,
                    "localStart": "09:00",
                    "localEnd": "10:00",
                    "timezone": "America/Mexico_City",
                },
                headers=a,
            )
            assert schedule.status_code == 201, schedule.text
            assert (await client.get("/api/v1/schedule", headers=b)).json()[
                "items"
            ] == []

    asyncio.run(scenario())
