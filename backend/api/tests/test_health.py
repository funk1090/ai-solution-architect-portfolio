"""The health check needs no auth, no database -- just the app itself."""
from fastapi.testclient import TestClient

from portfolio_api.main import app


def test_health_check_requires_no_authentication() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_route_rejects_missing_api_key() -> None:
    client = TestClient(app)

    response = client.post("/classifier/classify", json={"text": "anything"})

    assert response.status_code == 422  # missing required header
