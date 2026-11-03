from fastapi import APIRouter
from fastapi.responses import JSONResponse

from campus.api.errors import not_implemented_response
from campus.domain.contracts import ApiError

router = APIRouter(prefix="/api/v1", tags=["contracts"])


@router.get("/contracts", responses={501: {"model": ApiError}})
def contract_status() -> JSONResponse:
    """Deliberately visible until real domain routes are implemented."""
    return not_implemented_response()
