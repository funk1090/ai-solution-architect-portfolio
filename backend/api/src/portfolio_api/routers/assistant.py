"""Wraps knowledge_assistant (Phase 4/5).

Feature 0008: the embedding model is now loaded once per process
(FR7) and /ask also returns `source_details` (FR6) -- human-readable
document type and file name per source. `sources` is unchanged.
"""
from pathlib import PurePath
from typing import Callable
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from portfolio_api.auth import verify_api_key
from portfolio_api.dependencies import get_embedding_model

router = APIRouter(prefix="/assistant", tags=["assistant"], dependencies=[Depends(verify_api_key)])


class IndexResponse(BaseModel):
    documents_processed: int
    chunks_created: int
    chunks_skipped: int


class AskRequest(BaseModel):
    question: str


class SourceDetail(BaseModel):
    checksum: str
    document_type: str | None = None
    file_name: str | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    grounded: bool
    source_details: list[SourceDetail] = []


def resolve_source_details(
    checksums: list[str],
    lookup: Callable[[list[str]], dict[str, tuple[str, str]]],
) -> list[SourceDetail]:
    """Pure: map checksums to (document_type, file_path) using `lookup`.
    Unknown checksums are kept with empty details instead of dropped,
    so the UI never silently loses a source."""
    found = lookup(checksums) if checksums else {}
    details = []
    for checksum in checksums:
        doc_type, file_path = found.get(checksum, (None, None))
        details.append(
            SourceDetail(
                checksum=checksum,
                document_type=doc_type,
                file_name=PurePath(file_path).name if file_path else None,
            )
        )
    return details


def lookup_document_metadata(checksums: list[str]) -> dict[str, tuple[str, str]]:
    from knowledge_assistant.config import Settings
    from shared_core.schema import DocumentMetadataTable
    from sqlalchemy import create_engine, select

    engine = create_engine(Settings().database_url, future=True)
    with engine.connect() as conn:
        rows = conn.execute(
            select(
                DocumentMetadataTable.checksum_sha256,
                DocumentMetadataTable.document_type,
                DocumentMetadataTable.file_path,
            ).where(DocumentMetadataTable.checksum_sha256.in_(checksums))
        ).all()
    return {r[0]: (r[1], r[2]) for r in rows}


@router.post("/index", response_model=IndexResponse)
def index_documents() -> IndexResponse:
    from knowledge_assistant.config import Settings
    from knowledge_assistant.content_reader import PostgresIngestedContentReader
    from knowledge_assistant.pipeline_index import run_indexing
    from knowledge_assistant.vector_store import PgVectorRepository

    settings = Settings()
    reader = PostgresIngestedContentReader(settings.database_url)
    embedding_model = get_embedding_model(settings.embedding_model_name)
    vector_repo = PgVectorRepository(settings.database_url)
    vector_repo.create_tables()

    summary = run_indexing(
        reader, embedding_model, vector_repo, settings.chunk_size, settings.chunk_overlap
    )
    return IndexResponse(
        documents_processed=summary.documents_processed,
        chunks_created=summary.chunks_created,
        chunks_skipped=summary.chunks_skipped,
    )


@router.post("/ask", response_model=AskResponse)
def ask_assistant(request: AskRequest) -> AskResponse:
    from knowledge_assistant.config import Settings
    from knowledge_assistant.llm import LLMBackendFactory
    from knowledge_assistant.pipeline_query import ask_question
    from knowledge_assistant.vector_store import PgVectorRepository

    settings = Settings()
    embedding_model = get_embedding_model(settings.embedding_model_name)
    vector_repo = PgVectorRepository(settings.database_url)
    llm_backend = LLMBackendFactory().create(
        "ollama", settings.ollama_base_url, settings.ollama_model
    )

    result = ask_question(
        request.question,
        embedding_model,
        vector_repo,
        llm_backend,
        settings.top_k,
        settings.similarity_threshold,
    )
    return AskResponse(
        answer=result.answer,
        sources=result.sources,
        grounded=result.grounded,
        source_details=resolve_source_details(result.sources, lookup_document_metadata),
    )
