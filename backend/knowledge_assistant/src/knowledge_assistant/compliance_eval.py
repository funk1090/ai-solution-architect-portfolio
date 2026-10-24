"""Evaluation of the compliance engine against the synthetic answer key
(Feature 0009, ADR-0008).

Ground truth comes from shared_core.capabilities: a requirement is
supported exactly when the phrase it asks for is in the supported set.
Scores are on SYNTHETIC data with controlled vocabulary overlap, so
absolute numbers are optimistic compared with real documents. They are
useful to compare modes and thresholds, not as a claim about real RFPs.
"""
from __future__ import annotations

from dataclasses import dataclass

from shared_core.capabilities import is_supported

from knowledge_assistant.compliance import (
    Verdict,
    assess_requirement,
    parse_requirements,
    retrieve_evidence,
)
from knowledge_assistant.embeddings import EmbeddingModel
from knowledge_assistant.llm import LLMBackend
from knowledge_assistant.rfp_source import RfpRecord
from knowledge_assistant.vector_store import VectorStoreRepository


@dataclass(frozen=True)
class Metrics:
    total: int
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def accuracy(self) -> float:
        return (self.tp + self.tn) / self.total if self.total else 0.0

    @property
    def precision(self) -> float:
        denominator = self.tp + self.fp
        return self.tp / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        denominator = self.tp + self.fn
        return self.tp / denominator if denominator else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def score(predicted: list[bool], truth: list[bool]) -> Metrics:
    if len(predicted) != len(truth):
        raise ValueError("predicted and truth must have the same length")
    pairs = list(zip(predicted, truth))
    return Metrics(
        total=len(pairs),
        tp=sum(1 for p, t in pairs if p and t),
        fp=sum(1 for p, t in pairs if p and not t),
        fn=sum(1 for p, t in pairs if not p and t),
        tn=sum(1 for p, t in pairs if not p and not t),
    )


def baseline_always_supported(truth: list[bool]) -> Metrics:
    """The 'do nothing smart' baseline: declare every requirement supported."""
    return score([True] * len(truth), truth)


def labeled_requirements(rfps: list[RfpRecord]) -> list[tuple[str, bool]]:
    """(requirement text, ground truth) for every requirement whose
    ground truth can be determined."""
    labeled = []
    for rfp in rfps:
        for requirement in parse_requirements(rfp.text):
            truth = is_supported(requirement)
            if truth is not None:
                labeled.append((requirement, truth))
    return labeled


def sweep_thresholds(
    labeled: list[tuple[str, bool]],
    embedding_model: EmbeddingModel,
    vector_repo: VectorStoreRepository,
    top_k: int,
    thresholds: list[float],
) -> dict[float, Metrics]:
    """Retrieval-only mode at several thresholds. Retrieval runs ONCE per
    requirement (no LLM), then every threshold is applied to the best
    score, which makes calibration cheap."""
    truth = [t for _, t in labeled]
    best_scores = []
    for requirement, _ in labeled:
        retrieved = retrieve_evidence(requirement, embedding_model, vector_repo, top_k)
        best_scores.append(max((c.score for c in retrieved), default=float("-inf")))
    return {
        threshold: score([s >= threshold for s in best_scores], truth)
        for threshold in thresholds
    }


def evaluate_judge(
    labeled: list[tuple[str, bool]],
    embedding_model: EmbeddingModel,
    vector_repo: VectorStoreRepository,
    llm_backend: LLMBackend,
    top_k: int,
    threshold: float,
) -> tuple[Metrics, dict[str, int]]:
    """Retrieval + LLM judge. SUPPORTED and PARTIAL count as 'evidence
    found'; NOT_EVIDENCED and NEEDS_REVIEW count as 'no evidence'
    (conservative). Returns metrics plus the verdict distribution."""
    predicted: list[bool] = []
    distribution = {v.value: 0 for v in Verdict}
    for number, (requirement, _) in enumerate(labeled, start=1):
        assessment = assess_requirement(
            number, requirement, embedding_model, vector_repo, llm_backend, top_k, threshold
        )
        distribution[assessment.verdict.value] += 1
        predicted.append(assessment.verdict in (Verdict.SUPPORTED, Verdict.PARTIAL))
    return score(predicted, [t for _, t in labeled]), distribution
