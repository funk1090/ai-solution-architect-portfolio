"""Compliance engine tests with fakes: no model, database or LLM."""
from fakes import FakeEmbeddingModel, FakeLLMBackend

from knowledge_assistant.compliance import (
    Verdict,
    assess_requirement,
    check_rfp,
    core_statement,
    parse_judgement,
    parse_requirements,
)
from knowledge_assistant.models import DocumentChunk
from knowledge_assistant.vector_store import InMemoryVectorStoreRepository

RFP_TEXT = (
    "Request for Proposal (RFP)\nIssuing Organization: Acme\nBudget Range: USD 100,000 - 200,000\n"
    "Technical Requirements\n"
    "1. The solution shall provide complete regulatory audit trails. This requirement is high.\n"
    "2. The solution shall provide 99.99% uptime guarantees. This requirement is low.\n"
    "3. The solution shall provide configurable data residency by region. This requirement is medium."
)


def _repo_with_manual_chunk(vector: list[float]) -> InMemoryVectorStoreRepository:
    repo = InMemoryVectorStoreRepository(document_types={"man1": "technical_manual", "rfp1": "rfp"})
    repo.upsert_chunks(
        [
            DocumentChunk(source_checksum="man1", chunk_index=0, text="Built-in support for audit trails.", embedding=vector),
            DocumentChunk(source_checksum="rfp1", chunk_index=0, text="RFP text", embedding=[1.0, 0.0]),
        ]
    )
    return repo


# ---------------------------------------------------------------- parsing


def test_parse_requirements_from_multiline_text() -> None:
    requirements = parse_requirements(RFP_TEXT)

    assert len(requirements) == 3
    assert requirements[0].startswith("The solution shall provide complete regulatory audit trails")
    assert "99.99% uptime guarantees" in requirements[1]


def test_parse_requirements_from_whitespace_collapsed_text() -> None:
    collapsed = " ".join(RFP_TEXT.split())

    assert parse_requirements(collapsed) == parse_requirements(RFP_TEXT)


def test_parse_requirements_without_the_section_returns_nothing() -> None:
    assert parse_requirements("Just some text without the heading") == []


def test_parse_requirements_ignores_numbers_inside_requirement_text() -> None:
    text = "Technical Requirements 1. Provide 99.99% uptime in 2 regions. 2. Provide audit trails."

    assert parse_requirements(text) == ["Provide 99.99% uptime in 2 regions.", "Provide audit trails."]


def test_core_statement_drops_the_priority_sentence() -> None:
    assert core_statement("The solution shall provide X. This requirement is high.") == "The solution shall provide X"


# ---------------------------------------------------------------- judgement


def test_parse_judgement_accepts_plain_and_wrapped_json() -> None:
    assert parse_judgement('{"verdict": "supported", "rationale": "Found."}') == (Verdict.SUPPORTED, "Found.")
    wrapped = 'Sure! Here you go:\n{"verdict": "Partial", "rationale": "Only half."}\nHope it helps.'
    assert parse_judgement(wrapped) == (Verdict.PARTIAL, "Only half.")


def test_parse_judgement_maps_not_supported_to_not_evidenced() -> None:
    verdict, _ = parse_judgement('{"verdict": "not_supported", "rationale": "Nothing."}')

    assert verdict is Verdict.NOT_EVIDENCED


def test_parse_judgement_never_guesses_on_bad_output() -> None:
    for raw in ("no json at all", "{broken json", '{"verdict": "maybe"}', "[1, 2]"):
        verdict, _ = parse_judgement(raw)
        assert verdict is Verdict.NEEDS_REVIEW


# ------------------------------------------------------------------ engine


def test_no_evidence_means_not_evidenced_and_the_llm_is_never_called() -> None:
    repo = _repo_with_manual_chunk([0.0, 1.0])
    embedding = FakeEmbeddingModel(vectors={"The solution shall provide X": [1.0, 0.0]})
    llm = FakeLLMBackend()

    result = assess_requirement(1, "The solution shall provide X. This requirement is high.", embedding, repo, llm, 3, 0.5)

    assert result.verdict is Verdict.NOT_EVIDENCED
    assert result.evidence == []
    assert llm.last_prompt is None


def test_retrieval_only_mode_marks_evidence_as_supported() -> None:
    repo = _repo_with_manual_chunk([1.0, 0.0])
    embedding = FakeEmbeddingModel(vectors={"The solution shall provide X": [1.0, 0.0]})

    result = assess_requirement(1, "The solution shall provide X.", embedding, repo, None, 3, 0.5)

    assert result.verdict is Verdict.SUPPORTED
    assert result.evidence[0].source_checksum == "man1"


def test_retrieval_is_restricted_to_technical_manuals() -> None:
    # The RFP chunk matches the query perfectly; the manual chunk does not.
    repo = _repo_with_manual_chunk([0.0, 1.0])
    embedding = FakeEmbeddingModel(vectors={"The solution shall provide X": [1.0, 0.0]})

    result = assess_requirement(1, "The solution shall provide X.", embedding, repo, None, 3, 0.5)

    assert result.verdict is Verdict.NOT_EVIDENCED  # the matching RFP chunk was ignored


def test_judge_verdict_is_used_when_evidence_exists() -> None:
    repo = _repo_with_manual_chunk([1.0, 0.0])
    embedding = FakeEmbeddingModel(vectors={"The solution shall provide X": [1.0, 0.0]})
    llm = FakeLLMBackend(response='{"verdict": "partial", "rationale": "Covers part of it."}')

    result = assess_requirement(1, "The solution shall provide X.", embedding, repo, llm, 3, 0.5)

    assert result.verdict is Verdict.PARTIAL
    assert result.rationale == "Covers part of it."
    assert "audit trails" in llm.last_prompt


def test_malformed_judge_output_becomes_needs_review() -> None:
    repo = _repo_with_manual_chunk([1.0, 0.0])
    embedding = FakeEmbeddingModel(vectors={"The solution shall provide X": [1.0, 0.0]})
    llm = FakeLLMBackend(response="I think it is fine")

    result = assess_requirement(1, "The solution shall provide X.", embedding, repo, llm, 3, 0.5)

    assert result.verdict is Verdict.NEEDS_REVIEW
    assert len(result.evidence) == 1  # evidence is still shown to the human


def test_check_rfp_assesses_every_requirement_and_counts_verdicts() -> None:
    repo = _repo_with_manual_chunk([1.0, 0.0])
    claim = "The solution shall provide complete regulatory audit trails"
    embedding = FakeEmbeddingModel(vectors={claim: [1.0, 0.0]}, default=[0.0, 1.0])

    report = check_rfp(RFP_TEXT, embedding, repo, None, 3, 0.5)

    assert [a.number for a in report.assessments] == [1, 2, 3]
    assert report.assessments[0].verdict is Verdict.SUPPORTED
    assert report.counts() == {"SUPPORTED": 1, "PARTIAL": 0, "NOT_EVIDENCED": 2, "NEEDS_REVIEW": 0}
