"""Unit tests for RFPGenerator.

Note: no PostgreSQL connection is required to run these tests — they use
InMemoryDocumentMetadataRepository, which is exactly the point of the
Repository pattern described in Feature 0001 (NFR2: testability).
"""
from pathlib import Path

from document_generator.generators.rfp import RFPGenerator
from document_generator.providers import EnterpriseFakerProvider
from document_generator.repository import InMemoryDocumentMetadataRepository


def _build_generator(tmp_path: Path, seed: int = 42) -> RFPGenerator:
    provider = EnterpriseFakerProvider(seed=seed)
    repository = InMemoryDocumentMetadataRepository()
    return RFPGenerator(
        provider=provider,
        repository=repository,
        output_dir=tmp_path,
        seed=seed,
    )


def test_generates_requested_number_of_files(tmp_path: Path) -> None:
    generator = _build_generator(tmp_path)

    results = generator.generate(3)

    assert len(results) == 3
    for metadata in results:
        assert Path(metadata.file_path).exists()
        assert Path(metadata.file_path).suffix == ".pdf"


def test_each_generated_file_has_a_unique_checksum(tmp_path: Path) -> None:
    generator = _build_generator(tmp_path)

    results = generator.generate(5)

    checksums = {metadata.checksum_sha256 for metadata in results}
    assert len(checksums) == 5


def test_generation_is_reproducible_with_the_same_seed(tmp_path: Path) -> None:
    """Validates NFR1: identical seed must produce identical output."""
    first_run_dir = tmp_path / "run_1"
    second_run_dir = tmp_path / "run_2"

    first_results = _build_generator(first_run_dir, seed=123).generate(2)
    second_results = _build_generator(second_run_dir, seed=123).generate(2)

    first_checksums = [m.checksum_sha256 for m in first_results]
    second_checksums = [m.checksum_sha256 for m in second_results]

    assert first_checksums == second_checksums
