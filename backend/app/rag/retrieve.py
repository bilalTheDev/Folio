"""pgvector retrieval for a document's chunks."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.rag.embed import embed_texts
from backend.app.rag.prompt import ContextBlock

TOP_K = 6


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    page: int
    content: str
    score: float


async def retrieve_chunks(
    session: AsyncSession,
    *,
    document_id: uuid.UUID,
    question: str,
    top_k: int = TOP_K,
) -> list[RetrievedChunk]:
    """Embed the question and return top-k chunks by cosine distance."""
    vectors = embed_texts([question])
    if not vectors:
        return []
    query_vec = vectors[0]
    # pgvector expects a vector literal; asyncpg adapts list via string cast.
    vector_literal = "[" + ",".join(str(float(x)) for x in query_vec) + "]"

    sql = text(
        """
        SELECT
          id,
          page,
          content,
          1 - (embedding <=> CAST(:embedding AS vector)) AS score
        FROM document_chunks
        WHERE document_id = CAST(:document_id AS uuid)
        ORDER BY embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
        """
    )
    result = await session.execute(
        sql,
        {
            "embedding": vector_literal,
            "document_id": str(document_id),
            "top_k": top_k,
        },
    )
    rows = result.mappings().all()
    return [
        RetrievedChunk(
            chunk_id=row["id"],
            page=int(row["page"]),
            content=row["content"],
            score=float(row["score"] or 0.0),
        )
        for row in rows
    ]


def to_context_blocks(chunks: list[RetrievedChunk]) -> list[ContextBlock]:
    """Map retrieved chunks to numbered context blocks starting at 1."""
    return [
        ContextBlock(
            marker=index,
            page=chunk.page,
            content=chunk.content,
            score=chunk.score,
            chunk_id=str(chunk.chunk_id),
        )
        for index, chunk in enumerate(chunks, start=1)
    ]
