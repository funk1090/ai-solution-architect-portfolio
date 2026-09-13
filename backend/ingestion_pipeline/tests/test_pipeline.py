"""Unit tests for the pipeline orchestration: idempotency (NFR1) and
fault isolation (NFR5), using in-memory doubles for both repositories.
"""
import uuid
from pathlib import Path

from fpdf import FPDF

from ingestion_pipeline.factory import ParserFactory
from ingestion_pipeline.models import DocumentType, PendingDocument
from ingestion_pipeline.pipeline import run_ingestion
from ingestion_pipeline.repository import (
    InMemoryDocumentMetadataReader,
    InMemoryIngestedContentRepository,
)


def _build_test_pdf(path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", size=12)
    pdf.multi_cell(0, 8, "Sample content")
    pdf.output(str(path))


def test_ingesting_the_same_document_twice_creates_one_record(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _build_test_pdf(pdf_path)

    document = PendingDocument(
        id=uuid.uuid4(),
        document_type=DocumentType.RFP,
        file_path=str(pdf_path),
        checksum_sha256="fixed-checksum-for-test",
    )
    reader = InMemoryDocumentMetadataReader(documents=[document])
    repository = InMemoryIngestedContentRepository()
    factory = ParserFactory()

    first_summary = run_ingestion(reader, repository, factory)
    second_summary = run_ingestion(reader, repository, factory)

    assert first_summary.processed == 1
    assert second_summary.processed == 0
    assert second_summary.skipped == 1
    assert len(repository.list_all()) == 1


def test_a_failing_document_does_not_block_the_rest(tmp_path: Path) -> None:
    valid_pdf = tmp_path / "valid.pdf"
    _build_test_pdf(valid_pdf)

    valid_document = PendingDocument(
        id=uuid.uuid4(),
        document_type=DocumentType.RFP,
        file_path=str(valid_pdf),
        checksum_sha256="valid-checksum",
    )
    broken_document = PendingDocument(
        id=uuid.uuid4(),
        document_type=DocumentType.RFP,
        file_path=str(tmp_path / "does_not_exist.pdf"),
        checksum_sha256="broken-checksum",
    )

    reader = InMemoryDocumentMetadataReader(documents=[broken_document, valid_document])
    repository = InMemoryIngestedContentRepository()
    factory = ParserFactory()

    summary = run_ingestion(reader, repository, factory)

    assert summary.processed == 1
    assert summary.failed == 1
    records = repository.list_all()
    assert len(records) == 2
    failed_record = next(r for r in records if r.source_checksum == "broken-checksum")
    assert failed_record.status.value == "failed"
    assert failed_record.error_message is not None
