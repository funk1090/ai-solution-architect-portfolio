"""Compliance validation endpoints (Feature 0009). Wraps the engine in
knowledge_assistant; evidence is enriched with file names for the UI.

As in /corpus/summary, database access happens inside the endpoint (via
an injected provider), never in a dependency, so unauthenticated calls
cannot reach it.
"""
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from portfolio_api.auth import verify_api_key
from portfolio_api.rate_limit import limit_expensive
from portfolio_api.dependencies import get_embedding_model
from portfolio_api.routers.assistant import lookup_document_metadata

router = APIRouter(
    prefix="/compliance", tags=["compliance"], dependencies=[Depends(verify_api_key)]
)


class RfpInfo(BaseModel):
    source_checksum: str
    file_name: str
    issuing_organization: str


class CheckRequest(BaseModel):
    rfp_checksum: str
    use_judge: bool = True


class EvidenceItem(BaseModel):
    source_checksum: str
    file_name: str | None = None
    text: str
    score: float


class AssessmentItem(BaseModel):
    number: int
    requirement: str
    verdict: str
    rationale: str
    evidence: list[EvidenceItem]


class CheckResponse(BaseModel):
    rfp: RfpInfo
    counts: dict[str, int]
    assessments: list[AssessmentItem]


def build_response(
    record: Any,
    report: Any,
    lookup: Callable[[list[str]], dict[str, tuple[str, str]]],
) -> CheckResponse:
    """Pure: turn an engine report into the API shape, resolving manual
    file names in a single lookup."""
    from pathlib import PurePath

    checksums = sorted({e.source_checksum for a in report.assessments for e in a.evidence})
    found = lookup(checksums) if checksums else {}

    def file_name(checksum: str) -> str | None:
        entry = found.get(checksum)
        return PurePath(entry[1]).name if entry else None

    return CheckResponse(
        rfp=RfpInfo(
            source_checksum=record.source_checksum,
            file_name=record.file_name,
            issuing_organization=record.issuing_organization,
        ),
        counts=report.counts(),
        assessments=[
            AssessmentItem(
                number=a.number,
                requirement=a.requirement,
                verdict=a.verdict.value,
                rationale=a.rationale,
                evidence=[
                    EvidenceItem(
                        source_checksum=e.source_checksum,
                        file_name=file_name(e.source_checksum),
                        text=e.text,
                        score=e.score,
                    )
                    for e in a.evidence
                ],
            )
            for a in report.assessments
        ],
    )


def get_rfp_source() -> Any:
    """Dependency returning a factory (not a connection) so nothing touches
    the database until the endpoint runs."""

    def factory() -> Any:
        from knowledge_assistant.config import Settings
        from knowledge_assistant.rfp_source import PostgresRfpSource

        return PostgresRfpSource(Settings().database_url)

    return factory


@router.get("/rfps", response_model=list[RfpInfo])
def list_rfps(source_factory: Callable[[], Any] = Depends(get_rfp_source)) -> list[RfpInfo]:
    return [
        RfpInfo(
            source_checksum=r.source_checksum,
            file_name=r.file_name,
            issuing_organization=r.issuing_organization,
        )
        for r in source_factory().list_rfps()
    ]


@router.post("/check", response_model=CheckResponse, dependencies=[Depends(limit_expensive)])
def check_compliance(
    request: CheckRequest, source_factory: Callable[[], Any] = Depends(get_rfp_source)
) -> CheckResponse:
    from knowledge_assistant.compliance import check_rfp
    from knowledge_assistant.config import Settings
    from knowledge_assistant.llm import LLMBackendFactory
    from knowledge_assistant.vector_store import PgVectorRepository

    record = source_factory().get_rfp(request.rfp_checksum)
    if record is None:
        raise HTTPException(status_code=404, detail="RFP not found")

    settings = Settings()
    embedding_model = get_embedding_model(settings.embedding_model_name)
    vector_repo = PgVectorRepository(settings.database_url)
    llm_backend = (
        LLMBackendFactory().create(
            "ollama", settings.ollama_base_url, settings.ollama_model, temperature=0.0
        )
        if request.use_judge
        else None
    )
    report = check_rfp(
        record.text,
        embedding_model,
        vector_repo,
        llm_backend,
        settings.compliance_top_k,
        settings.compliance_similarity_threshold,
    )
    return build_response(record, report, lookup_document_metadata)
