"""Pipeline orchestration — this is what the Airflow DAG will call.

Per-document error isolation (FR8/NFR5): one corrupt file must not
abort the whole run. Each document gets its own try/except, and a
failure is recorded as data (status='failed'), not just logged and lost.

Performance note (Feature 0005, FR4): the actual per-document work
(parse -> build the record) is extracted into `_process_single_document`,
a pure function with no database access. This is what makes it safe to
run inside a multiprocessing worker (NFR5: each worker opens its own
database connection, never a shared one) AND fully unit-testable
without a live database or real multiprocessing -- the exact same
function is exercised by both `run_ingestion` (sequential) and
`run_ingestion_parallel` (FR4), so there is only one place where the
actual parsing/error-handling logic is defined and tested.
"""
import logging
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

from ingestion_pipeline.factory import ParserFactory
from ingestion_pipeline.models import IngestedContent, IngestionStatus, PendingDocument
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


def _process_single_document(
    document: PendingDocument, factory: ParserFactory
) -> IngestedContent:
    """Pure per-document processing: parse -> build the record. No
    database access -- safe to call from any process, and fully
    testable with nothing but a real or fake file on disk.
    """
    try:
        parser = factory.create(document.document_type)
        parsed = parser.parse(Path(document.file_path))
        return IngestedContent(
            source_checksum=document.checksum_sha256,
            document_type=document.document_type,
            extracted_text=parsed.extracted_text,
            structured_data=parsed.structured_data,
            status=IngestionStatus.SUCCESS,
        )
    except Exception as exc:  # noqa: BLE001 - intentional: isolate any parser failure
        return IngestedContent(
            source_checksum=document.checksum_sha256,
            document_type=document.document_type,
            status=IngestionStatus.FAILED,
            error_message=str(exc),
        )


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

        record = _process_single_document(document, factory)
        if record.status == IngestionStatus.SUCCESS:
            processed += 1
            logger.info("Ingested %s (%s)", document.file_path, document.document_type.value)
        else:
            failed += 1
            logger.warning("Failed to ingest %s: %s", document.file_path, record.error_message)

        repository.save(record)

    summary = IngestionSummary(processed=processed, skipped=skipped, failed=failed)
    logger.info(
        "Ingestion run complete: %s processed, %s skipped, %s failed",
        summary.processed,
        summary.skipped,
        summary.failed,
    )
    return summary


_worker_repository = None  # type: ignore[var-annotated]  # process-local, set by _init_worker


def _init_worker(database_url: str) -> None:
    """Runs ONCE when a worker process starts (Pool's `initializer`) --
    this is what actually satisfies NFR5 ("each worker process uses its
    own database engine"). The first implementation of this function
    created a new engine inside `_worker` itself, called once PER
    DOCUMENT rather than once per PROCESS -- with a large batch and
    several workers, that opened far more simultaneous connections than
    PostgreSQL's default `max_connections` allows, failing with
    "sorry, too many clients already". Creating the engine here, in the
    initializer, means exactly `worker_count` engines exist for the
    entire run, reused across every document that worker is assigned.
    """
    global _worker_repository
    from ingestion_pipeline.repository import PostgresIngestedContentRepository

    _worker_repository = PostgresIngestedContentRepository(database_url)


def _worker(document: PendingDocument) -> str:
    if _worker_repository.exists_checksum(document.checksum_sha256):
        return "skipped"

    record = _process_single_document(document, ParserFactory())
    _worker_repository.save(record)
    return "processed" if record.status == IngestionStatus.SUCCESS else "failed"


def run_ingestion_parallel(
    reader: DocumentMetadataReader,
    database_url: str,
    worker_count: int | None = None,
) -> IngestionSummary:
    """FR4: parallelizes document parsing across CPU cores.

    Note: this path requires a real database -- each worker process
    needs a durable, shared place to check for and record its own
    results. It cannot be exercised with the in-memory test doubles
    used elsewhere in this codebase (a forked process gets its own copy
    of any in-memory Python object, not a shared view of it), which is
    exactly why `_process_single_document` above is factored out to be
    tested on its own, without needing real multiprocessing or a live
    database to validate the logic that runs inside each worker.
    """
    documents = reader.list_all_documents()

    with Pool(
        processes=worker_count, initializer=_init_worker, initargs=(database_url,)
    ) as pool:
        results = pool.map(_worker, documents)

    summary = IngestionSummary(
        processed=results.count("processed"),
        skipped=results.count("skipped"),
        failed=results.count("failed"),
    )
    logger.info(
        "Parallel ingestion run complete: %s processed, %s skipped, %s failed",
        summary.processed,
        summary.skipped,
        summary.failed,
    )
    return summary
