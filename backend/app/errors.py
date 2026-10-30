"""Application error hierarchy and JSON error shape (PRD-aligned)."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class FolioError(Exception):
    """Base application error."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after


class UnauthorizedError(FolioError):
    def __init__(self, message: str = "Sign in required", code: str = "unauthorized") -> None:
        super().__init__(code, message, status_code=401)


class NotFoundError(FolioError):
    def __init__(self, message: str = "Not found", code: str = "not_found") -> None:
        super().__init__(code, message, status_code=404)


class RateLimitError(FolioError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "rate_limited",
        retry_after: int | None = None,
    ) -> None:
        super().__init__(code, message, status_code=429, retry_after=retry_after)


class ProviderAppError(FolioError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retry_after: int | None = None,
    ) -> None:
        status = 429 if code == "rate_limited" else 400
        if code == "provider_unavailable":
            status = 502
        super().__init__(code, message, status_code=status, retry_after=retry_after)


def error_body(code: str, message: str, retry_after: int | None = None) -> dict[str, Any]:
    """Canonical JSON error payload."""
    return {
        "error": {
            "code": code,
            "message": message,
            "retry_after": retry_after,
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Attach Folio error handlers to the FastAPI app."""

    @app.exception_handler(FolioError)
    async def folio_error_handler(_request: Request, exc: FolioError) -> JSONResponse:
        headers = {}
        if exc.retry_after is not None:
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.retry_after),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(part) for part in first.get("loc", []) if part != "body")
        msg = first.get("msg", "Invalid request")
        message = f"{loc}: {msg}" if loc else str(msg)
        return JSONResponse(
            status_code=422,
            content=error_body("validation_error", message),
        )
