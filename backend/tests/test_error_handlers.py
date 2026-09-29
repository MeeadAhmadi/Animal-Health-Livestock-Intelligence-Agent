from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.error_handlers import unhandled_exception_handler
from app.middleware import RequestContextMiddleware

error_app = FastAPI()
error_app.add_exception_handler(Exception, unhandled_exception_handler)
error_app.add_middleware(RequestContextMiddleware)


@error_app.get("/test-error")
def trigger_error_route() -> None:
    raise RuntimeError("sensitive internal detail")


client = TestClient(error_app, raise_server_exceptions=False)


def test_unhandled_exception_returns_safe_response() -> None:
    response = client.get("/test-error")

    assert response.status_code == 500

    body = response.json()

    assert body["status"] == "error"
    assert body["message"] == "Internal server error"
    assert "sensitive internal detail" not in response.text

    request_id = body["request_id"]

    assert UUID(request_id).version == 4
    assert response.headers["X-Request-ID"] == request_id
