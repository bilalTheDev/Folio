from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.config import settings

_client: AsyncIOMotorClient | None = None


def connect() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_uri, tz_aware=True, uuidRepresentation="standard")


def close() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_db() -> AsyncIOMotorDatabase:
    if _client is None:
        raise RuntimeError("MongoDB client is not connected")
    return _client[settings.mongodb_db_name]


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    await db.users.create_index([("email", ASCENDING)], unique=True)
    await db.documents.create_index([("user_id", ASCENDING), ("uploaded_at", DESCENDING)])
    await db.chat_sessions.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])
    await db.chat_messages.create_index([("session_id", ASCENDING), ("created_at", ASCENDING)])
