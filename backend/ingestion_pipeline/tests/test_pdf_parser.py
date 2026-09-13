"""Unit tests for PDFParser.

Uses fpdf2 (dev dependency only) to build a minimal known PDF at test
time, rather than depending on the document-generator project — the two
are independent uv projects (ADR-0003).
"""
from pathlib import Path

from fpdf import FPDF

from ingestion_pipeline.parsers.pdf_parser import PDFParser


def _build_test_pdf(path: Path, text: str) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", size=12)
    pdf.multi_cell(0, 8, text)
    pdf.output(str(path))


def test_extracts_known_text(tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    _build_test_pdf(pdf_path, "Hello synthetic RFP world")

    result = PDFParser().parse(pdf_path)

    assert result.extracted_text is not None
    assert "Hello synthetic RFP world" in result.extracted_text
    assert result.structured_data is None


def test_normalizes_excess_whitespace(tmp_path: Path) -> None:
    pdf_path = tmp_path / "messy.pdf"
    _build_test_pdf(pdf_path, "Word1    Word2     Word3")

    result = PDFParser().parse(pdf_path)

    assert "Word1 Word2 Word3" in result.extracted_text
