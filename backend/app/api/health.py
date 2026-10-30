"""Health check endpoint."""

from fastapi import APIRouter
from sqlalchemy import text

from backend.app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a health payload; probes Neon when DATABASE_URL is configured."""
    settings = get_settings()
    payload: dict[str, str] = {
        "status": "ok",
        "version": "0.1.0",
        "database": "unconfigured",
    }
    if settings.neon_branch:
        payload["neon_branch"] = settings.neon_branch

    if not settings.app_database_url:
        return payload

    try:
        from backend.app.db import get_engine

        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            has_users = await conn.scalar(
                text(
                    "SELECT EXISTS ("
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'users'"
                    ")"
                )
            )
        payload["database"] = "ok"
        payload["schema"] = "ready" if has_users else "pending_migrations"
    except Exception as exc:  # noqa: BLE001
        payload["status"] = "degraded"
        payload["database"] = "error"
        payload["database_error"] = type(exc).__name__
    return payload
