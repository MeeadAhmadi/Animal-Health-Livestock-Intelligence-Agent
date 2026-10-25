import socket

import pytest

from app.collection.url_safety import UnsafeUrlError, validate_collection_url


def test_accepts_public_literal_ip() -> None:
    result = validate_collection_url("https://8.8.8.8/path")

    assert result.scheme == "https"
    assert result.hostname == "8.8.8.8"
    assert result.port == 443
    assert result.resolved_ips == ("8.8.8.8",)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://169.254.1.1",
        "http://192.168.1.10",
        "http://[::1]",
        "http://[fc00::1]",
        "http://localhost",
        "http://service.localhost",
    ],
)
def test_blocks_non_public_destinations(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        validate_collection_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/file",
        "file:///etc/passwd",
        "http://user:pass@example.com",
        "http://example.com:99999",
        "http://example.com/path with space",
        r"http://example.com\internal",
        "",
    ],
)
def test_rejects_unsafe_or_malformed_urls(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        validate_collection_url(url)


def test_resolves_public_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_getaddrinfo(*args, **kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 443),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    result = validate_collection_url("https://example.com/article")

    assert result.hostname == "example.com"
    assert result.resolved_ips == ("8.8.8.8",)


def test_rejects_hostname_if_any_dns_result_is_non_public(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_getaddrinfo(*args, **kwargs):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("8.8.8.8", 443),
            ),
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 443),
            ),
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    with pytest.raises(UnsafeUrlError):
        validate_collection_url("https://example.com")


def test_rejects_unresolvable_hostname(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_getaddrinfo(*args, **kwargs):
        raise socket.gaierror("resolution failed")

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    with pytest.raises(UnsafeUrlError):
        validate_collection_url("https://example.com")
