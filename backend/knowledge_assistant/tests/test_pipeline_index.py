from fakes import FakeEmbeddingModel

from knowledge_assistant.content_reader import InMemoryIngestedContentReader
from knowledge_assistant.models import IndexableDocument
from knowledge_assistant.pipeline_index import run_indexing
from knowledge_assistant.vector_store import InMemoryVectorStoreRepository


def test_reindexing_does_not_duplicate_chunks() -> None:
    document = IndexableDocument(
        source_checksum="doc1",
        text="one two three four five six seven eight nine ten",
    )
    reader = InMemoryIngestedContentReader([document])
    repo = InMemoryVectorStoreRepository()
    embedding_model = FakeEmbeddingModel(vectors={}, default=[1.0, 0.0])

    first = run_indexing(reader, embedding_model, repo, chunk_size=5, chunk_overlap=1)
    second = run_indexing(reader, embedding_model, repo, chunk_size=5, chunk_overlap=1)

    assert first.chunks_created > 0
    assert second.chunks_created == 0
    assert second.chunks_skipped == first.chunks_created
