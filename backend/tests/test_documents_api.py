"""API-level document route tests with auth and DB overridden."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.db import get_session
from backend.app.main import create_app
from backend.app.models import Document
from backend.app.rag.validate import IngestError
from backend.app.security.auth import AuthUser, get_current_db_user, get_current_user


@pytest.fixture
def auth_user() -> AuthUser:
    return AuthUser(id="user_test_1", email="test@example.com", display_name="Tester")


@pytest.fixture
def app(auth_user: AuthUser):
    application = create_app()

    async def _override_user() -> AuthUser:
        return auth_user

    async def _override_session():
        session = AsyncMock()
        session.commit = AsyncMock()
        yield session

    application.dependency_overrides[get_current_user] = _override_user
    application.dependency_overrides[get_current_db_user] = _override_user
    application.dependency_overrides[get_session] = _override_session
    return application


@pytest.mark.asyncio
async def test_upload_requires_auth() -> None:
    application = create_app()

    async def _override_session():
        yield AsyncMock()

    application.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/documents",
            files={"file": ("note.txt", b"hello", "text/plain")},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_success(app, auth_user: AuthUser) -> None:
    doc = Document(
        id=uuid.uuid4(),
        user_id=auth_user.id,
        title="note",
        file_type="txt",
        byte_size=5,
        page_count=1,
        chunk_count=1,
        status="ready",
        is_sample=False,
        created_at=datetime.now(UTC),
    )

    with patch(
        "backend.app.services.documents.ingest_document",
        new=AsyncMock(return_value=doc),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/documents",
                files={"file": ("note.txt", b"hello", "text/plain")},
                headers={"Authorization": "Bearer test"},
            )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["title"] == "note"


@pytest.mark.asyncio
async def test_upload_too_large_maps_error(app) -> None:
    with patch(
        "backend.app.services.documents.ingest_document",
        new=AsyncMock(side_effect=IngestError("too_large", "File exceeds the 10 MB limit.")),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/documents",
                files={"file": ("big.txt", b"hello", "text/plain")},
                headers={"Authorization": "Bearer test"},
            )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "too_large"
