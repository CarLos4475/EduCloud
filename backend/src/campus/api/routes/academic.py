from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel

from campus.api.dependencies import academic_service, current_actor
from campus.domain.academic import MODELS, READ_MODELS, UPDATE_MODELS, ProfileUpdate
from campus.domain.contracts import Actor, Page
from campus.services.academic import ILLUSTRATIONS, AcademicService, DomainError

router = APIRouter(prefix="/api/v1", tags=["academic"])
ActorDependency = Annotated[Actor, Depends(current_actor)]
ServiceDependency = Annotated[AcademicService, Depends(academic_service)]


@router.get("/catalog/illustrations")
def illustrations():
    return {"items": ILLUSTRATIONS}


@router.get("/me")
def me(actor: ActorDependency, service: ServiceDependency):
    row = service.records.get(actor.uid, "profiles", "me")
    return row or {
        "id": "me",
        "revision": 0,
        "displayName": "",
        "career": "",
        "timezone": "America/Mexico_City",
        "tutorialStep": 0,
    }


@router.put("/me")
@router.patch("/me")
def update_profile(
    body: ProfileUpdate, actor: ActorDependency, service: ServiceDependency
):
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        ZoneInfo(body.timezone)
    except ZoneInfoNotFoundError:
        raise DomainError(422, "La zona horaria no es válida.") from None
    current = service.records.get(actor.uid, "profiles", "me")
    revision = current["revision"] if current else None
    if body.expected_revision != (revision or 0):
        raise DomainError(
            409, "Tu perfil cambió en otra sesión. Recarga para continuar."
        )
    row = {
        **body.model_dump(mode="json", by_alias=True, exclude={"expected_revision"}),
        "id": "me",
        "revision": (revision or 0) + 1,
    }
    service.records.save(actor.uid, "profiles", "me", row, revision)
    return row


def register(collection: str, model: type[BaseModel], update_model: type[BaseModel]):
    def listing(
        actor: ActorDependency,
        service: ServiceDependency,
        limit: int = Query(default=50, ge=1, le=50),
        cursor: str | None = Query(default=None, max_length=128),
    ):
        rows = service.list(actor.uid, collection)
        if cursor:
            rows = [r for r in rows if r["id"] > cursor]
        page = rows[:limit]
        return {
            "items": page,
            "nextCursor": page[-1]["id"] if len(rows) > limit else None,
        }

    def get(key: str, actor: ActorDependency, service: ServiceDependency):
        return service.get(actor.uid, collection, key)

    def create(body, actor: ActorDependency, service: ServiceDependency):
        return service.create(
            actor.uid, collection, body.model_dump(mode="json", by_alias=True)
        )

    def update(key: str, body, actor: ActorDependency, service: ServiceDependency):
        data = body.model_dump(mode="json", by_alias=True, exclude_unset=True)
        expected = data.pop("expectedRevision")
        # Revalidate the merged object with the create model: null must not bypass field rules.
        existing = service.get(actor.uid, collection, key)
        editable = {
            k: v
            for k, v in existing.items()
            if k not in ("id", "revision", "createdAt", "updatedAt")
        }
        validated = model.model_validate({**editable, **data}).model_dump(
            mode="json", by_alias=True
        )
        return service.update(actor.uid, collection, key, validated, expected)

    def remove(key: str, actor: ActorDependency, service: ServiceDependency):
        service.delete(actor.uid, collection, key)
        return Response(status_code=204)

    create.__annotations__["body"] = model
    update.__annotations__["body"] = update_model
    routes: list[tuple[str, Callable[..., Any], str, int]] = [
        ("", listing, "GET", 200),
        ("/{key}", get, "GET", 200),
        ("", create, "POST", 201),
        ("/{key}", update, "PATCH", 200),
        ("/{key}", remove, "DELETE", 204),
    ]
    for path, fn, method, code in routes:
        router.add_api_route(
            "/" + collection + path,
            fn,
            methods=[method],
            status_code=code,
            name=f"{collection}_{fn.__name__}",
            response_model=(
                None
                if method == "DELETE"
                else Page.__class_getitem__(READ_MODELS[collection])
                if fn is listing
                else READ_MODELS[collection]
            ),
        )


for collection, model in MODELS.items():
    register(collection, model, UPDATE_MODELS[collection])
