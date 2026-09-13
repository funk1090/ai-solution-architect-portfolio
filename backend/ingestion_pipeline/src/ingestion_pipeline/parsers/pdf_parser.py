"""PDF parser (FR1): extracts full text from RFPs and technical manuals."""
from pathlib import Path

import pdfplumber

from ingestion_pipeline.normalization import normalize_text
from ingestion_pipeline.parsers.base import DocumentParser, ParsedContent


class PDFParser(DocumentParser):
    def parse(self, file_path: Path) -> ParsedContent:
        text_chunks: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text_chunks.append(page.extract_text() or "")

        full_text = normalize_text("\n".join(text_chunks))
        return ParsedContent(extracted_text=full_text, structured_data=None)
