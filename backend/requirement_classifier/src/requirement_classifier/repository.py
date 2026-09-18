"""Read-only access to ingested_content (owned by ingestion_pipeline).

Table definition now lives in the shared_core package (ADR-0006).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from shared_core.schema import IngestedContentTable

from requirement_classifier.models import TrainingExample


class TrainingDataReader(ABC):
    @abstractmethod
    def get_training_examples(self) -> list[TrainingExample]: ...


class InMemoryTrainingDataReader(TrainingDataReader):
    """Test double — never used in production."""

    def __init__(self, examples: list[TrainingExample]) -> None:
        self._examples = examples

    def get_training_examples(self) -> list[TrainingExample]:
        return list(self._examples)


class PostgresTrainingDataReader(TrainingDataReader):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)

    def get_training_examples(self) -> list[TrainingExample]:
        with Session(self._engine) as session:
            stmt = select(IngestedContentTable).where(
                IngestedContentTable.document_type == "excel_requirements",
                IngestedContentTable.status == "success",
            )
            rows = session.execute(stmt).scalars().all()

        examples: list[TrainingExample] = []
        for row in rows:
            for record in row.structured_data or []:
                examples.append(
                    TrainingExample(
                        description=record["Description"],
                        category=record["Category"],
                        priority=record["Priority"],
                    )
                )
        return examples
