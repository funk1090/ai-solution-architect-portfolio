"""LLM backend abstraction (FR5/NFR6)."""
from abc import ABC, abstractmethod


class LLMBackend(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...


class OllamaLLMBackend(LLMBackend):
    def __init__(self, base_url: str, model: str, temperature: float | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature

    def generate(self, prompt: str) -> str:
        import requests

        payload: dict = {"model": self._model, "prompt": prompt, "stream": False}
        if self._temperature is not None:
            # Fixed seed + temperature: repeatable output (used by the compliance judge).
            payload["options"] = {"temperature": self._temperature, "seed": 0}
        response = requests.post(
            f"{self._base_url}/api/generate",
            json=payload,
            timeout=180,
        )
        response.raise_for_status()
        return response.json()["response"].strip()


class LLMBackendFactory:
    def create(
        self, backend: str, base_url: str, model: str, temperature: float | None = None
    ) -> LLMBackend:
        if backend == "ollama":
            return OllamaLLMBackend(base_url, model, temperature)
        raise ValueError(f"No LLM backend registered for: {backend}")
