"""Base class for every document generator (Strategy pattern, FR8/NFR3).

A concrete generator only needs to implement `_render`, returning the
raw file bytes plus the fictional entity the document is "about". This
base class handles everything that must be consistent across every
document type: checksum computation, duplicate detection (FR7), writing
to disk, and recording metadata through the repository.
"""
from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path

from document_generator.models import DocumentMetadata, DocumentType
from document_generator.providers import EnterpriseFakerProvider
from document_generator.repository import DocumentMetadataRepository

logger = logging.getLogger(__name__)


class DocumentGenerator(ABC):
    document_type: DocumentType
    file_extension: str

    def __init__(
        self,
        provider: EnterpriseFakerProvider,
        repository: DocumentMetadataRepository,
        output_dir: Path,
        seed: int,
    ) -> None:
        self._provider = provider
        self._repository = repository
        self._output_dir = output_dir
        self._seed = seed
        self._output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def _render(self, index: int) -> tuple[bytes, str]:
        """Return (file_content_bytes, related_entity_name)."""

    def generate(self, count: int) -> list[DocumentMetadata]:
        results: list[DocumentMetadata] = []
        for index in range(count):
            content, related_entity = self._render(index)
            checksum = hashlib.sha256(content).hexdigest()

            if self._repository.exists_checksum(checksum):
                logger.warning(
                    "Skipping duplicate document (checksum=%s)", checksum
                )
                continue

            filename = f"{self.document_type.value}_{index:04d}.{self.file_extension}"
            file_path = self._output_dir / filename
            file_path.write_bytes(content)

            metadata = DocumentMetadata(
                document_type=self.document_type,
                file_path=str(file_path),
                checksum_sha256=checksum,
                related_entity=related_entity,
                seed=self._seed,
            )
            self._repository.save(metadata)
            results.append(metadata)

            logger.info(
                "Generated %s (%s) for %s",
                filename,
                self.document_type.value,
                related_entity,
            )

        return results
