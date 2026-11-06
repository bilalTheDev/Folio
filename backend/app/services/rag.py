"""Per-user ingestion and retrieval with LlamaIndex over a per-user Chroma store.

Each user has their own Chroma directory at storage/{user_id}/index. Retrieval opens only the
caller's directory and also filters on the user_id metadata, so there is no shared index to leak from.
Leaf nodes are embedded; parent nodes live in a JSON docstore so answers can use surrounding context.
"""

from __future__ import annotations

import asyncio
import logging
import re
import threading
from functools import lru_cache
from pathlib import Path

import chromadb
from bson import ObjectId
from chromadb.config import Settings as ChromaSettings
from llama_index.core import VectorStoreIndex
from llama_index.core.node_parser import HierarchicalNodeParser, get_leaf_nodes
from llama_index.core.schema import MetadataMode, NodeRelationship, TextNode
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.vector_stores import ExactMatchFilter, FilterOperator, MetadataFilters
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.config import BACKEND_DIR, settings
from app.models.document import DocumentStatus
from app.services import storage
from app.services.extraction import EXCLUDED_EMBED, EXCLUDED_LLM, ExtractionError, extract_documents

logger = logging.getLogger("folio.rag")

MODEL_CACHE = BACKEND_DIR / ".cache" / "fastembed"

_clients: dict[str, chromadb.ClientAPI] = {}
_clients_lock = threading.Lock()
_write_locks: dict[str, threading.Lock] = {}


def collection_name() -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", settings.embed_model.lower()).strip("_")[:48]
    return f"folio_chunks_{slug}"


def _prefix_query(model_name: str, query: str) -> str:
    name = model_name.lower()
    if "e5" in name:
        return f"query: {query}"
    if "bge" in name:
        return f"Represent this sentence for searching relevant passages: {query}"
    return query


def _prefix_passage(model_name: str, text: str) -> str:
    if "e5" in model_name.lower():
        return f"passage: {text}"
    return text


class FolioEmbedding(FastEmbedEmbedding):
    """Applies BGE/E5 query vs passage prefixes that FastEmbed does not always attach."""

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._get_text_embedding(_prefix_query(self.model_name, query))

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        prefixed = [_prefix_passage(self.model_name, text) for text in texts]
        return [embedding.tolist() for embedding in self._model.embed(prefixed)]


@lru_cache
def embed_model() -> FastEmbedEmbedding:
    MODEL_CACHE.mkdir(parents=True, exist_ok=True)
    return FolioEmbedding(model_name=settings.embed_model, cache_dir=str(MODEL_CACHE))


def index_dir(user_id: str) -> Path:
    return storage.user_dir(user_id) / "index"


def nodes_dir(user_id: str) -> Path:
    return storage.user_dir(user_id) / "nodes"


def _docstore_path(user_id: str) -> Path:
    return nodes_dir(user_id) / "docstore.json"


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
    return _client(user_id).get_or_create_collection(collection_name(), metadata={"hnsw:space": "cosine"})


def _index(collection) -> VectorStoreIndex:
    return VectorStoreIndex.from_vector_store(ChromaVectorStore(chroma_collection=collection), embed_model=embed_model())


def _load_docstore(user_id: str) -> SimpleDocumentStore:
    path = _docstore_path(user_id)
    if path.exists():
        return SimpleDocumentStore.from_persist_path(str(path))
    return SimpleDocumentStore()


def _save_docstore(user_id: str, store: SimpleDocumentStore) -> None:
    path = _docstore_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    store.persist(persist_path=str(path))


def _purge_docstore(store: SimpleDocumentStore, document_id: str) -> None:
    stale = [
        node_id
        for node_id, node in list(store.docs.items())
        if getattr(node, "metadata", {}).get("folio_document_id") == document_id
    ]
    for node_id in stale:
        try:
            store.delete_document(node_id)
        except Exception:
            store.docs.pop(node_id, None)


def _chunk_sizes(layout: str) -> list[int]:
    if layout == "structured":
        return [settings.chunk_parent_structured, settings.chunk_leaf_structured]
    return [settings.chunk_parent_prose, settings.chunk_leaf_prose]


def _display_where(meta: dict, index: int) -> str:
    heading = (meta.get("section_heading") or "").strip()
    page = meta.get("page_number")
    if page not in (None, ""):
        return f"Page {page} · {heading}" if heading else f"Page {page}"
    if heading:
        return heading
    return f"Part {index}"


def _as_leaf_node(document) -> TextNode:
    meta = dict(document.metadata or {})
    meta["node_kind"] = "leaf"
    meta["chunk_index"] = 1
    meta["page_or_section"] = _display_where(meta, 1)
    return TextNode(
        text=document.text,
        metadata=meta,
        excluded_embed_metadata_keys=list(EXCLUDED_EMBED),
        excluded_llm_metadata_keys=list(EXCLUDED_LLM),
    )


