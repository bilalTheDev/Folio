"""Thread and streaming message endpoints."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Header, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings, get_settings
from backend.app.db import get_session
from backend.app.models import Thread
from backend.app.providers import ProviderError
from backend.app.rag.generate import stream_chat_completion
from backend.app.repositories import threads as threads_repo
from backend.app.schemas.threads import (
    AskMessageIn,
    MessageOut,
    ThreadCreate,
    ThreadListOut,
    ThreadOut,
    ThreadUpdate,
)
from backend.app.security.auth import AuthUser, get_current_db_user
from backend.app.services import threads as threads_service

router = APIRouter(prefix="/threads", tags=["threads"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@router.get("", response_model=ThreadListOut)
async def list_threads(
    document_id: uuid.UUID | None = None,
    q: str | None = Query(default=None, max_length=200),
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> ThreadListOut:
    items = await threads_service.list_threads(
        session, user.id, document_id=document_id, q=q
    )
    return ThreadListOut(items=items, count=len(items))


@router.post("", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
async def create_thread(
    body: ThreadCreate,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Thread:
    return await threads_service.create_thread(
        session, user=user, document_id=body.document_id, title=body.title
    )


@router.patch("/{thread_id}", response_model=ThreadOut)
async def rename_thread(
    thread_id: uuid.UUID,
    body: ThreadUpdate,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Thread:
    return await threads_service.rename_thread(session, thread_id, user.id, body.title)


@router.delete(
    "/{thread_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_thread(
    thread_id: uuid.UUID,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await threads_service.delete_thread(session, thread_id, user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{thread_id}/messages", response_model=list[MessageOut])
async def list_messages(
    thread_id: uuid.UUID,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> list:
    await threads_service.get_owned_thread(session, thread_id, user.id)
    return await threads_repo.list_messages(session, thread_id)


@router.get("/{thread_id}/export")
async def export_thread_markdown(
    thread_id: uuid.UUID,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    body, filename = await threads_service.export_markdown(session, thread_id, user.id)
    return Response(
        content=body,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{thread_id}/messages")
async def ask_question(
    thread_id: uuid.UUID,
    body: AskMessageIn,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    x_provider_key: str | None = Header(default=None, alias="X-Provider-Key"),
) -> StreamingResponse:
    ctx = await threads_service.prepare_question(
        session,
        thread_id=thread_id,
        user=user,
        content=body.content,
        provider=body.provider,
        model=body.model,
        regenerate=body.regenerate,
        header_key=x_provider_key,
        settings=settings,
    )
    thread = ctx["thread"]
    cites = ctx["cites"]

    async def event_stream() -> AsyncIterator[str]:
        yield _sse(
            "meta",
            {
                "thread_id": str(thread.id),
                "provider": ctx["provider"],
                "model": ctx["model_name"],
            },
        )
        yield _sse("citations", {"items": cites})

        answer_parts: list[str] = []
        error_payload: dict | None = None
        try:
            async for token in stream_chat_completion(
                provider_id=ctx["provider"],
                model=ctx["model_name"],
                api_key=ctx["api_key"],
                question=ctx["question_text"],
                blocks=ctx["blocks"],
            ):
                answer_parts.append(token)
                yield _sse("token", {"text": token})
        except ProviderError as exc:
            error_payload = {
                "code": exc.code,
                "message": exc.message,
                "retry_after": exc.retry_after,
            }
            yield _sse("error", error_payload)

        content = "".join(answer_parts).strip()
        if error_payload and not content:
            content = error_payload["message"]

        assistant = await threads_service.persist_assistant_answer(
            session,
            thread=thread,
            user_id=user.id,
            content=content,
            provider=ctx["provider"],
            model_name=ctx["model_name"],
            cites=cites,
            stopped=False,
        )
        if not error_payload:
            yield _sse(
                "done",
                {"message_id": str(assistant.id), "stopped": False},
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
