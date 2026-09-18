"""Persistence layer for the ingestion pipeline.

Table definitions now live in the shared_core package (ADR-0006). This
module implements two distinct access policies around those shared
tables:

- DocumentMetadataReader: READ-ONLY access to document_metadata, owned
  and written by the document-generator project.
- IngestedContentRepository: read/write access to ingested_content,
  owned by THIS project. Its uniqueness constraint on source_checksum
  (defined in shared_core) is the real enforcement of idempotency
  (NFR1).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from shared_core.schema import Base, DocumentMetadataTable, IngestedContentTable

from ingestion_pipeline.models import (
    DocumentType,
    IngestedContent,
    IngestionStatus,
    PendingDocument,
)


# --- Reading document_metadata (owned by document-generator) ---------------


class DocumentMetadataReader(ABC):
    @abstractmethod
    def list_all_documents(self) -> list[PendingDocument]: ...


class InMemoryDocumentMetadataReader(DocumentMetadataReader):
    """Test double — never used in production."""

    def __init__(self, documents: list[PendingDocument]) -> None:
        self._documents = documents

    def list_all_documents(self) -> list[PendingDocument]:
        return list(self._documents)


class PostgresDocumentMetadataReader(DocumentMetadataReader):
    """Read-only: never calls create_all — that table belongs to the
    document-generator project and is expected to already exist."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)

    def list_all_documents(self) -> list[PendingDocument]:
        with Session(self._engine) as session:
            rows = session.execute(select(DocumentMetadataTable)).scalars().all()
            return [
                PendingDocument(
                    id=row.id,
                    document_type=DocumentType(row.document_type),
                    file_path=row.file_path,
                    checksum_sha256=row.checksum_sha256,
                )
                for row in rows
            ]


# --- Writing ingested_content (owned by THIS project) -----------------------


class IngestedContentRepository(ABC):
    @abstractmethod
    def save(self, content: IngestedContent) -> None: ...

    @abstractmethod
    def exists_checksum(self, checksum: str) -> bool: ...

    @abstractmethod
    def list_all(self) -> list[IngestedContent]: ...


class InMemoryIngestedContentRepository(IngestedContentRepository):
    def __init__(self) -> None:
        self._records: list[IngestedContent] = []

    def save(self, content: IngestedContent) -> None:
        self._records.append(content)

    def exists_checksum(self, checksum: str) -> bool:
        return any(r.source_checksum == checksum for r in self._records)

    def list_all(self) -> list[IngestedContent]:
        return list(self._records)


class PostgresIngestedContentRepository(IngestedContentRepository):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)

    def create_tables(self) -> None:
        """Idempotent — safe to call on every pipeline run."""
        Base.metadata.create_all(self._engine)

    def save(self, content: IngestedContent) -> None:
        row = IngestedContentTable(
            id=str(content.id),
            source_checksum=content.source_checksum,
            document_type=content.document_type.value,
            extracted_text=content.extracted_text,
            structured_data=content.structured_data,
            status=content.status.value,
            error_message=content.error_message,
            ingested_at=content.ingested_at,
        )
        with Session(self._engine) as session:
            session.add(row)
            session.commit()

    def exists_checksum(self, checksum: str) -> bool:
        with Session(self._engine) as session:
            stmt = select(IngestedContentTable).where(
                IngestedContentTable.source_checksum == checksum
            )
            return session.execute(stmt).first() is not None

    def list_all(self) -> list[IngestedContent]:
        with Session(self._engine) as session:
            rows = session.execute(select(IngestedContentTable)).scalars().all()
            return [
                IngestedContent(
                    id=row.id,
                    source_checksum=row.source_checksum,
                    document_type=DocumentType(row.document_type),
                    extracted_text=row.extracted_text,
                    structured_data=row.structured_data,
                    status=IngestionStatus(row.status),
                    error_message=row.error_message,
                    ingested_at=row.ingested_at,
                )
                for row in rows
            ]
