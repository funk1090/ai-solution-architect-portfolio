"""Compliance endpoints with fakes: no database, model or LLM."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

from knowledge_assistant.compliance import (
    ComplianceReport,
    Evidence,
    RequirementAssessment,
    Verdict,
)
from knowledge_assistant.rfp_source import InMemoryRfpSource, RfpRecord

from portfolio_api.main import app
from portfolio_api.routers.compliance import build_response, get_rfp_source

RECORD = RfpRecord(
    source_checksum="rfp-1", file_name="rfp_0001.pdf", issuing_organization="Acme", text="x"
)


def _report() -> ComplianceReport:
    return ComplianceReport(
        assessments=[
            RequirementAssessment(
                number=1,
                requirement="The solution shall provide audit trails.",
                verdict=Verdict.SUPPORTED,
                rationale="Found.",
                evidence=[Evidence(source_checksum="man-1", chunk_index=0, text="audit trails", score=0.8)],
            ),
            RequirementAssessment(
                number=2, requirement="Other", verdict=Verdict.NOT_EVIDENCED, rationale="None.", evidence=[]
            ),
        ]
    )


def test_build_response_resolves_manual_file_names_in_one_lookup() -> None:
    calls = []

    def lookup(checksums):
        calls.append(checksums)
        return {"man-1": ("technical_manual", "/data/technical_manual/technical_manual_0007.pdf")}

    response = build_response(RECORD, _report(), lookup)

    assert calls == [["man-1"]]
    assert response.assessments[0].evidence[0].file_name == "technical_manual_0007.pdf"
    assert response.counts["SUPPORTED"] == 1 and response.counts["NOT_EVIDENCED"] == 1


def test_build_response_skips_the_lookup_when_there_is_no_evidence() -> None:
    report = ComplianceReport(assessments=[_report().assessments[1]])

    def lookup(_):
        raise AssertionError("lookup must not be called")

    assert build_response(RECORD, report, lookup).assessments[0].evidence == []


def test_list_rfps_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("api_key", "k")
    app.dependency_overrides[get_rfp_source] = lambda: (lambda: InMemoryRfpSource([RECORD]))
    try:
        response = TestClient(app).get("/compliance/rfps", headers={"X-API-Key": "k"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {"source_checksum": "rfp-1", "file_name": "rfp_0001.pdf", "issuing_organization": "Acme"}
    ]


def test_check_returns_404_for_an_unknown_rfp(monkeypatch) -> None:
    monkeypatch.setenv("api_key", "k")
    app.dependency_overrides[get_rfp_source] = lambda: (lambda: InMemoryRfpSource([RECORD]))
    try:
        response = TestClient(app).post(
            "/compliance/check", json={"rfp_checksum": "nope"}, headers={"X-API-Key": "k"}
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_unauthenticated_calls_never_touch_the_source() -> None:
    def must_not_run():
        raise AssertionError("source created without authentication")

    app.dependency_overrides[get_rfp_source] = lambda: must_not_run
    try:
        client = TestClient(app)
        listing = client.get("/compliance/rfps")
        check = client.post("/compliance/check", json={"rfp_checksum": "x"})
    finally:
        app.dependency_overrides.clear()

    assert listing.status_code == 422 and check.status_code == 422
