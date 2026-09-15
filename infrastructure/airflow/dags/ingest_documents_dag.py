"""Real ingestion DAG for Phase 2 (Document Intelligence Pipeline).

Replaces the earlier placeholder (list_generated_documents). This DAG
calls ingestion_pipeline.pipeline.run_ingestion directly -- the exact
same function exercised by the CLI (ingestion-pipeline command) and by
the unit tests. No logic is duplicated here; Airflow is purely the
scheduler/trigger, not a second implementation of the pipeline.
"""
import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)


def run_document_ingestion() -> None:
    # Imports are inside the callable, not at module level: Airflow
    # parses every DAG file on a schedule to build the UI's DAG list,
    # and an import error here would only be visible in the task logs,
    # not at parse time -- keeping heavy/optional imports inside the
    # callable makes DAG parsing itself more resilient.
    from ingestion_pipeline.config import Settings
    from ingestion_pipeline.factory import ParserFactory
    from ingestion_pipeline.pipeline import run_ingestion
    from ingestion_pipeline.repository import (
        PostgresDocumentMetadataReader,
        PostgresIngestedContentRepository,
    )

    # Settings() reads DATABASE_URL from the environment automatically
    # (pydantic-settings matches env vars case-insensitively) -- same
    # mechanism the CLI uses, just sourced from the container's env
    # instead of a local .env file.
    settings = Settings()

    reader = PostgresDocumentMetadataReader(settings.database_url)
    repository = PostgresIngestedContentRepository(settings.database_url)
    repository.create_tables()
    factory = ParserFactory()

    summary = run_ingestion(reader=reader, repository=repository, factory=factory)
    logger.info(
        "Ingestion run complete: %s processed, %s skipped, %s failed",
        summary.processed,
        summary.skipped,
        summary.failed,
    )


with DAG(
    dag_id="ingest_documents",
    description="Extracts text/structured data from the Phase 1 synthetic document corpus.",
    start_date=datetime(2026, 1, 1),
    schedule=None,  # Manual trigger for now; a schedule can be added once volume justifies it.
    catchup=False,
    tags=["phase-2", "ingestion-pipeline"],
) as dag:
    ingest_task = PythonOperator(
        task_id="run_document_ingestion",
        python_callable=run_document_ingestion,
    )
