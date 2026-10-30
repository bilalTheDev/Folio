"""Lightweight public rate-limit middleware helpers."""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.errors import error_body
from backend.app.security.rate_limit import allow_request, client_ip

PUBLIC_PREFIXES = ("/api/sample", "/api/health", "/api/providers")


class PublicRateLimitMiddleware(BaseHTTPMiddleware):
    """Apply LM-06 style limits to auth-free API prefixes."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES):
            ip = client_ip(
                dict(request.headers),
                fallback=request.client.host if request.client else "unknown",
            )
            allowed, retry_after = allow_request(
                f"public:{ip}",
                limit=30,
                window_seconds=60,
            )
            if not allowed:
                return Response(
                    content=__import__("json").dumps(
                        error_body("rate_limited", "Too many requests", retry_after)
                    ),
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(retry_after)},
                )
        return await call_next(request)
