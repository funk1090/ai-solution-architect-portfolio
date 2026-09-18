"""Vector store persistence (FR3, FR7).

document_chunks stays LOCAL to this module, not in shared_core -- per
ADR-0006's own principle, a table is only extracted into the shared
package once a second owner or reader genuinely needs it. No other
module touches this table.

Idempotency (FR7) is enforced at the database level via a unique
constraint on (source_checksum, chunk_index), the same pattern used for
ingested_content (ADR-0005's lesson: never trust an application-level
check alone).
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Integer, String, UniqueConstraint, create_engine, select, text
from sqlalchemy.orm import Session, declarative_base

from knowledge_assistant.models import DocumentChunk, RetrievedChunk

Base = declarative_base()


class _DocumentChunkTable(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint("source_checksum", "chunk_index", name="uq_document_chunk"),
    )

    id = Column(String(36), primary_key=True)
    source_checksum = Column(String(64), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    embedding = Column(Vector(384), nullable=False)  # 384 = all-MiniLM-L6-v2's dimension


class VectorStoreRepository(ABC):
    @abstractmethod
    def upsert_chunks(self, chunks: list[DocumentChunk]) -> None: ...

    @abstractmethod
    def exists(self, source_checksum: str, chunk_index: int) -> bool: ...

    @abstractmethod
    def similarity_search(
        self, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]: ...


class InMemoryVectorStoreRepository(VectorStoreRepository):
    """Test double — never used in production."""

    def __init__(self) -> None:
        self._chunks: list[DocumentChunk] = []

    def upsert_chunks(self, chunks: list[DocumentChunk]) -> None:
        for chunk in chunks:
            if not self.exists(chunk.source_checksum, chunk.chunk_index):
                self._chunks.append(chunk)

    def exists(self, source_checksum: str, chunk_index: int) -> bool:
        return any(
            c.source_checksum == source_checksum and c.chunk_index == chunk_index
            for c in self._chunks
        )

    def similarity_search(
        self, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(y * y for y in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot / (norm_a * norm_b)

        scored = [
            RetrievedChunk(
                source_checksum=c.source_checksum,
                chunk_index=c.chunk_index,
                text=c.text,
                score=cosine(query_embedding, c.embedding or []),
            )
            for c in self._chunks
        ]
        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]


class PgVectorRepository(VectorStoreRepository):
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)

    def create_tables(self) -> None:
        """Idempotent — enables the pgvector extension and creates the
        table if either is missing, safe to call on every run."""
        with self._engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(self._engine)

    def upsert_chunks(self, chunks: list[DocumentChunk]) -> None:
        with Session(self._engine) as session:
            for chunk in chunks:
                stmt = select(_DocumentChunkTable).where(
                    _DocumentChunkTable.source_checksum == chunk.source_checksum,
                    _DocumentChunkTable.chunk_index == chunk.chunk_index,
                )
                if session.execute(stmt).first() is not None:
                    continue
                row = _DocumentChunkTable(
                    id=str(chunk.id),
                    source_checksum=chunk.source_checksum,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    embedding=chunk.embedding,
                )
                session.add(row)
            session.commit()

    def exists(self, source_checksum: str, chunk_index: int) -> bool:
        with Session(self._engine) as session:
            stmt = select(_DocumentChunkTable).where(
                _DocumentChunkTable.source_checksum == source_checksum,
                _DocumentChunkTable.chunk_index == chunk_index,
            )
            return session.execute(stmt).first() is not None

    def similarity_search(
        self, query_embedding: list[float], top_k: int
    ) -> list[RetrievedChunk]:
        with Session(self._engine) as session:
            distance = _DocumentChunkTable.embedding.cosine_distance(query_embedding).label(
                "distance"
            )
            stmt = select(_DocumentChunkTable, distance).order_by(distance).limit(top_k)
            rows = session.execute(stmt).all()
            return [
                RetrievedChunk(
                    source_checksum=row[0].source_checksum,
                    chunk_index=row[0].chunk_index,
                    text=row[0].text,
                    score=1 - row[1],
                )
                for row in rows
            ]
