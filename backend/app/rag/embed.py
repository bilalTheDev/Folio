"""Embedding helpers using fastembed BAAI/bge-small-en-v1.5."""

from __future__ import annotations

import os
import threading
from functools import lru_cache

from fastembed import TextEmbedding

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384
EMBED_BATCH_SIZE = 32

_lock = threading.Lock()


def _cache_dir() -> str | None:
    """On Vercel, keep the model under /tmp so it stays out of the bundle."""
    if os.getenv("VERCEL") == "1":
        path = "/tmp/fastembed"
        os.makedirs(path, exist_ok=True)
        return path
    return os.getenv("FOLIO_EMBED_CACHE_DIR")


@lru_cache(maxsize=1)
def get_embedding_model() -> TextEmbedding:
    """Load (and cache) the CPU embedding model."""
    return TextEmbedding(model_name=EMBED_MODEL, cache_dir=_cache_dir())


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts in batches of 32. Returns float vectors of length 384."""
    if not texts:
        return []

    with _lock:
        model = get_embedding_model()
        vectors: list[list[float]] = []
        for start in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = texts[start : start + EMBED_BATCH_SIZE]
            for vector in model.embed(batch, batch_size=EMBED_BATCH_SIZE):
                arr = list(map(float, vector))
                if len(arr) != EMBED_DIM:
                    raise RuntimeError(
                        f"Unexpected embedding dimension {len(arr)}; expected {EMBED_DIM}"
                    )
                vectors.append(arr)
        return vectors
