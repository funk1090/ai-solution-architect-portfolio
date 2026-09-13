"""Command-line entry point for manual runs (Airflow will call run_ingestion directly)."""
import logging

import typer

from ingestion_pipeline.config import Settings
from ingestion_pipeline.factory import ParserFactory
from ingestion_pipeline.pipeline import run_ingestion
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
def ingest() -> None:
    settings = Settings()

    reader = PostgresDocumentMetadataReader(settings.database_url)
    repository = PostgresIngestedContentRepository(settings.database_url)
    repository.create_tables()
    factory = ParserFactory()

    summary = run_ingestion(reader=reader, repository=repository, factory=factory)
    typer.echo(
        f"Processed: {summary.processed} | Skipped: {summary.skipped} | Failed: {summary.failed}"
    )


if __name__ == "__main__":
    app()
