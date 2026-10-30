"""Vercel Python entrypoint. Exposes the FastAPI app under /api/*."""

from backend.app.main import app

__all__ = ["app"]
