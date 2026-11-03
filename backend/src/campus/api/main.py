from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from campus.adapters.records import RevisionConflict
from campus.api.body_limit import BodyLimit
from campus.api.routes import contracts_router
from campus.api.routes.academic import router as academic_router
from campus.api.routes.study import router as study_router
from campus.services.academic import DomainError

app = FastAPI(title="Campus API")
app.include_router(contracts_router)
app.include_router(academic_router)
app.include_router(study_router)
app.add_middleware(BodyLimit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "PUT", "POST", "PATCH", "DELETE"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Idempotency-Key",
        "X-Upload-Token",
    ],
)


@app.middleware("http")
async def request_id(request: Request, call_next):
    request.state.request_id = uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    if request.url.path.startswith("/api/v1/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(DomainError)
async def domain_error(request: Request, error: DomainError):
    return JSONResponse(
        status_code=error.status,
        content={
            "code": f"error_{error.status}",
            "message": error.message,
            "requestId": request.state.request_id,
            "details": None,
        },
    )


@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_error(request: Request, error):
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Revisa los datos del formulario.",
            "requestId": request.state.request_id,
            "details": {
                "fields": [
                    ".".join(str(part) for part in item["loc"])
                    for item in error.errors()
                ]
            },
        },
    )


@app.exception_handler(RevisionConflict)
async def revision_error(request: Request, error):
    return JSONResponse(
        status_code=409,
        content={
            "code": "revision_conflict",
            "message": "Los datos cambiaron. Recarga la página.",
            "requestId": request.state.request_id,
            "details": None,
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
