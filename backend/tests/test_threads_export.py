"""Thread Markdown export tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.db import get_session
from backend.app.main import create_app
from backend.app.models import Citation, Message, Thread
from backend.app.security.auth import AuthUser, get_current_db_user, get_current_user


@pytest.fixture
def auth_user() -> AuthUser:
    return AuthUser(id="user_export", email="export@example.com", display_name="Exporter")


@pytest.mark.asyncio
async def test_export_thread_markdown(auth_user: AuthUser) -> None:
    thread_id = uuid.uuid4()
    thread = Thread(
        id=thread_id,
        user_id=auth_user.id,
        document_id=uuid.uuid4(),
        title="Margin drivers",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    user_msg = Message(
        id=uuid.uuid4(),
        thread_id=thread_id,
        role="user",
        content="What drove margins?",
        created_at=datetime.now(UTC),
    )
    assistant = Message(
        id=uuid.uuid4(),
        thread_id=thread_id,
        role="assistant",
        content="FX and logistics [1].",
        created_at=datetime.now(UTC),
        citations=[
            Citation(
                id=uuid.uuid4(),
                message_id=uuid.uuid4(),
                marker=1,
                page=14,
                excerpt="Margins contracted 240 bps",
                score=0.95,
            )
        ],
    )

    app = create_app()

    async def _override_user() -> AuthUser:
        return auth_user

    class _Result:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

        def scalars(self):
            return self

        def unique(self):
            return self

        def all(self):
            return self._value

    session = AsyncMock()
    calls = {"n": 0}

    async def _execute_ordered(_stmt):
        calls["n"] += 1
        if calls["n"] == 1:
            return _Result(thread)
        return _Result([user_msg, assistant])

    session.execute = AsyncMock(side_effect=_execute_ordered)

    async def _override_session():
        yield session

    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_current_db_user] = _override_user
    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/threads/{thread_id}/export",
            headers={"Authorization": "Bearer test"},
        )

    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    text = response.text
    assert "# Margin drivers" in text
    assert "## User" in text
    assert "What drove margins?" in text
    assert "## Assistant" in text
    assert "FX and logistics" in text
    assert "### Sources" in text
    assert "Margins contracted 240 bps" in text