def build_nodes(documents) -> tuple[list, list]:
    """Return (all_nodes including parents, leaf_nodes). Tables stay one leaf so rows are not split."""
    layout = (documents[0].metadata.get("layout") if documents else "prose") or "prose"
    parser = HierarchicalNodeParser.from_defaults(
        chunk_sizes=_chunk_sizes(layout),
        chunk_overlap=settings.chunk_overlap,
        include_metadata=True,
    )
    all_nodes: list = []
    for document in documents:
        if document.metadata.get("kind") == "table":
            all_nodes.append(_as_leaf_node(document))
            continue
        all_nodes.extend(parser.get_nodes_from_documents([document]))

    leaves = get_leaf_nodes(all_nodes)
    for index, node in enumerate(leaves, start=1):
        node.metadata["node_kind"] = "leaf"
        node.metadata["chunk_index"] = index
        node.metadata["page_or_section"] = _display_where(node.metadata, index)
        node.excluded_embed_metadata_keys = list(EXCLUDED_EMBED)
        node.excluded_llm_metadata_keys = list(EXCLUDED_LLM)
    for node in all_nodes:
        if node.metadata.get("node_kind") != "leaf":
            node.metadata["node_kind"] = "parent"
    return all_nodes, leaves


def _ingest_sync(user_id: str, document_id: str, path: Path, mime_type: str, filename: str) -> int:
    documents = extract_documents(path, mime_type, document_id=document_id, user_id=user_id, filename=filename)
    all_nodes, leaves = build_nodes(documents)
    texts = [node.get_content(metadata_mode=MetadataMode.EMBED) for node in leaves]
    for node, vector in zip(leaves, embed_model().get_text_embedding_batch(texts)):
        node.embedding = vector

    collection = _collection(user_id)
    store = _load_docstore(user_id)
    with _write_locks[user_id]:
        collection.delete(where={"folio_document_id": document_id})
        _purge_docstore(store, document_id)
        store.add_documents(all_nodes)
        _save_docstore(user_id, store)
        _index(collection).insert_nodes(leaves)
    return len(leaves)


def _delete_sync(user_id: str, document_id: str) -> None:
    if not index_dir(user_id).exists() and not _docstore_path(user_id).exists():
        return
    if index_dir(user_id).exists():
        collection = _collection(user_id)
        with _write_locks[user_id]:
            collection.delete(where={"folio_document_id": document_id})
            store = _load_docstore(user_id)
            _purge_docstore(store, document_id)
            _save_docstore(user_id, store)
    else:
        with _write_locks.setdefault(user_id, threading.Lock()):
            store = _load_docstore(user_id)
            _purge_docstore(store, document_id)
            _save_docstore(user_id, store)


def _parent_text(store: SimpleDocumentStore, node) -> str:
    leaf_text = node.get_content(metadata_mode=MetadataMode.NONE)
    rel = node.relationships.get(NodeRelationship.PARENT)
    if rel is None:
        stored = None
        try:
            stored = store.get_node(node.node_id)
        except Exception:
            stored = None
        if stored is not None:
            rel = stored.relationships.get(NodeRelationship.PARENT)
            node = stored
    if rel is None:
        return leaf_text
    parent_id = rel.node_id if hasattr(rel, "node_id") else rel
    try:
        parent = store.get_node(parent_id)
        text = parent.get_content(metadata_mode=MetadataMode.NONE)
        return text or leaf_text
    except Exception:
        return leaf_text


def _source_from_node(node, store: SimpleDocumentStore, score=None) -> dict:
    meta = node.metadata or {}
    leaf = node.get_content(metadata_mode=MetadataMode.NONE)
    return {
        "document_id": meta.get("folio_document_id"),
        "filename": meta.get("filename"),
        "page_or_section": meta.get("page_or_section"),
        "section_heading": meta.get("section_heading") or None,
        "page_number": meta.get("page_number") if meta.get("page_number") not in (None, "") else None,
        "chunk_text": leaf,
        "parent_text": _parent_text(store, node),
        "score": score,
    }


def _metadata_filters(user_id: str, document_ids: list[str] | None) -> MetadataFilters:
    filters = [ExactMatchFilter(key="user_id", value=user_id)]
    if document_ids and len(document_ids) == 1:
        filters.append(ExactMatchFilter(key="folio_document_id", value=document_ids[0]))
    elif document_ids:
        filters.append(
            ExactMatchFilter(key="folio_document_id", value=document_ids, operator=FilterOperator.IN)
        )
    return MetadataFilters(filters=filters)


