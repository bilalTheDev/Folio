"""FastAPI dependencies shared across routers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header

from backend.app.config import Settings, get_settings
from backend.app.db import get_session
from backend.app.security.auth import AuthUser, get_current_db_user, get_current_user

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[object, Depends(get_session)]
CurrentUserDep = Annotated[AuthUser, Depends(get_current_user)]
CurrentDbUserDep = Annotated[AuthUser, Depends(get_current_db_user)]


def provider_key_header(
    x_provider_key: Annotated[str | None, Header(alias="X-Provider-Key")] = None,
) -> str | None:
    """Optional BYOK header for the current request only."""
    return x_provider_key


ProviderKeyDep = Annotated[str | None, Depends(provider_key_header)]

__all__ = [
    "CurrentDbUserDep",
    "CurrentUserDep",
    "ProviderKeyDep",
    "SessionDep",
    "SettingsDep",
    "get_session",
    "get_settings",
    "provider_key_header",
]
