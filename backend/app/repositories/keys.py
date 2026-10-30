"""Remembered provider-key persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import ProviderKey


async def get_key(
    session: AsyncSession, user_id: str, provider: str
) -> ProviderKey | None:
    result = await session.execute(
        select(ProviderKey).where(
            ProviderKey.user_id == user_id, ProviderKey.provider == provider
        )
    )
    return result.scalar_one_or_none()


async def upsert_key(
    session: AsyncSession,
    *,
    user_id: str,
    provider: str,
    ciphertext: bytes,
    nonce: bytes,
    last4: str,
) -> ProviderKey:
    existing = await get_key(session, user_id, provider)
    if existing:
        existing.key_ciphertext = ciphertext
        existing.key_nonce = nonce
        existing.key_last4 = last4
        return existing
    row = ProviderKey(
        user_id=user_id,
        provider=provider,
        key_ciphertext=ciphertext,
        key_nonce=nonce,
        key_last4=last4,
    )
    session.add(row)
    await session.flush()
    return row


async def delete_key(session: AsyncSession, user_id: str, provider: str) -> bool:
    row = await get_key(session, user_id, provider)
    if row is None:
        return False
    await session.delete(row)
    return True
