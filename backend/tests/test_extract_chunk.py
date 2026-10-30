"""Tests for text extraction and chunking."""

import pytest

from backend.app.rag.chunk import chunk_document
from backend.app.rag.extract import extract_text
from backend.app.rag.validate import IngestError


def test_extract_txt_pages() -> None:
    body = ("Paragraph one. " * 40) + ("\n\nParagraph two. " * 40)
    extracted = extract_text("txt", body.encode("utf-8"))
    assert extracted.page_count >= 1
    assert any(page.text for page in extracted.pages)


def test_extract_empty_txt_rejected() -> None:
    with pytest.raises(IngestError) as exc:
        extract_text("txt", b"   \n  ")
    assert exc.value.code == "no_text"


def test_chunk_respects_max() -> None:
    text = "Sentence number. " * 400
    extracted = extract_text("txt", text.encode("utf-8"))
    with pytest.raises(IngestError) as exc:
        chunk_document(extracted, max_chunks=1)
    assert exc.value.code == "too_many_chunks"


def test_chunk_produces_chunks() -> None:
    text = "Folio answers questions from documents. " * 20
    extracted = extract_text("txt", text.encode("utf-8"))
    chunks = chunk_document(extracted, max_chunks=50)
    assert len(chunks) >= 1
    assert chunks[0].content
    assert chunks[0].page >= 1
