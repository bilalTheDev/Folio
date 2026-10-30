"""Public sample-document trial endpoints."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.config import Settings, get_settings
from backend.app.rag.generate import ProviderError, stream_chat_completion
from backend.app.rag.prompt import citation_items
from backend.app.rag.sample_index import retrieve_sample, sample_meta
from backend.app.security.rate_limit import allow_request, client_ip

router = APIRouter(prefix="/sample", tags=["sample"])

# Per-IP trial questions per day (DM-03).
TRIAL_IP_DAILY_LIMIT = 5
# Auth-free endpoint burst limit (LM-06 style for sample).
TRIAL_IP_BURST_LIMIT = 30
TRIAL_IP_BURST_WINDOW = 60


class SampleAskIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    provider: str = "groq"
    model: str | None = None


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@router.get("")
async def get_sample(settings: Settings = Depends(get_settings)) -> dict:
    """Return sample document metadata and suggested questions."""
    if settings.folio_disable_trial:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "trial_disabled", "message": "Trial is disabled"},
        )
    return sample_meta()


@router.post("/messages")
async def ask_sample(
    body: SampleAskIn,
    request: Request,
    settings: Settings = Depends(get_settings),
    x_provider_key: str | None = Header(default=None, alias="X-Provider-Key"),
) -> StreamingResponse:
    """Trial question against the sample document (IP-limited, optional Folio key)."""
    if settings.folio_disable_trial:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "trial_disabled",
                "message": "Sign up and add your own key to continue.",
            },
        )

    fallback = request.client.host if request.client else "unknown"
    ip = client_ip(dict(request.headers), fallback=fallback)
    allowed_burst, retry_burst = allow_request(
        f"sample-burst:{ip}",
        limit=TRIAL_IP_BURST_LIMIT,
        window_seconds=TRIAL_IP_BURST_WINDOW,
    )
    if not allowed_burst:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "rate_limited",
                "message": "Too many requests. Try again shortly.",
                "retry_after": retry_burst,
            },
        )

    allowed_daily, retry_daily = allow_request(
        f"sample-daily:{ip}",
        limit=TRIAL_IP_DAILY_LIMIT,
        window_seconds=86_400,
    )
    if not allowed_daily:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "daily_limit",
                "message": "Trial limit reached for today. Sign up and add your own key.",
                "retry_after": retry_daily,
            },
        )

    # Prefer visitor key; else optional Folio-owned sample key.
    api_key = x_provider_key or os.getenv("FOLIO_SAMPLE_GROQ_KEY", "").strip()
    blocks = retrieve_sample(body.content)
    cites = citation_items(blocks)

    async def event_stream() -> AsyncIterator[str]:
        yield _sse(
            "meta",
            {
                "thread_id": "sample",
                "provider": body.provider,
                "model": body.model or "llama-3.1-8b-instant",
                "is_sample": True,
            },
        )
        yield _sse("citations", {"items": cites})

        if not api_key:
            # Deterministic offline answer for portfolio demos without a key.
            offline = (
                "International operating margins contracted about 240 bps, driven by FX "
                "translation variances and elevated EMEA logistics costs [1]. Logistics "
                "overhead rose 18% YoY [2], while North American manufacturing scale "
                "partially offset the pressure [3]."
                if blocks
                else "I could not find this in the document."
            )
            for word in offline.split(" "):
                yield _sse("token", {"text": word + " "})
            yield _sse("done", {"message_id": "sample-offline", "stopped": False})
            return

        try:
            async for token in stream_chat_completion(
                provider_id=body.provider,
                model=body.model,
                api_key=api_key,
                question=body.content,
                blocks=blocks,
            ):
                yield _sse("token", {"text": token})
            yield _sse("done", {"message_id": "sample-live", "stopped": False})
        except ProviderError as exc:
            yield _sse(
                "error",
                {
                    "code": exc.code,
                    "message": exc.message,
                    "retry_after": exc.retry_after,
                },
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
