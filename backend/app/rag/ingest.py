"""Document ingestion orchestration: validate → extract → chunk → embed → store."""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings
from backend.app.models import Document, DocumentChunk, UsageDaily
from backend.app.rag.chunk import chunk_document
from backend.app.rag.embed import embed_texts
from backend.app.rag.extract import extract_text
from backend.app.rag.validate import IngestError, validate_upload
from backend.app.security.auth import AuthUser


async def _count_user_documents(session: AsyncSession, user_id: str) -> int:
    result = await session.execute(
        select(func.count()).select_from(Document).where(Document.user_id == user_id)
    )
    return int(result.scalar_one())


async def _uploads_in_last_hour(session: AsyncSession, user_id: str) -> int:
    # Approximate with today's upload counter; refined hourly window comes later.
    today = date.today()
    result = await session.execute(
        select(UsageDaily).where(UsageDaily.user_id == user_id, UsageDaily.day == today)
    )
    row = result.scalar_one_or_none()
    return int(row.uploads) if row else 0


async def _increment_uploads(session: AsyncSession, user_id: str) -> None:
    today = date.today()
    result = await session.execute(
        select(UsageDaily).where(UsageDaily.user_id == user_id, UsageDaily.day == today)
    )
    row = result.scalar_one_or_none()
    if row is None:
        session.add(UsageDaily(user_id=user_id, day=today, questions=0, uploads=1))
    else:
        row.uploads += 1


async def ingest_document(
    *,
    session: AsyncSession,
    user: AuthUser,
    filename: str,
    data: bytes,
    settings: Settings,
) -> Document:
    """Run the full ingestion pipeline and return the document row."""
    doc_count = await _count_user_documents(session, user.id)
    if doc_count >= settings.max_documents_per_user:
        raise IngestError(
            "document_limit",
            f"You can store up to {settings.max_documents_per_user} documents.",
        )

    uploads = await _uploads_in_last_hour(session, user.id)
    if uploads >= settings.uploads_per_hour:
        raise IngestError(
            "upload_rate",
            f"Upload limit reached ({settings.uploads_per_hour} per hour). Try later.",
        )

    validated = validate_upload(
        filename=filename,
        data=data,
        max_file_mb=settings.max_file_mb,
    )

    document = Document(
        user_id=user.id,
        title=validated.title,
        file_type=validated.file_type,
        byte_size=len(validated.data),
        page_count=0,
        chunk_count=0,
        status="extracting",
    )
    session.add(document)
    await session.flush()

    try:
        extracted = extract_text(validated.file_type, validated.data)
        if extracted.page_count > settings.max_pages:
            raise IngestError(
                "too_many_pages",
                f"Document has {extracted.page_count} pages; the limit is {settings.max_pages}.",
            )

        document.page_count = extracted.page_count
        document.status = "embedding"
        await session.flush()

        chunks = chunk_document(extracted, max_chunks=settings.max_chunks_per_document)
        vectors = embed_texts([chunk.content for chunk in chunks])

        for chunk, vector in zip(chunks, vectors, strict=True):
            session.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    page=chunk.page,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    embedding=vector,
                )
            )

        document.chunk_count = len(chunks)
        document.status = "ready"
        document.failure_reason = None
        await _increment_uploads(session, user.id)
        await session.flush()
        return document
    except IngestError as exc:
        document.status = "failed"
        document.failure_reason = exc.message
        await session.flush()
        raise
    except Exception as exc:
        document.status = "failed"
        document.failure_reason = "Ingestion failed unexpectedly."
        await session.flush()
        raise IngestError("failed", "Ingestion failed unexpectedly.") from exc
