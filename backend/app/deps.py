from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.errors import AppError
from app.core.security import InvalidToken, decode_token
from app.db import get_db
from app.services.users import migrate_legacy_credentials, needs_legacy_migration

_bearer = HTTPBearer(auto_error=False)


def _unauthorized(message: str = "Not authenticated.") -> AppError:
    return AppError(401, "not_authenticated", message)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        user_id = ObjectId(decode_token(credentials.credentials, "access"))
    except (InvalidToken, InvalidId):
        raise _unauthorized("Session expired. Sign in again.")
    user = await db.users.find_one({"_id": user_id})
    if user is None:
        raise _unauthorized()
    if needs_legacy_migration(user):
        user = await migrate_legacy_credentials(db, user)
    else:
        user.setdefault("credentials", [])
    return user


async def require_onboarded(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("onboarding_completed"):
        raise AppError(403, "onboarding_incomplete", "Finish onboarding before using chat.")
    return user
