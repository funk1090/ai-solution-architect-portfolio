"""Pipeline page (FR3): generate -> ingest -> index."""
import streamlit as st

from portfolio_frontend.views.common import call_api

DOCUMENT_TYPES = ["rfp", "technical_manual", "excel_requirements"]


def render(client) -> None:
    st.header("Pipeline")
    st.caption("Run each stage of the data pipeline. Long stages block until finished.")

    st.subheader("1. Generate documents")
    doc_type = st.selectbox("Document type", DOCUMENT_TYPES)
    count = st.number_input("How many", min_value=1, max_value=500, value=5, step=1)
    if st.button("Generate"):
        result = call_api(
            lambda: client.generate(doc_type, int(count)), "Generating documents..."
        )
        if result is not None:
            st.success(f"Generated {result.generated} document(s) in {result.output_dir}")

    st.subheader("2. Ingest")
    parallel = st.checkbox("Parallel (multiprocessing)", value=True)
    if st.button("Run ingestion"):
        result = call_api(lambda: client.ingest(parallel), "Ingesting documents...")
        if result is not None:
            st.success(
                f"Processed {result.processed} | Skipped {result.skipped} | Failed {result.failed}"
            )
            if result.failed:
                st.warning("Some documents failed. Check the API logs.")

    st.subheader("3. Index for the assistant")
    if st.button("Run indexing"):
        result = call_api(client.index, "Indexing (embeddings)...")
        if result is not None:
            st.success(
                f"Documents processed {result.documents_processed} | "
                f"Chunks created {result.chunks_created} | Skipped {result.chunks_skipped}"
            )
