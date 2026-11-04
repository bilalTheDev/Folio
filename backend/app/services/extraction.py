"""Turn an uploaded file into LlamaIndex Documents, one per page (PDF) or section (DOCX/Markdown)."""

import re
from pathlib import Path

from docx import Document as DocxDocument
from llama_index.core import Document
from pypdf import PdfReader

from app.services.storage import DOCX, MD, PDF, TXT


class ExtractionError(Exception):
    pass


def _clean(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _pdf_sections(path: Path) -> list[tuple[str, str]]:
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise ExtractionError("The PDF is password protected.") from exc
    return [(f"Page {i}", page.extract_text() or "") for i, page in enumerate(reader.pages, start=1)]


def _docx_sections(path: Path) -> list[tuple[str, str]]:
    doc = DocxDocument(str(path))
    sections: list[tuple[str, list[str]]] = []
    current_title, current_lines = "Introduction", []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style = (paragraph.style.name if paragraph.style is not None else "") or ""
        if style.lower().startswith(("heading", "title")):
            if current_lines:
                sections.append((current_title, current_lines))
            current_title, current_lines = text[:120], []
        else:
            current_lines.append(text)
    if current_lines:
        sections.append((current_title, current_lines))

    for n, table in enumerate(doc.tables, start=1):
        rows = [" | ".join(cell.text.strip() for cell in row.cells) for row in table.rows]
        rows = [r for r in rows if r.strip(" |")]
        if rows:
            sections.append((f"Table {n}", rows))
    return [(title, "\n".join(lines)) for title, lines in sections]


def _text_sections(path: Path, markdown: bool) -> list[tuple[str, str]]:
    text = path.read_bytes().decode("utf-8-sig", errors="replace")
    if not markdown:
        return [("", text)]
    sections: list[tuple[str, list[str]]] = []
    title, lines = "", []
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s+(.*)", line)
        if heading:
            if any(l.strip() for l in lines):
                sections.append((title, lines))
            title, lines = heading.group(1).strip()[:120], []
        else:
            lines.append(line)
    if any(l.strip() for l in lines):
        sections.append((title, lines))
    return [(t, "\n".join(ls)) for t, ls in sections]


def extract_documents(path: Path, mime_type: str, *, document_id: str, user_id: str, filename: str) -> list[Document]:
    if mime_type == PDF:
        sections = _pdf_sections(path)
    elif mime_type == DOCX:
        sections = _docx_sections(path)
    elif mime_type in (TXT, MD):
        sections = _text_sections(path, markdown=mime_type == MD)
    else:
        raise ExtractionError(f"Unsupported file type: {mime_type}")

    documents = []
    for n, (label, raw) in enumerate(sections, start=1):
        text = _clean(raw)
        if not text:
            continue
        documents.append(
            Document(
                id_=f"{document_id}:{n}",
                text=text,
                metadata={
                    "user_id": user_id,
                    "folio_document_id": document_id,
                    "filename": filename,
                    "page_or_section": label,
                },
                excluded_embed_metadata_keys=["user_id", "folio_document_id", "page_or_section"],
                excluded_llm_metadata_keys=["user_id", "folio_document_id"],
            )
        )
    if not documents:
        raise ExtractionError("No extractable text was found (scanned PDFs are not supported yet).")
    return documents
