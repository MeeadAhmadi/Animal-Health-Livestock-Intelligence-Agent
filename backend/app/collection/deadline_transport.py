from __future__ import annotations

import time
from collections.abc import Iterable

import httpcore
import httpx


class TransportDeadlineExceededError(RuntimeError):
    """Raised when the absolute collection deadline is exhausted."""


def _ensure_deadline(deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise TransportDeadlineExceededError(
            "Collection exceeded the configured total time budget."
        )


def _bounded_timeout(
    deadline: float,
    requested_timeout: float | None,
) -> float:
    remaining = deadline - time.monotonic()

    if remaining <= 0:
        raise TransportDeadlineExceededError(
            "Collection exceeded the configured total time budget."
        )

    if requested_timeout is None:
        return remaining

    return min(requested_timeout, remaining)


def _raise_deadline_if_expired(
    deadline: float,
    exc: httpcore.TimeoutException,
) -> None:
    if time.monotonic() >= deadline:
        raise TransportDeadlineExceededError(
            "Collection exceeded the configured total time budget."
        ) from exc


class _DeadlineNetworkStream(httpcore.NetworkStream):
    def __init__(
        self,
        stream: httpcore.NetworkStream,
        *,
        deadline: float,
    ) -> None:
        self._stream = stream
        self._deadline = deadline

    def read(
        self,
        max_bytes: int,
        timeout: float | None = None,
    ) -> bytes:
        bounded_timeout = _bounded_timeout(self._deadline, timeout)

        try:
            data = self._stream.read(
                max_bytes,
                timeout=bounded_timeout,
            )
        except httpcore.TimeoutException as exc:
            _raise_deadline_if_expired(self._deadline, exc)
            raise

        _ensure_deadline(self._deadline)
        return data

    def write(
        self,
        buffer: bytes,
        timeout: float | None = None,
    ) -> None:
        bounded_timeout = _bounded_timeout(self._deadline, timeout)

        try:
            self._stream.write(
                buffer,
                timeout=bounded_timeout,
            )
        except httpcore.TimeoutException as exc:
            _raise_deadline_if_expired(self._deadline, exc)
            raise

        _ensure_deadline(self._deadline)

    def close(self) -> None:
        self._stream.close()

    def start_tls(
        self,
        ssl_context,
        server_hostname: str | None = None,
        timeout: float | None = None,
    ) -> httpcore.NetworkStream:
        bounded_timeout = _bounded_timeout(self._deadline, timeout)

        try:
            stream = self._stream.start_tls(
                ssl_context,
                server_hostname=server_hostname,
                timeout=bounded_timeout,
            )
        except httpcore.TimeoutException as exc:
            _raise_deadline_if_expired(self._deadline, exc)
            raise

        _ensure_deadline(self._deadline)

        return _DeadlineNetworkStream(
            stream,
            deadline=self._deadline,
        )

    def get_extra_info(self, info: str):
        return self._stream.get_extra_info(info)


class _DeadlineNetworkBackend(httpcore.NetworkBackend):
    def __init__(self, *, deadline: float) -> None:
        self._backend = httpcore.SyncBackend()
        self._deadline = deadline

    def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options=None,
    ) -> httpcore.NetworkStream:
        bounded_timeout = _bounded_timeout(self._deadline, timeout)

        try:
            stream = self._backend.connect_tcp(
                host,
                port,
                timeout=bounded_timeout,
                local_address=local_address,
                socket_options=socket_options,
            )
        except httpcore.TimeoutException as exc:
            _raise_deadline_if_expired(self._deadline, exc)
            raise

        _ensure_deadline(self._deadline)

        return _DeadlineNetworkStream(
            stream,
            deadline=self._deadline,
        )

    def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options=None,
    ) -> httpcore.NetworkStream:
        bounded_timeout = _bounded_timeout(self._deadline, timeout)

        try:
            stream = self._backend.connect_unix_socket(
                path,
                timeout=bounded_timeout,
                socket_options=socket_options,
            )
        except httpcore.TimeoutException as exc:
            _raise_deadline_if_expired(self._deadline, exc)
            raise

        _ensure_deadline(self._deadline)

        return _DeadlineNetworkStream(
            stream,
            deadline=self._deadline,
        )

    def sleep(self, seconds: float) -> None:
        remaining = _bounded_timeout(self._deadline, None)
        self._backend.sleep(min(seconds, remaining))
        _ensure_deadline(self._deadline)


def _map_httpcore_error(
    exc: Exception,
    request: httpx.Request,
) -> Exception:
    if isinstance(exc, httpcore.TimeoutException):
        return httpx.TimeoutException(
            str(exc),
            request=request,
        )

    if isinstance(
        exc,
        (
            httpcore.NetworkError,
            httpcore.ProtocolError,
            httpcore.ProxyError,
            httpcore.UnsupportedProtocol,
        ),
    ):
        return httpx.RequestError(
            str(exc),
            request=request,
        )

    return exc


class _ResponseStream(httpx.SyncByteStream):
    def __init__(
        self,
        stream: Iterable[bytes],
        *,
        request: httpx.Request,
    ) -> None:
        self._stream = stream
        self._request = request

    def __iter__(self):
        try:
            yield from self._stream
        except TransportDeadlineExceededError:
            raise
        except Exception as exc:
            mapped = _map_httpcore_error(exc, self._request)

            if mapped is exc:
                raise

            raise mapped from exc

    def close(self) -> None:
        close = getattr(self._stream, "close", None)

        if close is not None:
            close()


class DeadlineHTTPTransport(httpx.BaseTransport):
    """HTTPX transport that enforces one absolute monotonic deadline."""

    def __init__(self, *, deadline: float) -> None:
        backend = _DeadlineNetworkBackend(deadline=deadline)

        self._pool = httpcore.ConnectionPool(
            ssl_context=httpcore.default_ssl_context(),
            network_backend=backend,
        )

    def handle_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        core_request = httpcore.Request(
            method=request.method,
            url=httpcore.URL(
                scheme=request.url.raw_scheme,
                host=request.url.raw_host,
                port=request.url.port,
                target=request.url.raw_path,
            ),
            headers=request.headers.raw,
            content=request.stream,
            extensions=request.extensions,
        )

        try:
            response = self._pool.handle_request(core_request)
        except TransportDeadlineExceededError:
            raise
        except Exception as exc:
            mapped = _map_httpcore_error(exc, request)

            if mapped is exc:
                raise

            raise mapped from exc

        return httpx.Response(
            status_code=response.status,
            headers=response.headers,
            stream=_ResponseStream(
                response.stream,
                request=request,
            ),
            extensions=response.extensions,
        )

    def close(self) -> None:
        self._pool.close()
