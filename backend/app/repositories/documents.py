"""Document persistence helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Document


async def list_for_user(session: AsyncSession, user_id: str) -> list[Document]:
    result = await session.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())


async def get_owned(
    session: AsyncSession, document_id: uuid.UUID, user_id: str
) -> Document | None:
    result = await session.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def delete_owned(
    session: AsyncSession, document_id: uuid.UUID, user_id: str
) -> bool:
    document = await get_owned(session, document_id, user_id)
    if document is None:
        return False
    await session.delete(document)
    return True


async def count_for_user(session: AsyncSession, user_id: str) -> int:
    result = await session.execute(select(Document).where(Document.user_id == user_id))
    return len(list(result.scalars().all()))
