"""Clerk JWT verification for protected routes."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db import get_session
from backend.app.models import User

_bearer = HTTPBearer(auto_error=False)
_jwks_clients: dict[str, PyJWKClient] = {}


@dataclass(frozen=True)
class AuthUser:
    """Authenticated caller derived from a Clerk session JWT."""

    id: str
    email: str
    display_name: str | None


def _get_jwks_client(jwks_url: str) -> PyJWKClient:
    client = _jwks_clients.get(jwks_url)
    if client is None:
        client = PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)
        _jwks_clients[jwks_url] = client
    return client


def decode_clerk_token(token: str, settings: Settings) -> dict[str, Any]:
    """Verify a Clerk session JWT and return its claims."""
    if not settings.clerk_jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "auth_not_configured", "message": "CLERK_JWKS_URL is not set"},
        )

    try:
        jwks = _get_jwks_client(settings.clerk_jwks_url)
        signing_key = jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid or expired session"},
        ) from exc

    if claims.get("exp", 0) < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Session expired"},
        )
    return claims


async def ensure_user(session: AsyncSession, auth_user: AuthUser) -> User:
    """Create the local user row on first authenticated request."""
    result = await session.execute(select(User).where(User.id == auth_user.id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            id=auth_user.id,
            email=auth_user.email,
            display_name=auth_user.display_name,
        )
        session.add(user)
        await session.flush()
        return user

    if auth_user.email and user.email != auth_user.email:
        user.email = auth_user.email
    if auth_user.display_name and user.display_name != auth_user.display_name:
        user.display_name = auth_user.display_name
    return user


def claims_to_auth_user(claims: dict[str, Any]) -> AuthUser:
    """Map Clerk JWT claims to AuthUser."""
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Token missing subject"},
        )
    email = (
        claims.get("email")
        or claims.get("primary_email_address")
        or f"{sub}@users.clerk.local"
    )
    name = claims.get("name") or claims.get("full_name")
    return AuthUser(id=sub, email=str(email), display_name=name)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> AuthUser:
    """FastAPI dependency: require a valid Clerk Bearer token (no DB)."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Sign in required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = decode_clerk_token(credentials.credentials, settings)
    return claims_to_auth_user(claims)


async def get_current_db_user(
    user: AuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AuthUser:
    """Authenticated user with a local users row ensured."""
    await ensure_user(session, user)
    return user


async def warm_jwks(settings: Settings) -> None:
    """Best-effort JWKS prefetch so the first request is faster."""
    if not settings.clerk_jwks_url:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(settings.clerk_jwks_url)
        _get_jwks_client(settings.clerk_jwks_url)
    except Exception:
        return
