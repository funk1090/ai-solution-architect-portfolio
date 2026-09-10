"""Command-line entry point.

Usage examples:
    uv run python -m document_generator.cli generate --document-type rfp --count 10
    uv run python -m document_generator.cli generate --document-type rfp --count 5 --no-use-postgres
"""
import logging

import typer

from document_generator.config import Settings
from document_generator.factory import GeneratorFactory
from document_generator.models import DocumentType
from document_generator.providers import EnterpriseFakerProvider
from document_generator.repository import (
    InMemoryDocumentMetadataRepository,
    PostgresDocumentMetadataRepository,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = typer.Typer()


@app.callback()
def callback() -> None:
    """Synthetic Enterprise Document Generator CLI.

    An explicit (empty) callback is required here so Typer keeps
    subcommands explicit (e.g. `generate`) even while there is only one
    command registered. Without it, Typer collapses a single-command
    app and stops expecting the command name at all — which breaks the
    moment a second command (e.g. `list`) is added later.
    """


@app.command()
def generate(
    document_type: DocumentType = typer.Option(..., help="Type of document to generate."),
    count: int = typer.Option(5, help="Number of documents to generate."),
    seed: int = typer.Option(None, help="Override the seed from .env for this run."),
    use_postgres: bool = typer.Option(
        True, help="Persist metadata to PostgreSQL (False uses an in-memory store)."
    ),
) -> None:
    settings = Settings()
    effective_seed = seed if seed is not None else settings.generation_seed

    provider = EnterpriseFakerProvider(seed=effective_seed)
    output_dir = settings.document_output_dir / document_type.value

    if use_postgres:
        repository = PostgresDocumentMetadataRepository(settings.database_url)
        repository.create_tables()
    else:
        repository = InMemoryDocumentMetadataRepository()

    factory = GeneratorFactory(provider=provider, repository=repository)
    generator = factory.create(document_type, output_dir=output_dir, seed=effective_seed)

    results = generator.generate(count)
    typer.echo(f"Generated {len(results)} '{document_type.value}' document(s) in {output_dir}")


if __name__ == "__main__":
    app()
