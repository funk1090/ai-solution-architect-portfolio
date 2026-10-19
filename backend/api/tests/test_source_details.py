"""Feature 0008 (FR6/FR7): source details resolution and model caching."""
from portfolio_api.dependencies import get_embedding_model
from portfolio_api.routers.assistant import resolve_source_details


def test_resolves_document_type_and_file_name() -> None:
    lookup = lambda cs: {"abc": ("rfp", "/data/generated/rfp/rfp_0001.pdf")}

    details = resolve_source_details(["abc"], lookup)

    assert details[0].document_type == "rfp"
    assert details[0].file_name == "rfp_0001.pdf"


def test_unknown_checksum_is_kept_with_empty_details() -> None:
    details = resolve_source_details(["zzz"], lambda cs: {})

    assert len(details) == 1
    assert details[0].checksum == "zzz"
    assert details[0].file_name is None


def test_no_sources_does_not_call_the_lookup() -> None:
    def boom(_):
        raise AssertionError("lookup must not be called")

    assert resolve_source_details([], boom) == []


def test_embedding_model_is_created_once_per_name(monkeypatch) -> None:
    import types, sys

    calls = []

    class Factory:
        def create(self, backend, name):
            calls.append(name)
            return object()

    fake = types.ModuleType("knowledge_assistant.embeddings")
    fake.EmbeddingModelFactory = Factory
    monkeypatch.setitem(sys.modules, "knowledge_assistant", types.ModuleType("knowledge_assistant"))
    monkeypatch.setitem(sys.modules, "knowledge_assistant.embeddings", fake)
    get_embedding_model.cache_clear()

    first = get_embedding_model("m")
    second = get_embedding_model("m")

    assert first is second
    assert calls == ["m"]
    get_embedding_model.cache_clear()
