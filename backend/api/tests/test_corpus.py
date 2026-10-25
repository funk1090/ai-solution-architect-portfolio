"""Feature 0008 (FR2/FR6): corpus summary logic and endpoint, no database."""
from fastapi.testclient import TestClient

from portfolio_api.main import app
from portfolio_api.routers.corpus import CorpusCounts, build_summary, get_counts_reader


def test_build_summary_merges_types_and_totals() -> None:
    counts = CorpusCounts(
        generated={"rfp": 10, "technical_manual": 5},
        ingested={"rfp": 8},
        indexed_chunks=20,
    )

    summary = build_summary(counts)

    by_type = {s.document_type: s for s in summary.by_type}
    assert by_type["rfp"].generated == 10 and by_type["rfp"].ingested == 8
    assert by_type["technical_manual"].ingested == 0
    assert summary.total_generated == 15
    assert summary.total_ingested == 8
    assert summary.indexed_chunks == 20


def test_build_summary_of_empty_corpus_is_all_zero() -> None:
    summary = build_summary(CorpusCounts())

    assert summary.by_type == []
    assert summary.total_generated == 0 and summary.indexed_chunks == 0


def test_endpoint_returns_summary_with_valid_key(monkeypatch) -> None:
    monkeypatch.setenv("api_key", "k")
    app.dependency_overrides[get_counts_reader] = lambda: (lambda: CorpusCounts(generated={"rfp": 2}))
    try:
        response = TestClient(app).get("/corpus/summary", headers={"X-API-Key": "k"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total_generated"] == 2


def test_unauthenticated_request_never_reads_the_database() -> None:
    def must_not_run() -> CorpusCounts:
        raise AssertionError("database read attempted without authentication")

    app.dependency_overrides[get_counts_reader] = lambda: must_not_run
    try:
        response = TestClient(app).get("/corpus/summary")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_read_counts_on_an_empty_database_is_all_zero(tmp_path) -> None:
    from portfolio_api.routers.corpus import read_counts

    counts = read_counts(f"sqlite:///{tmp_path / 'empty.db'}")

    assert counts.generated == {} and counts.ingested == {} and counts.indexed_chunks == 0


def test_read_counts_with_only_some_tables_created(tmp_path) -> None:
    from sqlalchemy import create_engine, text

    from portfolio_api.routers.corpus import read_counts

    url = f"sqlite:///{tmp_path / 'partial.db'}"
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE document_chunks (id INTEGER)"))
        conn.execute(text("INSERT INTO document_chunks VALUES (1), (2), (3)"))
    engine.dispose()

    counts = read_counts(url)

    assert counts.indexed_chunks == 3
    assert counts.generated == {} and counts.ingested == {}
