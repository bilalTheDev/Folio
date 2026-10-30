"""Provider catalog route tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.main import create_app


@pytest.mark.asyncio
async def test_list_providers() -> None:
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/providers")
    assert response.status_code == 200
    items = response.json()["items"]
    ids = {item["id"] for item in items}
    assert {"groq", "cerebras", "novita", "huggingface"} <= ids
