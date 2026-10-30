"""FastAPI application factory for Folio."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.routes import health
from backend.app.security.logging_filter import install_logging_filter

APP_VERSION = "0.1.0"


def create_app() -> FastAPI:
    """Build and return the Folio FastAPI application."""
    settings = get_settings()
    on_vercel = os.getenv("VERCEL") == "1"
    is_development = settings.folio_env == "development"

    install_logging_filter()

    app = FastAPI(
        title="Folio API",
        version=APP_VERSION,
        root_path="/api" if on_vercel else "",
        docs_url="/docs" if is_development else None,
        redoc_url="/redoc" if is_development else None,
        openapi_url="/openapi.json" if is_development else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.folio_cors_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes are registered under /api so local tests and Vercel full-path
    # requests both hit GET /api/health.
    app.include_router(health.router, prefix="/api")

    return app


app = create_app()
