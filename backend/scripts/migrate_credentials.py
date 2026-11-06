"""Move legacy hf_token_encrypted users onto the credentials array. Never logs tokens."""

import asyncio
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.db import close, connect, get_db  # noqa: E402
from app.services.users import migrate_legacy_credentials, needs_legacy_migration  # noqa: E402


async def main() -> None:
    connect()
    db = get_db()
    scanned = migrated = skipped = 0
    async for user in db.users.find({}):
        scanned += 1
        if not needs_legacy_migration(user):
            skipped += 1
            continue
        await migrate_legacy_credentials(db, user)
        migrated += 1
    close()
    print(f"scanned={scanned} migrated={migrated} skipped={skipped}")


if __name__ == "__main__":
    asyncio.run(main())
