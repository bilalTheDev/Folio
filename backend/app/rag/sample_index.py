"""In-memory sample document index for the public trial flow."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from backend.app.rag.prompt import ContextBlock

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_report.txt"

SUGGESTED_QUESTIONS = [
    "What drove operating margin contraction in the international segment?",
    "How did logistics costs change year over year?",
    "What offset international margin pressure?",
]


@dataclass(frozen=True)
class SampleChunk:
    page: int
    content: str


@lru_cache
def load_sample_chunks() -> list[SampleChunk]:
    text = SAMPLE_PATH.read_text(encoding="utf-8")
    pages: list[SampleChunk] = []
    current_page = 1
    buffer: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("page ") and stripped[5:].split()[0].isdigit():
            if buffer:
                pages.append(SampleChunk(page=current_page, content="\n".join(buffer).strip()))
                buffer = []
            current_page = int(stripped.split()[1])
            continue
        if stripped:
            buffer.append(stripped)
    if buffer:
        pages.append(SampleChunk(page=current_page, content="\n".join(buffer).strip()))
    return pages


def sample_meta() -> dict:
    chunks = load_sample_chunks()
    return {
        "id": "sample",
        "title": "Folio Sample Report — Q3 Operations Overview",
        "page_count": len(chunks) or 3,
        "is_sample": True,
        "suggested_questions": SUGGESTED_QUESTIONS,
    }


def retrieve_sample(question: str, top_k: int = 3, min_score: float = 0.2) -> list[ContextBlock]:
    """Simple lexical retrieval over the sample report (no DB required)."""
    tokens = {t.lower().strip(".,?!") for t in question.split() if len(t) > 2}
    # Drop ultra-common tokens that inflate weak matches on branded sample text.
    tokens -= {"the", "and", "for", "what", "how", "did", "which", "folio", "this", "that"}
    scored: list[tuple[float, SampleChunk]] = []
    for chunk in load_sample_chunks():
        words = {t.lower().strip(".,?!") for t in chunk.content.split() if len(t) > 2}
        overlap = len(tokens & words)
        score = overlap / max(len(tokens), 1)
        scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    blocks: list[ContextBlock] = []
    for index, (score, chunk) in enumerate(scored[:top_k], start=1):
        if score < min_score:
            continue
        blocks.append(
            ContextBlock(
                marker=index,
                page=chunk.page,
                content=chunk.content,
                score=score,
                chunk_id=None,
            )
        )
    return blocks
