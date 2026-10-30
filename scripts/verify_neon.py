"""End-to-end Neon connectivity check using Folio settings + asyncpg/SQLAlchemy."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import text  # noqa: E402

from backend.app.config import get_settings  # noqa: E402
from backend.app.db import dispose_engine, get_engine  # noqa: E402


async def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    if not settings.app_database_url:
        print("FAIL: DATABASE_URL missing")
        return 1

    engine = get_engine()
    async with engine.connect() as conn:
        one = await conn.scalar(text("SELECT 1"))
        tables = await conn.scalar(
            text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' "
                "AND table_name IN ('users','documents','document_chunks','threads','messages')"
            )
        )
        ext = await conn.scalar(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
    await dispose_engine()

    print(f"SELECT 1 => {one}")
    print(f"core tables present => {tables}/5")
    print(f"pgvector => {ext}")
    print(f"neon_branch => {settings.neon_branch or '(unset)'}")
    ok = one == 1 and tables == 5 and ext == "vector"
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