def _leaf_nodes(store: SimpleDocumentStore, user_id: str, document_ids: list[str] | None) -> list:
    allowed = set(document_ids) if document_ids else None
    leaves = []
    for node in store.docs.values():
        meta = getattr(node, "metadata", None) or {}
        if meta.get("user_id") != user_id:
            continue
        if NodeRelationship.CHILD in getattr(node, "relationships", {}):
            continue
        if allowed is not None and meta.get("folio_document_id") not in allowed:
            continue
        leaves.append(node)
    return leaves


def _rrf(result_lists: list[list], k: int = 60) -> list[tuple]:
    scores: dict[str, float] = {}
    nodes: dict[str, object] = {}
    for results in result_lists:
        for rank, item in enumerate(results, start=1):
            node = item.node if hasattr(item, "node") else item
            node_id = node.node_id
            nodes[node_id] = node
            scores[node_id] = scores.get(node_id, 0.0) + 1.0 / (k + rank)
    return [(nodes[node_id], scores[node_id]) for node_id in sorted(scores, key=scores.get, reverse=True)]


def _dense_retrieve(collection, user_id: str, query: str, candidate_k: int, document_ids: list[str] | None):
    retriever = _index(collection).as_retriever(
        similarity_top_k=candidate_k,
        filters=_metadata_filters(user_id, document_ids),
    )
    return retriever.retrieve(query)


def _bm25_retrieve(leaves: list, query: str, candidate_k: int):
    if not leaves:
        return []
    from llama_index.retrievers.bm25 import BM25Retriever

    retriever = BM25Retriever.from_defaults(nodes=leaves, similarity_top_k=min(candidate_k, len(leaves)))
    return retriever.retrieve(query)


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    norm_l = sum(a * a for a in left) ** 0.5
    norm_r = sum(b * b for b in right) ** 0.5
    if not norm_l or not norm_r:
        return 0.0
    return dot / (norm_l * norm_r)


def _maybe_rerank(query: str, ranked: list[tuple], top_k: int) -> list[tuple]:
    """Rerank fused candidates with the same local embed model already used for ingest."""
    if not ranked:
        return []
    if not settings.rerank_enabled:
        return ranked[:top_k]
    try:
        model = embed_model()
        query_vec = model.get_query_embedding(query)
        scored = []
        for node, _fuse in ranked:
            text = node.get_content(metadata_mode=MetadataMode.NONE)
            score = _cosine(query_vec, model.get_text_embedding(text))
            scored.append((node, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]
    except Exception:
        logger.exception("Rerank failed; using fused ranking")
        return ranked[:top_k]


def _retrieve_sync(
    user_id: str, query: str, top_k: int, document_ids: list[str] | None = None
) -> list[dict]:
    if not index_dir(user_id).exists():
        return []
    collection = _collection(user_id)
    if collection.count() == 0:
        return []
    store = _load_docstore(user_id)
    candidate_k = max(top_k, settings.retrieval_candidate_k)
    leaves = _leaf_nodes(store, user_id, document_ids)
    try:
        dense = _dense_retrieve(collection, user_id, query, candidate_k, document_ids)
    except Exception as exc:
        if "dimension" in str(exc).lower():
            logger.warning("Skipping retrieve for %s: embedding dimension mismatch (%s)", user_id, exc)
            return []
        raise
    try:
        sparse = _bm25_retrieve(leaves, query, candidate_k)
    except Exception:
        logger.exception("BM25 retrieve failed; using dense results only")
        sparse = []

    fused = _rrf([dense, sparse]) if sparse else [(item.node, getattr(item, "score", 0.0)) for item in dense]
    fused = _maybe_rerank(query, fused, top_k)

    allowed = set(document_ids) if document_ids else None
    results = []
    seen = set()
    for node, score in fused:
        meta = node.metadata or {}
        if meta.get("user_id") != user_id:
            continue
        doc_id = meta.get("folio_document_id")
        if allowed is not None and doc_id not in allowed:
            continue
        if node.node_id in seen:
            continue
        seen.add(node.node_id)
        try:
            stored = store.get_node(node.node_id)
        except Exception:
            stored = node
        results.append(_source_from_node(stored, store, score))
        if len(results) >= top_k:
            break
    return results


async def retrieve(
    user_id: ObjectId,
    query: str,
    top_k: int | None = None,
    document_ids: list[str] | None = None,
) -> list[dict]:
    return await asyncio.to_thread(
        _retrieve_sync, str(user_id), query, top_k or settings.retrieval_top_k, document_ids
    )


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
        embed_model().get_query_embedding("warm up")
    except Exception:
        logger.exception("Embedding model warm-up failed")
