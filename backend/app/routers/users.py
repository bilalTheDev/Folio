from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.errors import AppError
from app.db import get_db
from app.deps import get_current_user
from app.models.common import utcnow
from app.models.user import CredentialActiveIn, CredentialIn, CredentialOut, UserOut
from app.services.encryption import encrypt
from app.services.providers import expected_prefix, is_allowed
from app.services.users import credential_out, onboarding_state, to_user_out

router = APIRouter(prefix="/users", tags=["users"])


def _validate_token(body: CredentialIn) -> None:
    prefix = expected_prefix(body.provider, body.auth_mode)
    if prefix and not body.token.startswith(prefix):
        raise AppError(422, "invalid_token", f"That key should start with {prefix}.")


def _deactivate_all(credentials: list[dict]) -> None:
    for cred in credentials:
        cred["is_active"] = False


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    return await to_user_out(db, user)


@router.get("/me/credentials", response_model=list[CredentialOut])
async def list_credentials(user: dict = Depends(get_current_user)):
    return [credential_out(c) for c in user.get("credentials") or []]


@router.patch("/me/credentials", response_model=UserOut)
async def save_credential(
    body: CredentialIn, user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)
):
    if not is_allowed(body.provider, body.auth_mode, body.model):
        raise AppError(422, "invalid_provider", "That provider, auth mode, and model combination isn't supported.")
    _validate_token(body)
    encrypted = encrypt(body.token)
    credentials = list(user.get("credentials") or [])
    _deactivate_all(credentials)
    existing = next((c for c in credentials if c.get("provider") == body.provider), None)
    now = utcnow()
    if existing:
        existing.update(
            {
                "auth_mode": body.auth_mode,
                "token_encrypted": encrypted,
                "model": body.model,
                "is_active": True,
            }
        )
    else:
        credentials.append(
            {
                "provider": body.provider,
                "auth_mode": body.auth_mode,
                "token_encrypted": encrypted,
                "model": body.model,
                "added_at": now,
                "is_active": True,
            }
        )
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"credentials": credentials}})
    user["credentials"] = credentials
    return await to_user_out(db, user)


@router.patch("/me/credentials/active", response_model=UserOut)
async def activate_credential(
    body: CredentialActiveIn, user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)
):
    credentials = list(user.get("credentials") or [])
    match = next((c for c in credentials if c.get("provider") == body.provider), None)
    if match is None:
        raise AppError(404, "not_found", "That provider isn't configured.")
    _deactivate_all(credentials)
    match["is_active"] = True
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"credentials": credentials}})
    user["credentials"] = credentials
    return await to_user_out(db, user)


@router.delete("/me/credentials/{provider}", response_model=UserOut)
async def delete_credential(
    provider: str, user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)
):
    credentials = list(user.get("credentials") or [])
    if not any(c.get("provider") == provider for c in credentials):
        raise AppError(404, "not_found", "That provider isn't configured.")
    if len(credentials) <= 1:
        raise AppError(409, "last_credential", "Add another provider before removing this one.")
    remaining = [c for c in credentials if c.get("provider") != provider]
    if not any(c.get("is_active") for c in remaining) and remaining:
        remaining[0]["is_active"] = True
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"credentials": remaining}})
    user["credentials"] = remaining
    return await to_user_out(db, user)


@router.patch("/me/onboarding", response_model=UserOut)
async def complete_onboarding(
    user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)
):
    state = await onboarding_state(db, user)
    if not state.has_document:
        raise AppError(409, "onboarding_upload", "Upload at least one document first.")
    if not state.has_credential:
        raise AppError(409, "onboarding_credential", "Save a provider API key first.")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"onboarding_completed": True}})
    user["onboarding_completed"] = True
    return await to_user_out(db, user)
