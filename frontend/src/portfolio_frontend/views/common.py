"""Shared helper: run an API call and turn failures into friendly UI
messages instead of stack traces (NFR4)."""
from collections.abc import Callable
from typing import TypeVar

import streamlit as st

from portfolio_frontend.api_client import ApiError, ApiUnauthorized, ApiUnreachable

T = TypeVar("T")


def call_api(action: Callable[[], T], spinner: str) -> T | None:
    try:
        with st.spinner(spinner):
            return action()
    except ApiUnreachable as exc:
        st.error(f"{exc}")
    except ApiUnauthorized as exc:
        st.error(f"{exc}")
    except ApiError as exc:
        st.error(f"{exc}")
    return None
