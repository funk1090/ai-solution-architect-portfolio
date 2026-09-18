"""Indexing pipeline: chunk -> embed -> store (FR1/FR2/FR3/FR7).

Performance note (Feature 0005, FR3): embeddings are computed in ONE
batched call per document, covering every chunk that still needs
indexing -- not one call per chunk. The embedding model runs on GPU,
which is built to process batches efficiently; calling it one item at
a time (the original implementation) wasted that entirely. See
Feature 0005's benchmark for the measured before/after difference.
"""
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

        pending_indices: list[int] = []
        pending_texts: list[str] = []
        for index, chunk_body in enumerate(text_chunks):
            if vector_repo.exists(document.source_checksum, index):
                chunks_skipped += 1
            else:
                pending_indices.append(index)
                pending_texts.append(chunk_body)

        if not pending_texts:
            continue

        embeddings = embedding_model.embed(pending_texts)  # ONE call for the whole document

        new_chunks = [
            DocumentChunk(
                source_checksum=document.source_checksum,
                chunk_index=index,
                text=text,
                embedding=embedding,
            )
            for index, text, embedding in zip(pending_indices, pending_texts, embeddings)
        ]
        vector_repo.upsert_chunks(new_chunks)
        chunks_created += len(new_chunks)

    return IndexingSummary(
        documents_processed=len(documents),
        chunks_created=chunks_created,
        chunks_skipped=chunks_skipped,
    )
