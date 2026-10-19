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


def read_counts() -> CorpusCounts:
    from shared_core.schema import DocumentMetadataTable, IngestedContentTable
    from sqlalchemy import create_engine, func, select, text
    from sqlalchemy.exc import ProgrammingError

    from knowledge_assistant.config import Settings

    engine = create_engine(Settings().database_url, future=True)
    with engine.connect() as conn:
        generated = dict(
            conn.execute(
                select(DocumentMetadataTable.document_type, func.count()).group_by(
                    DocumentMetadataTable.document_type
                )
            ).all()
        )
        ingested = dict(
            conn.execute(
                select(IngestedContentTable.document_type, func.count())
                .where(IngestedContentTable.status == "success")
                .group_by(IngestedContentTable.document_type)
            ).all()
        )
        try:
            chunks = conn.execute(text("SELECT COUNT(*) FROM document_chunks")).scalar_one()
        except ProgrammingError:  # table not created yet: nothing indexed
            chunks = 0
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
