from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.errors import AppError
from app.db import get_db
from app.deps import get_current_user
from app.models.user import HfTokenIn, ProviderIn, UserOut
from app.services.encryption import encrypt
from app.services.providers import is_allowed
from app.services.users import onboarding_state, to_user_out

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    return await to_user_out(db, user)


@router.patch("/me/hf-token", response_model=UserOut)
async def save_hf_token(
    body: HfTokenIn, user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)
):
    encrypted = encrypt(body.token)
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"hf_token_encrypted": encrypted}})
    user["hf_token_encrypted"] = encrypted
    return await to_user_out(db, user)


@router.patch("/me/provider", response_model=UserOut)
async def save_provider(
    body: ProviderIn, user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)
):
    if not is_allowed(body.provider, body.model):
        raise AppError(422, "invalid_provider", "That provider and model combination isn't supported.")
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"selected_provider": body.provider, "selected_model": body.model}},
    )
    user["selected_provider"] = body.provider
    user["selected_model"] = body.model
    return await to_user_out(db, user)


@router.patch("/me/onboarding", response_model=UserOut)
async def complete_onboarding(
    user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)
):
    state = await onboarding_state(db, user)
    if not state.has_document:
        raise AppError(409, "onboarding_upload", "Upload at least one document first.")
    if not state.has_token:
        raise AppError(409, "onboarding_token", "Save your Hugging Face token first.")
    if not state.has_provider:
        raise AppError(409, "onboarding_provider", "Choose a provider and model first.")
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"onboarding_completed": True}})
    user["onboarding_completed"] = True
    return await to_user_out(db, user)
