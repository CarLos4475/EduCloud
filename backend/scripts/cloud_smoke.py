"""Bounded live smoke; only the generated test account and its records are removed."""

import asyncio
import json
import os
import re
import sys
from uuid import uuid4

import firebase_admin
import httpx
from campus.adapters.records import FirestoreRecords
from campus.services.academic import AcademicService
from firebase_admin import auth, credentials
from google.oauth2.credentials import Credentials


def main():
    project = "educloud-1d5de"
    config = json.loads(os.environ["CAMPUS_FIREBASE_WEB_CONFIG"])
    if config["projectId"] != project:
        raise RuntimeError("El proyecto no coincide con el autorizado.")
    google_credential = Credentials(
        os.environ.pop("CAMPUS_SMOKE_ACCESS_TOKEN"), quota_project_id=project
    )

    class Credential(credentials.Base):
        def get_credential(self):
            return google_credential

    os.environ["GOOGLE_CLOUD_PROJECT"] = project
    os.environ["CAMPUS_ENV"] = "production"
    os.environ.pop("FIREBASE_AUTH_EMULATOR_HOST", None)
    os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
    firebase_admin.initialize_app(Credential(), options={"projectId": project})
    if "--preflight" in sys.argv:
        fixtures = []
        for user in auth.list_users().iterate_all():
            if re.fullmatch(r"h1-smoke-[a-f0-9]{32}@(example\.test|pcpuma\.acatlan\.unam\.mx)", user.email or ""):
                fixtures.append({"uid": user.uid, "synthetic": True})
        print(
            json.dumps(
                {
                    "readOnly": True,
                    "authReadPermission": True,
                    "syntheticFixtures": fixtures,
                }
            )
        )
        return
    if "--cleanup-fixture" in sys.argv:
        uid = sys.argv[sys.argv.index("--cleanup-fixture") + 1]
        user = auth.get_user(uid)
        if not re.fullmatch(r"h1-smoke-[a-f0-9]{32}@example\.test", user.email or ""):
            raise RuntimeError(
                "El identificador no corresponde a un fixture de esta prueba."
            )
        auth.delete_user(uid)
        print(json.dumps({"deletedSyntheticFixture": uid}))
        return
    identifier = uuid4().hex
    password = uuid4().hex + "Aa!"
    response = httpx.post(
        "https://identitytoolkit.googleapis.com/v1/accounts:signUp",
        params={"key": config["apiKey"]},
        json={
            "email": f"h1-smoke-{identifier}@example.test",
            "password": password,
            "returnSecureToken": True,
        },
        timeout=30,
    )
    if response.status_code != 200:
        code = response.json().get("error", {}).get("message", "UNKNOWN").split(":")[0]
        raise RuntimeError(
            f"No se pudo crear la cuenta de prueba: {code} (HTTP {response.status_code})."
        )
    data = response.json()
    uid = data["localId"]
    os.environ["CAMPUS_PILOT_UIDS"] = uid
    from campus.api.dependencies import academic_service
    from campus.api.main import app

    records = FirestoreRecords(project, google_credential)
    app.dependency_overrides[academic_service] = lambda: AcademicService(records)
    created_ids = []

    def refresh():
        result = httpx.post(
            "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
            params={"key": config["apiKey"]},
            json={
                "email": f"h1-smoke-{identifier}@pcpuma.acatlan.unam.mx",
                "password": password,
                "returnSecureToken": True,
            },
            timeout=30,
        )
        if result.status_code != 200:
            raise RuntimeError("No se pudo renovar la sesión sintética.")
        return result.json()["idToken"]

    async def smoke():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {data['idToken']}"},
        ) as client:
            outside = await client.get("/api/v1/subjects")
            if outside.status_code != 403:
                raise RuntimeError(
                    f"Correo externo: se esperaba 403, se recibió {outside.status_code}."
                )
            auth.update_user(
                uid,
                email=f"h1-smoke-{identifier}@pcpuma.acatlan.unam.mx",
                email_verified=False,
            )
            client.headers["Authorization"] = f"Bearer {refresh()}"
            unverified = await client.get("/api/v1/subjects")
            if unverified.status_code != 403:
                raise RuntimeError("No se rechazó el correo no verificado.")
            # Only this ephemeral fixture is marked verified administratively; no message is sent.
            auth.update_user(uid, email_verified=True)
            client.headers["Authorization"] = f"Bearer {refresh()}"
            result = await client.post(
                "/api/v1/subjects",
                json={"name": "Prueba H1 sintética", "illustrationId": "grid"},
            )
            if result.status_code != 201:
                raise RuntimeError(
                    f"Falló la creación autorizada (HTTP {result.status_code})."
                )
            row = result.json()
            created_ids.append(row["id"])
            persisted = await client.get(f"/api/v1/subjects/{row['id']}")
            if (
                persisted.status_code != 200
                or persisted.json()["name"] != "Prueba H1 sintética"
            ):
                raise RuntimeError("No se verificó la lectura persistente.")
            denied = await client.get(
                "/api/v1/subjects", headers={"Authorization": "Bearer invalid"}
            )
            if denied.status_code != 401:
                raise RuntimeError("No se rechazó el token inválido.")
            print(
                json.dumps(
                    {
                        "project": project,
                        "realAuth": True,
                        "realFirestore": True,
                        "create": 201,
                        "read": 200,
                        "invalidToken": 401,
                        "outsideDomain": 403,
                        "unverifiedEmail": 403,
                        "syntheticOnly": True,
                    }
                )
            )

    try:
        asyncio.run(smoke())
    finally:
        for key in created_ids:
            records.remove(uid, "subjects", key)
        auth.delete_user(uid)
        print(
            "Limpieza completada: cuenta sintética y documentos creados por esta prueba."
        )


if __name__ == "__main__":
    main()
