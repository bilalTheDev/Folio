"""Database engine factory. Queries are added in a later phase."""

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from backend.app.config import Settings


def create_engine_from_settings(settings: Settings) -> AsyncEngine:
    """Create an async SQLAlchemy engine from DATABASE_URL.

    Expects a Neon Postgres URL. Converts postgres:// to postgresql+asyncpg://
    when needed. Does not open connections or run queries.
    """
    url = settings.database_url
    if not url:
        raise ValueError("DATABASE_URL is not set")

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return create_async_engine(url, pool_pre_ping=True)
