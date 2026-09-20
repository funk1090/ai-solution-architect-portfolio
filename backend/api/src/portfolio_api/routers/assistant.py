"""Wraps knowledge_assistant (Phase 4/5)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from portfolio_api.auth import verify_api_key

router = APIRouter(prefix="/assistant", tags=["assistant"], dependencies=[Depends(verify_api_key)])


class IndexResponse(BaseModel):
    documents_processed: int
    chunks_created: int
    chunks_skipped: int


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    grounded: bool


@router.post("/index", response_model=IndexResponse)
def index_documents() -> IndexResponse:
    from knowledge_assistant.config import Settings
    from knowledge_assistant.content_reader import PostgresIngestedContentReader
    from knowledge_assistant.embeddings import EmbeddingModelFactory
    from knowledge_assistant.pipeline_index import run_indexing
    from knowledge_assistant.vector_store import PgVectorRepository

    settings = Settings()
    reader = PostgresIngestedContentReader(settings.database_url)
    embedding_model = EmbeddingModelFactory().create(
        "sentence-transformers", settings.embedding_model_name
    )
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
    from knowledge_assistant.embeddings import EmbeddingModelFactory
    from knowledge_assistant.llm import LLMBackendFactory
    from knowledge_assistant.pipeline_query import ask_question
    from knowledge_assistant.vector_store import PgVectorRepository

    settings = Settings()
    embedding_model = EmbeddingModelFactory().create(
        "sentence-transformers", settings.embedding_model_name
    )
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
    return AskResponse(answer=result.answer, sources=result.sources, grounded=result.grounded)
