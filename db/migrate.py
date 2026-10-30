"""Apply SQL migration files in db/migrations/ against DATABASE_URL.

Prefer DATABASE_URL_UNPOOLED (direct Neon endpoint) for migrations.
"""

from __future__ import annotations

import asyncio
import os
import ssl
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import asyncpg

ROOT = Path(__file__).resolve().parents[1]


def _load_env_files() -> None:
    """Load .env.local / .env without overriding existing process env."""
    for name in (".env.local", ".env"):
        path = ROOT / name
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def _to_asyncpg_url(url: str) -> str:
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlparse(url)
    filtered = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in {"sslmode", "channel_binding"}
    ]
    return urlunparse(parsed._replace(query=urlencode(filtered)))


async def apply_migrations(database_url: str) -> None:
    migrations_dir = Path(__file__).resolve().parent / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("No migration files found.")
        return

    conn = await asyncpg.connect(
        _to_asyncpg_url(database_url),
        ssl=ssl.create_default_context(),
    )
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
    _load_env_files()
    url = (
        os.getenv("DATABASE_URL_UNPOOLED", "").strip()
        or os.getenv("DATABASE_URL", "").strip()
    )
    if not url:
        print("DATABASE_URL or DATABASE_URL_UNPOOLED is required", file=sys.stderr)
        sys.exit(1)
    asyncio.run(apply_migrations(url))


if __name__ == "__main__":
    main()
