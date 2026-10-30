"""Daily usage counters."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import UsageDaily


async def get_or_create_usage(session: AsyncSession, user_id: str) -> UsageDaily:
    today = date.today()
    result = await session.execute(
        select(UsageDaily).where(UsageDaily.user_id == user_id, UsageDaily.day == today)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = UsageDaily(user_id=user_id, day=today, questions=0, uploads=0)
        session.add(row)
        await session.flush()
    return row


async def increment_questions(session: AsyncSession, user_id: str) -> int:
    row = await get_or_create_usage(session, user_id)
    row.questions += 1
    await session.flush()
    return row.questions
