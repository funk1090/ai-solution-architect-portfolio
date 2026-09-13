"""Parser factory (FR7/NFR3): same extensibility pattern as Feature 0001.

To support a new document type in the future: create a new DocumentParser
subclass and add one line here. No other file needs to change.
"""
from ingestion_pipeline.models import DocumentType
from ingestion_pipeline.parsers.base import DocumentParser
from ingestion_pipeline.parsers.excel_parser import ExcelParser
from ingestion_pipeline.parsers.pdf_parser import PDFParser

_REGISTRY: dict[DocumentType, type[DocumentParser]] = {
    DocumentType.RFP: PDFParser,
    DocumentType.TECHNICAL_MANUAL: PDFParser,
    DocumentType.EXCEL_REQUIREMENTS: ExcelParser,
}


class ParserFactory:
    def create(self, document_type: DocumentType) -> DocumentParser:
        try:
            parser_cls = _REGISTRY[document_type]
        except KeyError as exc:
            raise ValueError(f"No parser registered for type: {document_type}") from exc
        return parser_cls()
