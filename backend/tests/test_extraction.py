from pathlib import Path

import pymupdf as fitz
from docx import Document as DocxDocument

from app.services.extraction import extract_documents
from app.services.rag import build_nodes
from app.services.storage import DOCX, MD, PDF, TXT


def _pdf_with_heading_and_table(path: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Termination", fontsize=18)
    page.insert_text(
        (72, 100),
        "Either party may terminate this Agreement for convenience by giving sixty days notice.",
        fontsize=11,
    )
    origin = fitz.Point(72, 140)
    col_w, row_h = 140, 22
    data = [["Code", "Amount"], ["BLUE-HERON", "15000"]]
    for r, row in enumerate(data):
        for c, value in enumerate(row):
            rect = fitz.Rect(
                origin.x + c * col_w,
                origin.y + r * row_h,
                origin.x + (c + 1) * col_w,
                origin.y + (r + 1) * row_h,
            )
            page.draw_rect(rect, width=0.6)
            page.insert_text((rect.x0 + 6, rect.y0 + 14), value, fontsize=11)
    page.insert_text((72, 220), "Renewal", fontsize=16)
    page.insert_text((72, 244), "The term renews automatically unless notice is given.", fontsize=11)
    doc.save(path)
    doc.close()
    return path


def test_pdf_extracts_heading_page_and_table(tmp_path):
    path = _pdf_with_heading_and_table(tmp_path / "policy.pdf")
    docs = extract_documents(path, PDF, document_id="doc1", user_id="user1", filename="policy.pdf")
    assert docs
    assert all(d.metadata["page_number"] not in (None, "") for d in docs)
    headings = " ".join(d.metadata.get("section_heading") or "" for d in docs)
    texts = "\n".join(d.text for d in docs)
    assert "Termination" in headings or "Termination" in texts
    assert "HERON" in texts
    assert "15000" in texts
    tables = [d for d in docs if d.metadata.get("kind") == "table"]
    assert tables, "layout-aware PDF parse should keep the drawn table as its own segment"
    for table in tables:
        row = next((line for line in table.text.splitlines() if "HERON" in line), "")
        assert row and "15000" in row


def test_txt_keeps_headings_and_paragraphs(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text(
        "Launch plan\n\n"
        "The launch codename is BLUE HERON.\n\n"
        "Budget rules\n\n"
        "Expense reports are due within ten working days.\n",
        encoding="utf-8",
    )
    docs = extract_documents(path, TXT, document_id="doc2", user_id="user1", filename="notes.txt")
    assert len(docs) >= 2
    headings = [d.metadata.get("section_heading") for d in docs]
    assert any("Launch" in (h or "") for h in headings)
    assert any("BLUE HERON" in d.text for d in docs)
    _, leaves = build_nodes(docs)
    assert leaves
    assert all(leaf.metadata.get("chunk_index") for leaf in leaves)
    joined = " ".join(leaf.get_content() for leaf in leaves)
    assert "BLUE HERON" in joined


def test_markdown_heading_metadata(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("# Safety\n\nWear gloves.\n\n## Storage\n\nKeep dry.\n", encoding="utf-8")
    docs = extract_documents(path, MD, document_id="doc3", user_id="user1", filename="guide.md")
    assert [d.metadata["section_heading"] for d in docs] == ["Safety", "Storage"]


def test_docx_tables_stay_with_heading(tmp_path):
    path = tmp_path / "spec.docx"
    doc = DocxDocument()
    doc.add_heading("Pricing", level=1)
    doc.add_paragraph("List prices follow.")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "SKU"
    table.cell(0, 1).text = "Price"
    table.cell(1, 0).text = "A-100"
    table.cell(1, 1).text = "42"
    doc.add_heading("Support", level=1)
    doc.add_paragraph("Email support@example.com")
    doc.save(path)

    docs = extract_documents(path, DOCX, document_id="doc4", user_id="user1", filename="spec.docx")
    table_docs = [d for d in docs if d.metadata.get("kind") == "table"]
    assert table_docs
    assert table_docs[0].metadata["section_heading"] == "Pricing"
    assert "A-100" in table_docs[0].text and "42" in table_docs[0].text
    _, leaves = build_nodes(table_docs)
    assert len(leaves) == 1
    assert "A-100 | 42" in leaves[0].get_content() or "A-100" in leaves[0].get_content()


def test_table_leaf_is_not_split(tmp_path):
    from llama_index.core import Document

    table = Document(
        text="Code | Amount\nBLUE-HERON | 15000\nRED-KITE | 8000",
        metadata={"kind": "table", "layout": "structured", "section_heading": "Codes", "filename": "t.txt"},
    )
    _, leaves = build_nodes([table])
    assert len(leaves) == 1
    assert "BLUE-HERON" in leaves[0].get_content() and "RED-KITE" in leaves[0].get_content()
