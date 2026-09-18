"""Metadata persistence layer (ADR-0002: filesystem + PostgreSQL metadata).

Table definition now lives in the shared_core package (ADR-0006) — this
module only implements the read/write policy specific to
document-generator, which owns this table.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from shared_core.schema import Base, DocumentMetadataTable

from document_generator.models import DocumentMetadata, DocumentType


class DocumentMetadataRepository(ABC):
    @abstractmethod
    def save(self, metadata: DocumentMetadata) -> None: ...

    @abstractmethod
    def exists_checksum(self, checksum: str) -> bool: ...

    @abstractmethod
    def list_all(self) -> list[DocumentMetadata]: ...


class InMemoryDocumentMetadataRepository(DocumentMetadataRepository):
    """Test double — used by unit tests, never by production code."""

    def __init__(self) -> None:
        self._records: list[DocumentMetadata] = []

    def save(self, metadata: DocumentMetadata) -> None:
        self._records.append(metadata)

    def exists_checksum(self, checksum: str) -> bool:
        return any(r.checksum_sha256 == checksum for r in self._records)

    def list_all(self) -> list[DocumentMetadata]:
        return list(self._records)


class PostgresDocumentMetadataRepository(DocumentMetadataRepository):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)

    def create_tables(self) -> None:
        """Idempotent — safe to call on every application startup."""
        Base.metadata.create_all(self._engine)

    def save(self, metadata: DocumentMetadata) -> None:
        row = DocumentMetadataTable(
            id=str(metadata.id),
            document_type=metadata.document_type.value,
            file_path=metadata.file_path,
            checksum_sha256=metadata.checksum_sha256,
            generated_at=metadata.generated_at,
            related_entity=metadata.related_entity,
            seed=metadata.seed,
        )
        with Session(self._engine) as session:
            session.add(row)
            session.commit()

    def exists_checksum(self, checksum: str) -> bool:
        with Session(self._engine) as session:
            stmt = select(DocumentMetadataTable).where(
                DocumentMetadataTable.checksum_sha256 == checksum
            )
            return session.execute(stmt).first() is not None

    def list_all(self) -> list[DocumentMetadata]:
        with Session(self._engine) as session:
            rows = session.execute(select(DocumentMetadataTable)).scalars().all()
            return [
                DocumentMetadata(
                    id=row.id,
                    document_type=DocumentType(row.document_type),
                    file_path=row.file_path,
                    checksum_sha256=row.checksum_sha256,
                    generated_at=row.generated_at,
                    related_entity=row.related_entity,
                    seed=row.seed,
                )
                for row in rows
            ]
