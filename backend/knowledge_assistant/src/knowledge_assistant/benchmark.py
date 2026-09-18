"""Benchmark: per-chunk vs batched embedding calls (FR1/FR2/FR3/FR6).

Run manually: `uv run knowledge-assistant benchmark-embeddings`

This measures the ACTUAL difference on this machine's hardware, rather
than assuming batching helps -- NFR4: measured, not assumed.
"""
import time

from knowledge_assistant.chunker import chunk_text
from knowledge_assistant.config import Settings
from knowledge_assistant.embeddings import EmbeddingModelFactory


def _sample_document_text(word_count: int) -> str:
    return " ".join(f"word{i}" for i in range(word_count))


def run_benchmark() -> None:
    settings = Settings()
    embedding_model = EmbeddingModelFactory().create(
        "sentence-transformers", settings.embedding_model_name
    )

    text = _sample_document_text(4000)
    chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    print(f"Sample document split into {len(chunks)} chunks.\n")

    # "Before" (the original bottleneck): one embed() call per chunk.
    start = time.perf_counter()
    for chunk in chunks:
        embedding_model.embed([chunk])
    unbatched_seconds = time.perf_counter() - start

    # "After" (FR3): one embed() call for every chunk in the document.
    start = time.perf_counter()
    embedding_model.embed(chunks)
    batched_seconds = time.perf_counter() - start

    print(f"Unbatched (one call per chunk):  {unbatched_seconds:.3f}s")
    print(f"Batched   (one call for all):    {batched_seconds:.3f}s")
    if batched_seconds > 0:
        print(f"Speedup: {unbatched_seconds / batched_seconds:.1f}x")


if __name__ == "__main__":
    run_benchmark()
