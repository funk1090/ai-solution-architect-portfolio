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


def test_check_compliance_parses_the_report_and_uses_the_long_timeout() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["timeout"] = request.extensions["timeout"]["read"]
        seen["body"] = request.content
        return httpx.Response(
            200,
            json={
                "rfp": {"source_checksum": "r1", "file_name": "rfp_0001.pdf", "issuing_organization": "Acme"},
                "counts": {"SUPPORTED": 1, "PARTIAL": 0, "NOT_EVIDENCED": 0, "NEEDS_REVIEW": 0},
                "assessments": [
                    {
                        "number": 1, "requirement": "req", "verdict": "SUPPORTED", "rationale": "ok",
                        "evidence": [{"source_checksum": "m1", "file_name": "technical_manual_0001.pdf", "text": "t", "score": 0.8}],
                    }
                ],
            },
        )

    client = ApiClient("http://api.test", "k", long_timeout=99, transport=httpx.MockTransport(handler))
    result = client.check_compliance("r1", use_judge=False)

    assert seen["timeout"] == 99
    assert b'"use_judge":false' in seen["body"].replace(b" ", b"")
    assert result.assessments[0].evidence[0].file_name == "technical_manual_0001.pdf"


def test_list_rfps_parses_a_list_and_maps_errors() -> None:
    ok = make_client(lambda r: httpx.Response(200, json=[{"source_checksum": "a", "file_name": "rfp_0000.pdf", "issuing_organization": "X"}]))
    assert ok.list_rfps()[0].file_name == "rfp_0000.pdf"

    with pytest.raises(ApiUnauthorized):
        make_client(lambda r: httpx.Response(401)).list_rfps()


def test_429_becomes_rate_limited_with_retry_after() -> None:
    from portfolio_frontend.api_client import ApiRateLimited

    client = make_client(lambda r: httpx.Response(429, headers={"Retry-After": "7"}))

    with pytest.raises(ApiRateLimited) as exc_info:
        client.ask("anything")

    assert exc_info.value.retry_after == 7
    assert "7 seconds" in str(exc_info.value)


def test_429_without_retry_after_still_gives_a_friendly_message() -> None:
    from portfolio_frontend.api_client import ApiRateLimited

    with pytest.raises(ApiRateLimited) as exc_info:
        make_client(lambda r: httpx.Response(429)).list_rfps()

    assert exc_info.value.retry_after is None
    assert "Try again shortly" in str(exc_info.value)
