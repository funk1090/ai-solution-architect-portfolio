"""Pipeline orchestration — this is what the Airflow DAG will call.

Per-document error isolation (FR8/NFR5): one corrupt file must not
abort the whole run. Each document gets its own try/except, and a
failure is recorded as data (status='failed'), not just logged and lost.
"""
import logging
from dataclasses import dataclass
from pathlib import Path

from ingestion_pipeline.factory import ParserFactory
from ingestion_pipeline.models import IngestedContent, IngestionStatus
from ingestion_pipeline.repository import (
    DocumentMetadataReader,
    IngestedContentRepository,
)

logger = logging.getLogger(__name__)


@dataclass
class IngestionSummary:
    processed: int
    skipped: int
    failed: int


def run_ingestion(
    reader: DocumentMetadataReader,
    repository: IngestedContentRepository,
    factory: ParserFactory,
) -> IngestionSummary:
    processed = skipped = failed = 0

    for document in reader.list_all_documents():
        if repository.exists_checksum(document.checksum_sha256):
            skipped += 1
            continue

        try:
            parser = factory.create(document.document_type)
            parsed = parser.parse(Path(document.file_path))
            record = IngestedContent(
                source_checksum=document.checksum_sha256,
                document_type=document.document_type,
                extracted_text=parsed.extracted_text,
                structured_data=parsed.structured_data,
                status=IngestionStatus.SUCCESS,
            )
            processed += 1
            logger.info("Ingested %s (%s)", document.file_path, document.document_type.value)
        except Exception as exc:  # noqa: BLE001 - intentional: isolate any parser failure
            record = IngestedContent(
                source_checksum=document.checksum_sha256,
                document_type=document.document_type,
                status=IngestionStatus.FAILED,
                error_message=str(exc),
            )
            failed += 1
            logger.warning("Failed to ingest %s: %s", document.file_path, exc)

        repository.save(record)

    summary = IngestionSummary(processed=processed, skipped=skipped, failed=failed)
    logger.info(
        "Ingestion run complete: %s processed, %s skipped, %s failed",
        summary.processed,
        summary.skipped,
        summary.failed,
    )
    return summary
