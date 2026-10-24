"""Reads RFPs for compliance checks (Feature 0009).

Combines document_metadata (file name, issuing company) with
ingested_content (extracted text) through the shared schema (ADR-0006).
Read-only.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import PurePath

from pydantic import BaseModel
from shared_core.schema import DocumentMetadataTable, IngestedContentTable
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session


class RfpRecord(BaseModel):
    source_checksum: str
    file_name: str
    issuing_organization: str
    text: str


class RfpSource(ABC):
    @abstractmethod
    def list_rfps(self) -> list[RfpRecord]: ...

    def get_rfp(self, source_checksum: str) -> RfpRecord | None:
        for record in self.list_rfps():
            if record.source_checksum == source_checksum:
                return record
        return None


class InMemoryRfpSource(RfpSource):
    """Test double -- never used in production."""

    def __init__(self, records: list[RfpRecord]) -> None:
        self._records = records

    def list_rfps(self) -> list[RfpRecord]:
        return list(self._records)


class PostgresRfpSource(RfpSource):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)

    def list_rfps(self) -> list[RfpRecord]:
        with Session(self._engine) as session:
            stmt = (
                select(
                    IngestedContentTable.source_checksum,
                    IngestedContentTable.extracted_text,
                    DocumentMetadataTable.file_path,
                    DocumentMetadataTable.related_entity,
                )
                .join(
                    DocumentMetadataTable,
                    DocumentMetadataTable.checksum_sha256 == IngestedContentTable.source_checksum,
                )
                .where(
                    IngestedContentTable.document_type == "rfp",
                    IngestedContentTable.status == "success",
                )
                .order_by(DocumentMetadataTable.file_path)
            )
            rows = session.execute(stmt).all()
        return [
            RfpRecord(
                source_checksum=checksum,
                file_name=PurePath(file_path).name,
                issuing_organization=entity,
                text=text or "",
            )
            for checksum, text, file_path, entity in rows
        ]
