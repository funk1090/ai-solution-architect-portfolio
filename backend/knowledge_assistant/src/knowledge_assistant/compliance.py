"""Compliance validation: RFP requirements vs. technical manuals
(Feature 0009).

Evidence for a human decision, not a certification. Pipeline per
requirement:

  retrieve passages from technical manuals only
      -> none clears the threshold: NOT_EVIDENCED, and the LLM is NEVER
         called (same groundedness-first principle as Feature 0004)
      -> otherwise an LLM judge answers in strict JSON; anything
         unparseable becomes NEEDS_REVIEW, never a guessed verdict.

Everything here depends on abstractions (EmbeddingModel,
VectorStoreRepository, LLMBackend), so it is unit-testable with fakes.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from enum import Enum

from pydantic import BaseModel

from knowledge_assistant.embeddings import EmbeddingModel
from knowledge_assistant.llm import LLMBackend
from knowledge_assistant.models import RetrievedChunk
from knowledge_assistant.vector_store import VectorStoreRepository

MANUAL_DOCUMENT_TYPE = "technical_manual"
_REQUIREMENTS_HEADING = "Technical Requirements"
_PRIORITY_SENTENCE = ". This requirement"


class Verdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    NOT_EVIDENCED = "NOT_EVIDENCED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class Evidence(BaseModel):
    source_checksum: str
    chunk_index: int
    text: str
    score: float


class RequirementAssessment(BaseModel):
    number: int
    requirement: str
    verdict: Verdict
    rationale: str
    evidence: list[Evidence]


class ComplianceReport(BaseModel):
    assessments: list[RequirementAssessment]

    def counts(self) -> dict[str, int]:
        tally = Counter(a.verdict.value for a in self.assessments)
        return {verdict.value: tally.get(verdict.value, 0) for verdict in Verdict}


# ---------------------------------------------------------------- parsing


def parse_requirements(text: str) -> list[str]:
    """Extract the numbered items under 'Technical Requirements' from an
    ingested RFP. Works on both multi-line and whitespace-collapsed text.
    Numbering must be sequential (1., 2., 3. ...), which makes stray
    numbers inside requirement text harmless."""
    heading = text.find(_REQUIREMENTS_HEADING)
    if heading == -1:
        return []
    body = text[heading + len(_REQUIREMENTS_HEADING):]

    starts: list[tuple[int, int]] = []  # (match_start, content_start)
    cursor = 0
    number = 1
    while True:
        match = re.compile(rf"(?:(?<=\s)|^){number}\.\s+").search(body, cursor)
        if match is None:
            break
        starts.append((match.start(), match.end()))
        cursor = match.end()
        number += 1

    requirements = []
    for i, (_, content_start) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(body)
        item = " ".join(body[content_start:end].split())
        if item:
            requirements.append(item)
    return requirements


def core_statement(requirement: str) -> str:
    """The capability being asked for, without the trailing priority
    sentence ('This requirement is ...'), which only dilutes retrieval."""
    return requirement.split(_PRIORITY_SENTENCE, 1)[0].strip().rstrip(".").strip()


def parse_judgement(raw: str) -> tuple[Verdict, str]:
    """Parse the judge's reply. Defensive by design: a small local model
    may wrap JSON in prose or return garbage."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match is None:
        return Verdict.NEEDS_REVIEW, "The judge did not return JSON."
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return Verdict.NEEDS_REVIEW, "The judge returned malformed JSON."
    if not isinstance(data, dict):
        return Verdict.NEEDS_REVIEW, "The judge returned an unexpected structure."

    label = str(data.get("verdict", "")).strip().lower().replace(" ", "_")
    rationale = str(data.get("rationale", "")).strip() or "No rationale given."
    mapping = {
        "supported": Verdict.SUPPORTED,
        "partial": Verdict.PARTIAL,
        "partially_supported": Verdict.PARTIAL,
        "not_supported": Verdict.NOT_EVIDENCED,
        "unsupported": Verdict.NOT_EVIDENCED,
    }
    verdict = mapping.get(label)
    if verdict is None:
        return Verdict.NEEDS_REVIEW, f"The judge returned an unknown verdict: {label!r}."
    return verdict, rationale


def build_judge_prompt(requirement: str, passages: list[RetrievedChunk]) -> str:
    context = "\n\n".join(f"[Passage {i + 1}]: {p.text}" for i, p in enumerate(passages))
    return (
        "You check whether product documentation supports a customer requirement. "
        "Use ONLY the passages below. Answer with a single JSON object and nothing else:\n"
        '{"verdict": "supported" | "partial" | "not_supported", "rationale": "<one sentence>"}\n\n'
        f"Requirement: {requirement}\n\nPassages:\n{context}\n\nJSON:"
    )


# ----------------------------------------------------------------- engine


def retrieve_evidence(
    requirement: str,
    embedding_model: EmbeddingModel,
    vector_repo: VectorStoreRepository,
    top_k: int,
) -> list[RetrievedChunk]:
    query = embedding_model.embed([core_statement(requirement)])[0]
    return vector_repo.similarity_search(query, top_k, document_type=MANUAL_DOCUMENT_TYPE)


def assess_requirement(
    number: int,
    requirement: str,
    embedding_model: EmbeddingModel,
    vector_repo: VectorStoreRepository,
    llm_backend: LLMBackend | None,
    top_k: int,
    similarity_threshold: float,
) -> RequirementAssessment:
    """llm_backend=None selects retrieval-only mode (evidence above the
    threshold is SUPPORTED); otherwise the LLM judge decides."""
    retrieved = retrieve_evidence(requirement, embedding_model, vector_repo, top_k)
    relevant = [c for c in retrieved if c.score >= similarity_threshold]
    evidence = [
        Evidence(
            source_checksum=c.source_checksum,
            chunk_index=c.chunk_index,
            text=c.text,
            score=round(c.score, 4),
        )
        for c in relevant
    ]

    if not relevant:
        best = f"{retrieved[0].score:.2f}" if retrieved else "n/a"
        return RequirementAssessment(
            number=number,
            requirement=requirement,
            verdict=Verdict.NOT_EVIDENCED,
            rationale=(
                f"No manual passage reached the similarity threshold "
                f"({similarity_threshold}); best score {best}."
            ),
            evidence=[],
        )

    if llm_backend is None:
        return RequirementAssessment(
            number=number,
            requirement=requirement,
            verdict=Verdict.SUPPORTED,
            rationale=f"Retrieval-only: best passage score {relevant[0].score:.2f}.",
            evidence=evidence,
        )

    verdict, rationale = parse_judgement(
        llm_backend.generate(build_judge_prompt(requirement, relevant))
    )
    return RequirementAssessment(
        number=number,
        requirement=requirement,
        verdict=verdict,
        rationale=rationale,
        evidence=evidence,
    )


def check_rfp(
    rfp_text: str,
    embedding_model: EmbeddingModel,
    vector_repo: VectorStoreRepository,
    llm_backend: LLMBackend | None,
    top_k: int,
    similarity_threshold: float,
) -> ComplianceReport:
    requirements = parse_requirements(rfp_text)
    return ComplianceReport(
        assessments=[
            assess_requirement(
                number,
                requirement,
                embedding_model,
                vector_repo,
                llm_backend,
                top_k,
                similarity_threshold,
            )
            for number, requirement in enumerate(requirements, start=1)
        ]
    )
