"""Streamlit entrypoint. Run with:  uv run streamlit run src/portfolio_frontend/app.py"""
import streamlit as st

from portfolio_frontend.api_client import ApiClient
from portfolio_frontend.config import Settings
from portfolio_frontend.views import ask, classify, corpus, pipeline


@st.cache_resource
def get_client() -> ApiClient:
    settings = Settings()
    return ApiClient(
        settings.api_base_url,
        settings.api_key,
        short_timeout=settings.short_timeout,
        long_timeout=settings.long_timeout,
    )


def main() -> None:
    st.set_page_config(page_title="Andes Digital Networks - AI Platform", layout="wide")
    client = get_client()

    pages = {
        "Corpus": corpus,
        "Pipeline": pipeline,
        "Ask": ask,
        "Classify": classify,
    }
    choice = st.sidebar.radio("Navigate", list(pages))
    st.sidebar.caption("Frontend v0.1.0 - client of the Portfolio API")
    pages[choice].render(client)


main()
