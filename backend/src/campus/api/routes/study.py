import asyncio
import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import Response, StreamingResponse
from starlette.concurrency import run_in_threadpool

from campus.api.routes.academic import ActorDependency
from campus.api.study_runtime import StudyRuntime, study_runtime
from campus.domain.contracts import ContractModel, Page, SourceRef
from campus.domain.practice import (
    AttemptInput,
    AttemptRead,
    PassportRead,
    ProgressRead,
    ReviewInput,
    ReviewRead,
    StateInput,
    StateRead,
)
from campus.domain.resources import (
    ResourceChange,
    ResourceDetail,
    ResourceInput,
    ResourceRead,
    ResourceUpdate,
)
from campus.domain.study import (
    PERSONALITIES,
    BlockRead,
    ConversationInput,
    ConversationRead,
    ConversationUpdate,
    JobRead,
    MaterialAccepted,
    MaterialRead,
    ObjectReceipt,
    TranscriptInput,
    TurnInput,
    TurnRead,
    UploadComplete,
    UploadInput,
    UploadTicket,
)
from campus.services.academic import DomainError
from campus.services.paging import page_rows

router = APIRouter(prefix="/api/v1", tags=["study"])
State = Annotated[StudyRuntime, Depends(study_runtime)]
Idempotency = Annotated[
    str, Header(alias="Idempotency-Key", min_length=1, max_length=128)
]


def public_job(row):
    return {
        name: row.get(name)
        for name in (
            "id",
            "revision",
            "kind",
            "entityId",
            "status",
            "stage",
            "progress",
            "attempts",
            "result",
            "error",
            "usageUnknown",
            "usage",
            "createdAt",
        )
    }


def public_material(row):
    return {
        name: value
        for name, value in row.items()
        if name not in ("objectKey", "generation")
    }


@router.get("/catalog/personalities")
def personalities():
    return {"items": PERSONALITIES}


@router.post(
    "/subjects/{subject}/uploads", status_code=201, response_model=UploadTicket
)
def ticket(subject: str, body: UploadInput, actor: ActorDependency, state: State):
    return state.uploads.create(actor.uid, subject, body.model_dump(by_alias=True))


@router.put("/uploads/{key}/content", response_model=ObjectReceipt)
async def upload(
    key: str,
    request: Request,
    actor: ActorDependency,
    state: State,
    signature: Annotated[str, Header(alias="X-Upload-Token", max_length=128)],
):
    ticket = await run_in_threadpool(state.uploads.get, actor.uid, key)
    data = bytearray()
    async for part in request.stream():
        data.extend(part)
        if len(data) > ticket["size"]:
            raise DomainError(413, "La carga excede el tamaño autorizado.")
    return await run_in_threadpool(
        state.uploads.put, actor.uid, key, signature, bytes(data)
    )


@router.post(
    "/uploads/{key}/complete", status_code=202, response_model=MaterialAccepted
)
def complete(
    key: str,
    body: UploadComplete,
    actor: ActorDependency,
    state: State,
    idempotency: Idempotency,
):
    result = state.uploads.complete(actor.uid, key, body.generation, idempotency)
    return {
        "material": public_material(result["material"]),
        "job": public_job(result["job"]),
    }


@router.get("/subjects/{subject}/materials", response_model=Page[MaterialRead])
def materials(
    subject: str,
    actor: ActorDependency,
    state: State,
    limit: int = Query(default=50, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=512),
):
    return page_rows(
        [public_material(m) for m in state.materials.list(actor.uid, subject)],
        actor.uid,
        f"materials:{subject}",
        limit,
        cursor,
    )


@router.get("/materials/{key}", response_model=MaterialRead)
def material(key: str, actor: ActorDependency, state: State):
    row = state.materials.get(actor.uid, key)
    result = public_material(row)
    if row.get("extractionVersion"):
        result["blocks"] = state.materials.version(actor.uid, key)
        result["suggestedTopicIds"] = state.materials.suggestions(actor.uid, key)
    return result


