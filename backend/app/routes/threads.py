"""Thread and streaming message endpoints."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.config import Settings, get_settings
from backend.app.db import get_session
from backend.app.models import Citation, Document, Message, Thread
from backend.app.providers import get_provider
from backend.app.rag.generate import ProviderError, stream_chat_completion
from backend.app.rag.prompt import citation_items
from backend.app.rag.retrieve import retrieve_chunks, to_context_blocks
from backend.app.routes.me import resolve_provider_key
from backend.app.schemas.threads import (
    AskMessageIn,
    MessageOut,
    ThreadCreate,
    ThreadListOut,
    ThreadOut,
    ThreadUpdate,
)
from backend.app.security.auth import AuthUser, get_current_db_user
from backend.app.services.usage import get_or_create_usage, increment_questions

router = APIRouter(prefix="/threads", tags=["threads"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


async def _get_owned_thread(
    session: AsyncSession, thread_id: uuid.UUID, user_id: str
) -> Thread:
    result = await session.execute(
        select(Thread).where(Thread.id == thread_id, Thread.user_id == user_id)
    )
    thread = result.scalar_one_or_none()
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Thread not found"},
        )
    return thread


@router.get("", response_model=ThreadListOut)
async def list_threads(
    document_id: uuid.UUID | None = None,
    q: str | None = Query(default=None, max_length=200),
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> ThreadListOut:
    stmt = select(Thread).where(Thread.user_id == user.id)
    if document_id:
        stmt = stmt.where(Thread.document_id == document_id)
    if q:
        stmt = stmt.where(Thread.title.ilike(f"%{q}%"))
    stmt = stmt.order_by(Thread.updated_at.desc())
    result = await session.execute(stmt)
    items = list(result.scalars().all())
    return ThreadListOut(items=items, count=len(items))


@router.post("", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
async def create_thread(
    body: ThreadCreate,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Thread:
    doc = await session.execute(
        select(Document).where(Document.id == body.document_id, Document.user_id == user.id)
    )
    if doc.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Document not found"},
        )
    title = (body.title or "New chat").strip()[:60] or "New chat"
    thread = Thread(user_id=user.id, document_id=body.document_id, title=title)
    session.add(thread)
    await session.flush()
    return thread


@router.patch("/{thread_id}", response_model=ThreadOut)
async def rename_thread(
    thread_id: uuid.UUID,
    body: ThreadUpdate,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Thread:
    thread = await _get_owned_thread(session, thread_id, user.id)
    thread.title = body.title.strip()[:200]
    thread.updated_at = datetime.now(UTC)
    await session.flush()
    return thread


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
    thread = await _get_owned_thread(session, thread_id, user.id)
    await session.delete(thread)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{thread_id}/messages", response_model=list[MessageOut])
async def list_messages(
    thread_id: uuid.UUID,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> list[Message]:
    await _get_owned_thread(session, thread_id, user.id)
    result = await session.execute(
        select(Message)
        .where(Message.thread_id == thread_id)
        .options(selectinload(Message.citations))
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().unique().all())


@router.get("/{thread_id}/export")
async def export_thread_markdown(
    thread_id: uuid.UUID,
    user: AuthUser = Depends(get_current_db_user),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Export a thread as Markdown (HI-04)."""
    thread = await _get_owned_thread(session, thread_id, user.id)
    result = await session.execute(
        select(Message)
        .where(Message.thread_id == thread_id)
        .options(selectinload(Message.citations))
        .order_by(Message.created_at.asc())
    )
    messages = list(result.scalars().unique().all())
    lines = [f"# {thread.title}", "", f"_Exported from Folio · thread `{thread.id}`_", ""]
    for message in messages:
        heading = "User" if message.role == "user" else "Assistant"
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(message.content)
        lines.append("")
        if message.role == "assistant" and message.citations:
            lines.append("### Sources")
            lines.append("")
            for cite in sorted(message.citations, key=lambda c: c.marker):
                lines.append(
                    f"- [{cite.marker}] page {cite.page} (score {cite.score:.2f}): "
                    f"{cite.excerpt}"
                )
            lines.append("")
    body = "\n".join(lines)
    filename = f"folio-thread-{thread_id}.md"
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
    """Ask a question; stream the answer as SSE."""
    if len(body.content) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "too_long", "message": "Question must be 1000 characters or fewer"},
        )

    thread = await _get_owned_thread(session, thread_id, user.id)
    if thread.document_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "not_found", "message": "Thread document was deleted"},
        )

    usage = await get_or_create_usage(session, user.id)
    if usage.questions >= settings.daily_question_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "daily_limit",
                "message": f"Daily question limit of {settings.daily_question_limit} reached",
            },
        )

    api_key = await resolve_provider_key(
        session,
        user_id=user.id,
        provider=body.provider,
        header_key=x_provider_key,
        settings=settings,
    )

    try:
        provider = get_provider(body.provider)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "provider_unavailable", "message": "Unknown provider"},
        ) from exc

    model_name = body.model or provider["default_model"]

    question_text = body.content.strip()

    # Regenerate: reuse the last user question when flagged.
    if body.regenerate:
        last_user = await session.execute(
            select(Message)
            .where(Message.thread_id == thread_id, Message.role == "user")
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        prior = last_user.scalar_one_or_none()
        if prior is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "not_found", "message": "No prior question to regenerate"},
            )
        question_text = prior.content
    else:
        existing = await session.execute(
            select(Message).where(Message.thread_id == thread_id).limit(1)
        )
        if existing.scalar_one_or_none() is None:
            thread.title = question_text[:60]
        session.add(
            Message(
                thread_id=thread.id,
                role="user",
                content=question_text,
            )
        )
        await session.flush()

    chunks = await retrieve_chunks(
        session, document_id=thread.document_id, question=question_text
    )
    blocks = to_context_blocks(chunks)
    cites = citation_items(blocks)

    async def event_stream() -> AsyncIterator[str]:
        yield _sse(
            "meta",
            {
                "thread_id": str(thread.id),
                "provider": body.provider,
                "model": model_name,
            },
        )
        yield _sse("citations", {"items": cites})

        answer_parts: list[str] = []
        stopped = False
        error_payload: dict | None = None

        try:
            async for token in stream_chat_completion(
                provider_id=body.provider,
                model=model_name,
                api_key=api_key,
                question=question_text,
                blocks=blocks,
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

        assistant = Message(
            thread_id=thread.id,
            role="assistant",
            content=content or "I could not find this in the document.",
            provider=body.provider,
            model=model_name,
            stopped=stopped,
        )
        session.add(assistant)
        await session.flush()

        for item in cites:
            chunk_uuid = None
            if item.get("chunk_id"):
                try:
                    chunk_uuid = uuid.UUID(str(item["chunk_id"]))
                except ValueError:
                    chunk_uuid = None
            session.add(
                Citation(
                    message_id=assistant.id,
                    marker=item["marker"],
                    chunk_id=chunk_uuid,
                    page=item["page"],
                    excerpt=item["excerpt"],
                    score=item["score"],
                )
            )

        await increment_questions(session, user.id)
        thread.updated_at = datetime.now(UTC)
        await session.commit()

        if not error_payload:
            yield _sse(
                "done",
                {"message_id": str(assistant.id), "stopped": stopped},
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
