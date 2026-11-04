"""Per-user ingestion and retrieval with LlamaIndex over a per-user Chroma store.

Each user has their own Chroma directory at storage/{user_id}/index. Retrieval opens only the
caller's directory and also filters on the user_id metadata, so there is no shared index to leak from.
"""

import asyncio
import logging
import threading
from functools import lru_cache
from pathlib import Path

import chromadb
from bson import ObjectId
from chromadb.config import Settings as ChromaSettings
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import MetadataMode
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.config import BACKEND_DIR, settings
from app.models.document import DocumentStatus
from app.services import storage
from app.services.extraction import ExtractionError, extract_documents

logger = logging.getLogger("folio.rag")

COLLECTION = "folio_chunks"
MODEL_CACHE = BACKEND_DIR / ".cache" / "fastembed"

_clients: dict[str, chromadb.ClientAPI] = {}
_clients_lock = threading.Lock()
_write_locks: dict[str, threading.Lock] = {}


@lru_cache
def embed_model() -> FastEmbedEmbedding:
    MODEL_CACHE.mkdir(parents=True, exist_ok=True)
    return FastEmbedEmbedding(model_name=settings.embed_model, cache_dir=str(MODEL_CACHE))


def index_dir(user_id: str) -> Path:
    return storage.user_dir(user_id) / "index"


def _client(user_id: str) -> chromadb.ClientAPI:
    with _clients_lock:
        client = _clients.get(user_id)
        if client is None:
            path = index_dir(user_id)
            path.mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(
                path=str(path), settings=ChromaSettings(anonymized_telemetry=False)
            )
            _clients[user_id] = client
            _write_locks[user_id] = threading.Lock()
        return client


def _collection(user_id: str):
    return _client(user_id).get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


def _index(collection) -> VectorStoreIndex:
    return VectorStoreIndex.from_vector_store(ChromaVectorStore(chroma_collection=collection), embed_model=embed_model())


def _ingest_sync(user_id: str, document_id: str, path: Path, mime_type: str, filename: str) -> int:
    documents = extract_documents(path, mime_type, document_id=document_id, user_id=user_id, filename=filename)
    splitter = SentenceSplitter(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    nodes = splitter.get_nodes_from_documents(documents)
    for n, node in enumerate(nodes, start=1):
        if not node.metadata.get("page_or_section"):
            node.metadata["page_or_section"] = f"Part {n}"

    # Embed before taking the write lock so long documents don't block other writes for this user.
    texts = [node.get_content(metadata_mode=MetadataMode.EMBED) for node in nodes]
    for node, vector in zip(nodes, embed_model().get_text_embedding_batch(texts)):
        node.embedding = vector

    collection = _collection(user_id)
    with _write_locks[user_id]:
        collection.delete(where={"folio_document_id": document_id})
        _index(collection).insert_nodes(nodes)
    return len(nodes)


def _delete_sync(user_id: str, document_id: str) -> None:
    if not index_dir(user_id).exists():
        return
    collection = _collection(user_id)
    with _write_locks[user_id]:
        collection.delete(where={"folio_document_id": document_id})


def _retrieve_sync(user_id: str, query: str, top_k: int) -> list[dict]:
    if not index_dir(user_id).exists():
        return []
    collection = _collection(user_id)
    if collection.count() == 0:
        return []
    retriever = _index(collection).as_retriever(
        similarity_top_k=top_k,
        filters=MetadataFilters(filters=[ExactMatchFilter(key="user_id", value=user_id)]),
    )
    results = []
    for scored in retriever.retrieve(query):
        meta = scored.node.metadata
        if meta.get("user_id") != user_id:
            continue
        results.append(
            {
                "document_id": meta.get("folio_document_id"),
                "filename": meta.get("filename"),
                "page_or_section": meta.get("page_or_section"),
                "chunk_text": scored.node.get_content(metadata_mode=MetadataMode.NONE),
                "score": scored.score,
            }
        )
    return results


async def retrieve(user_id: ObjectId, query: str, top_k: int | None = None) -> list[dict]:
    return await asyncio.to_thread(_retrieve_sync, str(user_id), query, top_k or settings.retrieval_top_k)


async def delete_document_nodes(user_id: ObjectId, document_id: ObjectId) -> None:
    await asyncio.to_thread(_delete_sync, str(user_id), str(document_id))


async def ingest_document(db: AsyncIOMotorDatabase, document_id: ObjectId) -> None:
    """Background job: uploaded -> indexing -> indexed | failed."""
    doc = await db.documents.find_one_and_update(
        {"_id": document_id},
        {"$set": {"status": DocumentStatus.indexing.value}},
        return_document=ReturnDocument.AFTER,
    )
    if doc is None:
        return
    user_id, doc_id = str(doc["user_id"]), str(doc["_id"])
    try:
        chunk_count = await asyncio.to_thread(
            _ingest_sync, user_id, doc_id, storage.resolve(doc["storage_path"]), doc["mime_type"], doc["filename"]
        )
    except ExtractionError as exc:
        logger.warning("Indexing failed for document %s: %s", doc_id, exc)
        await _mark_failed(db, document_id)
        return
    except Exception:
        logger.exception("Indexing failed for document %s", doc_id)
        await _mark_failed(db, document_id)
        return

    result = await db.documents.update_one(
        {"_id": document_id},
        {"$set": {"status": DocumentStatus.indexed.value, "chunk_count": chunk_count}},
    )
    if result.matched_count == 0:
        # Deleted while indexing: drop the chunks we just wrote.
        await asyncio.to_thread(_delete_sync, user_id, doc_id)


async def _mark_failed(db: AsyncIOMotorDatabase, document_id: ObjectId) -> None:
    await db.documents.update_one(
        {"_id": document_id}, {"$set": {"status": DocumentStatus.failed.value, "chunk_count": 0}}
    )


async def resume_pending(db: AsyncIOMotorDatabase) -> None:
    """Re-queue documents left unfinished by a restart."""
    pending = db.documents.find(
        {"status": {"$in": [DocumentStatus.uploaded.value, DocumentStatus.indexing.value]}}, {"_id": 1}
    )
    async for doc in pending:
        await ingest_document(db, doc["_id"])


def warm_up() -> None:
    try:
        embed_model().get_text_embedding("warm up")
    except Exception:
        logger.exception("Embedding model warm-up failed")
