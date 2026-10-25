"""Feature 0010 (FR4/FR5): token bucket, tiers and wiring. No database."""
import pathlib
import re

from fastapi.testclient import TestClient

from portfolio_api.main import app
from knowledge_assistant.rfp_source import InMemoryRfpSource

from portfolio_api.rate_limit import TokenBucketLimiter, reset_limiters
from portfolio_api.routers.compliance import get_rfp_source
from portfolio_api.routers.corpus import CorpusCounts, get_counts_reader


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


# -- token bucket -------------------------------------------------------
def test_allows_a_burst_up_to_capacity_then_rejects() -> None:
    limiter = TokenBucketLimiter(per_minute=3, clock=FakeClock())

    assert [limiter.acquire("k")[0] for _ in range(4)] == [True, True, True, False]


def test_retry_after_matches_the_refill_rate() -> None:
    clock = FakeClock()
    limiter = TokenBucketLimiter(per_minute=10, clock=clock)  # 1 token / 6 s
    for _ in range(10):
        limiter.acquire("k")

    allowed, retry_after = limiter.acquire("k")

    assert not allowed
    assert 5.9 < retry_after <= 6.0


def test_tokens_refill_over_time() -> None:
    clock = FakeClock()
    limiter = TokenBucketLimiter(per_minute=10, clock=clock)
    for _ in range(10):
        limiter.acquire("k")
    assert not limiter.acquire("k")[0]

    clock.now += 6.0

    assert limiter.acquire("k")[0]
    assert not limiter.acquire("k")[0]


def test_refill_never_exceeds_capacity() -> None:
    clock = FakeClock()
    limiter = TokenBucketLimiter(per_minute=2, clock=clock)
    limiter.acquire("k")

    clock.now += 3600.0

    assert [limiter.acquire("k")[0] for _ in range(3)] == [True, True, False]


def test_keys_are_isolated() -> None:
    limiter = TokenBucketLimiter(per_minute=1, clock=FakeClock())

    assert limiter.acquire("a")[0]
    assert not limiter.acquire("a")[0]
    assert limiter.acquire("b")[0]


def test_zero_disables_the_limiter() -> None:
    limiter = TokenBucketLimiter(per_minute=0, clock=FakeClock())

    assert all(limiter.acquire("k")[0] for _ in range(1000))
    assert len(limiter) == 0


def test_memory_is_bounded() -> None:
    limiter = TokenBucketLimiter(per_minute=5, clock=FakeClock(), max_keys=10)

    for i in range(100):
        limiter.acquire(f"key-{i}")

    assert len(limiter) == 10


# -- wiring (version-independent: source scan + behaviour) ----------------
_SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "portfolio_api"
_EXPENSIVE_DECORATORS = {
    "assistant.py": {'"/index"', '"/ask"'},
    "compliance.py": {'"/check"'},
    "classifier.py": {'"/compare"'},
    "documents.py": {'"/generate"'},
    "ingestion.py": {'"/run"'},
}


def test_exactly_the_expensive_routes_declare_the_strict_limit() -> None:
    found: dict[str, set[str]] = {}
    for path in (_SRC / "routers").glob("*.py"):
        paths = set(
            re.findall(r'@router\.\w+\((".*?")[^\n]*limit_expensive', path.read_text())
        )
        if paths:
            found[path.name] = paths

    assert found == _EXPENSIVE_DECORATORS


def test_every_included_router_has_the_default_limit() -> None:
    lines = [
        line for line in (_SRC / "main.py").read_text().splitlines()
        if line.startswith("app.include_router(")
    ]

    assert len(lines) == 6
    assert all("limit_default" in line for line in lines)


def test_health_is_never_rate_limited(monkeypatch) -> None:
    monkeypatch.setenv("rate_limit_default_per_minute", "1")
    reset_limiters()
    client = TestClient(app)

    assert [client.get("/health").status_code for _ in range(5)] == [200] * 5


# -- behaviour through the API -------------------------------------------
def _summary(client: TestClient, key: str = "k"):
    return client.get("/corpus/summary", headers={"X-API-Key": key})


def test_returns_429_with_retry_after_when_exceeded(monkeypatch) -> None:
    monkeypatch.setenv("api_key", "k")
    monkeypatch.setenv("rate_limit_default_per_minute", "2")
    reset_limiters()
    app.dependency_overrides[get_counts_reader] = lambda: (lambda: CorpusCounts())
    try:
        client = TestClient(app)
        statuses = [_summary(client).status_code for _ in range(3)]
        rejected = _summary(client)
    finally:
        app.dependency_overrides.clear()

    assert statuses == [200, 200, 429]
    assert rejected.status_code == 429
    assert int(rejected.headers["Retry-After"]) >= 1


def test_rejected_requests_do_not_consume_tokens(monkeypatch) -> None:
    monkeypatch.setenv("api_key", "k")
    monkeypatch.setenv("rate_limit_default_per_minute", "2")
    reset_limiters()
    app.dependency_overrides[get_counts_reader] = lambda: (lambda: CorpusCounts())
    try:
        client = TestClient(app)
        for _ in range(5):
            assert client.get("/corpus/summary").status_code == 422  # no header
            assert _summary(client, key="wrong").status_code == 401
        first, second = _summary(client), _summary(client)
    finally:
        app.dependency_overrides.clear()

    assert (first.status_code, second.status_code) == (200, 200)


def test_zero_disables_rate_limiting_through_the_api(monkeypatch) -> None:
    monkeypatch.setenv("api_key", "k")
    monkeypatch.setenv("rate_limit_default_per_minute", "0")
    reset_limiters()
    app.dependency_overrides[get_counts_reader] = lambda: (lambda: CorpusCounts())
    try:
        client = TestClient(app)
        codes = {_summary(client).status_code for _ in range(30)}
    finally:
        app.dependency_overrides.clear()

    assert codes == {200}


def test_strict_tier_is_separate_from_the_default_tier(monkeypatch) -> None:
    monkeypatch.setenv("api_key", "k")
    monkeypatch.setenv("rate_limit_default_per_minute", "100")
    monkeypatch.setenv("rate_limit_expensive_per_minute", "2")
    reset_limiters()
    app.dependency_overrides[get_rfp_source] = lambda: (lambda: InMemoryRfpSource([]))
    app.dependency_overrides[get_counts_reader] = lambda: (lambda: CorpusCounts())
    headers = {"X-API-Key": "k"}
    try:
        client = TestClient(app)
        checks = [
            client.post("/compliance/check", json={"rfp_checksum": "x"}, headers=headers)
            for _ in range(3)
        ]
        cheap = _summary(client)
    finally:
        app.dependency_overrides.clear()

    assert [c.status_code for c in checks] == [404, 404, 429]  # 404 = handler reached
    assert cheap.status_code == 200  # default tier still has tokens
