"""Provider catalog and key test endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.deps import CurrentUserDep, ProviderKeyDep
from backend.app.errors import FolioError
from backend.app.providers import list_providers_public, test_key

router = APIRouter(prefix="/providers", tags=["providers"])


class TestKeyIn(BaseModel):
    provider: str = Field(min_length=1)
    key: str = Field(default="", min_length=0)


@router.get("")
async def get_providers() -> dict:
    return {"items": list_providers_public()}


@router.post("/test")
async def test_provider_key_route(
    body: TestKeyIn,
    _user: CurrentUserDep,
    x_provider_key: ProviderKeyDep,
) -> dict:
    key = body.key or x_provider_key
    if not key:
        raise FolioError("invalid_key", "Key is required", status_code=400)
    return await test_key(body.provider, key)
