"""Reads indexable documents from ingested_content (owned by
ingestion_pipeline), using the shared schema (ADR-0006) -- the fourth
module to consume it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from shared_core.schema import IngestedContentTable

from knowledge_assistant.models import IndexableDocument

_INDEXABLE_TYPES = ("rfp", "technical_manual")


class IngestedContentReader(ABC):
    @abstractmethod
    def get_indexable_documents(self) -> list[IndexableDocument]: ...


class InMemoryIngestedContentReader(IngestedContentReader):
    """Test double — never used in production."""

    def __init__(self, documents: list[IndexableDocument]) -> None:
        self._documents = documents

    def get_indexable_documents(self) -> list[IndexableDocument]:
        return list(self._documents)


class PostgresIngestedContentReader(IngestedContentReader):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)

    def get_indexable_documents(self) -> list[IndexableDocument]:
        with Session(self._engine) as session:
            stmt = select(IngestedContentTable).where(
                IngestedContentTable.document_type.in_(_INDEXABLE_TYPES),
                IngestedContentTable.status == "success",
            )
            rows = session.execute(stmt).scalars().all()

        return [
            IndexableDocument(source_checksum=row.source_checksum, text=row.extracted_text)
            for row in rows
            if row.extracted_text
        ]
