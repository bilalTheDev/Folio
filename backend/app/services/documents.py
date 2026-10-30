"""Document upload/list/delete business logic."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings
from backend.app.errors import FolioError, NotFoundError
from backend.app.models import Document
from backend.app.rag.ingest import ingest_document
from backend.app.rag.validate import IngestError
from backend.app.repositories import documents as documents_repo
from backend.app.security.auth import AuthUser


async def upload_document(
    session: AsyncSession,
    *,
    user: AuthUser,
    filename: str,
    data: bytes,
    settings: Settings,
) -> Document:
    return await ingest_document(
        session=session,
        user=user,
        filename=filename,
        data=data,
        settings=settings,
    )


async def list_documents(session: AsyncSession, user_id: str) -> list[Document]:
    return await documents_repo.list_for_user(session, user_id)


async def get_document(
    session: AsyncSession, document_id: uuid.UUID, user_id: str
) -> Document:
    document = await documents_repo.get_owned(session, document_id, user_id)
    if document is None:
        raise NotFoundError("Document not found")
    return document


async def delete_document(
    session: AsyncSession, document_id: uuid.UUID, user_id: str
) -> None:
    deleted = await documents_repo.delete_owned(session, document_id, user_id)
    if not deleted:
        raise NotFoundError("Document not found")


def map_ingest_error(exc: IngestError) -> FolioError:
    code_map = {
        "too_large": 413,
        "too_many_pages": 400,
        "too_many_chunks": 400,
        "invalid_type": 400,
        "empty": 400,
        "no_text": 400,
        "unreadable": 400,
        "document_limit": 403,
        "upload_rate": 429,
        "failed": 500,
    }
    return FolioError(
        exc.code,
        exc.message,
        status_code=code_map.get(exc.code, 400),
    )
