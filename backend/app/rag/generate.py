"""OpenAI-compatible streaming generation for Folio providers."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from backend.app.providers import get_provider
from backend.app.rag.prompt import ContextBlock, build_messages


class ProviderError(Exception):
    def __init__(self, code: str, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retry_after = retry_after


async def stream_chat_completion(
    *,
    provider_id: str,
    model: str | None,
    api_key: str,
    question: str,
    blocks: list[ContextBlock],
) -> AsyncIterator[str]:
    """Yield plain text token fragments from the provider stream."""
    try:
        provider = get_provider(provider_id)
    except KeyError as exc:
        raise ProviderError("provider_unavailable", f"Unknown provider: {provider_id}") from exc

    model_name = model or provider["default_model"]
    url = provider["base_url"].rstrip("/") + "/chat/completions"
    payload: dict[str, Any] = {
        "model": model_name,
        "messages": build_messages(question, blocks),
        "stream": True,
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                if response.status_code == 401:
                    raise ProviderError("invalid_key", "Provider key is invalid.")
                if response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    retry = (
                        int(retry_after)
                        if retry_after and retry_after.isdigit()
                        else None
                    )
                    raise ProviderError(
                        "rate_limited",
                        "Provider rate limit reached.",
                        retry_after=retry,
                    )
                if response.status_code >= 400:
                    body = (await response.aread()).decode("utf-8", errors="replace")[:300]
                    raise ProviderError(
                        "provider_unavailable",
                        f"Provider error ({response.status_code}): {body}",
                    )

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        data = line[5:].strip()
                    else:
                        continue
                    if data == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = parsed.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")
                    if content:
                        yield content
    except ProviderError:
        raise
    except httpx.HTTPError as exc:
        raise ProviderError(
            "provider_unavailable",
            "Could not reach the inference provider.",
        ) from exc


async def test_provider_key(provider_id: str, api_key: str) -> dict[str, Any]:
    """Make a minimal non-streaming request to validate a key."""
    try:
        provider = get_provider(provider_id)
    except KeyError:
        return {"status": "invalid", "message": "Unknown provider"}

    url = provider["base_url"].rstrip("/") + "/chat/completions"
    payload = {
        "model": provider["default_model"],
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.HTTPError:
        return {"status": "invalid", "message": "Could not reach provider"}

    if response.status_code == 401:
        return {"status": "invalid", "message": "Invalid key"}
    if response.status_code == 429:
        return {"status": "rate_limited", "message": "Rate limited", "retry_after": 30}
    if response.status_code >= 400:
        return {
            "status": "invalid",
            "message": f"Provider returned {response.status_code}",
        }
    return {"status": "valid", "message": "Key works"}
