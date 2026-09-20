"""API key authentication (FR2).

A single shared key, checked on every route except /health. This is
the appropriate level of security for a single-operator portfolio API
-- see Feature 0007, Design Decision 2 for why a full identity provider
would be solving a problem this project doesn't have.
"""
from fastapi import Header, HTTPException, status

from portfolio_api.config import Settings


def verify_api_key(x_api_key: str = Header(...)) -> None:
    settings = Settings()
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )
