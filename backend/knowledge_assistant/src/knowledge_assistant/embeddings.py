"""Embedding model abstraction (FR2/NFR6)."""
from abc import ABC, abstractmethod


class EmbeddingModel(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...


class SentenceTransformerEmbeddingModel(EmbeddingModel):
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts)
        return [[float(x) for x in vector] for vector in vectors]

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()


class EmbeddingModelFactory:
    def create(self, backend: str, model_name: str) -> EmbeddingModel:
        if backend == "sentence-transformers":
            return SentenceTransformerEmbeddingModel(model_name)
        raise ValueError(f"No embedding backend registered for: {backend}")
