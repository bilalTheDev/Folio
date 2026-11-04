from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.services.providers import PROVIDERS

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("")
async def list_providers(_: dict = Depends(get_current_user)):
    return PROVIDERS
