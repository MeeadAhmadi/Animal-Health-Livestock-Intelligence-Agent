from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_request_context_headers_are_added() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    request_id = response.headers["X-Request-ID"]
    assert UUID(request_id).version == 4

    process_time_ms = float(response.headers["X-Process-Time-Ms"])
    assert process_time_ms >= 0
