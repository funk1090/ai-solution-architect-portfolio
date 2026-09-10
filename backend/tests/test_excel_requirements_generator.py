"""Unit tests for ExcelRequirementsGenerator."""
from pathlib import Path

import pandas as pd

from document_generator.generators.excel_requirements import ExcelRequirementsGenerator
from document_generator.providers import EnterpriseFakerProvider
from document_generator.repository import InMemoryDocumentMetadataRepository


def _build_generator(tmp_path: Path, seed: int = 42) -> ExcelRequirementsGenerator:
    provider = EnterpriseFakerProvider(seed=seed)
    repository = InMemoryDocumentMetadataRepository()
    return ExcelRequirementsGenerator(
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
        assert Path(metadata.file_path).suffix == ".xlsx"


def test_workbook_has_expected_columns_and_rows(tmp_path: Path) -> None:
    generator = _build_generator(tmp_path)

    [metadata] = generator.generate(1)
    dataframe = pd.read_excel(metadata.file_path, sheet_name="Requirements")

    assert list(dataframe.columns) == [
        "Requirement ID",
        "Description",
        "Category",
        "Priority",
        "Source RFP Reference",
    ]
    assert len(dataframe) == 10


def test_generation_is_reproducible_with_the_same_seed(tmp_path: Path) -> None:
    first_results = _build_generator(tmp_path / "run_1", seed=99).generate(1)
    second_results = _build_generator(tmp_path / "run_2", seed=99).generate(1)

    assert first_results[0].checksum_sha256 == second_results[0].checksum_sha256
