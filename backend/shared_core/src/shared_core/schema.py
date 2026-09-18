"""Shared SQLAlchemy table definitions (ADR-0006).

Single source of truth for the document_metadata and ingested_content
schemas, used by:
  - document_generator: owns and writes document_metadata.
  - ingestion_pipeline: reads document_metadata (read-only), owns and
    writes ingested_content.
  - requirement_classifier: reads ingested_content (read-only).

Uses the function-based declarative_base() rather than the SQLAlchemy
2.0-only DeclarativeBase class -- required for compatibility with the
older SQLAlchemy version pinned by Airflow's constraints file, since
ingestion_pipeline imports this package from within the Airflow
container (see ADR-0003's Feature 0002 implementation notes).

This module intentionally contains ONLY table definitions -- no
business logic, no read/write policy. Each consuming module implements
its own repository around these tables, preserving the read-only vs.
read/write access boundaries that were deliberately designed per
module.
"""
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DocumentMetadataTable(Base):
    __tablename__ = "document_metadata"

    id = Column(String(36), primary_key=True)
    document_type = Column(String(64), nullable=False)
    file_path = Column(String(1024), nullable=False)
    checksum_sha256 = Column(String(64), nullable=False, unique=True)
    generated_at = Column(DateTime(timezone=True), nullable=False)
    related_entity = Column(String(256), nullable=False)
    seed = Column(Integer, nullable=False)


class IngestedContentTable(Base):
    __tablename__ = "ingested_content"

    id = Column(String(36), primary_key=True)
    source_checksum = Column(String(64), nullable=False, unique=True)
    document_type = Column(String(64), nullable=False)
    extracted_text = Column(String, nullable=True)
    structured_data = Column(JSONB, nullable=True)
    status = Column(String(16), nullable=False)
    error_message = Column(String, nullable=True)
    ingested_at = Column(DateTime(timezone=True), nullable=False)
