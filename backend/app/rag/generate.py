"""RAG-facing generation helpers (no FastAPI imports)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from backend.app.providers import ProviderError, stream_chat, test_key
from backend.app.providers.catalog import get_provider
from backend.app.rag.prompt import ContextBlock, build_messages

# Re-export for existing callers/tests.
__all__ = [
    "ProviderError",
    "stream_chat_completion",
    "test_provider_key",
]


async def stream_chat_completion(
    *,
    provider_id: str,
    model: str | None,
    api_key: str,
    question: str,
    blocks: list[ContextBlock],
) -> AsyncIterator[str]:
    """Yield tokens for a grounded Q&A completion."""
    messages = build_messages(question, blocks)
    async for token in stream_chat(
        provider_id=provider_id,
        model=model,
        api_key=api_key,
        messages=messages,
    ):
        yield token


async def test_provider_key(provider_id: str, api_key: str) -> dict[str, Any]:
    """Validate a provider key with a minimal request."""
    return await test_key(provider_id, api_key)


def resolve_model(provider_id: str, model: str | None) -> str:
    """Return the model name, falling back to the provider default."""
    provider = get_provider(provider_id)
    return model or provider["default_model"]
