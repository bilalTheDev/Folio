from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    indexing = "indexing"
    indexed = "indexed"
    failed = "failed"


class DocumentOut(BaseModel):
    id: str
    filename: str
    size_bytes: int
    mime_type: str
    status: DocumentStatus
    uploaded_at: datetime
    chunk_count: int


def to_document_out(doc: dict) -> DocumentOut:
    return DocumentOut(
        id=str(doc["_id"]),
        filename=doc["filename"],
        size_bytes=doc["size_bytes"],
        mime_type=doc["mime_type"],
        status=doc["status"],
        uploaded_at=doc["uploaded_at"],
        chunk_count=doc.get("chunk_count", 0),
    )
