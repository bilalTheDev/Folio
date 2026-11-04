from bson import ObjectId
from fastapi import APIRouter, Depends, Query, Request, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.rate_limit import CHAT_LIMIT, limiter
from app.db import get_db
from app.deps import require_onboarded
from app.models.chat import ExchangeOut, MessageIn, MessageOut, SessionCreateIn, SessionOut, SessionRenameIn
from app.models.common import parse_object_id, utcnow
from app.services import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreateIn | None = None,
    user: dict = Depends(require_onboarded),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    now = utcnow()
    title = " ".join((body.title or "").split()) if body else ""
    session = {"_id": ObjectId(), "user_id": user["_id"], "title": title or chat_service.DEFAULT_TITLE,
               "created_at": now, "updated_at": now}
    await db.chat_sessions.insert_one(session)
    return chat_service.session_out(session)


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=100, ge=1, le=200),
    user: dict = Depends(require_onboarded),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    return await chat_service.list_sessions(db, user, q.strip() if q else None, limit)


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: str, user: dict = Depends(require_onboarded), db: AsyncIOMotorDatabase = Depends(get_db)
):
    session = await chat_service.owned_session(db, user, parse_object_id(session_id, "Chat"))
    return chat_service.session_out(session)


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def list_messages(
    session_id: str, user: dict = Depends(require_onboarded), db: AsyncIOMotorDatabase = Depends(get_db)
):
    session = await chat_service.owned_session(db, user, parse_object_id(session_id, "Chat"))
    messages = await db.chat_messages.find({"session_id": session["_id"]}).sort("created_at", 1).to_list(None)
    return await chat_service.messages_out(db, user, messages)


@router.post("/sessions/{session_id}/messages", response_model=ExchangeOut)
@limiter.limit(CHAT_LIMIT)
async def send_message(
    request: Request,
    session_id: str,
    body: MessageIn,
    user: dict = Depends(require_onboarded),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    session = await chat_service.owned_session(db, user, parse_object_id(session_id, "Chat"))
    session_out, user_message, assistant_message = await chat_service.send_message(db, user, session, body.content)
    return ExchangeOut(session=session_out, user_message=user_message, assistant_message=assistant_message)


@router.patch("/sessions/{session_id}", response_model=SessionOut)
async def rename_session(
    session_id: str,
    body: SessionRenameIn,
    user: dict = Depends(require_onboarded),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    session = await chat_service.owned_session(db, user, parse_object_id(session_id, "Chat"))
    now = utcnow()
    await db.chat_sessions.update_one(
        {"_id": session["_id"], "user_id": user["_id"]},
        {"$set": {"title": body.title, "updated_at": now}},
    )
    session["title"] = body.title
    session["updated_at"] = now
    return chat_service.session_out(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str, user: dict = Depends(require_onboarded), db: AsyncIOMotorDatabase = Depends(get_db)
):
    session = await chat_service.owned_session(db, user, parse_object_id(session_id, "Chat"))
    await db.chat_messages.delete_many({"session_id": session["_id"]})
    await db.chat_sessions.delete_one({"_id": session["_id"], "user_id": user["_id"]})
