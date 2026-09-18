"""Command-line entry point for manual runs (Airflow will call run_ingestion directly)."""
import logging
import time

import typer

from ingestion_pipeline.config import Settings
from ingestion_pipeline.factory import ParserFactory
from ingestion_pipeline.pipeline import run_ingestion, run_ingestion_parallel
from ingestion_pipeline.repository import (
    PostgresDocumentMetadataReader,
    PostgresIngestedContentRepository,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = typer.Typer()


@app.callback()
def callback() -> None:
    """Document Intelligence Pipeline CLI."""


@app.command()
def ingest(
    parallel: bool = typer.Option(
        False, help="Feature 0005/FR4: parse documents across multiple CPU cores."
    ),
    workers: int = typer.Option(
        None, help="Worker process count for --parallel (defaults to CPU count)."
    ),
) -> None:
    settings = Settings()

    reader = PostgresDocumentMetadataReader(settings.database_url)
    repository = PostgresIngestedContentRepository(settings.database_url)
    repository.create_tables()

    start = time.perf_counter()
    if parallel:
        summary = run_ingestion_parallel(reader, settings.database_url, worker_count=workers)
    else:
        factory = ParserFactory()
        summary = run_ingestion(reader=reader, repository=repository, factory=factory)
    elapsed = time.perf_counter() - start

    typer.echo(
        f"Processed: {summary.processed} | Skipped: {summary.skipped} | "
        f"Failed: {summary.failed} | Elapsed: {elapsed:.2f}s"
    )


@app.command()
def benchmark(
    workers: int = typer.Option(None, help="Worker count for the parallel run."),
) -> None:
    """Feature 0005: times sequential vs. parallel ingestion.

    Note: to compare fairly, clear ingested_content for these documents
    BEFORE running this command (e.g. `DELETE FROM ingested_content;`
    in psql) -- this benchmark does not delete anything on its own, by
    design (see this project's established caution around destructive
    operations on real data).
    """
    settings = Settings()
    reader = PostgresDocumentMetadataReader(settings.database_url)
    documents = reader.list_all_documents()
    typer.echo(f"Benchmarking against {len(documents)} documents in document_metadata.\n")

    repository = PostgresIngestedContentRepository(settings.database_url)
    repository.create_tables()
    factory = ParserFactory()

    start = time.perf_counter()
    sequential_summary = run_ingestion(reader, repository, factory)
    sequential_seconds = time.perf_counter() - start
    typer.echo(
        f"Sequential: {sequential_seconds:.2f}s "
        f"(processed={sequential_summary.processed}, skipped={sequential_summary.skipped})"
    )

    typer.echo(
        "\nTo benchmark the parallel path fairly, clear ingested_content now "
        "and re-run: uv run ingestion-pipeline ingest --parallel"
    )


if __name__ == "__main__":
    app()
