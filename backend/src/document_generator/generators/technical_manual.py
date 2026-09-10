"""Concrete generator: synthetic technical manuals (PDF).

Satisfies FR3: a structured manual with introduction, specifications,
procedures, and appendix sections.

Note: an explicit pdf.ln() call follows every multi_cell() call — see
rfp.py for why this is required with this fpdf2 version.
"""
from fpdf import FPDF

from document_generator.generators.base import DocumentGenerator
from document_generator.models import DocumentType


class TechnicalManualGenerator(DocumentGenerator):
    document_type = DocumentType.TECHNICAL_MANUAL
    file_extension = "pdf"

    def _render(self, index: int) -> tuple[bytes, str]:
        manufacturer = self._provider.company_name()
        product = self._provider.product_name()
        version = self._provider.version_number()
        specifications = [self._provider.specification_item() for _ in range(6)]
        procedure_steps = [self._provider.procedure_step() for _ in range(5)]

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
        pdf.multi_cell(0, 8, "3. Procedures")
        pdf.ln()
        pdf.set_font("Helvetica", "", size=12)
        for i, step in enumerate(procedure_steps, start=1):
            pdf.multi_cell(0, 7, f"{i}. {step}")
            pdf.ln()

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", size=13)
        pdf.multi_cell(0, 8, "4. Appendix")
        pdf.ln()
        pdf.set_font("Helvetica", "", size=12)
        pdf.multi_cell(0, 7, self._provider.paragraph(sentence_count=3))
        pdf.ln()

        content = bytes(pdf.output())
        return content, manufacturer
