"""Process-wide shared resources for the API (Feature 0008, FR7).

The embedding model is expensive to load (weights from disk, GPU
placement). Before this module, /assistant/ask built a new model on
every request. Caching it per process makes that a one-time cost.
"""
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=4)
def get_embedding_model(model_name: str) -> Any:
    """Return the embedding model for `model_name`, creating it once
    per process. Heavy imports stay inside the function so importing
    the API (and running its unit tests) never loads torch."""
    from knowledge_assistant.embeddings import EmbeddingModelFactory

    return EmbeddingModelFactory().create("sentence-transformers", model_name)
