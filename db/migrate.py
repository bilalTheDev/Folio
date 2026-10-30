"""Apply SQL migration files in db/migrations/ against DATABASE_URL."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import asyncpg


def _to_asyncpg_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


async def apply_migrations(database_url: str) -> None:
    migrations_dir = Path(__file__).resolve().parent / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("No migration files found.")
        return

    conn = await asyncpg.connect(_to_asyncpg_url(database_url))
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              filename TEXT PRIMARY KEY,
              applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        for path in files:
            exists = await conn.fetchval(
                "SELECT 1 FROM schema_migrations WHERE filename = $1", path.name
            )
            if exists:
                print(f"skip {path.name}")
                continue
            sql = path.read_text(encoding="utf-8")
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)", path.name
                )
            print(f"applied {path.name}")
    finally:
        await conn.close()


def main() -> None:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL is required", file=sys.stderr)
        sys.exit(1)
    asyncio.run(apply_migrations(url))


if __name__ == "__main__":
    main()
