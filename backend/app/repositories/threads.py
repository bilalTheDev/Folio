"""Thread and message persistence helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models import Document, Message, Thread


async def list_for_user(
    session: AsyncSession,
    user_id: str,
    *,
    document_id: uuid.UUID | None = None,
    q: str | None = None,
) -> list[Thread]:
    stmt = select(Thread).where(Thread.user_id == user_id)
    if document_id:
        stmt = stmt.where(Thread.document_id == document_id)
    if q:
        pattern = f"%{q}%"
        # Title match; message-text match via exists-style OR on joined messages.
        msg_ids = select(Message.thread_id).where(Message.content.ilike(pattern))
        stmt = stmt.where(or_(Thread.title.ilike(pattern), Thread.id.in_(msg_ids)))
    stmt = stmt.order_by(Thread.updated_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_owned(session: AsyncSession, thread_id: uuid.UUID, user_id: str) -> Thread | None:
    result = await session.execute(
        select(Thread).where(Thread.id == thread_id, Thread.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def list_messages(session: AsyncSession, thread_id: uuid.UUID) -> list[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.thread_id == thread_id)
        .options(selectinload(Message.citations))
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().unique().all())


async def document_title_for_thread(session: AsyncSession, thread: Thread) -> str | None:
    if thread.document_id is None:
        return None
    result = await session.execute(select(Document).where(Document.id == thread.document_id))
    doc = result.scalar_one_or_none()
    return doc.title if doc else None
