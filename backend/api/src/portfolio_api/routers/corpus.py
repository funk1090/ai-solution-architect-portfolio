"""Corpus overview for the web frontend (Feature 0008, FR2/FR6).

Read-only. The pure function `build_summary` holds the logic and is
unit-tested; `read_counts` is the only part that touches the database
and is injected as a FastAPI dependency so tests can replace it.
"""
from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from portfolio_api.auth import verify_api_key

router = APIRouter(prefix="/corpus", tags=["corpus"], dependencies=[Depends(verify_api_key)])


class DocumentTypeSummary(BaseModel):
    document_type: str
    generated: int
    ingested: int


class CorpusSummary(BaseModel):
    by_type: list[DocumentTypeSummary]
    total_generated: int
    total_ingested: int
    indexed_chunks: int


@dataclass
class CorpusCounts:
    generated: dict[str, int] = field(default_factory=dict)
    ingested: dict[str, int] = field(default_factory=dict)
    indexed_chunks: int = 0


def build_summary(counts: CorpusCounts) -> CorpusSummary:
    types = sorted(set(counts.generated) | set(counts.ingested))
    by_type = [
        DocumentTypeSummary(
            document_type=t,
            generated=counts.generated.get(t, 0),
            ingested=counts.ingested.get(t, 0),
        )
        for t in types
    ]
    return CorpusSummary(
        by_type=by_type,
        total_generated=sum(counts.generated.values()),
        total_ingested=sum(counts.ingested.values()),
        indexed_chunks=counts.indexed_chunks,
    )


def read_counts(database_url: str | None = None) -> CorpusCounts:
    """Counts per document type. Every table is created lazily by the first
    feature that needs it, so on a fresh database any of them may not exist
    yet: a missing table simply counts as empty (never an error)."""
    from shared_core.schema import DocumentMetadataTable, IngestedContentTable
    from sqlalchemy import create_engine, func, inspect, select, text

    from knowledge_assistant.config import Settings

    engine = create_engine(database_url or Settings().database_url, future=True)
    existing = set(inspect(engine).get_table_names())
    generated: dict[str, int] = {}
    ingested: dict[str, int] = {}
    chunks = 0
    with engine.connect() as conn:
        if DocumentMetadataTable.__tablename__ in existing:
            generated = dict(
                conn.execute(
                    select(DocumentMetadataTable.document_type, func.count()).group_by(
                        DocumentMetadataTable.document_type
                    )
                ).all()
            )
        if IngestedContentTable.__tablename__ in existing:
            ingested = dict(
                conn.execute(
                    select(IngestedContentTable.document_type, func.count())
                    .where(IngestedContentTable.status == "success")
                    .group_by(IngestedContentTable.document_type)
                ).all()
            )
        if "document_chunks" in existing:
            chunks = conn.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar_one()
    engine.dispose()
    return CorpusCounts(generated=generated, ingested=ingested, indexed_chunks=chunks)


def get_counts_reader() -> Callable[[], CorpusCounts]:
    """Dependency returning the reader WITHOUT calling it. FastAPI keeps
    resolving other dependencies after a validation error (e.g. a missing
    API key header), so a dependency that queried the database directly
    would hit it for unauthenticated requests. Calling the reader inside
    the endpoint guarantees auth has passed first."""
    return read_counts


@router.get("/summary", response_model=CorpusSummary)
def corpus_summary(
    reader: Callable[[], CorpusCounts] = Depends(get_counts_reader),
) -> CorpusSummary:
    return build_summary(reader())
