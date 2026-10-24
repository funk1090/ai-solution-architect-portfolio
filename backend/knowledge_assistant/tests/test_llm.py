"""Ollama backend request payload (temperature is opt-in)."""
import sys
import types

from knowledge_assistant.llm import LLMBackendFactory, OllamaLLMBackend


def _capture(monkeypatch):
    sent = {}

    class _Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {"response": " ok "}

    def fake_post(url, json, timeout):
        sent["url"] = url
        sent["json"] = json
        return _Response()

    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(post=fake_post))
    return sent


def test_default_payload_has_no_options(monkeypatch):
    sent = _capture(monkeypatch)
    assert OllamaLLMBackend("http://x:1/", "m").generate("hi") == "ok"
    assert sent["url"] == "http://x:1/api/generate"
    assert "options" not in sent["json"]


def test_temperature_sets_options_with_fixed_seed(monkeypatch):
    sent = _capture(monkeypatch)
    backend = LLMBackendFactory().create("ollama", "http://x:1", "m", temperature=0.0)
    backend.generate("hi")
    assert sent["json"]["options"] == {"temperature": 0.0, "seed": 0}
