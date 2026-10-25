"""Shared fixtures: rate-limit buckets must not leak between tests."""
import pytest

from portfolio_api.rate_limit import reset_limiters


@pytest.fixture(autouse=True)
def _fresh_rate_limiters():
    reset_limiters()
    yield
    reset_limiters()
