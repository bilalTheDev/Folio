"""Tests for upload validation."""

import pytest

from backend.app.rag.validate import IngestError, validate_upload


def test_validate_txt_ok() -> None:
    data = b"Hello Folio document text."
    result = validate_upload(filename="notes.txt", data=data, max_file_mb=10)
    assert result.file_type == "txt"
    assert result.title == "notes"


def test_validate_pdf_magic() -> None:
    data = b"%PDF-1.4 fake content"
    result = validate_upload(filename="paper.pdf", data=data, max_file_mb=10)
    assert result.file_type == "pdf"


def test_validate_rejects_empty() -> None:
    with pytest.raises(IngestError) as exc:
        validate_upload(filename="empty.txt", data=b"", max_file_mb=10)
    assert exc.value.code == "empty"


def test_validate_rejects_too_large() -> None:
    data = b"a" * (2 * 1024 * 1024)
    with pytest.raises(IngestError) as exc:
        validate_upload(filename="big.txt", data=data, max_file_mb=1)
    assert exc.value.code == "too_large"


def test_validate_rejects_binary_as_txt() -> None:
    with pytest.raises(IngestError) as exc:
        validate_upload(filename="blob.bin", data=b"\x00\x01\x02\x03", max_file_mb=10)
    assert exc.value.code == "invalid_type"
