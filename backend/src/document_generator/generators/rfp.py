"""Concrete generator: synthetic Request for Proposal (RFP) documents.

Satisfies FR1: PDF output containing a fictional issuing company,
project scope, budget range, and a technical requirements section.

Note on fpdf2 usage: an explicit pdf.ln() call is required after every
multi_cell() call. Without it, consecutive multi_cell() calls in this
fpdf2 version do not reliably reset the horizontal cursor position,
eventually raising "Not enough horizontal space to render a single
character" even for short, plain ASCII text. This was diagnosed by
reproducing the failure in isolation before patching (see git history /
commit message for this fix).
"""
from fpdf import FPDF

from document_generator.generators.base import DocumentGenerator
from document_generator.models import DocumentType


class RFPGenerator(DocumentGenerator):
    document_type = DocumentType.RFP
    file_extension = "pdf"

    def _render(self, index: int) -> tuple[bytes, str]:
        company = self._provider.company_name()
        project = self._provider.project_name()
        budget_low, budget_high = self._provider.budget_range_usd()
        requirements = [self._provider.technical_requirement() for _ in range(5)]

        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Helvetica", "B", size=16)
        pdf.multi_cell(0, 10, "Request for Proposal (RFP)")
        pdf.ln()

        pdf.set_font("Helvetica", "", size=12)
        pdf.ln(4)
        pdf.multi_cell(0, 8, f"Issuing Organization: {company}")
        pdf.ln()
        pdf.multi_cell(0, 8, f"Project Title: {project}")
        pdf.ln()
        pdf.multi_cell(0, 8, f"Budget Range: USD {budget_low:,} - {budget_high:,}")
        pdf.ln()

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", size=13)
        pdf.multi_cell(0, 8, "Project Overview")
        pdf.ln()
        pdf.set_font("Helvetica", "", size=12)
        pdf.multi_cell(0, 7, self._provider.paragraph(sentence_count=6))
        pdf.ln()

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", size=13)
        pdf.multi_cell(0, 8, "Technical Requirements")
        pdf.ln()
        pdf.set_font("Helvetica", "", size=12)
        for i, requirement in enumerate(requirements, start=1):
            pdf.multi_cell(0, 7, f"{i}. {requirement}")
            pdf.ln()

        content = bytes(pdf.output())
        return content, company
