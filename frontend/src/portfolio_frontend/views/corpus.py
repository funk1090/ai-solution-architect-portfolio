"""Corpus page (FR2): API status and document counts."""
import streamlit as st

from portfolio_frontend.views.common import call_api


def render(client) -> None:
    st.header("Corpus")
    st.caption("What exists in the platform right now.")

    if st.button("Refresh"):
        st.rerun()

    if client.is_healthy():
        st.success("API is reachable.")
    else:
        st.error("API is not reachable. Start it and refresh.")
        return

    summary = call_api(client.corpus_summary, "Reading corpus...")
    if summary is None:
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Generated", summary.total_generated)
    col2.metric("Ingested", summary.total_ingested)
    col3.metric("Indexed chunks", summary.indexed_chunks)

    st.subheader("By document type")
    if summary.by_type:
        st.table(
            [
                {
                    "Document type": row.document_type,
                    "Generated": row.generated,
                    "Ingested": row.ingested,
                }
                for row in summary.by_type
            ]
        )
    else:
        st.info("No documents yet. Use the Pipeline page to generate some.")

    if summary.total_ingested > 0 and summary.indexed_chunks == 0:
        st.warning("Documents are ingested but nothing is indexed. Run indexing on the Pipeline page.")
