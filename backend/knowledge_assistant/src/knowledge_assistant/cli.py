"""Command-line entry point."""
import logging

import typer

from knowledge_assistant.config import Settings
from knowledge_assistant.content_reader import PostgresIngestedContentReader
from knowledge_assistant.embeddings import EmbeddingModelFactory
from knowledge_assistant.llm import LLMBackendFactory
from knowledge_assistant.pipeline_index import run_indexing
from knowledge_assistant.pipeline_query import ask_question
from knowledge_assistant.vector_store import PgVectorRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = typer.Typer()


@app.callback()
def callback() -> None:
    """Enterprise AI Knowledge Assistant CLI."""


@app.command()
def index() -> None:
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
    typer.echo(
        f"Documents processed: {summary.documents_processed} | "
        f"Chunks created: {summary.chunks_created} | "
        f"Skipped: {summary.chunks_skipped}"
    )


@app.command()
def ask(question: str = typer.Option(..., help="Question to ask the knowledge base.")) -> None:
    settings = Settings()

    embedding_model = EmbeddingModelFactory().create(
        "sentence-transformers", settings.embedding_model_name
    )
    vector_repo = PgVectorRepository(settings.database_url)
    llm_backend = LLMBackendFactory().create(
        "ollama", settings.ollama_base_url, settings.ollama_model
    )

    result = ask_question(
        question,
        embedding_model,
        vector_repo,
        llm_backend,
        settings.top_k,
        settings.similarity_threshold,
    )

    typer.echo(f"Answer: {result.answer}")
    if result.sources:
        typer.echo(f"Sources: {', '.join(s[:8] for s in result.sources)}")


if __name__ == "__main__":
    app()