@router.get("/materials/{key}/original")
def original(key: str, actor: ActorDependency, state: State):
    row = state.materials.get(actor.uid, key)
    return Response(
        state.objects.get(row["objectKey"], row["generation"]),
        media_type=row["mediaType"],
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": "attachment; filename=material",
        },
    )


@router.patch("/materials/{key}/transcript", response_model=MaterialRead)
def transcript(key: str, body: TranscriptInput, actor: ActorDependency, state: State):
    return public_material(
        state.materials.revise(
            actor.uid,
            key,
            body.expected_revision,
            [edit.model_dump(by_alias=True) for edit in body.edits],
            body.topic_ids,
        )
    )


@router.post("/citations/resolve", response_model=BlockRead)
def citation(body: SourceRef, actor: ActorDependency, state: State):
    return state.retrieval.citation(
        actor.uid, body.model_dump(by_alias=True, exclude_none=True)
    )


@router.get("/jobs/{key}", response_model=JobRead)
def job(key: str, actor: ActorDependency, state: State):
    return public_job(state.jobs.get(actor.uid, key))


@router.post("/jobs/{key}/cancel", response_model=JobRead)
def cancel(key: str, actor: ActorDependency, state: State):
    return public_job(state.cancel(actor.uid, key))


class AccountDeletion(ContractModel):
    confirm: Literal["ELIMINAR"]


@router.post("/me/delete", status_code=204)
def delete_account(body: AccountDeletion, actor: ActorDependency, state: State):
    state.delete_account_data(actor.uid)
    return Response(status_code=204)


class RetryInput(ContractModel):
    accept_possible_charge: bool = False


@router.post("/jobs/{key}/retry", status_code=202, response_model=JobRead)
def retry(key: str, body: RetryInput, actor: ActorDependency, state: State):
    return public_job(state.retry(actor.uid, key, body.accept_possible_charge))


@router.post("/resources", status_code=202, response_model=ResourceDetail)
def create_resource(
    body: ResourceInput, actor: ActorDependency, state: State, idempotency: Idempotency
):
    return state.resources.create(
        actor.uid, body.model_dump(by_alias=True), idempotency
    )


@router.get("/subjects/{subject}/resources", response_model=Page[ResourceRead])
def resources(
    subject: str,
    actor: ActorDependency,
    state: State,
    archived: bool = False,
    limit: int = Query(default=50, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=512),
):
    return page_rows(
        state.resources.list(actor.uid, subject, archived),
        actor.uid,
        f"resources:{subject}:{archived}",
        limit,
        cursor,
    )


@router.get("/resources/{key}", response_model=ResourceDetail)
def get_resource(key: str, actor: ActorDependency, state: State):
    return state.resources.detail(actor.uid, key)


@router.patch("/resources/{key}", response_model=ResourceDetail)
def update_resource(
    key: str, body: ResourceUpdate, actor: ActorDependency, state: State
):
    return state.resources.update(actor.uid, key, body.model_dump(by_alias=True))


@router.post(
    "/resources/{key}/versions", status_code=202, response_model=ResourceDetail
)
def change_resource(
    key: str,
    body: ResourceChange,
    actor: ActorDependency,
    state: State,
    idempotency: Idempotency,
):
    return state.resources.change(
        actor.uid, key, body.model_dump(by_alias=True), idempotency
    )


@router.post(
    "/resources/versions/{key}/attempts", status_code=201, response_model=AttemptRead
)
def attempt(key: str, body: AttemptInput, actor: ActorDependency, state: State):
    return state.practice.attempt(actor.uid, key, body.model_dump(by_alias=True))


@router.get("/resources/versions/{key}/review", response_model=ReviewRead)
def get_review(key: str, actor: ActorDependency, state: State):
    return state.practice.get_review(actor.uid, key)


@router.put("/resources/versions/{key}/review", response_model=ReviewRead)
def put_review(key: str, body: ReviewInput, actor: ActorDependency, state: State):
    return state.practice.put_review(actor.uid, key, body.model_dump(by_alias=True))


