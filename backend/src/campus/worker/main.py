"""Private HTTP worker for Tasks, or an explicit local persistent poller."""

import os
import time

from fastapi import Depends, FastAPI, Header, HTTPException
from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from pydantic import Field

from campus.adapters.records import RevisionConflict
from campus.api.study_runtime import study_runtime
from campus.domain.contracts import ContractModel
from campus.services.academic import DomainError

app = FastAPI(
    title="Campus private worker", docs_url=None, redoc_url=None, openapi_url=None
)


def invoker(authorization: str | None = Header(default=None)):
    audience = os.getenv("CAMPUS_WORKER_AUDIENCE")
    account = os.getenv("CAMPUS_TASK_INVOKER")
    if (
        not audience
        or not account
        or not authorization
        or not authorization.startswith("Bearer ")
    ):
        raise HTTPException(403, "Service identity required")
    try:
        claims = id_token.verify_oauth2_token(
            authorization[7:], GoogleRequest(), audience=audience
        )
    except (ValueError, GoogleAuthError):
        raise HTTPException(403, "Invalid service identity") from None
    if claims.get("email") != account or not claims.get("email_verified"):
        raise HTTPException(403, "Invoker not allowed")


class JobReference(ContractModel):
    owner_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,128}$")
    job_id: str = Field(pattern=r"^[a-f0-9]{32}$")


@app.post("/internal/jobs", dependencies=[Depends(invoker)])
def execute(body: JobReference):
    state = study_runtime()
    state.run_job(state.jobs.get(body.owner_id, body.job_id))
    return {"accepted": True}


def poll():
    if os.getenv("K_SERVICE"):
        raise RuntimeError("Use the authenticated HTTP worker on Cloud Run.")
    state = study_runtime()
    print("Worker local: trabajos persistentes; sin servidor público.", flush=True)
    while True:
        try:
            for reference in state.records.pending_jobs():
                state.run_job(reference)
        except (
            GoogleAPIError,
            GoogleAuthError,
            DomainError,
            RevisionConflict,
            OSError,
            ValueError,
        ):
            # Poll supervisor only: preserve queued work, don't log tokens/documents.
            print(
                "Worker: dependencia no disponible; se reintentará la consulta.",
                flush=True,
            )
        time.sleep(1)


if __name__ == "__main__":
    poll()
