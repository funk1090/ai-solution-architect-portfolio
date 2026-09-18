"""Indexing pipeline: chunk -> embed -> store (FR1/FR2/FR3/FR7)."""
from dataclasses import dataclass

from knowledge_assistant.chunker import chunk_text
from knowledge_assistant.content_reader import IngestedContentReader
from knowledge_assistant.embeddings import EmbeddingModel
from knowledge_assistant.models import DocumentChunk
from knowledge_assistant.vector_store import VectorStoreRepository


@dataclass
class IndexingSummary:
    documents_processed: int
    chunks_created: int
    chunks_skipped: int


def run_indexing(
    content_reader: IngestedContentReader,
    embedding_model: EmbeddingModel,
    vector_repo: VectorStoreRepository,
    chunk_size: int,
    chunk_overlap: int,
) -> IndexingSummary:
    documents = content_reader.get_indexable_documents()
    chunks_created = 0
    chunks_skipped = 0

    for document in documents:
        text_chunks = chunk_text(document.text, chunk_size, chunk_overlap)
        for index, chunk_body in enumerate(text_chunks):
            if vector_repo.exists(document.source_checksum, index):
                chunks_skipped += 1
                continue

            embedding = embedding_model.embed([chunk_body])[0]
            chunk = DocumentChunk(
                source_checksum=document.source_checksum,
                chunk_index=index,
                text=chunk_body,
                embedding=embedding,
            )
            vector_repo.upsert_chunks([chunk])
            chunks_created += 1

    return IndexingSummary(
        documents_processed=len(documents),
        chunks_created=chunks_created,
        chunks_skipped=chunks_skipped,
    )
