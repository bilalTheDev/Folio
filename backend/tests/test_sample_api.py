"""Public sample trial endpoint tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app
from backend.app.security import rate_limit


@pytest.fixture(autouse=True)
def clear_rate_limits():
    rate_limit._hits.clear()
    yield
    rate_limit._hits.clear()


@pytest.mark.asyncio
async def test_get_sample_meta() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/sample",
            headers={"X-Forwarded-For": "203.0.113.10"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "sample"
    assert payload["is_sample"] is True
    assert payload["suggested_questions"]


@pytest.mark.asyncio
async def test_ask_sample_streams_offline_answer() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/sample/messages",
            json={"content": "What drove operating margin contraction?"},
            headers={"X-Forwarded-For": "203.0.113.11"},
        )
    assert response.status_code == 200
    body = response.text
    assert "event: meta" in body
    assert "event: citations" in body
    assert "event: token" in body
    assert "event: done" in body
    assert "is_sample" in body


@pytest.mark.asyncio
async def test_sample_daily_limit() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    headers = {"X-Forwarded-For": "203.0.113.12"}
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            ok = await client.post(
                "/api/sample/messages",
                json={"content": "How did logistics costs change?"},
                headers=headers,
            )
            assert ok.status_code == 200
        limited = await client.post(
            "/api/sample/messages",
            json={"content": "What offset international margin pressure?"},
            headers=headers,
        )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "daily_limit"
