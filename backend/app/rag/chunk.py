"""Chunk extracted pages with LlamaIndex SentenceSplitter."""

from __future__ import annotations

from dataclasses import dataclass

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document as LIDocument
from llama_index.core.schema import TextNode

from backend.app.rag.extract import ExtractedDocument
from backend.app.rag.validate import IngestError

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    page: int
    content: str
    token_count: int


def chunk_document(
    extracted: ExtractedDocument,
    *,
    max_chunks: int,
) -> list[TextChunk]:
    """Split extracted pages into overlapping sentence chunks."""
    documents: list[LIDocument] = []
    for page in extracted.pages:
        if not page.text.strip():
            continue
        documents.append(
            LIDocument(
                text=page.text,
                metadata={"page": page.page},
            )
        )

    if not documents:
        raise IngestError(
            "no_text",
            "This file has no selectable text. OCR is not supported yet.",
        )

    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes: list[TextNode] = splitter.get_nodes_from_documents(documents)

    chunks: list[TextChunk] = []
    for index, node in enumerate(nodes):
        content = (node.get_content() or "").strip()
        if not content:
            continue
        page = int(node.metadata.get("page") or 1)
        # SentenceSplitter uses token-ish sizing; store chunk_size budget as estimate.
        token_count = max(1, len(content.split()))
        chunks.append(
            TextChunk(
                chunk_index=index,
                page=page,
                content=content,
                token_count=token_count,
            )
        )

    if not chunks:
        raise IngestError("empty", "No text chunks could be created from this file.")

    if len(chunks) > max_chunks:
        raise IngestError(
            "too_many_chunks",
            f"Document produced {len(chunks)} chunks; the limit is {max_chunks}.",
        )
    return chunks
