"""Turn an uploaded file into LlamaIndex Documents with section and page metadata."""

from __future__ import annotations

import re
from pathlib import Path

import pymupdf as fitz
from docx import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph
from llama_index.core import Document

from app.services.storage import DOCX, MD, PDF, TXT

EXCLUDED_EMBED = [
    "user_id",
    "folio_document_id",
    "page_or_section",
    "page_number",
    "chunk_index",
    "kind",
    "node_kind",
]
EXCLUDED_LLM = ["user_id", "folio_document_id"]


class ExtractionError(Exception):
    pass


def _clean(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _looks_like_heading(text: str, *, font_size: float | None = None, median_size: float | None = None) -> bool:
    line = " ".join(text.split())
    if not line or len(line) > 100:
        return False
    if line.endswith((".", "?", "!")):
        return False
    if font_size is not None and median_size and font_size >= median_size * 1.18:
        return True
    if line.startswith("#"):
        return True
    words = line.split()
    if len(words) <= 12 and (line.isupper() or (line[:1].isupper() and "," not in line)):
        return True
    return False


def _table_to_text(rows: list[list[str | None]]) -> str:
    lines = []
    for row in rows:
        cells = [re.sub(r"\s+", " ", (cell or "").strip()) for cell in row]
        if any(cells):
            lines.append(" | ".join(cells))
    return "\n".join(lines)


def _overlaps(bbox, tables, thresh: float = 0.45) -> bool:
    rect = fitz.Rect(bbox)
    area = rect.get_area() or 1.0
    for table in tables:
        inter = rect & fitz.Rect(table.bbox)
        if inter.get_area() / area > thresh:
            return True
    return False


def _pdf_segments(path: Path) -> list[dict]:
    try:
        doc = fitz.open(path)
    except Exception as exc:
        raise ExtractionError("The PDF could not be read.") from exc
    try:
        if doc.is_encrypted and not doc.authenticate(""):
            raise ExtractionError("The PDF is password protected.")
        segments: list[dict] = []
        for page_number, page in enumerate(doc, start=1):
            tables = []
            try:
                found = page.find_tables()
                tables = list(found.tables) if found else []
            except Exception:
                tables = []

            heading = ""
            sizes: list[float] = []
            data = page.get_text("dict")
            for block in data.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span.get("size"):
                            sizes.append(float(span["size"]))
            median = sorted(sizes)[len(sizes) // 2] if sizes else 11.0

            prose: list[str] = []

            def flush_prose():
                text = _clean("\n".join(prose))
                prose.clear()
                if text:
                    segments.append(
                        {
                            "text": text,
                            "section_heading": heading,
                            "page_number": page_number,
                            "kind": "prose",
                        }
                    )

            for table in tables:
                try:
                    rows = table.extract()
                except Exception:
                    continue
                table_text = _table_to_text(rows)
                if table_text:
                    flush_prose()
                    segments.append(
                        {
                            "text": table_text,
                            "section_heading": heading or "Table",
                            "page_number": page_number,
                            "kind": "table",
                        }
                    )

            for block in data.get("blocks", []):
                if block.get("type") != 0:
                    continue
                if tables and _overlaps(block.get("bbox"), tables):
                    continue
                lines_out = []
                max_size = 0.0
                for line in block.get("lines", []):
                    parts = [span.get("text", "") for span in line.get("spans", [])]
                    joined = "".join(parts).strip()
                    if joined:
                        lines_out.append(joined)
                    for span in line.get("spans", []):
                        max_size = max(max_size, float(span.get("size") or 0))
                block_text = _clean("\n".join(lines_out))
                if not block_text:
                    continue
                if _looks_like_heading(block_text, font_size=max_size, median_size=median):
                    flush_prose()
                    heading = " ".join(block_text.split())[:120]
                    continue
                prose.append(block_text)
            flush_prose()
        return segments
    finally:
        doc.close()


def _iter_docx_blocks(doc: DocxDocument):
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield DocxTable(child, doc)


def _docx_segments(path: Path) -> list[dict]:
    doc = DocxDocument(str(path))
    segments: list[dict] = []
    heading = "Introduction"
    lines: list[str] = []

    def flush():
        text = _clean("\n".join(lines))
        lines.clear()
        if text:
            segments.append({"text": text, "section_heading": heading, "page_number": None, "kind": "prose"})

    for block in _iter_docx_blocks(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if not text:
                continue
            style = (block.style.name if block.style is not None else "") or ""
            if style.lower().startswith(("heading", "title")):
                flush()
                heading = text[:120]
            else:
                lines.append(text)
        else:
            rows = [[cell.text for cell in row.cells] for row in block.rows]
            table_text = _table_to_text(rows)
            if table_text:
                flush()
                segments.append(
                    {"text": table_text, "section_heading": heading, "page_number": None, "kind": "table"}
                )
    flush()
    return segments


def _text_segments(path: Path, markdown: bool) -> list[dict]:
    raw = path.read_bytes().decode("utf-8-sig", errors="replace")
    segments: list[dict] = []
    heading = ""
    lines: list[str] = []

    def flush():
        text = _clean("\n".join(lines))
        lines.clear()
        if text:
            segments.append({"text": text, "section_heading": heading, "page_number": None, "kind": "prose"})

    for line in raw.splitlines():
        md = re.match(r"^#{1,6}\s+(.*)", line)
        if md:
            flush()
            heading = md.group(1).strip()[:120]
            continue
        if markdown:
            lines.append(line)
            continue
        stripped = line.strip()
        if not stripped:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if _looks_like_heading(stripped) and (not lines or lines[-1] == ""):
            flush()
            heading = stripped[:120]
            continue
        lines.append(stripped)
    flush()
    return segments


def classify_layout(segments: list[dict]) -> str:
    if any(s.get("kind") == "table" for s in segments):
        return "structured"
    headings = [s.get("section_heading") for s in segments if s.get("section_heading")]
    total = sum(len(s.get("text") or "") for s in segments) or 1
    if len(headings) >= 4 and total / max(len(headings), 1) < 900:
        return "structured"
    return "prose"


def extract_documents(path: Path, mime_type: str, *, document_id: str, user_id: str, filename: str) -> list[Document]:
    if mime_type == PDF:
        segments = _pdf_segments(path)
    elif mime_type == DOCX:
        segments = _docx_segments(path)
    elif mime_type in (TXT, MD):
        segments = _text_segments(path, markdown=mime_type == MD)
    else:
        raise ExtractionError(f"Unsupported file type: {mime_type}")

    layout = classify_layout(segments)
    documents = []
    for n, segment in enumerate(segments, start=1):
        text = _clean(segment["text"])
        if not text:
            continue
        heading = (segment.get("section_heading") or "").strip()
        page = segment.get("page_number")
        kind = segment.get("kind") or "prose"
        page_or_section = _display_where(heading, page, n)
        documents.append(
            Document(
                id_=f"{document_id}:{n}",
                text=text,
                metadata={
                    "user_id": user_id,
                    "folio_document_id": document_id,
                    "filename": filename,
                    "section_heading": heading,
                    "page_number": page if page is not None else "",
                    "kind": kind,
                    "layout": layout,
                    "page_or_section": page_or_section,
                },
                excluded_embed_metadata_keys=list(EXCLUDED_EMBED),
                excluded_llm_metadata_keys=list(EXCLUDED_LLM),
            )
        )
    if not documents:
        raise ExtractionError("No extractable text was found (scanned PDFs are not supported yet).")
    return documents


def _display_where(heading: str, page, index: int) -> str:
    if page and heading:
        return f"Page {page} · {heading}"
    if page:
        return f"Page {page}"
    if heading:
        return heading
    return f"Part {index}"
