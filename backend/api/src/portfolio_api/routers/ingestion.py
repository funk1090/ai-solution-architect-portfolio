"""Wraps ingestion_pipeline (Phase 2/5). Exposes both the sequential
and multiprocessing paths built in Feature 0005.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from portfolio_api.auth import verify_api_key

router = APIRouter(prefix="/ingestion", tags=["ingestion"], dependencies=[Depends(verify_api_key)])


class IngestRequest(BaseModel):
    parallel: bool = False
    workers: int | None = None


class IngestResponse(BaseModel):
    processed: int
    skipped: int
    failed: int


@router.post("/run", response_model=IngestResponse)
def run_ingestion_endpoint(request: IngestRequest) -> IngestResponse:
    from ingestion_pipeline.config import Settings
    from ingestion_pipeline.factory import ParserFactory
    from ingestion_pipeline.pipeline import run_ingestion, run_ingestion_parallel
    from ingestion_pipeline.repository import (
        PostgresDocumentMetadataReader,
        PostgresIngestedContentRepository,
    )

    settings = Settings()
    reader = PostgresDocumentMetadataReader(settings.database_url)
    repository = PostgresIngestedContentRepository(settings.database_url)
    repository.create_tables()

    if request.parallel:
        summary = run_ingestion_parallel(
            reader, settings.database_url, worker_count=request.workers
        )
    else:
        factory = ParserFactory()
        summary = run_ingestion(reader, repository, factory)

    return IngestResponse(
        processed=summary.processed, skipped=summary.skipped, failed=summary.failed
    )
