from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from app.collection.url_safety import ValidatedUrl, validate_collection_url

_REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}


class CollectionFetchError(RuntimeError):
    """Base error for bounded HTTP collection failures."""


class TooManyRedirectsError(CollectionFetchError):
    """Raised when a response exceeds the configured redirect limit."""


class ResponseTooLargeError(CollectionFetchError):
    """Raised when a response exceeds the configured byte limit."""


class HttpStatusError(CollectionFetchError):
    """Raised when the final response is not successful."""


class RedirectLocationError(CollectionFetchError):
    """Raised when a redirect response has no usable Location header."""


@dataclass(frozen=True, slots=True)
class FetchLimits:
    connect_timeout_seconds: float
    read_timeout_seconds: float
    max_redirects: int
    max_response_bytes: int

    def __post_init__(self) -> None:
        if self.connect_timeout_seconds <= 0:
            raise ValueError("connect_timeout_seconds must be positive.")

        if self.read_timeout_seconds <= 0:
            raise ValueError("read_timeout_seconds must be positive.")

        if self.max_redirects < 0:
            raise ValueError("max_redirects cannot be negative.")

        if self.max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive.")


@dataclass(frozen=True, slots=True)
class FetchResult:
    requested_url: str
    final_url: str
    status_code: int
    content_type: str | None
    content: bytes
    redirect_count: int


def _format_ip_for_url(address: str) -> str:
    ip = ipaddress.ip_address(address)

    if ip.version == 6:
        return f"[{ip.compressed}]"

    return ip.compressed


def _ascii_hostname(hostname: str) -> str:
    try:
        return hostname.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise CollectionFetchError("Hostname could not be IDNA encoded.") from exc


def _host_header(validated: ValidatedUrl) -> str:
    hostname = _ascii_hostname(validated.hostname)

    if ":" in hostname:
        hostname = f"[{hostname}]"

    default_port = 443 if validated.scheme == "https" else 80

    if validated.port != default_port:
        return f"{hostname}:{validated.port}"

    return hostname


def _pinned_request_url(validated: ValidatedUrl, address: str) -> str:
    parsed = urlsplit(validated.url)
    host = _format_ip_for_url(address)
    default_port = 443 if validated.scheme == "https" else 80

    if validated.port != default_port:
        host = f"{host}:{validated.port}"

    return urlunsplit(
        (
            validated.scheme,
            host,
            parsed.path or "/",
            parsed.query,
            "",
        )
    )


def _read_bounded_body(
    response: httpx.Response,
    max_response_bytes: int,
) -> bytes:
    content_length = response.headers.get("content-length")

    if content_length is not None:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = None

        if declared_size is not None and declared_size > max_response_bytes:
            raise ResponseTooLargeError(
                "Response Content-Length exceeds the configured byte limit."
            )

    body = bytearray()

    for chunk in response.iter_bytes():
        if len(body) + len(chunk) > max_response_bytes:
            raise ResponseTooLargeError(
                "Response body exceeds the configured byte limit."
            )

        body.extend(chunk)

    return bytes(body)


def fetch_url(url: str, *, limits: FetchLimits) -> FetchResult:
    requested_url = url
    current_url = url
    redirect_count = 0

    timeout = httpx.Timeout(
        connect=limits.connect_timeout_seconds,
        read=limits.read_timeout_seconds,
        write=limits.read_timeout_seconds,
        pool=limits.connect_timeout_seconds,
    )

    while True:
        validated = validate_collection_url(current_url)
        pinned_url = _pinned_request_url(
            validated,
            validated.resolved_ips[0],
        )

        headers = {
            "Host": _host_header(validated),
        }

        extensions: dict[str, object] = {}

        if validated.scheme == "https":
            extensions["sni_hostname"] = _ascii_hostname(validated.hostname)

        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            trust_env=False,
        ) as client:
            request = client.build_request(
                "GET",
                pinned_url,
                headers=headers,
                extensions=extensions,
            )

            response = client.send(request, stream=True)

            try:
                if response.status_code in _REDIRECT_STATUS_CODES:
                    location = response.headers.get("location")

                    if not location:
                        raise RedirectLocationError(
                            "Redirect response did not include a Location header."
                        )

                    if redirect_count >= limits.max_redirects:
                        raise TooManyRedirectsError(
                            "Response exceeded the configured redirect limit."
                        )

                    current_url = urljoin(current_url, location)
                    redirect_count += 1
                    continue

                if not 200 <= response.status_code < 300:
                    raise HttpStatusError(
                        f"HTTP collection failed with status {response.status_code}."
                    )

                content = _read_bounded_body(
                    response,
                    limits.max_response_bytes,
                )

                return FetchResult(
                    requested_url=requested_url,
                    final_url=current_url,
                    status_code=response.status_code,
                    content_type=response.headers.get("content-type"),
                    content=content,
                    redirect_count=redirect_count,
                )
            finally:
                response.close()
