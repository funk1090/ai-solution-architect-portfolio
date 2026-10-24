"""Unit tests for TechnicalManualGenerator."""
from pathlib import Path

from document_generator.generators.technical_manual import TechnicalManualGenerator
from document_generator.providers import EnterpriseFakerProvider
from document_generator.repository import InMemoryDocumentMetadataRepository


def _build_generator(tmp_path: Path, seed: int = 42) -> TechnicalManualGenerator:
    provider = EnterpriseFakerProvider(seed=seed)
    repository = InMemoryDocumentMetadataRepository()
    return TechnicalManualGenerator(
        provider=provider,
        repository=repository,
        output_dir=tmp_path,
        seed=seed,
    )


def test_generates_requested_number_of_files(tmp_path: Path) -> None:
    generator = _build_generator(tmp_path)

    results = generator.generate(2)

    assert len(results) == 2
    for metadata in results:
        assert Path(metadata.file_path).exists()
        assert Path(metadata.file_path).suffix == ".pdf"


def test_each_generated_file_has_a_unique_checksum(tmp_path: Path) -> None:
    generator = _build_generator(tmp_path)

    results = generator.generate(4)

    checksums = {metadata.checksum_sha256 for metadata in results}
    assert len(checksums) == 4


def test_generation_is_reproducible_with_the_same_seed(tmp_path: Path) -> None:
    first_results = _build_generator(tmp_path / "run_1", seed=7).generate(2)
    second_results = _build_generator(tmp_path / "run_2", seed=7).generate(2)

    first_checksums = [m.checksum_sha256 for m in first_results]
    second_checksums = [m.checksum_sha256 for m in second_results]

    assert first_checksums == second_checksums


def test_capabilities_come_only_from_the_supported_catalog() -> None:
    from shared_core.capabilities import ALL_SUPPORTED_PHRASES

    from document_generator.generators.technical_manual import pick_capability_statements

    for index in range(25):
        statements = pick_capability_statements(seed=42, index=index)

        assert len(statements) == 6
        for statement in statements:
            assert any(phrase in statement for phrase in ALL_SUPPORTED_PHRASES)


def test_capability_selection_is_reproducible_and_varies_by_document() -> None:
    from document_generator.generators.technical_manual import pick_capability_statements

    assert pick_capability_statements(7, 0) == pick_capability_statements(7, 0)
    assert pick_capability_statements(7, 0) != pick_capability_statements(7, 1)


def test_supported_phrases_exist_in_the_generator_vocabulary() -> None:
    """Drift guard: the answer key must stay a subset of the ADR-0004 phrase bank."""
    from shared_core.capabilities import ALL_SUPPORTED_PHRASES

    from document_generator.providers import _CATEGORY_VOCAB

    bank = {phrase for phrases in _CATEGORY_VOCAB.values() for phrase in phrases}
    assert ALL_SUPPORTED_PHRASES <= bank
