from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Room for the multipart envelope (boundaries, part headers) around a file at the limit.
MULTIPART_OVERHEAD = 64 * 1024


class BodySizeLimitMiddleware:
    """Reject oversized request bodies on upload paths before they are buffered.

    The declared Content-Length is checked first; the streamed byte count is enforced too,
    so chunked or mislabelled requests cannot slip past.
    """

    def __init__(self, app: ASGIApp, max_bytes: int, path_prefixes: tuple[str, ...]):
        self.app = app
        self.max_body = max_bytes + MULTIPART_OVERHEAD
        self.path_prefixes = path_prefixes
        self.limit_mb = max_bytes // (1024 * 1024)

    def _reject(self) -> JSONResponse:
        return JSONResponse(
            status_code=413,
            content={"detail": f"File is larger than the {self.limit_mb} MB limit.", "code": "file_too_large"},
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(self.path_prefixes):
            await self.app(scope, receive, send)
            return

        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    declared = 0
                if declared > self.max_body:
                    await self._reject()(scope, receive, send)
                    return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body:
                    raise HTTPException(413, f"File is larger than the {self.limit_mb} MB limit.")
            return message

        await self.app(scope, limited_receive, send)
