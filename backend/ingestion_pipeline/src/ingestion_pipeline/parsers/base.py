"""Base parser interface (Strategy pattern, FR7/NFR3).

Mirrors DocumentGenerator's design from Feature 0001 deliberately: a
proven extensibility pattern is worth reusing consistently across the
codebase rather than reinventing per feature.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedContent:
    extracted_text: str | None
    structured_data: list[dict] | None


class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedContent: ...
