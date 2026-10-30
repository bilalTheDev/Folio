"""Upload validation: size, type signature, and limits."""

from __future__ import annotations

from dataclasses import dataclass

PDF_MAGIC = b"%PDF"
ZIP_MAGIC = b"PK\x03\x04"  # DOCX is a ZIP container
TXT_SAMPLE_BYTES = 2048


class IngestError(Exception):
    """Raised when a document fails validation or ingestion rules."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    file_type: str
    data: bytes
    title: str


def _detect_type(data: bytes, filename: str) -> str | None:
    """Detect file type from content signature, with extension as a hint."""
    if data.startswith(PDF_MAGIC):
        return "pdf"
    if data.startswith(ZIP_MAGIC) and filename.lower().endswith(".docx"):
        return "docx"
    # TXT: reject binary-looking payloads
    sample = data[:TXT_SAMPLE_BYTES]
    if b"\x00" in sample:
        return None
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        try:
            sample.decode("latin-1")
        except UnicodeDecodeError:
            return None
    if filename.lower().endswith(".txt") or not filename.lower().endswith(
        (".pdf", ".docx")
    ):
        return "txt"
    return None


def validate_upload(
    *,
    filename: str,
    data: bytes,
    max_file_mb: int,
) -> ValidatedUpload:
    """Validate raw upload bytes against Folio limits and signatures."""
    if not data:
        raise IngestError("empty", "The uploaded file is empty.")

    max_bytes = max_file_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise IngestError(
            "too_large",
            f"File exceeds the {max_file_mb} MB limit.",
        )

    file_type = _detect_type(data, filename)
    if file_type is None:
        raise IngestError(
            "invalid_type",
            "Only PDF, DOCX, and TXT files with selectable text are supported.",
        )

    stem = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    title = stem.rsplit(".", 1)[0].strip() or "Untitled"
    return ValidatedUpload(
        filename=stem,
        file_type=file_type,
        data=data,
        title=title[:200],
    )
