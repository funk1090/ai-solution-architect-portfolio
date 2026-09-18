from fakes import FakeEmbeddingModel, FakeLLMBackend

from knowledge_assistant.models import DocumentChunk
from knowledge_assistant.pipeline_query import ask_question
from knowledge_assistant.vector_store import InMemoryVectorStoreRepository


def test_returns_fallback_when_nothing_is_relevant() -> None:
    repo = InMemoryVectorStoreRepository()
    repo.upsert_chunks(
        [DocumentChunk(source_checksum="doc1", chunk_index=0, text="irrelevant", embedding=[0.0, 1.0])]
    )
    embedding_model = FakeEmbeddingModel(vectors={"my question": [1.0, 0.0]})
    llm = FakeLLMBackend()

    result = ask_question(
        "my question", embedding_model, repo, llm, top_k=1, similarity_threshold=0.9
    )

    assert result.grounded is False
    assert result.sources == []
    assert llm.last_prompt is None  # the LLM must never be called (NFR5)


def test_generates_grounded_answer_with_citations() -> None:
    repo = InMemoryVectorStoreRepository()
    repo.upsert_chunks(
        [DocumentChunk(source_checksum="doc1", chunk_index=0, text="relevant content", embedding=[1.0, 0.0])]
    )
    embedding_model = FakeEmbeddingModel(vectors={"my question": [1.0, 0.0]})
    llm = FakeLLMBackend(response="the answer")

    result = ask_question(
        "my question", embedding_model, repo, llm, top_k=1, similarity_threshold=0.5
    )

    assert result.grounded is True
    assert result.answer == "the answer"
    assert result.sources == ["doc1"]
    assert llm.last_prompt is not None
    assert "relevant content" in llm.last_prompt
