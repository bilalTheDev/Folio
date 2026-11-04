from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SessionCreateIn(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class SessionRenameIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def strip(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Title cannot be empty")
        return value


class SessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    last_message: str | None = None


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")
        return value


class SourceOut(BaseModel):
    document_id: str
    filename: str | None
    chunk_text: str
    page_or_section: str | None


class MessageOut(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant"]
    content: str
    sources: list[SourceOut] = []
    created_at: datetime


class ExchangeOut(BaseModel):
    session: SessionOut
    user_message: MessageOut
    assistant_message: MessageOut
