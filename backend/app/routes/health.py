"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a simple health payload for probes and warm-up cron."""
    return {"status": "ok", "version": "0.1.0"}
