"""Test doubles for EmbeddingModel and LLMBackend."""
from knowledge_assistant.embeddings import EmbeddingModel
from knowledge_assistant.llm import LLMBackend


class FakeEmbeddingModel(EmbeddingModel):
    def __init__(self, vectors: dict[str, list[float]], default: list[float] | None = None) -> None:
        self._vectors = vectors
        self._default = default or [0.0, 0.0]
        self.call_count = 0
        self.call_sizes: list[int] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        self.call_sizes.append(len(texts))
        return [self._vectors.get(t, self._default) for t in texts]

    @property
    def dimension(self) -> int:
        return len(self._default)


class FakeLLMBackend(LLMBackend):
    def __init__(self, response: str = "fake answer") -> None:
        self.response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response
