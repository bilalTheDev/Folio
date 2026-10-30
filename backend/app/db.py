"""Database engine and session helpers."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.config import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def normalize_database_url(url: str) -> str:
    """Convert a Neon URL to an asyncpg SQLAlchemy URL."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def create_engine_from_settings(settings: Settings) -> AsyncEngine:
    """Create an async SQLAlchemy engine from DATABASE_URL."""
    url = settings.database_url
    if not url:
        raise ValueError("DATABASE_URL is not set")

    return create_async_engine(
        normalize_database_url(url),
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
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
