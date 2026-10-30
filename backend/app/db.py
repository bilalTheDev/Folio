"""Database engine and session helpers."""

from __future__ import annotations

import ssl
from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.app.config import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def normalize_database_url(url: str) -> str:
    """Convert a Neon/libpq URL to an asyncpg SQLAlchemy URL.

    Drops libpq-only query params (sslmode, channel_binding) that asyncpg
    rejects; TLS is enabled via connect_args instead.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    filtered = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in {"sslmode", "channel_binding"}
    ]
    return urlunparse(parsed._replace(query=urlencode(filtered)))


def create_engine_from_settings(settings: Settings) -> AsyncEngine:
    """Create an async SQLAlchemy engine from DATABASE_URL (pooled preferred)."""
    url = settings.app_database_url
    if not url:
        raise ValueError("DATABASE_URL is not set")

    connect_args: dict = {"ssl": ssl.create_default_context()}
    if settings.on_vercel:
        return create_async_engine(
            normalize_database_url(url),
            poolclass=NullPool,
            connect_args=connect_args,
        )

    return create_async_engine(
        normalize_database_url(url),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args=connect_args,
    )


def get_engine() -> AsyncEngine:
    """Return the process-wide async engine, creating it on first use."""
    global _engine, _session_factory
    if _engine is None:
        settings = get_settings()
        _engine = create_engine_from_settings(settings)
        _session_factory = async_sessionmaker(
            _engine, class_=AsyncSession, expire_on_commit=False
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory, ensuring the engine exists."""
    get_engine()
    assert _session_factory is not None
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped async session."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Dispose the engine (used on app shutdown / tests)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
