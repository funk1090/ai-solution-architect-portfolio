"""LLM backend abstraction (FR5/NFR6)."""
from abc import ABC, abstractmethod


class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...


class OllamaLLMBackend(LLMBackend):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def generate(self, prompt: str) -> str:
        import requests

        response = requests.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=180,
        )
        response.raise_for_status()
        return response.json()["response"].strip()


class LLMBackendFactory:
    def create(self, backend: str, base_url: str, model: str) -> LLMBackend:
        if backend == "ollama":
            return OllamaLLMBackend(base_url, model)
        raise ValueError(f"No LLM backend registered for: {backend}")
