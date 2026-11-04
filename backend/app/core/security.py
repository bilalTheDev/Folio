import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

TokenKind = Literal["access", "refresh"]

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


class InvalidToken(Exception):
    pass


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd.verify(password, password_hash)
    except ValueError:
        return False


def _secret(kind: TokenKind) -> str:
    return settings.jwt_secret if kind == "access" else settings.jwt_refresh_secret


def create_token(user_id: str, kind: TokenKind) -> str:
    now = datetime.now(timezone.utc)
    lifetime = (
        timedelta(minutes=settings.access_token_expire_minutes)
        if kind == "access"
        else timedelta(days=settings.refresh_token_expire_days)
    )
    payload = {
        "sub": user_id,
        "type": kind,
        "iat": now,
        "exp": now + lifetime,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, _secret(kind), algorithm=settings.jwt_algorithm)


def decode_token(token: str, kind: TokenKind) -> str:
    """Return the user id in a valid token of the given kind, or raise InvalidToken."""
    try:
        payload = jwt.decode(token, _secret(kind), algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidToken() from exc
    if payload.get("type") != kind or not payload.get("sub"):
        raise InvalidToken()
    return payload["sub"]
