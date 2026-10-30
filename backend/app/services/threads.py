"""Thread lifecycle and question orchestration helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import Settings
from backend.app.errors import FolioError, NotFoundError, RateLimitError
from backend.app.models import Citation, Document, Message, Thread
from backend.app.providers.catalog import get_provider
from backend.app.rag.prompt import citation_items
from backend.app.rag.retrieve import retrieve_chunks, to_context_blocks
from backend.app.repositories import threads as threads_repo
from backend.app.security.auth import AuthUser
from backend.app.services.keys import resolve_provider_key
from backend.app.services.usage import get_or_create_usage, increment_questions


async def list_threads(
    session: AsyncSession,
    user_id: str,
    *,
    document_id: uuid.UUID | None = None,
    q: str | None = None,
) -> list[Thread]:
    return await threads_repo.list_for_user(
        session, user_id, document_id=document_id, q=q
    )


async def create_thread(
    session: AsyncSession,
    *,
    user: AuthUser,
    document_id: uuid.UUID,
    title: str | None,
) -> Thread:
    doc = await session.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    if doc.scalar_one_or_none() is None:
        raise NotFoundError("Document not found")
    thread_title = (title or "New chat").strip()[:60] or "New chat"
    thread = Thread(user_id=user.id, document_id=document_id, title=thread_title)
    session.add(thread)
    await session.flush()
    return thread


async def get_owned_thread(
    session: AsyncSession, thread_id: uuid.UUID, user_id: str
) -> Thread:
    thread = await threads_repo.get_owned(session, thread_id, user_id)
    if thread is None:
        raise NotFoundError("Thread not found")
    return thread


async def rename_thread(
    session: AsyncSession, thread_id: uuid.UUID, user_id: str, title: str
) -> Thread:
    thread = await get_owned_thread(session, thread_id, user_id)
    thread.title = title.strip()[:200]
    thread.updated_at = datetime.now(UTC)
    await session.flush()
    return thread


async def delete_thread(session: AsyncSession, thread_id: uuid.UUID, user_id: str) -> None:
    thread = await get_owned_thread(session, thread_id, user_id)
    await session.delete(thread)


async def export_markdown(
    session: AsyncSession, thread_id: uuid.UUID, user_id: str
) -> tuple[str, str]:
    thread = await get_owned_thread(session, thread_id, user_id)
    messages = await threads_repo.list_messages(session, thread_id)
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
    filename = f"folio-thread-{thread_id}.md"
    return "\n".join(lines), filename


async def prepare_question(
    session: AsyncSession,
    *,
    thread_id: uuid.UUID,
    user: AuthUser,
    content: str,
    provider: str,
    model: str | None,
    regenerate: bool,
    header_key: str | None,
    settings: Settings,
) -> dict:
    """Validate limits, resolve key, retrieve context. Returns ask context dict."""
    if len(content) > 1000:
        raise FolioError(
            "too_long",
            "Question must be 1000 characters or fewer",
            status_code=400,
        )

    thread = await get_owned_thread(session, thread_id, user.id)
    if thread.document_id is None:
        raise FolioError(
            "not_found",
            "Thread document was deleted",
            status_code=400,
        )

    usage = await get_or_create_usage(session, user.id)
    if usage.questions >= settings.daily_question_limit:
        raise RateLimitError(
            f"Daily question limit of {settings.daily_question_limit} reached",
            code="daily_limit",
        )

    api_key = await resolve_provider_key(
        session,
        user_id=user.id,
        provider=provider,
        header_key=header_key,
        settings=settings,
    )

    try:
        provider_cfg = get_provider(provider)
    except KeyError as exc:
        raise FolioError(
            "provider_unavailable",
            "Unknown provider",
            status_code=400,
        ) from exc

    model_name = model or provider_cfg["default_model"]
    question_text = content.strip()

    if regenerate:
        last_user = await session.execute(
            select(Message)
            .where(Message.thread_id == thread_id, Message.role == "user")
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        prior = last_user.scalar_one_or_none()
        if prior is None:
            raise FolioError(
                "not_found",
                "No prior question to regenerate",
                status_code=400,
            )
        question_text = prior.content
    else:
        existing = await session.execute(
            select(Message).where(Message.thread_id == thread_id).limit(1)
        )
        if existing.scalar_one_or_none() is None:
            thread.title = question_text[:60]
        session.add(Message(thread_id=thread.id, role="user", content=question_text))
        await session.flush()

    chunks = await retrieve_chunks(
        session, document_id=thread.document_id, question=question_text
    )
    blocks = to_context_blocks(chunks)
    cites = citation_items(blocks)
    return {
        "thread": thread,
        "api_key": api_key,
        "provider": provider,
        "model_name": model_name,
        "question_text": question_text,
        "blocks": blocks,
        "cites": cites,
    }


async def persist_assistant_answer(
    session: AsyncSession,
    *,
    thread: Thread,
    user_id: str,
    content: str,
    provider: str,
    model_name: str,
    cites: list[dict],
    stopped: bool,
) -> Message:
    assistant = Message(
        thread_id=thread.id,
        role="assistant",
        content=content or "I could not find this in the document.",
        provider=provider,
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
    await increment_questions(session, user_id)
    thread.updated_at = datetime.now(UTC)
    await session.commit()
    return assistant
