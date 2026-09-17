"""Read-only access to ingested_content (owned by ingestion_pipeline).

NOTE (ADR-0003 follow-up): this is the third independent module to
duplicate knowledge of this table's schema (after ingestion_pipeline
itself). This is the trigger condition ADR-0003 flagged for extracting
a shared internal package -- deliberately deferred to a dedicated
future session rather than introducing a new cross-project dependency
mechanism (uv path dependencies) under time pressure. Tracked as the
top item for the next architecture session.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import Column, String, create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, declarative_base

from requirement_classifier.models import TrainingExample

_Base = declarative_base()


class _IngestedContentRow(_Base):
    __tablename__ = "ingested_content"

    id = Column(String(36), primary_key=True)
    document_type = Column(String(64), nullable=False)
    structured_data = Column(JSONB, nullable=True)
    status = Column(String(16), nullable=False)


class TrainingDataReader(ABC):
    @abstractmethod
    def get_training_examples(self) -> list[TrainingExample]: ...


class InMemoryTrainingDataReader(TrainingDataReader):
    """Test double -- never used in production."""

    def __init__(self, examples: list[TrainingExample]) -> None:
        self._examples = examples

    def get_training_examples(self) -> list[TrainingExample]:
        return list(self._examples)


class PostgresTrainingDataReader(TrainingDataReader):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)

    def get_training_examples(self) -> list[TrainingExample]:
        with Session(self._engine) as session:
            stmt = select(_IngestedContentRow).where(
                _IngestedContentRow.document_type == "excel_requirements",
                _IngestedContentRow.status == "success",
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
