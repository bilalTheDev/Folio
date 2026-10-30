"""Print redacted DATABASE_URL shape from .env.local (no secrets)."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

root = Path(__file__).resolve().parents[1]
env = (root / ".env.local").read_text(encoding="utf-8")
for line in env.splitlines():
    if not line.startswith("DATABASE_URL"):
        continue
    key, value = line.split("=", 1)
    value = value.strip().strip('"').strip("'")
    redacted = re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", value)
    parsed = urlparse(value)
    print(f"{key}: {redacted}")
    print(f"  host={parsed.hostname} query={parsed.query}")
