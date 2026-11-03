from fastapi.responses import JSONResponse

from campus.domain.contracts import ApiError


def not_implemented_response() -> JSONResponse:
    error = ApiError(
        code="not_implemented",
        message="Esta operación aún no está implementada.",
        request_id="local-request",
    )
    return JSONResponse(status_code=501, content=error.model_dump(by_alias=True))
