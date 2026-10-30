"""Document upload, list, detail, and delete endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db import get_session
from backend.app.models import Document
from backend.app.rag.ingest import ingest_document
from backend.app.rag.validate import IngestError
from backend.app.schemas.documents import DocumentListOut, DocumentOut
from backend.app.security.auth import AuthUser, get_current_db_user

router = APIRouter(prefix="/documents", tags=["documents"])


def _http_for_ingest_error(exc: IngestError) -> HTTPException:
    code_map = {
        "too_large": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        "too_many_pages": status.HTTP_400_BAD_REQUEST,
        "too_many_chunks": status.HTTP_400_BAD_REQUEST,
        "invalid_type": status.HTTP_400_BAD_REQUEST,
        "empty": status.HTTP_400_BAD_REQUEST,
        "no_text": status.HTTP_400_BAD_REQUEST,
        "unreadable": status.HTTP_400_BAD_REQUEST,
        "document_limit": status.HTTP_403_FORBIDDEN,
        "upload_rate": status.HTTP_429_TOO_MANY_REQUESTS,
        "failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    return HTTPException(
        status_code=code_map.get(exc.code, status.HTTP_400_BAD_REQUEST),
        detail={"code": exc.code, "message": exc.message},
    )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Document:
    """Upload and ingest a PDF, DOCX, or TXT file."""
    data = await file.read()
    # Discard raw bytes after ingestion; do not persist the upload.
    try:
        document = await ingest_document(
            session=session,
            user=user,
            filename=file.filename or "upload.txt",
            data=data,
            settings=settings,
        )
    except IngestError as exc:
        # Persist the failed document row before the request session rolls back.
        await session.commit()
        raise _http_for_ingest_error(exc) from exc
    finally:
        del data

    return document


@router.get("", response_model=DocumentListOut)
async def list_documents(
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentListOut:
    """List the caller's documents, newest first."""
    result = await session.execute(
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())
    )
    items = list(result.scalars().all())
    return DocumentListOut(items=items, count=len(items))


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: uuid.UUID,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Document:
    """Return document detail and ingestion status."""
    result = await session.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Document not found"},
        )
    return document


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_document(
    document_id: uuid.UUID,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Delete a document and its chunks. Linked threads keep a null document_id."""
    result = await session.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Document not found"},
        )
    await session.delete(document)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
