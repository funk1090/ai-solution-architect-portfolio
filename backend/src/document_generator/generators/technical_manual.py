"""Concrete generator: synthetic technical manuals (PDF).

Satisfies FR3: a structured manual with introduction, specifications,
procedures, and appendix sections.

Feature 0009 / ADR-0008: a "Capabilities" section states what the
fictional company's products provide, drawn ONLY from the supported
subset of the capability catalog. RFP requirements are drawn from the
full catalog, so some are supported by these manuals and some are not,
and the right answer is known. The selection uses its own seeded
random.Random (seed + document index), independent of the Faker stream,
so existing document content and reproducibility are unaffected.

Note: an explicit pdf.ln() call follows every multi_cell() call — see
rfp.py for why this is required with this fpdf2 version.
"""
import random

from fpdf import FPDF
from shared_core.capabilities import ALL_SUPPORTED_PHRASES

from document_generator.generators.base import DocumentGenerator
from document_generator.models import DocumentType


_CAPABILITY_TEMPLATES = (
    "The product delivers {phrase}.",
    "Built-in support for {phrase}.",
    "Customers benefit from {phrase}.",
)
_CAPABILITIES_PER_MANUAL = 6


def pick_capability_statements(seed: int, index: int) -> list[str]:
    """Deterministic, Faker-independent selection of capability
    statements for one manual (ADR-0008). Module-level so it is unit
    testable without rendering a PDF."""
    rng = random.Random(f"{seed}-{index}")
    phrases = rng.sample(sorted(ALL_SUPPORTED_PHRASES), _CAPABILITIES_PER_MANUAL)
    return [rng.choice(_CAPABILITY_TEMPLATES).format(phrase=p) for p in phrases]


class TechnicalManualGenerator(DocumentGenerator):
    document_type = DocumentType.TECHNICAL_MANUAL
    file_extension = "pdf"

    def _render(self, index: int) -> tuple[bytes, str]:
        manufacturer = self._provider.company_name()
        product = self._provider.product_name()
        version = self._provider.version_number()
        specifications = [self._provider.specification_item() for _ in range(6)]
        procedure_steps = [self._provider.procedure_step() for _ in range(5)]
        capabilities = pick_capability_statements(self._seed, index)

        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Helvetica", "B", size=16)
        pdf.multi_cell(0, 10, f"{product} Technical Manual")
        pdf.ln()

        pdf.set_font("Helvetica", "", size=12)
        pdf.ln(2)
        pdf.multi_cell(0, 8, f"Manufacturer: {manufacturer}")
        pdf.ln()
        pdf.multi_cell(0, 8, f"Version: {version}")
        pdf.ln()

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", size=13)
        pdf.multi_cell(0, 8, "1. Introduction")
        pdf.ln()
        pdf.set_font("Helvetica", "", size=12)
        pdf.multi_cell(0, 7, self._provider.paragraph(sentence_count=6))
        pdf.ln()

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", size=13)
        pdf.multi_cell(0, 8, "2. Specifications")
        pdf.ln()
        pdf.set_font("Helvetica", "", size=12)
        for label, value in specifications:
            pdf.multi_cell(0, 7, f"- {label}: {value}")
            pdf.ln()

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", size=13)
        pdf.multi_cell(0, 8, "3. Capabilities")
        pdf.ln()
        pdf.set_font("Helvetica", "", size=12)
        for statement in capabilities:
            pdf.multi_cell(0, 7, f"- {statement}")
            pdf.ln()

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", size=13)
        pdf.multi_cell(0, 8, "4. Procedures")
        pdf.ln()
        pdf.set_font("Helvetica", "", size=12)
        for i, step in enumerate(procedure_steps, start=1):
            pdf.multi_cell(0, 7, f"{i}. {step}")
            pdf.ln()

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", size=13)
        pdf.multi_cell(0, 8, "5. Appendix")
        pdf.ln()
        pdf.set_font("Helvetica", "", size=12)
        pdf.multi_cell(0, 7, self._provider.paragraph(sentence_count=3))
        pdf.ln()

        content = bytes(pdf.output())
        return content, manufacturer
