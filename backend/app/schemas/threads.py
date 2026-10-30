"""Pydantic schemas for threads and messages."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ThreadCreate(BaseModel):
    document_id: uuid.UUID
    title: str | None = None


class ThreadUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ThreadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID | None
    title: str
    created_at: datetime
    updated_at: datetime


class CitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    marker: int
    page: int
    excerpt: str
    score: float
    chunk_id: uuid.UUID | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    provider: str | None = None
    model: str | None = None
    stopped: bool = False
    created_at: datetime
    citations: list[CitationOut] = []


class AskMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    provider: str = "groq"
    model: str | None = None
    regenerate: bool = False



class ThreadListOut(BaseModel):
    items: list[ThreadOut]
    count: int
