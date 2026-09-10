"""Generator factory (FR8/NFR3: extensibility without modification).

To add a new document type in a future phase:
  1. Create a new class in generators/ inheriting from DocumentGenerator.
  2. Register it in _REGISTRY below.
No other file in this package needs to change.
"""
from pathlib import Path

from document_generator.generators.base import DocumentGenerator
from document_generator.generators.excel_requirements import ExcelRequirementsGenerator
from document_generator.generators.rfp import RFPGenerator
from document_generator.models import DocumentType
from document_generator.providers import EnterpriseFakerProvider
from document_generator.repository import DocumentMetadataRepository

_REGISTRY: dict[DocumentType, type[DocumentGenerator]] = {
    DocumentType.RFP: RFPGenerator,
    DocumentType.EXCEL_REQUIREMENTS: ExcelRequirementsGenerator,
    # DocumentType.TECHNICAL_MANUAL: TechnicalManualGenerator,       (next iteration)
}


class GeneratorFactory:
    def __init__(
        self,
        provider: EnterpriseFakerProvider,
        repository: DocumentMetadataRepository,
    ) -> None:
        self._provider = provider
        self._repository = repository

    def create(
        self, document_type: DocumentType, output_dir: Path, seed: int
    ) -> DocumentGenerator:
        try:
            generator_cls = _REGISTRY[document_type]
        except KeyError as exc:
            raise ValueError(
                f"No generator registered for document type: {document_type}"
            ) from exc

        return generator_cls(
            provider=self._provider,
            repository=self._repository,
            output_dir=output_dir,
            seed=seed,
        )
