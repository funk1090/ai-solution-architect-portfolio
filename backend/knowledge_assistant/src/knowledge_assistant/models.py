"""Typed domain models for the knowledge assistant."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class IndexableDocument(BaseModel):
    """A document read from ingested_content, ready to be chunked."""

    source_checksum: str
    text: str


class DocumentChunk(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_checksum: str
    chunk_index: int
    text: str
    embedding: list[float] | None = None


class RetrievedChunk(BaseModel):
    source_checksum: str
    chunk_index: int
    text: str
    score: float  # cosine similarity -- higher is more similar


class AnswerResult(BaseModel):
    answer: str
    sources: list[str]
    grounded: bool
