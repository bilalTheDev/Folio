"""Current user profile, settings, and remembered keys."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db import get_session
from backend.app.models import ProviderKey, User
from backend.app.security.auth import AuthUser, get_current_db_user
from backend.app.services import keys as keys_service
from backend.app.services.usage import get_or_create_usage

router = APIRouter(prefix="/me", tags=["me"])


class MeOut(BaseModel):
    id: str
    email: str
    display_name: str | None
    theme: str
    default_provider: str
    default_model: str | None
    usage: dict
    keys: list[dict]


class MeUpdate(BaseModel):
    theme: str | None = Field(default=None, pattern="^(dark|light|system)$")
    default_provider: str | None = None
    default_model: str | None = None
    display_name: str | None = None


class RememberKeyIn(BaseModel):
    provider: str
    key: str = Field(min_length=8)


@router.get("", response_model=MeOut)
async def get_me(
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MeOut:
    result = await session.execute(select(User).where(User.id == user.id))
    row = result.scalar_one()
    usage = await get_or_create_usage(session, user.id)
    keys_result = await session.execute(
        select(ProviderKey).where(ProviderKey.user_id == user.id)
    )
    keys = [
        {
            "provider": item.provider,
            "key_last4": item.key_last4,
            "created_at": item.created_at.isoformat(),
        }
        for item in keys_result.scalars().all()
    ]
    return MeOut(
        id=row.id,
        email=row.email,
        display_name=row.display_name,
        theme=row.theme,
        default_provider=row.default_provider,
        default_model=row.default_model,
        usage={
            "questions_today": usage.questions,
            "uploads_today": usage.uploads,
            "daily_question_limit": settings.daily_question_limit,
            "day": date.today().isoformat(),
        },
        keys=keys,
    )


@router.patch("", response_model=MeOut)
async def update_me(
    body: MeUpdate,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MeOut:
    result = await session.execute(select(User).where(User.id == user.id))
    row = result.scalar_one()
    if body.theme is not None:
        row.theme = body.theme
    if body.default_provider is not None:
        row.default_provider = body.default_provider
    if body.default_model is not None:
        row.default_model = body.default_model
    if body.display_name is not None:
        row.display_name = body.display_name
    await session.flush()
    return await get_me(user=user, session=session, settings=settings)


@router.post("/keys", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def remember_key(
    body: RememberKeyIn,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    await keys_service.remember_provider_key(
        session,
        user_id=user.id,
        provider=body.provider,
        key=body.key,
        settings=settings,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/keys/{provider}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_key(
    provider: str,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await keys_service.forget_provider_key(session, user_id=user.id, provider=provider)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
