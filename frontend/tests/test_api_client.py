"""ApiClient behaviour against a fake HTTP transport (NFR3)."""
import httpx
import pytest

from portfolio_frontend.api_client import (
    ApiClient,
    ApiError,
    ApiTimeout,
    ApiUnauthorized,
    ApiUnreachable,
)


def make_client(handler) -> ApiClient:
    return ApiClient("http://api.test", "secret", transport=httpx.MockTransport(handler))


def test_sends_the_api_key_header_and_parses_the_summary() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["key"] = request.headers["X-API-Key"]
        seen["path"] = request.url.path
        return httpx.Response(
            200,
            json={
                "by_type": [{"document_type": "rfp", "generated": 3, "ingested": 2}],
                "total_generated": 3,
                "total_ingested": 2,
                "indexed_chunks": 1,
            },
        )

    summary = make_client(handler).corpus_summary()

    assert seen == {"key": "secret", "path": "/corpus/summary"}
    assert summary.by_type[0].document_type == "rfp"
    assert summary.indexed_chunks == 1


def test_ask_parses_source_details_and_builds_readable_labels() -> None:
    payload = {
        "answer": "USD 100",
        "sources": ["abcdef123456"],
        "grounded": True,
        "source_details": [
            {"checksum": "abcdef123456", "document_type": "rfp", "file_name": "rfp_0001.pdf"},
            {"checksum": "zzzzzzzz9999", "document_type": None, "file_name": None},
        ],
    }
    client = make_client(lambda request: httpx.Response(200, json=payload))

    result = client.ask("budget?")

    assert result.grounded is True
    assert result.source_details[0].label == "rfp - rfp_0001.pdf"
    assert result.source_details[1].label == "document zzzzzzzz"


def test_ask_still_works_when_the_api_omits_source_details() -> None:
    payload = {"answer": "x", "sources": ["a"], "grounded": True}
    client = make_client(lambda request: httpx.Response(200, json=payload))

    assert client.ask("q").source_details == []


def test_401_becomes_unauthorized() -> None:
    client = make_client(lambda request: httpx.Response(401, json={"detail": "Invalid API key"}))

    with pytest.raises(ApiUnauthorized):
        client.corpus_summary()


def test_server_error_becomes_api_error() -> None:
    client = make_client(lambda request: httpx.Response(500, text="boom"))

    with pytest.raises(ApiError, match="500"):
        client.index()


def test_connection_failure_becomes_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(ApiUnreachable):
        make_client(handler).corpus_summary()


def test_timeout_becomes_api_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    with pytest.raises(ApiTimeout):
        make_client(handler).ask("q")


def test_malformed_payload_becomes_api_error() -> None:
    client = make_client(lambda request: httpx.Response(200, json={"unexpected": True}))

    with pytest.raises(ApiError, match="unexpected"):
        client.classify("text")


def test_is_healthy_is_false_when_unreachable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    assert make_client(handler).is_healthy() is False


def test_long_operations_use_the_long_timeout() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["timeout"] = request.extensions["timeout"]["read"]
        return httpx.Response(200, json={"processed": 1, "skipped": 0, "failed": 0})

    client = ApiClient(
        "http://api.test", "k", short_timeout=5, long_timeout=123,
        transport=httpx.MockTransport(handler),
    )
    client.ingest(parallel=True)

    assert seen["timeout"] == 123
