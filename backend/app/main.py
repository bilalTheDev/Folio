from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.body_limit import BodySizeLimitMiddleware
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.core.rate_limit import limiter, rate_limit_handler
from app.db import close, connect, ensure_indexes, get_db
from app.routers import auth, chat, documents, health, providers, users
from app.services import rag, storage


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    storage.ensure_storage_root()
    connect()
    await ensure_indexes(get_db())
    if settings.app_env != "test":
        rag.warm_up()
        await rag.resume_pending(get_db())
    try:
        yield
    finally:
        close()


def create_app() -> FastAPI:
    application = FastAPI(
        title="Folio API",
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    register_error_handlers(application)

    # CORS first so preflight responses carry the right headers even after later middleware.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    application.add_middleware(
        BodySizeLimitMiddleware,
        max_bytes=settings.max_upload_bytes,
        path_prefixes=("/documents/upload",),
    )

    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(users.router)
    application.include_router(providers.router)
    application.include_router(documents.router)
    application.include_router(chat.router)
    return application


app = create_app()
