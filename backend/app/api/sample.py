"""Public sample-document trial endpoints."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.config import Settings, get_settings
from backend.app.errors import FolioError, RateLimitError
from backend.app.providers import ProviderError
from backend.app.rag.generate import stream_chat_completion
from backend.app.rag.prompt import citation_items
from backend.app.rag.sample_index import retrieve_sample, sample_meta
from backend.app.security.rate_limit import allow_request, client_ip

router = APIRouter(prefix="/sample", tags=["sample"])

TRIAL_IP_DAILY_LIMIT = 5
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
    if settings.folio_disable_trial:
        raise FolioError("trial_disabled", "Trial is disabled", status_code=403)
    return sample_meta()


@router.post("/messages")
async def ask_sample(
    body: SampleAskIn,
    request: Request,
    settings: Settings = Depends(get_settings),
    x_provider_key: str | None = Header(default=None, alias="X-Provider-Key"),
) -> StreamingResponse:
    if settings.folio_disable_trial:
        raise FolioError(
            "trial_disabled",
            "Sign up and add your own key to continue.",
            status_code=403,
        )

    fallback = request.client.host if request.client else "unknown"
    ip = client_ip(dict(request.headers), fallback=fallback)
    allowed_burst, retry_burst = allow_request(
        f"sample-burst:{ip}",
        limit=TRIAL_IP_BURST_LIMIT,
        window_seconds=TRIAL_IP_BURST_WINDOW,
    )
    if not allowed_burst:
        raise RateLimitError(
            "Too many requests. Try again shortly.",
            retry_after=retry_burst,
        )

    allowed_daily, retry_daily = allow_request(
        f"sample-daily:{ip}",
        limit=TRIAL_IP_DAILY_LIMIT,
        window_seconds=86_400,
    )
    if not allowed_daily:
        raise RateLimitError(
            "Trial limit reached for today. Sign up and add your own key.",
            code="daily_limit",
            retry_after=retry_daily,
        )

    api_key = x_provider_key or settings.folio_sample_groq_key.strip()
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
