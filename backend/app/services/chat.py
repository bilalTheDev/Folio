import re
from datetime import timedelta

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.errors import AppError
from app.models.chat import MessageOut, SessionOut, SourceOut
from app.models.common import utcnow
from app.services import llm, rag
from app.services.encryption import DecryptionError, decrypt
from app.services.providers import is_allowed

DEFAULT_TITLE = "Untitled chat"
HISTORY_LIMIT = 10
TITLE_LENGTH = 60
NO_CONTEXT_REPLY = (
    "I couldn't find anything in your indexed documents to answer that. "
    "Upload a document on the Documents page, or wait for indexing to finish, and ask again."
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
            )
            for s in message.get("sources", [])
        ],
        created_at=message["created_at"],
    )


async def messages_out(db: AsyncIOMotorDatabase, user: dict, messages: list[dict]) -> list[MessageOut]:
    filenames = await _filenames(db, user, messages)
    return [_message_out(m, filenames) for m in messages]


async def send_message(db: AsyncIOMotorDatabase, user: dict, session: dict, content: str):
    encrypted = user.get("hf_token_encrypted")
    provider, model = user.get("selected_provider"), user.get("selected_model")
    if not encrypted:
        raise AppError(409, "missing_token", "Add your Hugging Face token in Settings first.")
    if not provider or not model or not is_allowed(provider, model):
        raise AppError(409, "missing_provider", "Choose a provider and model in Settings first.")

    history = (
        await db.chat_messages.find({"session_id": session["_id"]})
        .sort("created_at", -1)
        .limit(HISTORY_LIMIT)
        .to_list(HISTORY_LIMIT)
    )
    history.reverse()

    sources = await rag.retrieve(user["_id"], content)
    if sources:
        try:
            hf_token = decrypt(encrypted)
        except DecryptionError:
            raise AppError(409, "token_unreadable", "Your saved token can't be read. Re-enter it in Settings.")
        reply = await llm.answer(
            hf_token=hf_token, provider=provider, model=model, question=content, history=history, sources=sources
        )
        del hf_token
    else:
        reply = NO_CONTEXT_REPLY

    now = utcnow()
    user_message = {"session_id": session["_id"], "role": "user", "content": content, "sources": [], "created_at": now}
    assistant_message = {
        "session_id": session["_id"],
        "role": "assistant",
        "content": reply or "The model returned an empty answer. Try rephrasing the question.",
        "sources": [
            {
                "document_id": ObjectId(s["document_id"]),
                "chunk_text": s["chunk_text"],
                "page_or_section": s.get("page_or_section"),
            }
            for s in sources
        ],
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
