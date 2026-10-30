"""Document upload, list, detail, and delete endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db import get_session
from backend.app.models import Document
from backend.app.rag.validate import IngestError
from backend.app.schemas.documents import DocumentListOut, DocumentOut
from backend.app.security.auth import AuthUser, get_current_db_user
from backend.app.services import documents as documents_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Document:
    data = await file.read()
    try:
        document = await documents_service.upload_document(
            session,
            user=user,
            filename=file.filename or "upload.txt",
            data=data,
            settings=settings,
        )
    except IngestError as exc:
        await session.commit()
        raise documents_service.map_ingest_error(exc) from exc
    finally:
        del data
    return document


@router.get("", response_model=DocumentListOut)
async def list_documents(
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentListOut:
    items = await documents_service.list_documents(session, user.id)
    return DocumentListOut(items=items, count=len(items))


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: uuid.UUID,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Document:
    return await documents_service.get_document(session, document_id, user.id)


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
    await documents_service.delete_document(session, document_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
