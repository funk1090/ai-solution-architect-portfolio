"""Ask page (FR4): grounded question answering over the indexed corpus."""
import streamlit as st

from portfolio_frontend.views.common import call_api


def render(client) -> None:
    st.header("Ask")
    st.caption("Answers come only from indexed documents, with their sources.")

    question = st.text_area("Question", placeholder="What is the budget range mentioned in the proposals?")
    if st.button("Ask") and question.strip():
        result = call_api(lambda: client.ask(question.strip()), "Thinking...")
        if result is None:
            return

        if not result.grounded:
            st.warning("Not grounded: nothing relevant was found in the indexed documents.")
        st.markdown(result.answer)

        if result.sources:
            st.subheader("Sources")
            if result.source_details:
                for detail in result.source_details:
                    st.write(f"- {detail.label}")
            else:
                for checksum in result.sources:
                    st.write(f"- document {checksum[:8]}")
