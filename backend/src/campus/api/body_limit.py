from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


class BodyLimit:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        upload = (
            scope["method"] == "PUT"
            and scope["path"].startswith("/api/v1/uploads/")
            and scope["path"].endswith("/content")
        )
        maximum = (20 if upload else 2) * 1024 * 1024
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = maximum + 1
        if declared > maximum:
            response = JSONResponse(
                status_code=413,
                content={
                    "code": "body_too_large",
                    "message": "La solicitud excede el límite permitido.",
                    "requestId": scope.get("state", {}).get("request_id", ""),
                    "details": None,
                },
            )
            return await response(scope, receive, send)
        size = 0

        async def bounded_receive():
            nonlocal size
            message = await receive()
            if message["type"] == "http.request":
                size += len(message.get("body", b""))
                if size > maximum:
                    raise HTTPException(
                        status_code=413,
                        detail="La solicitud excede el límite permitido.",
                    )
            return message

        await self.app(scope, bounded_receive, send)
