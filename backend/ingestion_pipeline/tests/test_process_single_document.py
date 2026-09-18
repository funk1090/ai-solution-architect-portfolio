"""Unit tests for _process_single_document -- the exact logic that runs
both sequentially (run_ingestion) and inside each worker process
(run_ingestion_parallel, Feature 0005/FR4). No database required.
"""
import uuid
from pathlib import Path

from fpdf import FPDF

from ingestion_pipeline.factory import ParserFactory
from ingestion_pipeline.models import DocumentType, IngestionStatus, PendingDocument
from ingestion_pipeline.pipeline import _process_single_document


def _build_test_pdf(path: Path, text: str) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", size=12)
    pdf.multi_cell(0, 8, text)
    pdf.output(str(path))


def test_successfully_parses_a_valid_document(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _build_test_pdf(pdf_path, "Sample content for parsing")

    document = PendingDocument(
        id=uuid.uuid4(),
        document_type=DocumentType.RFP,
        file_path=str(pdf_path),
        checksum_sha256="abc123",
    )

    record = _process_single_document(document, ParserFactory())

    assert record.status == IngestionStatus.SUCCESS
    assert "Sample content for parsing" in record.extracted_text
    assert record.source_checksum == "abc123"


def test_records_failure_for_a_missing_file(tmp_path: Path) -> None:
    document = PendingDocument(
        id=uuid.uuid4(),
        document_type=DocumentType.RFP,
        file_path=str(tmp_path / "does_not_exist.pdf"),
        checksum_sha256="broken",
    )

    record = _process_single_document(document, ParserFactory())

    assert record.status == IngestionStatus.FAILED
    assert record.error_message is not None
