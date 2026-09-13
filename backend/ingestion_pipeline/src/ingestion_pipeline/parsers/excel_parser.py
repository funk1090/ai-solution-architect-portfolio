"""Excel parser (FR2): extracts structured rows from requirement matrices."""
from pathlib import Path

import pandas as pd

from ingestion_pipeline.parsers.base import DocumentParser, ParsedContent


class ExcelParser(DocumentParser):
    def parse(self, file_path: Path) -> ParsedContent:
        dataframe = pd.read_excel(file_path, sheet_name="Requirements")
        structured_data = dataframe.to_dict(orient="records")
        return ParsedContent(extracted_text=None, structured_data=structured_data)
