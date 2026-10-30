"""Pydantic schemas for document endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    file_type: str
    byte_size: int
    page_count: int
    chunk_count: int
    status: str
    failure_reason: str | None = None
    is_sample: bool
    created_at: datetime


class DocumentListOut(BaseModel):
    items: list[DocumentOut]
    count: int = Field(description="Number of documents returned")


class ErrorOut(BaseModel):
    code: str
    message: str
