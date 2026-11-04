from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import OnboardingState, UserOut
from app.services.encryption import DecryptionError, decrypt, mask_token


def _masked(user: dict) -> str | None:
    encrypted = user.get("hf_token_encrypted")
    if not encrypted:
        return None
    try:
        return mask_token(decrypt(encrypted))
    except DecryptionError:
        return "hf_****"


async def onboarding_state(db: AsyncIOMotorDatabase, user: dict) -> OnboardingState:
    has_document = (
        await db.documents.count_documents({"user_id": user["_id"], "status": {"$ne": "failed"}}, limit=1)
    ) > 0
    has_token = bool(user.get("hf_token_encrypted"))
    has_provider = bool(user.get("selected_provider") and user.get("selected_model"))
    if not has_document:
        next_step = "upload"
    elif not has_token:
        next_step = "token"
    elif not has_provider:
        next_step = "provider"
    else:
        next_step = "done"
    return OnboardingState(
        has_document=has_document, has_token=has_token, has_provider=has_provider, next_step=next_step
    )


async def to_user_out(db: AsyncIOMotorDatabase, user: dict) -> UserOut:
    return UserOut(
        id=str(user["_id"]),
        email=user["email"],
        created_at=user["created_at"],
        onboarding_completed=bool(user.get("onboarding_completed")),
        has_hf_token=bool(user.get("hf_token_encrypted")),
        hf_token_masked=_masked(user),
        selected_provider=user.get("selected_provider"),
        selected_model=user.get("selected_model"),
        onboarding=await onboarding_state(db, user),
    )
