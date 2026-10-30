"""Provider key resolution and remember/forget logic."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings
from backend.app.errors import FolioError
from backend.app.repositories import keys as keys_repo
from backend.app.security.crypto import CryptoError, decrypt_secret, encrypt_secret


async def remember_provider_key(
    session: AsyncSession,
    *,
    user_id: str,
    provider: str,
    key: str,
    settings: Settings,
) -> None:
    try:
        ciphertext, nonce = encrypt_secret(key, settings.folio_encryption_key)
    except CryptoError as exc:
        raise FolioError("crypto_unavailable", str(exc), status_code=503) from exc
    await keys_repo.upsert_key(
        session,
        user_id=user_id,
        provider=provider,
        ciphertext=ciphertext,
        nonce=nonce,
        last4=key[-4:],
    )


async def forget_provider_key(
    session: AsyncSession, *, user_id: str, provider: str
) -> None:
    await keys_repo.delete_key(session, user_id, provider)


async def resolve_provider_key(
    session: AsyncSession,
    *,
    user_id: str,
    provider: str,
    header_key: str | None,
    settings: Settings,
) -> str:
    """Prefer request header key; fall back to decrypted remembered key."""
    if header_key:
        return header_key
    row = await keys_repo.get_key(session, user_id, provider)
    if row is None:
        raise FolioError(
            "invalid_key",
            "Provide X-Provider-Key or remember a key in Settings",
            status_code=400,
        )
    try:
        return decrypt_secret(row.key_ciphertext, row.key_nonce, settings.folio_encryption_key)
    except CryptoError as exc:
        raise FolioError("crypto_unavailable", str(exc), status_code=503) from exc
