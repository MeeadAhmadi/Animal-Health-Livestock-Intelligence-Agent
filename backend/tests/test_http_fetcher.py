import socket

import httpx
import pytest

from app.collection.http_fetcher import (
    FetchLimits,
    HttpStatusError,
    RedirectLocationError,
    ResponseTooLargeError,
    TooManyRedirectsError,
    fetch_url,
)
from app.collection.url_safety import UnsafeUrlError


@pytest.fixture
def limits() -> FetchLimits:
    return FetchLimits(
        connect_timeout_seconds=2.0,
        read_timeout_seconds=2.0,
        max_redirects=2,
        max_response_bytes=1024,
    )


@pytest.fixture(autouse=True)
def public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_getaddrinfo(host, port, *args, **kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", port),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


def install_mock_transport(
    monkeypatch: pytest.MonkeyPatch,
    handler,
) -> None:
    real_client = httpx.Client
    transport = httpx.MockTransport(handler)

    def client_factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", client_factory)


def test_fetches_using_validated_pinned_ip(
    monkeypatch: pytest.MonkeyPatch,
    limits: FetchLimits,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://8.8.8.8/article"
        assert request.headers["host"] == "example.com"

        return httpx.Response(
            200,
            headers={"content-type": "text/plain"},
            content=b"safe content",
        )

    install_mock_transport(monkeypatch, handler)

    result = fetch_url(
        "https://example.com/article",
        limits=limits,
    )

    assert result.requested_url == "https://example.com/article"
    assert result.final_url == "https://example.com/article"
    assert result.content == b"safe content"
    assert result.redirect_count == 0


def test_redirect_destination_is_revalidated(
    monkeypatch: pytest.MonkeyPatch,
    limits: FetchLimits,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "http://127.0.0.1/private"},
        )

    install_mock_transport(monkeypatch, handler)

    with pytest.raises(UnsafeUrlError):
        fetch_url("https://example.com/start", limits=limits)


def test_allows_safe_redirect(
    monkeypatch: pytest.MonkeyPatch,
    limits: FetchLimits,
) -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1

        if request_count == 1:
            return httpx.Response(
                302,
                headers={"location": "/final"},
            )

        assert str(request.url) == "https://8.8.8.8/final"

        return httpx.Response(200, content=b"done")

    install_mock_transport(monkeypatch, handler)

    result = fetch_url(
        "https://example.com/start",
        limits=limits,
    )

    assert result.final_url == "https://example.com/final"
    assert result.redirect_count == 1
    assert result.content == b"done"


def test_enforces_redirect_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits = FetchLimits(
        connect_timeout_seconds=2.0,
        read_timeout_seconds=2.0,
        max_redirects=0,
        max_response_bytes=1024,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "/next"},
        )

    install_mock_transport(monkeypatch, handler)

    with pytest.raises(TooManyRedirectsError):
        fetch_url("https://example.com/start", limits=limits)


def test_rejects_redirect_without_location(
    monkeypatch: pytest.MonkeyPatch,
    limits: FetchLimits,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302)

    install_mock_transport(monkeypatch, handler)

    with pytest.raises(RedirectLocationError):
        fetch_url("https://example.com/start", limits=limits)


def test_rejects_content_length_over_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits = FetchLimits(
        connect_timeout_seconds=2.0,
        read_timeout_seconds=2.0,
        max_redirects=2,
        max_response_bytes=4,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-length": "10"},
            content=b"0123456789",
        )

    install_mock_transport(monkeypatch, handler)

    with pytest.raises(ResponseTooLargeError):
        fetch_url("https://example.com/file", limits=limits)


def test_rejects_streamed_body_over_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits = FetchLimits(
        connect_timeout_seconds=2.0,
        read_timeout_seconds=2.0,
        max_redirects=2,
        max_response_bytes=4,
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"12345",
        )

    install_mock_transport(monkeypatch, handler)

    with pytest.raises(ResponseTooLargeError):
        fetch_url("https://example.com/file", limits=limits)


def test_rejects_non_success_status(
    monkeypatch: pytest.MonkeyPatch,
    limits: FetchLimits,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    install_mock_transport(monkeypatch, handler)

    with pytest.raises(HttpStatusError):
        fetch_url("https://example.com/outage", limits=limits)
