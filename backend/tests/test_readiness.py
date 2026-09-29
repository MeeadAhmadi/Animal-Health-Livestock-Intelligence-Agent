from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.main import app

client = TestClient(app)


def test_readiness_when_database_is_available() -> None:
    with patch("app.main.engine.connect"):
        response = client.get("/ready")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "status": "ready",
        "service": "livestock-intelligence-api",
    }


def test_readiness_when_database_is_unavailable() -> None:
    with patch(
        "app.main.engine.connect",
        side_effect=SQLAlchemyError("database unavailable"),
    ):
        response = client.get("/ready")

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {
        "status": "unavailable",
        "service": "livestock-intelligence-api",
    }