"""FastAPI application factory for Folio."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import documents, health, me, providers, sample, threads
from backend.app.api.limits import PublicRateLimitMiddleware
from backend.app.config import get_settings
from backend.app.db import dispose_engine
from backend.app.errors import register_exception_handlers
from backend.app.security.logging_filter import install_logging_filter

APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """App lifespan hooks."""
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    """Build and return the Folio FastAPI application."""
    settings = get_settings()

    install_logging_filter()

    app = FastAPI(
        title="Folio API",
        version=APP_VERSION,
        root_path="/api" if settings.on_vercel else "",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.folio_cors_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(PublicRateLimitMiddleware)

    app.include_router(health.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    app.include_router(threads.router, prefix="/api")
    app.include_router(providers.router, prefix="/api")
    app.include_router(me.router, prefix="/api")
    app.include_router(sample.router, prefix="/api")

    return app


app = create_app()
