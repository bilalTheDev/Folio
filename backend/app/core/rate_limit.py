from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.core.security import InvalidToken, decode_token


def _client_key(request: Request) -> str:
    """Limit signed-in calls per user and anonymous calls per IP."""
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        try:
            return f"user:{decode_token(auth[7:].strip(), 'access')}"
        except InvalidToken:
            pass
    return f"ip:{get_remote_address(request)}"


# In-memory storage: limits are per process. Use a shared backend (e.g. Redis) when running several workers.
limiter = Limiter(key_func=_client_key, enabled=settings.app_env != "test")

AUTH_LIMIT = settings.rate_limit_auth
UPLOAD_LIMIT = settings.rate_limit_upload
CHAT_LIMIT = settings.rate_limit_chat


async def rate_limit_handler(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Wait a moment and try again.", "code": "rate_limited"},
        headers={"Retry-After": "60"},
    )
