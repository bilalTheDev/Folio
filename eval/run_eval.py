"""RAG evaluation harness for the Folio sample document (lexical baseline)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.rag.sample_index import retrieve_sample  # noqa: E402


def main() -> int:
    data = json.loads((Path(__file__).parent / "sample_eval.json").read_text(encoding="utf-8"))
    hits = 0
    not_invented_ok = 0
    invent_total = 0

    for item in data["questions"]:
        blocks = retrieve_sample(item["question"], top_k=6)
        pages = {b.page for b in blocks}
        expected = set(item.get("expected_pages") or [])
        if expected:
            if pages & expected:
                hits += 1
                status = "HIT"
            else:
                status = "MISS"
        else:
            status = "N/A"
        if item.get("must_not_invent"):
            invent_total += 1
            # Lexical baseline: empty expected means answer should refuse; we only check retrieval emptiness.
            if not blocks or max(b.score for b in blocks) < 0.15:
                not_invented_ok += 1
                invent_status = "OK"
            else:
                invent_status = "WEAK"
        else:
            invent_status = "-"
        print(
            f"{item['id']}: retrieval={status} pages={sorted(pages)} "
            f"invent_check={invent_status} q={item['question'][:60]}"
        )

    hit_rate = hits / max(sum(1 for q in data["questions"] if q.get("expected_pages")), 1)
    print()
    print(f"Retrieval hit rate (expected-page questions): {hit_rate:.0%}")
    if invent_total:
        print(
            f"Not-in-document checks passed: {not_invented_ok}/{invent_total}"
        )
    print("Note: full answer correctness requires a live provider run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
