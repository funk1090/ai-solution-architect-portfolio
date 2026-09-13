"""Unit tests for ExcelParser."""
from pathlib import Path

import pandas as pd

from ingestion_pipeline.parsers.excel_parser import ExcelParser


def _build_test_workbook(path: Path) -> None:
    rows = [
        {
            "Requirement ID": "REQ-0000",
            "Description": "The solution shall provide test coverage.",
            "Category": "Reliability",
            "Priority": "High",
            "Source RFP Reference": "Test Company Inc",
        }
    ]
    pd.DataFrame(rows).to_excel(path, index=False, sheet_name="Requirements")


def test_extracts_structured_rows(tmp_path: Path) -> None:
    xlsx_path = tmp_path / "sample.xlsx"
    _build_test_workbook(xlsx_path)

    result = ExcelParser().parse(xlsx_path)

    assert result.extracted_text is None
    assert result.structured_data == [
        {
            "Requirement ID": "REQ-0000",
            "Description": "The solution shall provide test coverage.",
            "Category": "Reliability",
            "Priority": "High",
            "Source RFP Reference": "Test Company Inc",
        }
    ]
