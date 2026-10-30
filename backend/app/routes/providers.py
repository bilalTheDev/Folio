"""Provider catalog and key test endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.providers import list_providers_public
from backend.app.rag.generate import test_provider_key
from backend.app.security.auth import AuthUser, get_current_user

router = APIRouter(prefix="/providers", tags=["providers"])


class TestKeyIn(BaseModel):
    provider: str = Field(min_length=1)
    key: str = Field(min_length=8)


@router.get("")
async def get_providers() -> dict:
    """List supported providers and models."""
    return {"items": list_providers_public()}


@router.post("/test")
async def test_key(
    body: TestKeyIn,
    _user: AuthUser = Depends(get_current_user),
    x_provider_key: str | None = Header(default=None, alias="X-Provider-Key"),
) -> dict:
    """Test a provider key with a minimal request."""
    key = body.key or x_provider_key
    if not key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_key", "message": "Key is required"},
        )
    result = await test_provider_key(body.provider, key)
    return result
