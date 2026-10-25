from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

_ALLOWED_SCHEMES = {
    "http": 80,
    "https": 443,
}


class UnsafeUrlError(ValueError):
    """Raised when a collection URL fails SSRF safety validation."""


@dataclass(frozen=True, slots=True)
class ValidatedUrl:
    url: str
    scheme: str
    hostname: str
    port: int
    resolved_ips: tuple[str, ...]


def _require_global_ip(address: str) -> str:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError as exc:
        raise UnsafeUrlError(f"Invalid resolved IP address: {address!r}") from exc

    if not ip.is_global:
        raise UnsafeUrlError(
            f"URL resolves to a non-public destination: {ip.compressed}"
        )

    return ip.compressed


def _resolve_hostname(hostname: str, port: int) -> tuple[str, ...]:
    try:
        results = socket.getaddrinfo(
            hostname,
            port,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror as exc:
        raise UnsafeUrlError(
            f"Hostname could not be resolved: {hostname!r}"
        ) from exc

    addresses: list[str] = []

    for result in results:
        raw_address = result[4][0]

        if "%" in raw_address:
            raise UnsafeUrlError("Scoped IPv6 destinations are not allowed.")

        address = _require_global_ip(raw_address)

        if address not in addresses:
            addresses.append(address)

    if not addresses:
        raise UnsafeUrlError(
            f"Hostname resolved without usable addresses: {hostname!r}"
        )

    return tuple(addresses)


def validate_collection_url(url: str) -> ValidatedUrl:
    if not isinstance(url, str) or not url:
        raise UnsafeUrlError("URL must be a non-empty string.")

    if any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in url):
        raise UnsafeUrlError("URL contains whitespace or control characters.")

    if "\\" in url:
        raise UnsafeUrlError("Backslashes are not allowed in collection URLs.")

    try:
        parsed = urlsplit(url)
    except ValueError as exc:
        raise UnsafeUrlError("Malformed collection URL.") from exc

    scheme = parsed.scheme.lower()

    if scheme not in _ALLOWED_SCHEMES:
        raise UnsafeUrlError(
            f"URL scheme is not allowed: {parsed.scheme!r}"
        )

    if parsed.username is not None or parsed.password is not None:
        raise UnsafeUrlError("User credentials in collection URLs are not allowed.")

    hostname = parsed.hostname

    if hostname is None:
        raise UnsafeUrlError("URL must include a hostname.")

    hostname = hostname.rstrip(".").lower()

    if not hostname:
        raise UnsafeUrlError("URL hostname is empty.")

    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise UnsafeUrlError("Localhost destinations are not allowed.")

    if "%" in hostname:
        raise UnsafeUrlError("Scoped host destinations are not allowed.")

    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeUrlError("URL contains an invalid port.") from exc

    if port is None:
        port = _ALLOWED_SCHEMES[scheme]

    if not 1 <= port <= 65535:
        raise UnsafeUrlError("URL port is outside the valid range.")

    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        resolved_ips = _resolve_hostname(hostname, port)
    else:
        resolved_ips = (_require_global_ip(literal_ip.compressed),)

    return ValidatedUrl(
        url=url,
        scheme=scheme,
        hostname=hostname,
        port=port,
        resolved_ips=resolved_ips,
    )