@router.get("/resources/versions/{key}/state", response_model=StateRead)
def get_state(key: str, actor: ActorDependency, state: State):
    return state.practice.get_state(actor.uid, key)


@router.put("/resources/versions/{key}/state", response_model=StateRead)
def put_state(key: str, body: StateInput, actor: ActorDependency, state: State):
    return state.practice.put_state(actor.uid, key, body.model_dump(by_alias=True))


@router.delete("/resources/versions/{key}/state", status_code=204)
def delete_state(key: str, actor: ActorDependency, state: State):
    state.practice.delete_state(actor.uid, key)
    return Response(status_code=204)


@router.get("/subjects/{subject}/progress", response_model=ProgressRead)
def progress(subject: str, actor: ActorDependency, state: State):
    return state.practice.progress(actor.uid, subject)


@router.get("/passport", response_model=PassportRead)
def passport(actor: ActorDependency, state: State):
    return state.practice.passport(actor.uid)


@router.post("/conversations", status_code=201, response_model=ConversationRead)
def new_conversation(body: ConversationInput, actor: ActorDependency, state: State):
    return state.tutor.create(actor.uid, body.model_dump(by_alias=True))


@router.get("/conversations", response_model=Page[ConversationRead])
def conversations(
    actor: ActorDependency,
    state: State,
    subject_id: Annotated[str, Query(alias="subjectId")],
    limit: int = Query(default=50, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=512),
):
    if not state.records.get(actor.uid, "subjects", subject_id):
        raise DomainError(404, "No se encontró la materia.")
    return page_rows(
        [
            row
            for row in state.records.list(actor.uid, "conversations")
            if row["subjectId"] == subject_id
        ],
        actor.uid,
        f"conversations:{subject_id}",
        limit,
        cursor,
    )


@router.patch("/conversations/{key}", response_model=ConversationRead)
def update_conversation(
    key: str, body: ConversationUpdate, actor: ActorDependency, state: State
):
    return state.tutor.update(
        actor.uid,
        key,
        body.model_dump(by_alias=True, exclude={"expected_revision"}),
        body.expected_revision,
    )


@router.get("/conversations/{key}", response_model=ConversationRead)
def get_conversation(key: str, actor: ActorDependency, state: State):
    return state.tutor.conversation(actor.uid, key)


@router.get("/conversations/{key}/turns", response_model=Page[TurnRead])
def history(
    key: str,
    actor: ActorDependency,
    state: State,
    limit: int = Query(default=50, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=512),
):
    return page_rows(
        state.tutor.history(actor.uid, key), actor.uid, f"turns:{key}", limit, cursor
    )


@router.post("/conversations/{key}/turns", status_code=202, response_model=TurnRead)
def send_turn(
    key: str,
    body: TurnInput,
    actor: ActorDependency,
    state: State,
    idempotency: Idempotency,
):
    return state.tutor.send(actor.uid, key, body.model_dump(by_alias=True), idempotency)


@router.get("/turns/{key}", response_model=TurnRead)
def turn(key: str, actor: ActorDependency, state: State):
    return state.tutor.turn(actor.uid, key)


@router.get("/turns/{key}/events")
def events(
    key: str, actor: ActorDependency, state: State, after: int = Query(default=0, ge=0)
):
    state.tutor.turn(actor.uid, key)  # Authorize before starting a streaming response.

    async def stream():
        previous = after
        for _ in range(25):
            row = await run_in_threadpool(state.tutor.turn, actor.uid, key)
            if row["sequence"] > previous:
                event = (
                    "completed"
                    if row["status"] == "succeeded"
                    else "failed"
                    if row["status"] in ("failed", "canceled")
                    else row["status"]
                )
                payload = TurnRead.model_validate(row).model_dump(by_alias=True)
                yield f"id: {row['sequence']}\nevent: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
                previous = row["sequence"]
            else:
                yield ": heartbeat\n\n"
            if row["status"] in ("succeeded", "failed", "canceled"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
