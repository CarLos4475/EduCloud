"""Real Firestore smoke; no real student data or Firebase accounts are used."""

import json
import os
import re
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

from campus.adapters.objects import LocalObjects, digest
from campus.adapters.records import FirestoreRecords
from campus.adapters.testing import TestStudyProvider
from campus.api.study_runtime import StudyRuntime
from campus.services.academic import AcademicService
from google.api_core.exceptions import FailedPrecondition
from google.oauth2.credentials import Credentials


def main():
    project = "educloud-1d5de"
    os.environ.pop("FIRESTORE_EMULATOR_HOST", None)
    os.environ.pop("FIREBASE_AUTH_EMULATOR_HOST", None)
    credential = Credentials(
        os.environ.pop("CAMPUS_SMOKE_ACCESS_TOKEN"), quota_project_id=project
    )
    records = FirestoreRecords(project, credential)
    if "--preflight" in sys.argv:
        try:
            records.pending_jobs()
        except FailedPrecondition:
            print(
                json.dumps(
                    {
                        "readOnly": True,
                        "project": project,
                        "pendingQueryReady": False,
                        "state": "index_building",
                    }
                )
            )
            raise SystemExit(2) from None
        print(
            json.dumps(
                {"readOnly": True, "project": project, "pendingQueryReady": True}
            )
        )
        return
    uid = f"h2-smoke-{uuid4().hex}"
    assert re.fullmatch(r"h2-smoke-[a-f0-9]{32}", uid)
    report = {
        "project": project,
        "provider": "explicit test fixture",
        "objectStore": "local synthetic fixture",
    }
    cleaned = 0
    try:
        with TemporaryDirectory() as folder:
            state = StudyRuntime(
                records,
                LocalObjects(folder),
                b"synthetic-smoke-key",
                TestStudyProvider(),
            )
            subject = AcademicService(records).create(
                uid,
                "subjects",
                {"name": "Smoke H2 sintético", "illustrationId": "circuit"},
            )
            content = b"Ley de Ohm: V = I R. La resistencia limita la corriente."
            ticket = state.uploads.create(
                uid,
                subject["id"],
                {
                    "name": "Apunte sintético",
                    "mediaType": "text/plain",
                    "size": len(content),
                    "sha256": digest(content),
                },
            )
            receipt = state.uploads.put(
                uid,
                ticket["uploadId"],
                ticket["requiredHeaders"]["X-Upload-Token"],
                content,
            )
            accepted = state.uploads.complete(
                uid, ticket["uploadId"], receipt["generation"], "smoke-upload"
            )
            assert (
                records.get(uid, "outbox", accepted["job"]["id"])["status"] == "pending"
            )
            try:
                pending_matched = any(
                    job["id"] == accepted["job"]["id"] for job in records.pending_jobs()
                )
                assert pending_matched
            except FailedPrecondition:
                pending_matched = False
            state.run_job(accepted["job"])
            assert state.materials.get(uid, ticket["materialId"])["status"] == "ready"
            conv = state.tutor.create(
                uid, {"subjectId": subject["id"], "materialIds": [ticket["materialId"]]}
            )
            turn = state.tutor.send(
                uid,
                conv["id"],
                {"question": "resistencia", "allowGeneralForTurn": False},
                "smoke-turn",
            )
            state.run_job(state.jobs.get(uid, turn["jobId"]))
            fresh = StudyRuntime(
                FirestoreRecords(project, credential),
                LocalObjects(folder),
                b"synthetic-smoke-key",
                TestStudyProvider(),
            )
            restored = fresh.tutor.turn(uid, turn["id"])
            assert restored["status"] == "succeeded" and restored["citations"]
            report.update(
                {
                    "outboxPersisted": True,
                    "pendingQueryMatched": pending_matched,
                    "materialReady": True,
                    "turnRecoveredWithFreshClient": True,
                    "citationsVerified": len(restored["citations"]),
                }
            )
    finally:
        # This unique UID is generated above, not accepted from input; delete only its fixture collections.
        assert re.fullmatch(r"h2-smoke-[a-f0-9]{32}", uid)
        for collection in (
            "subjects",
            "materials",
            "uploads",
            "jobs",
            "outbox",
            "idempotency",
            "usage",
            "jobLimits",
            "materialVersions",
            "conversations",
            "turns",
        ):
            for snapshot in records.collection(uid, collection).stream():
                snapshot.reference.delete()
                cleaned += 1
    report["fixtureDocumentsDeleted"] = cleaned
    print(json.dumps(report))


if __name__ == "__main__":
    main()
