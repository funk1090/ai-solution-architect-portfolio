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


@app.command()
def benchmark_embeddings() -> None:
    """Feature 0005: measures per-chunk vs batched embedding calls."""
    from knowledge_assistant.benchmark import run_benchmark

    run_benchmark()


@app.command()
def compliance_check(
    rfp: str = typer.Option(..., help="RFP file name (e.g. rfp_0003.pdf) or checksum prefix."),
    judge: bool = typer.Option(True, help="Use the LLM judge (otherwise retrieval-only)."),
) -> None:
    """Feature 0009: check one RFP's requirements against the technical manuals."""
    from knowledge_assistant.compliance import check_rfp
    from knowledge_assistant.rfp_source import PostgresRfpSource

    settings = Settings()
    records = PostgresRfpSource(settings.database_url).list_rfps()
    matches = [r for r in records if r.file_name == rfp or r.source_checksum.startswith(rfp)]
    if len(matches) != 1:
        typer.echo(f"Expected exactly one RFP matching {rfp!r}, found {len(matches)}.")
        raise typer.Exit(code=1)
    record = matches[0]

    embedding_model = EmbeddingModelFactory().create(
        "sentence-transformers", settings.embedding_model_name
    )
    vector_repo = PgVectorRepository(settings.database_url)
    llm_backend = (
        LLMBackendFactory().create(
            "ollama", settings.ollama_base_url, settings.ollama_model, temperature=0.0
        )
        if judge
        else None
    )
    report = check_rfp(
        record.text,
        embedding_model,
        vector_repo,
        llm_backend,
        settings.compliance_top_k,
        settings.compliance_similarity_threshold,
    )

    typer.echo(f"{record.file_name} ({record.issuing_organization})")
    for a in report.assessments:
        typer.echo(f"  {a.number}. [{a.verdict.value}] {a.requirement}")
        typer.echo(f"       {a.rationale}")
    typer.echo(f"Summary: {report.counts()}")


@app.command()
def compliance_evaluate(
    judge_sample: int = typer.Option(
        0, help="Also evaluate the LLM judge on this many requirements (0 = skip; the judge is slow)."
    ),
) -> None:
    """Feature 0009: score the engine against the synthetic answer key (ADR-0008)."""
    from knowledge_assistant.compliance_eval import (
        baseline_always_supported,
        evaluate_judge,
        labeled_requirements,
        sweep_thresholds,
    )
    from knowledge_assistant.rfp_source import PostgresRfpSource

    settings = Settings()
    labeled = labeled_requirements(PostgresRfpSource(settings.database_url).list_rfps())
    if not labeled:
        typer.echo("No labeled requirements found. Are RFPs ingested?")
        raise typer.Exit(code=1)

    embedding_model = EmbeddingModelFactory().create(
        "sentence-transformers", settings.embedding_model_name
    )
    vector_repo = PgVectorRepository(settings.database_url)

    truth = [t for _, t in labeled]
    typer.echo(
        f"Requirements: {len(labeled)} | actually supported: {sum(truth)} "
        f"({sum(truth) / len(truth):.0%}) -- synthetic data, scores are optimistic"
    )
    base = baseline_always_supported(truth)
    typer.echo(f"Baseline (always SUPPORTED): accuracy={base.accuracy:.3f}")

    thresholds = [round(0.15 + 0.05 * i, 2) for i in range(10)]
    results = sweep_thresholds(labeled, embedding_model, vector_repo, settings.compliance_top_k, thresholds)
    typer.echo("Retrieval-only, by similarity threshold:")
    for threshold, m in results.items():
        typer.echo(
            f"  {threshold:.2f}  accuracy={m.accuracy:.3f} precision={m.precision:.3f} "
            f"recall={m.recall:.3f} f1={m.f1:.3f}"
        )
    best_threshold = max(results, key=lambda t: results[t].f1)
    typer.echo(f"Best threshold by F1: {best_threshold:.2f}")

    if judge_sample > 0:
        llm_backend = LLMBackendFactory().create(
            "ollama", settings.ollama_base_url, settings.ollama_model, temperature=0.0
        )
        sample = labeled[:: max(1, len(labeled) // judge_sample)][:judge_sample]
        m, distribution = evaluate_judge(
            sample, embedding_model, vector_repo, llm_backend,
            settings.compliance_top_k, best_threshold,
        )
        retrieval_only = sweep_thresholds(
            sample, embedding_model, vector_repo, settings.compliance_top_k, [best_threshold]
        )[best_threshold]
        typer.echo(f"On a sample of {len(sample)} requirements (threshold {best_threshold:.2f}):")
        typer.echo(f"  retrieval-only: accuracy={retrieval_only.accuracy:.3f} f1={retrieval_only.f1:.3f}")
        typer.echo(f"  retrieval+judge: accuracy={m.accuracy:.3f} f1={m.f1:.3f} verdicts={distribution}")


if __name__ == "__main__":
    app()
