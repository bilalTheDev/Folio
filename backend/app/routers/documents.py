from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, File, Request, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.errors import AppError
from app.core.rate_limit import UPLOAD_LIMIT, limiter
from app.db import get_db
from app.deps import get_current_user
from app.models.common import parse_object_id, utcnow
from app.models.document import DocumentOut, DocumentStatus, to_document_out
from app.services import rag, storage

router = APIRouter(prefix="/documents", tags=["documents"])


async def _owned_document(db: AsyncIOMotorDatabase, user: dict, document_id: str) -> dict:
    doc = await db.documents.find_one({"_id": parse_object_id(document_id, "Document"), "user_id": user["_id"]})
    if doc is None:
        raise AppError(404, "not_found", "Document not found.")
    return doc


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(UPLOAD_LIMIT)
async def upload_document(
    request: Request,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    document_id = ObjectId()
    storage_path, size, mime = await storage.save_upload(file, user["_id"], document_id)
    doc = {
        "_id": document_id,
        "user_id": user["_id"],
        "filename": storage.clean_filename(file.filename),
        "size_bytes": size,
        "mime_type": mime,
        "storage_path": storage_path,
        "status": DocumentStatus.uploaded.value,
        "uploaded_at": utcnow(),
        "chunk_count": 0,
    }
    try:
        await db.documents.insert_one(doc)
    except Exception:
        storage.delete_file(storage_path)
        raise
    background.add_task(rag.ingest_document, db, document_id)
    return to_document_out(doc)


@router.get("", response_model=list[DocumentOut])
async def list_documents(user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    cursor = db.documents.find({"user_id": user["_id"]}).sort("uploaded_at", -1)
    return [to_document_out(doc) async for doc in cursor]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await _owned_document(db, user, document_id)
    await db.documents.delete_one({"_id": doc["_id"], "user_id": user["_id"]})
    await rag.delete_document_nodes(user["_id"], doc["_id"])
    storage.delete_file(doc["storage_path"])


@router.post("/{document_id}/reindex", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def reindex_document(
    document_id: str,
    background: BackgroundTasks,
    user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await _owned_document(db, user, document_id)
    await db.documents.update_one(
        {"_id": doc["_id"], "user_id": user["_id"]},
        {"$set": {"status": DocumentStatus.uploaded.value, "chunk_count": 0}},
    )
    doc["status"] = DocumentStatus.uploaded.value
    doc["chunk_count"] = 0
    background.add_task(rag.ingest_document, db, doc["_id"])
    return to_document_out(doc)
