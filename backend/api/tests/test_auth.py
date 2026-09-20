"""Unit tests for API key authentication (FR2/NFR2).

Tests the dependency function directly, not through a live route --
this needs no database, no Postgres, nothing but the function itself.
"""
import pytest
from fastapi import HTTPException

from portfolio_api.auth import verify_api_key


def test_rejects_an_incorrect_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("api_key", "correct-key")

    with pytest.raises(HTTPException) as exc_info:
        verify_api_key(x_api_key="wrong-key")

    assert exc_info.value.status_code == 401


def test_accepts_the_correct_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("api_key", "correct-key")

    verify_api_key(x_api_key="correct-key")  # should not raise
