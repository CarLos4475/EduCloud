import asyncio
import hashlib
from uuid import uuid4

import httpx
from campus.api.main import app
from test_identity_academic import account


def test_upload_and_recovered_tutor_with_real_emulator_identity(tmp_path):
    from campus.adapters.objects import LocalObjects
    from campus.adapters.records import FirestoreRecords
    from campus.adapters.testing import TestStudyProvider
    from campus.api.study_runtime import StudyRuntime, study_runtime
    from campus.config import Settings

    Settings.load()
    state = StudyRuntime(
        FirestoreRecords("demo-campus"),
        LocalObjects(tmp_path),
        b"synthetic-signature",
        TestStudyProvider(),
    )
    app.dependency_overrides[study_runtime] = lambda: state
    alice, bob = account(), account()

    async def scenario():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            a = {"Authorization": f"Bearer {alice}"}
            b = {"Authorization": f"Bearer {bob}"}
            subject = (
                await client.post(
                    "/api/v1/subjects",
                    json={"name": "Física H2", "illustrationId": "wave"},
                    headers=a,
                )
            ).json()
            data = b"Ley de Ohm: V = I R. La resistencia limita la corriente."
            ticket_response = await client.post(
                f"/api/v1/subjects/{subject['id']}/uploads",
                json={
                    "name": "Apunte",
                    "mediaType": "text/plain",
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                },
                headers=a,
            )
            assert ticket_response.status_code == 201, ticket_response.text
            ticket = ticket_response.json()
            assert (
                await client.put(
                    f"/api/v1/uploads/{ticket['uploadId']}/content",
                    content=data,
                    headers={
                        **b,
                        **ticket["requiredHeaders"],
                        "Content-Type": "text/plain",
                    },
                )
            ).status_code == 404
            uploaded = await client.put(
                f"/api/v1/uploads/{ticket['uploadId']}/content",
                content=data,
                headers={
                    **a,
                    **ticket["requiredHeaders"],
                    "Content-Type": "text/plain",
                },
            )
            assert uploaded.status_code == 200, uploaded.text
            complete = await client.post(
                f"/api/v1/uploads/{ticket['uploadId']}/complete",
                json={"generation": uploaded.json()["generation"]},
                headers={**a, "Idempotency-Key": uuid4().hex},
            )
            assert complete.status_code == 202, complete.text
            job = complete.json()["job"]
            state.run_job(
                next(
                    row
                    for row in state.records.pending_jobs()
                    if row["id"] == job["id"]
                )
            )
            material = (
                await client.get(f"/api/v1/materials/{ticket['materialId']}", headers=a)
            ).json()
            assert material["status"] == "ready"
            assert (
                await client.get(f"/api/v1/materials/{ticket['materialId']}", headers=b)
            ).status_code == 404
            conversation = (
                await client.post(
                    "/api/v1/conversations",
                    json={
                        "subjectId": subject["id"],
                        "materialIds": [ticket["materialId"]],
                    },
                    headers=a,
                )
            ).json()
            turn = await client.post(
                f"/api/v1/conversations/{conversation['id']}/turns",
                json={"question": "¿Qué es la resistencia?"},
                headers={**a, "Idempotency-Key": uuid4().hex},
            )
            assert turn.status_code == 202, turn.text
            turn = turn.json()
            state.run_job(
                next(
                    row
                    for row in state.records.pending_jobs()
                    if row["id"] == turn["jobId"]
                )
            )
            restored = (
                await client.get(f"/api/v1/turns/{turn['id']}", headers=a)
            ).json()
            assert restored["status"] == "succeeded" and len(restored["citations"]) == 1
            assert (
                await client.get(f"/api/v1/turns/{turn['id']}/events", headers=b)
            ).status_code == 404

    try:
        asyncio.run(scenario())
    finally:
        app.dependency_overrides.pop(study_runtime, None)
