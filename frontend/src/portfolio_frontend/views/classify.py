"""Classify page (FR5): requirement classification and model comparison."""
import streamlit as st

from portfolio_frontend.views.common import call_api


def render(client) -> None:
    st.header("Classify")

    st.subheader("Classify a requirement")
    text = st.text_area(
        "Requirement text",
        placeholder="The system must encrypt all data using AES-256 and enforce strict access controls.",
    )
    st.caption(
        "Trained on synthetic requirements (~83% accuracy): short or ambiguous "
        "texts can land in a neighbouring category."
    )
    if st.button("Classify") and text.strip():
        result = call_api(lambda: client.classify(text.strip()), "Classifying...")
        if result is not None:
            st.success(f"Category: {result.category}")

    st.subheader("Compare models")
    st.caption(
        "Re-trains and compares the models with cross-validation, and OVERWRITES "
        "the saved model with the best one."
    )
    if st.button("Run comparison"):
        result = call_api(client.compare, "Cross-validating models...")
        if result is not None:
            st.success(f"Best model: {result.best_model}")
            st.table(
                [
                    {"Model": name, "Accuracy": f"{acc:.3f}"}
                    for name, acc in result.accuracies.items()
                ]
            )
