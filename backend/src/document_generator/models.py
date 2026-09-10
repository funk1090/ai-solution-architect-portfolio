"""Typed domain models for generated documents.

Using Pydantic here (rather than plain dicts) means invalid data is
rejected at the boundary, and every consumer of these objects gets
autocomplete and type-checking instead of guessing dictionary keys.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Every supported synthetic document type.

    Adding a new type here is intentional and cheap; it does NOT require
    touching existing generator classes (Open/Closed Principle) — only
    registering a new generator in the factory (see factory.py).
    """

    RFP = "rfp"
    EXCEL_REQUIREMENTS = "excel_requirements"
    TECHNICAL_MANUAL = "technical_manual"


class DocumentMetadata(BaseModel):
    """A single record describing one generated file.

    This is the object persisted by a DocumentMetadataRepository
    (see repository.py) — it never carries the binary file content
    itself, only the pointer to it plus integrity/traceability data.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    document_type: DocumentType
    file_path: str
    checksum_sha256: str
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    related_entity: str
    seed: int
