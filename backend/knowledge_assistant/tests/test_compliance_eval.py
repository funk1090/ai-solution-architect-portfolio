from fakes import FakeEmbeddingModel

from knowledge_assistant.compliance_eval import (
    baseline_always_supported,
    labeled_requirements,
    score,
    sweep_thresholds,
)
from knowledge_assistant.models import DocumentChunk
from knowledge_assistant.rfp_source import RfpRecord
from knowledge_assistant.vector_store import InMemoryVectorStoreRepository

SUPPORTED_REQ = "The solution shall provide complete regulatory audit trails. This requirement is high."
UNSUPPORTED_REQ = "The solution shall provide configurable data residency by region. This requirement is low."


def test_score_computes_confusion_matrix_and_rates() -> None:
    metrics = score([True, True, False, False], [True, False, True, False])

    assert (metrics.tp, metrics.fp, metrics.fn, metrics.tn) == (1, 1, 1, 1)
    assert metrics.accuracy == 0.5
    assert metrics.precision == 0.5 and metrics.recall == 0.5 and metrics.f1 == 0.5


def test_score_handles_empty_denominators() -> None:
    metrics = score([False, False], [False, False])

    assert metrics.precision == 0.0 and metrics.recall == 0.0 and metrics.f1 == 0.0
    assert metrics.accuracy == 1.0


def test_baseline_accuracy_equals_the_supported_share() -> None:
    assert baseline_always_supported([True, False, False, False]).accuracy == 0.25


def test_labeled_requirements_derives_truth_from_the_phrase() -> None:
    rfp = RfpRecord(
        source_checksum="r1", file_name="rfp_0000.pdf", issuing_organization="Acme",
        text=f"Technical Requirements 1. {SUPPORTED_REQ} 2. {UNSUPPORTED_REQ}",
    )

    labeled = labeled_requirements([rfp])

    assert [truth for _, truth in labeled] == [True, False]


def test_sweep_applies_each_threshold_to_the_best_score() -> None:
    repo = InMemoryVectorStoreRepository(document_types={"man1": "technical_manual"})
    repo.upsert_chunks([DocumentChunk(source_checksum="man1", chunk_index=0, text="manual", embedding=[1.0, 0.0])])
    good = "The solution shall provide complete regulatory audit trails"
    bad = "The solution shall provide configurable data residency by region"
    embedding = FakeEmbeddingModel(vectors={good: [1.0, 0.0], bad: [0.6, 0.8]})
    labeled = [(SUPPORTED_REQ, True), (UNSUPPORTED_REQ, False)]

    results = sweep_thresholds(labeled, embedding, repo, top_k=3, thresholds=[0.5, 0.9])

    assert results[0.5].accuracy == 0.5   # both clear 0.5 -> one false positive
    assert results[0.9].accuracy == 1.0   # only the genuine match clears 0.9
