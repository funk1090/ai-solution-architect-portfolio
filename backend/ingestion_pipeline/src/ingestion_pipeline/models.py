"""Typed domain models for the ingestion pipeline.

Note: DocumentType is intentionally duplicated from document_generator's
model of the same name, rather than imported across projects — the two
are independent uv projects (ADR-0003). If a third module needs this
enum, extracting a shared package becomes the right call; duplicating
it twice is a deliberate, documented trade-off, not an oversight.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    RFP = "rfp"
    EXCEL_REQUIREMENTS = "excel_requirements"
    TECHNICAL_MANUAL = "technical_manual"


class IngestionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class PendingDocument(BaseModel):
    """A document read from document_metadata, awaiting ingestion."""

    id: uuid.UUID
    document_type: DocumentType
    file_path: str
    checksum_sha256: str


class IngestedContent(BaseModel):
    """A single ingestion result — one row per attempted document."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_checksum: str
    document_type: DocumentType
    extracted_text: str | None = None
    structured_data: list[dict] | None = None
    status: IngestionStatus
    error_message: str | None = None
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
