"""The only place in the frontend that talks HTTP (NFR2/NFR3).

Pages call typed methods and receive typed models; they never build
URLs, headers or parse JSON. Failures are mapped to a small set of
exceptions so pages can show friendly messages (NFR4).
"""
from __future__ import annotations

import httpx
from pydantic import BaseModel, ValidationError


class ApiError(Exception):
    """The API answered, but not with what we can use."""


class ApiUnreachable(ApiError):
    """Could not connect to the API at all."""


class ApiTimeout(ApiError):
    """The API did not answer within the configured timeout."""


class ApiUnauthorized(ApiError):
    """The API rejected our key (HTTP 401)."""


class DocumentTypeSummary(BaseModel):
    document_type: str
    generated: int
    ingested: int


class CorpusSummary(BaseModel):
    by_type: list[DocumentTypeSummary]
    total_generated: int
    total_ingested: int
    indexed_chunks: int


class GenerateResult(BaseModel):
    generated: int
    output_dir: str


class IngestResult(BaseModel):
    processed: int
    skipped: int
    failed: int


class IndexResult(BaseModel):
    documents_processed: int
    chunks_created: int
    chunks_skipped: int


class SourceDetail(BaseModel):
    checksum: str
    document_type: str | None = None
    file_name: str | None = None

    @property
    def label(self) -> str:
        if self.document_type and self.file_name:
            return f"{self.document_type} - {self.file_name}"
        return f"document {self.checksum[:8]}"


class AskResult(BaseModel):
    answer: str
    sources: list[str]
    grounded: bool
    source_details: list[SourceDetail] = []


class ClassifyResult(BaseModel):
    category: str


class CompareResult(BaseModel):
    best_model: str
    accuracies: dict[str, float]


class RfpInfo(BaseModel):
    source_checksum: str
    file_name: str
    issuing_organization: str


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


class ComplianceResult(BaseModel):
    rfp: RfpInfo
    counts: dict[str, int]
    assessments: list[AssessmentItem]


class ApiClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        short_timeout: float = 15.0,
        long_timeout: float = 600.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._short = short_timeout
        self._long = long_timeout
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"X-API-Key": api_key},
            transport=transport,
        )

    # -- internals ---------------------------------------------------
    def _request(
        self, method: str, path: str, model: type[BaseModel], long: bool = False, **kwargs
    ):
        timeout = self._long if long else self._short
        try:
            response = self._client.request(method, path, timeout=timeout, **kwargs)
        except httpx.ConnectError as exc:
            raise ApiUnreachable(
                f"Cannot reach the API at {self._client.base_url}. Is it running?"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ApiTimeout(
                f"The API did not answer within {timeout:.0f}s."
            ) from exc

        if response.status_code == 401:
            raise ApiUnauthorized("The API rejected the API key (401). Check API_KEY.")
        if response.status_code >= 400:
            raise ApiError(f"API error {response.status_code}: {response.text[:300]}")
        try:
            return model.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise ApiError("The API returned an unexpected response format.") from exc

    # -- endpoints ---------------------------------------------------
    def is_healthy(self) -> bool:
        try:
            response = self._client.get("/health", timeout=self._short)
        except httpx.HTTPError:
            return False
        return response.status_code == 200

    def corpus_summary(self) -> CorpusSummary:
        return self._request("GET", "/corpus/summary", CorpusSummary)

    def generate(self, document_type: str, count: int) -> GenerateResult:
        return self._request(
            "POST",
            "/documents/generate",
            GenerateResult,
            long=True,
            json={"document_type": document_type, "count": count},
        )

    def ingest(self, parallel: bool, workers: int | None = None) -> IngestResult:
        return self._request(
            "POST",
            "/ingestion/run",
            IngestResult,
            long=True,
            json={"parallel": parallel, "workers": workers},
        )

    def index(self) -> IndexResult:
        return self._request("POST", "/assistant/index", IndexResult, long=True)

    def ask(self, question: str) -> AskResult:
        return self._request(
            "POST", "/assistant/ask", AskResult, long=True, json={"question": question}
        )

    def classify(self, text: str) -> ClassifyResult:
        return self._request("POST", "/classifier/classify", ClassifyResult, json={"text": text})

    def list_rfps(self) -> list[RfpInfo]:
        timeout = self._short
        try:
            response = self._client.get("/compliance/rfps", timeout=timeout)
        except httpx.ConnectError as exc:
            raise ApiUnreachable(
                f"Cannot reach the API at {self._client.base_url}. Is it running?"
            ) from exc
        except httpx.TimeoutException as exc:
            raise ApiTimeout(f"The API did not answer within {timeout:.0f}s.") from exc
        if response.status_code == 401:
            raise ApiUnauthorized("The API rejected the API key (401). Check API_KEY.")
        if response.status_code >= 400:
            raise ApiError(f"API error {response.status_code}: {response.text[:300]}")
        try:
            return [RfpInfo.model_validate(item) for item in response.json()]
        except (ValueError, ValidationError, TypeError) as exc:
            raise ApiError("The API returned an unexpected response format.") from exc

    def check_compliance(self, rfp_checksum: str, use_judge: bool = True) -> ComplianceResult:
        return self._request(
            "POST",
            "/compliance/check",
            ComplianceResult,
            long=True,
            json={"rfp_checksum": rfp_checksum, "use_judge": use_judge},
        )

    def compare(self) -> CompareResult:
        return self._request("POST", "/classifier/compare", CompareResult, long=True)
