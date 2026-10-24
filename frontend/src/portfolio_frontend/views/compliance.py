"""Compliance page (Feature 0009): RFP requirements vs. technical manuals."""
import streamlit as st

from portfolio_frontend.views.common import call_api

_ICONS = {
    "SUPPORTED": "SUPPORTED",
    "PARTIAL": "PARTIAL",
    "NOT_EVIDENCED": "NOT EVIDENCED",
    "NEEDS_REVIEW": "NEEDS REVIEW",
}


def render(client) -> None:
    st.header("Compliance")
    st.caption(
        "Checks each RFP requirement against the technical manuals and shows the "
        "evidence. It supports a human decision; it is not a certification."
    )

    rfps = call_api(client.list_rfps, "Loading RFPs...")
    if rfps is None:
        return
    if not rfps:
        st.info("No ingested RFPs yet. Generate and ingest some on the Pipeline page.")
        return

    labels = {f"{r.file_name} - {r.issuing_organization}": r for r in rfps}
    choice = st.selectbox("RFP", list(labels))
    use_judge = st.checkbox(
        "Use the LLM judge (slower, adds a rationale)", value=True,
        help="Off = retrieval only: a requirement is SUPPORTED when matching evidence exists.",
    )

    if not st.button("Check compliance"):
        return

    result = call_api(
        lambda: client.check_compliance(labels[choice].source_checksum, use_judge),
        "Checking requirements against the manuals...",
    )
    if result is None:
        return

    columns = st.columns(len(result.counts))
    for column, (verdict, count) in zip(columns, result.counts.items()):
        column.metric(_ICONS.get(verdict, verdict), count)

    for assessment in result.assessments:
        label = _ICONS.get(assessment.verdict, assessment.verdict)
        with st.expander(f"{assessment.number}. [{label}] {assessment.requirement}"):
            st.write(assessment.rationale)
            if assessment.evidence:
                st.caption("Evidence")
                for item in assessment.evidence:
                    source = item.file_name or f"document {item.source_checksum[:8]}"
                    st.write(f"- **{source}** (score {item.score:.2f})")
                    st.caption(item.text)
            else:
                st.caption("No supporting passage found in the manuals.")
