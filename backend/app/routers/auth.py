from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.config import settings
from app.core.cookies import clear_refresh_cookie, set_refresh_cookie
from app.core.errors import AppError
from app.core.rate_limit import AUTH_LIMIT, limiter
from app.core.security import InvalidToken, create_token, decode_token, hash_password, verify_password
from app.db import get_db
from app.models.common import utcnow
from app.models.user import AuthOut, SigninIn, SignupIn, UserOut
from app.services.users import to_user_out

router = APIRouter(prefix="/auth", tags=["auth"])

# Verifying against a real hash keeps response time the same whether or not the email exists.
_DUMMY_HASH = hash_password("folio-timing-equaliser")


async def _issue_session(db: AsyncIOMotorDatabase, user: dict, response: Response) -> AuthOut:
    user_id = str(user["_id"])
    set_refresh_cookie(response, create_token(user_id, "refresh"))
    return AuthOut(access_token=create_token(user_id, "access"), user=await to_user_out(db, user))


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_LIMIT)
async def signup(request: Request, body: SignupIn, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = {
        "email": body.email.lower(),
        "password_hash": hash_password(body.password),
        "created_at": utcnow(),
        "onboarding_completed": False,
        "credentials": [],
    }
    try:
        result = await db.users.insert_one(user)
    except DuplicateKeyError:
        raise AppError(409, "email_taken", "An account with this email already exists.")
    user["_id"] = result.inserted_id
    return await to_user_out(db, user)


@router.post("/signin", response_model=AuthOut)
@limiter.limit(AUTH_LIMIT)
async def signin(request: Request, body: SigninIn, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db.users.find_one({"email": body.email.lower()})
    valid = verify_password(body.password, user["password_hash"] if user else _DUMMY_HASH)
    if not user or not valid:
        raise AppError(401, "invalid_credentials", "Incorrect email or password.")
    return await _issue_session(db, user, response)


@router.post("/refresh", response_model=AuthOut)
@limiter.limit(AUTH_LIMIT)
async def refresh(request: Request, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    token = request.cookies.get(settings.refresh_cookie_name)
    if not token:
        raise AppError(401, "no_session", "Not signed in.")
    try:
        user_id = ObjectId(decode_token(token, "refresh"))
    except (InvalidToken, InvalidId):
        return _session_expired()
    user = await db.users.find_one({"_id": user_id})
    if user is None:
        return _session_expired()
    return await _issue_session(db, user, response)


def _session_expired() -> JSONResponse:
    response = JSONResponse(
        status_code=401, content={"detail": "Session expired. Sign in again.", "code": "session_expired"}
    )
    clear_refresh_cookie(response)
    return response


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
async def signout(response: Response):
    clear_refresh_cookie(response)
