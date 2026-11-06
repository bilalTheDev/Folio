from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.common import utcnow
from app.models.user import CredentialOut, OnboardingState, UserOut
from app.services.encryption import DecryptionError, decrypt, mask_token
from app.services.providers import active_credential, is_complete

OLD_FIELDS = ("hf_token_encrypted", "selected_provider", "selected_model")


def _mask_encrypted(encrypted: str | None) -> str | None:
    if not encrypted:
        return None
    try:
        return mask_token(decrypt(encrypted))
    except DecryptionError:
        return "****"


def needs_legacy_migration(user: dict) -> bool:
    if user.get("hf_token_encrypted") or user.get("selected_provider") or user.get("selected_model"):
        return True
    return "credentials" not in user


def _legacy_provider(user: dict) -> str | None:
    provider = user.get("selected_provider")
    return "huggingface" if provider == "auto" else provider


async def migrate_legacy_credentials(db: AsyncIOMotorDatabase, user: dict) -> dict:
    """Move hf_token_encrypted + selected_* into credentials[]. Never drops a stored token."""
    if not needs_legacy_migration(user):
        user.setdefault("credentials", [])
        return user

    credentials = list(user.get("credentials") or [])
    encrypted = user.get("hf_token_encrypted")
    provider = _legacy_provider(user)
    model = user.get("selected_model")
    if encrypted and not any(c.get("token_encrypted") == encrypted for c in credentials):
        if provider and model:
            credentials.append(
                {
                    "provider": provider,
                    "auth_mode": "hf_inference_providers",
                    "token_encrypted": encrypted,
                    "model": model,
                    "added_at": user.get("created_at") or utcnow(),
                    "is_active": not any(c.get("is_active") for c in credentials),
                }
            )
        elif encrypted:
            credentials.append(
                {
                    "provider": provider or "huggingface",
                    "auth_mode": "hf_inference_providers",
                    "token_encrypted": encrypted,
                    "model": model or "",
                    "added_at": user.get("created_at") or utcnow(),
                    "is_active": not any(c.get("is_active") for c in credentials),
                }
            )

    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"credentials": credentials}, "$unset": {field: "" for field in OLD_FIELDS}},
    )
    user["credentials"] = credentials
    for field in OLD_FIELDS:
        user.pop(field, None)
    return user


def has_complete_credential(user: dict) -> bool:
    return any(is_complete(c) for c in user.get("credentials") or [])


def credential_out(cred: dict) -> CredentialOut:
    return CredentialOut(
        provider=cred["provider"],
        auth_mode=cred.get("auth_mode") or "",
        model=cred.get("model") or "",
        token_masked=_mask_encrypted(cred.get("token_encrypted")),
        is_active=bool(cred.get("is_active")),
        added_at=cred.get("added_at") or utcnow(),
    )


async def onboarding_state(db: AsyncIOMotorDatabase, user: dict) -> OnboardingState:
    has_document = (
        await db.documents.count_documents({"user_id": user["_id"], "status": {"$ne": "failed"}}, limit=1)
    ) > 0
    has_credential = has_complete_credential(user)
    if not has_document:
        next_step = "upload"
    elif not has_credential:
        next_step = "provider"
    else:
        next_step = "done"
    return OnboardingState(has_document=has_document, has_credential=has_credential, next_step=next_step)


async def to_user_out(db: AsyncIOMotorDatabase, user: dict) -> UserOut:
    user = await migrate_legacy_credentials(db, user) if needs_legacy_migration(user) else user
    user.setdefault("credentials", [])
    active = active_credential(user)
    return UserOut(
        id=str(user["_id"]),
        email=user["email"],
        created_at=user["created_at"],
        onboarding_completed=bool(user.get("onboarding_completed")),
        has_credential=has_complete_credential(user),
        token_masked=_mask_encrypted(active.get("token_encrypted") if active else None),
        selected_provider=active.get("provider") if active else None,
        selected_model=active.get("model") if active else None,
        auth_mode=active.get("auth_mode") if active else None,
        onboarding=await onboarding_state(db, user),
    )
