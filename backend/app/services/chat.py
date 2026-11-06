import re
from datetime import timedelta
from pathlib import Path

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.errors import AppError
from app.models.chat import MessageOut, SessionOut, SourceOut
from app.models.common import utcnow
from app.models.document import DocumentStatus
from app.services import llm, rag
from app.services.encryption import DecryptionError, decrypt
from app.services.providers import active_credential, is_complete

DEFAULT_TITLE = "Untitled chat"
HISTORY_LIMIT = 10
TITLE_LENGTH = 60
NO_CONTEXT_REPLY = (
    "I couldn't find anything in your indexed documents to answer that. "
    "Upload a document on the Documents page, or wait for indexing to finish, and ask again."
)
_CITE_RE = re.compile(r"\[(\d+)\]")
_TOKEN_RE = re.compile(r"[a-z0-9]{3,}", re.I)
_STOPWORDS = frozenset(
    "the a an and or of to in for with on at by from as is was are be this that it your you we they their our not here what".split()
)


def make_title(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= TITLE_LENGTH:
        return text
    cut = text[:TITLE_LENGTH].rsplit(" ", 1)[0]
    return f"{cut or text[:TITLE_LENGTH]}…"


async def owned_session(db: AsyncIOMotorDatabase, user: dict, session_id: ObjectId) -> dict:
    session = await db.chat_sessions.find_one({"_id": session_id, "user_id": user["_id"]})
    if session is None:
        raise AppError(404, "not_found", "Chat not found.")
    return session


def session_out(session: dict, last_message: str | None = None) -> SessionOut:
    return SessionOut(
        id=str(session["_id"]),
        title=session["title"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        last_message=last_message,
    )


async def last_messages(db: AsyncIOMotorDatabase, session_ids: list[ObjectId]) -> dict[ObjectId, str]:
    if not session_ids:
        return {}
    pipeline = [
        {"$match": {"session_id": {"$in": session_ids}}},
        {"$sort": {"created_at": -1}},
        {"$group": {"_id": "$session_id", "content": {"$first": "$content"}}},
    ]
    return {row["_id"]: row["content"][:200] async for row in db.chat_messages.aggregate(pipeline)}


async def list_sessions(db: AsyncIOMotorDatabase, user: dict, query: str | None, limit: int) -> list[SessionOut]:
    criteria: dict = {"user_id": user["_id"]}
    if query:
        criteria["title"] = {"$regex": re.escape(query), "$options": "i"}
    sessions = await db.chat_sessions.find(criteria).sort("updated_at", -1).limit(limit).to_list(limit)
    previews = await last_messages(db, [s["_id"] for s in sessions])
    return [session_out(s, previews.get(s["_id"])) for s in sessions]


async def _filenames(db: AsyncIOMotorDatabase, user: dict, messages: list[dict]) -> dict[ObjectId, str]:
    ids = {s["document_id"] for m in messages for s in m.get("sources", [])}
    if not ids:
        return {}
    cursor = db.documents.find({"_id": {"$in": list(ids)}, "user_id": user["_id"]}, {"filename": 1})
    return {d["_id"]: d["filename"] async for d in cursor}


def named_document_ids(question: str, documents: list[dict]) -> list[str] | None:
    """If the question names an uploaded file, restrict retrieval to those documents."""
    matched: list[str] = []
    for doc in documents:
        filename = (doc.get("filename") or "").strip()
        if not filename:
            continue
        stem = Path(filename).stem
        names = {filename.lower()}
        if stem:
            names.add(stem.lower())
        if any(re.search(rf"(?<![\w.]){re.escape(name)}(?![\w])", question, re.I) for name in names):
            matched.append(str(doc["_id"]))
    return matched or None


def _page_number(value) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _tokens(text: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOPWORDS}


def groundedness_warning(answer: str, sources: list[dict]) -> bool:
    """Cheap overlap check; never blocks the reply."""
    if not sources or not (answer or "").strip():
        return False
    if "couldn't find" in answer.lower():
        return False
    cited = {int(n) for n in _CITE_RE.findall(answer)}
    if cited and any(n < 1 or n > len(sources) for n in cited):
        return True
    chosen = [sources[n - 1] for n in sorted(cited) if 1 <= n <= len(sources)] or sources
    context = " ".join((s.get("parent_text") or s.get("chunk_text") or "") for s in chosen)
    answer_tokens = _tokens(answer)
    if not answer_tokens:
        return False
    overlap = len(answer_tokens & _tokens(context)) / len(answer_tokens)
    return overlap < 0.18


def _source_payload(source: dict) -> dict:
    return {
        "document_id": ObjectId(source["document_id"]),
        "chunk_text": source["chunk_text"],
        "page_or_section": source.get("page_or_section"),
        "section_heading": source.get("section_heading") or None,
        "page_number": _page_number(source.get("page_number")),
    }


def _message_out(message: dict, filenames: dict[ObjectId, str]) -> MessageOut:
    return MessageOut(
        id=str(message["_id"]),
        session_id=str(message["session_id"]),
        role=message["role"],
        content=message["content"],
        sources=[
            SourceOut(
                document_id=str(s["document_id"]),
                filename=filenames.get(s["document_id"]),
                chunk_text=s["chunk_text"],
                page_or_section=s.get("page_or_section"),
                section_heading=s.get("section_heading"),
                page_number=_page_number(s.get("page_number")),
            )
            for s in message.get("sources", [])
        ],
        created_at=message["created_at"],
        groundedness_warning=message.get("groundedness_warning"),
    )


async def messages_out(db: AsyncIOMotorDatabase, user: dict, messages: list[dict]) -> list[MessageOut]:
    filenames = await _filenames(db, user, messages)
    return [_message_out(m, filenames) for m in messages]


async def send_message(db: AsyncIOMotorDatabase, user: dict, session: dict, content: str):
    cred = active_credential(user)
    if not is_complete(cred):
        raise AppError(409, "missing_provider", "Choose a provider and model in Settings first.")

    history = (
        await db.chat_messages.find({"session_id": session["_id"]})
        .sort("created_at", -1)
        .limit(HISTORY_LIMIT)
        .to_list(HISTORY_LIMIT)
    )
    history.reverse()

    token = None
    try:
        token = decrypt(cred["token_encrypted"])
    except DecryptionError:
        token = None

    search_query = content
    if history and token:
        search_query = await llm.condense_query(
            token=token, credential=cred, question=content, history=history
        )

    indexed = await db.documents.find(
        {"user_id": user["_id"], "status": DocumentStatus.indexed.value}, {"filename": 1}
    ).to_list(500)
    document_ids = named_document_ids(content, indexed)
    sources = await rag.retrieve(user["_id"], search_query, document_ids=document_ids)
    warning = False
    if sources:
        if token is None:
            raise AppError(409, "token_unreadable", "Your saved token can't be read. Re-enter it in Settings.")
        reply = await llm.answer(
            token=token, credential=cred, question=content, history=history, sources=sources
        )
        warning = groundedness_warning(reply, sources)
        del token
    else:
        reply = NO_CONTEXT_REPLY
        if token:
            del token

    now = utcnow()
    user_message = {"session_id": session["_id"], "role": "user", "content": content, "sources": [], "created_at": now}
    assistant_message = {
        "session_id": session["_id"],
        "role": "assistant",
        "content": reply or "The model returned an empty answer. Try rephrasing the question.",
        "sources": [_source_payload(s) for s in sources],
        "groundedness_warning": warning,
        "created_at": now + timedelta(milliseconds=1),
    }
    await db.chat_messages.insert_many([user_message, assistant_message])

    update = {"updated_at": assistant_message["created_at"]}
    if session["title"] == DEFAULT_TITLE and not history:
        update["title"] = make_title(content)
    await db.chat_sessions.update_one({"_id": session["_id"]}, {"$set": update})
    session = {**session, **update}

    out_user, out_assistant = await messages_out(db, user, [user_message, assistant_message])
    return session_out(session, assistant_message["content"][:200]), out_user, out_assistant
