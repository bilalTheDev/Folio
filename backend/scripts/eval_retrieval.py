"""Retrieval eval harness for Folio.

Run from the backend directory after ingest/embed/hybrid/rerank/query changes:

    python scripts/eval_retrieval.py

Retrieval-only by default (no live LLM). Pass --full to also score a mocked or live answer.

What should improve across phases:
  B  paraphrase questions (internal launch name)
  C  exact codes and amounts (ZX-4419, 18750.50)
  D  buried but relevant leaves rise into top-k
  E  follow-ups and filename-scoped questions (retrieval-only still checks the raw wording)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("MONGODB_DB_NAME", "folio_eval")
os.environ.setdefault("JWT_SECRET", "eval-access-secret-not-for-production-use-32+")
os.environ.setdefault("JWT_REFRESH_SECRET", "eval-refresh-secret-not-for-production-32+")
os.environ.setdefault("ENCRYPTION_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")

from bson import ObjectId  # noqa: E402

from app.config import settings  # noqa: E402
from app.services import rag  # noqa: E402
from app.services.storage import TXT  # noqa: E402

FIXTURE_DIR = BACKEND_DIR / "tests" / "fixtures" / "eval"
HANDBOOK = FIXTURE_DIR / "handbook.txt"
QUESTIONS = FIXTURE_DIR / "questions.json"


def _hit(sources: list[dict], expected: str) -> bool:
    needle = expected.lower()
    return any(needle in (s.get("chunk_text") or "").lower() for s in sources)


def _section_hit(sources: list[dict], expected: str) -> bool:
    needle = expected.lower()
    for source in sources:
        hay = " ".join(
            str(part)
            for part in (source.get("section_heading"), source.get("page_or_section"))
            if part
        ).lower()
        if needle in hay:
            return True
    return False


async def run_eval(top_k: int) -> int:
    rows = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="folio-eval-", ignore_cleanup_errors=True) as tmp:
        settings.storage_dir = Path(tmp)
        user_id = ObjectId()
        document_id = ObjectId()
        rag._ingest_sync(str(user_id), str(document_id), HANDBOOK, TXT, "handbook.txt")
        hits = section_hits = 0
        print(f"questions={len(rows)} top_k={top_k} embed={settings.embed_model} rerank={settings.rerank_enabled}")
        print("rerank uses the existing local embed model (no extra cross-encoder download)")
        for row in rows:
            sources = await rag.retrieve(user_id, row["question"], top_k=top_k)
            hit = _hit(sources, row["expected_substring"])
            section = _section_hit(sources, row["expected_section"])
            hits += int(hit)
            section_hits += int(section)
            mark = "ok" if hit and section else ("hit" if hit else "miss")
            print(f"  [{mark}] {row['question']}")
            if not hit:
                preview = " | ".join((s.get("chunk_text") or "").replace("\n", " ")[:80] for s in sources[:2])
                print(f"       expected {row['expected_substring']!r} in {preview!r}")
        total = len(rows)
        print(f"hit@{top_k}={hits}/{total} section={section_hits}/{total}")
        return 0 if hits == total else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Folio retrieval eval")
    parser.add_argument("--top-k", type=int, default=settings.retrieval_top_k)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Reserved for live/mocked LLM scoring. Retrieval-only is the default.",
    )
    args = parser.parse_args()
    if args.full:
        print("full mode is optional; scoring retrieval only (no live LLM in this run)")
    raise SystemExit(asyncio.run(run_eval(args.top_k)))


if __name__ == "__main__":
    main()
