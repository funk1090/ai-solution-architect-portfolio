"""Concrete generator: synthetic technical requirement matrices (Excel).

Satisfies FR2: an .xlsx workbook containing requirement ID, description,
category, priority, and a source RFP reference (the fictional company
the requirements are attributed to).
"""
import io

import pandas as pd

from document_generator.generators.base import DocumentGenerator
from document_generator.models import DocumentType


class ExcelRequirementsGenerator(DocumentGenerator):
    document_type = DocumentType.EXCEL_REQUIREMENTS
    file_extension = "xlsx"

    def _render(self, index: int) -> tuple[bytes, str]:
        source_company = self._provider.company_name()
        row_count = 10

        rows = [
            {
                "Requirement ID": self._provider.requirement_id(i),
                "Description": self._provider.technical_requirement(),
                "Category": self._provider.requirement_category(),
                "Priority": self._provider.requirement_priority(),
                "Source RFP Reference": source_company,
            }
            for i in range(row_count)
        ]
        dataframe = pd.DataFrame(rows)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Requirements")

        return buffer.getvalue(), source_company
