"""Query pipeline: retrieve -> ground -> generate (FR4/FR5/FR6/FR9).

The groundedness check (NFR5) happens BEFORE the LLM is ever called --
if nothing clears the similarity threshold, the fallback response is
produced by our own code, not by hoping the model says "I don't know."
"""
from knowledge_assistant.embeddings import EmbeddingModel
from knowledge_assistant.llm import LLMBackend
from knowledge_assistant.models import AnswerResult
from knowledge_assistant.vector_store import VectorStoreRepository

_NO_CONTEXT_RESPONSE = (
    "I don't have enough grounded information in the indexed documents "
    "to answer this question."
)


def ask_question(
    question: str,
    embedding_model: EmbeddingModel,
    vector_repo: VectorStoreRepository,
    llm_backend: LLMBackend,
    top_k: int,
    similarity_threshold: float,
) -> AnswerResult:
    query_embedding = embedding_model.embed([question])[0]
    results = vector_repo.similarity_search(query_embedding, top_k)
    relevant = [r for r in results if r.score >= similarity_threshold]

    if not relevant:
        return AnswerResult(answer=_NO_CONTEXT_RESPONSE, sources=[], grounded=False)

    context = "\n\n".join(
        f"[Source {i + 1}, document {r.source_checksum[:8]}]: {r.text}"
        for i, r in enumerate(relevant)
    )
    prompt = (
        "Answer the question using ONLY the context below. "
        "If the context does not contain the answer, say so explicitly.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )

    answer_text = llm_backend.generate(prompt)
    sources = sorted({r.source_checksum for r in relevant})
    return AnswerResult(answer=answer_text, sources=sources, grounded=True)
