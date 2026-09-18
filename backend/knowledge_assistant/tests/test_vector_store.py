from knowledge_assistant.models import DocumentChunk
from knowledge_assistant.vector_store import InMemoryVectorStoreRepository


def test_upsert_is_idempotent() -> None:
    repo = InMemoryVectorStoreRepository()
    chunk = DocumentChunk(
        source_checksum="abc", chunk_index=0, text="hello", embedding=[1.0, 0.0]
    )

    repo.upsert_chunks([chunk])
    repo.upsert_chunks([chunk])

    assert len(repo.similarity_search([1.0, 0.0], top_k=10)) == 1


def test_similarity_search_orders_by_cosine_similarity() -> None:
    repo = InMemoryVectorStoreRepository()
    repo.upsert_chunks(
        [
            DocumentChunk(source_checksum="a", chunk_index=0, text="close", embedding=[1.0, 0.0]),
            DocumentChunk(source_checksum="b", chunk_index=0, text="far", embedding=[0.0, 1.0]),
        ]
    )

    results = repo.similarity_search([1.0, 0.0], top_k=2)

    assert results[0].source_checksum == "a"
    assert results[0].score > results[1].score
