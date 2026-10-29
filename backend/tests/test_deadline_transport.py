import httpcore
import httpx
import pytest

from app.collection.deadline_transport import (
    DeadlineHTTPTransport,
    TransportDeadlineExceededError,
)


def test_deadline_transport_stops_slow_response_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = {"now": 0.0}

    def fake_monotonic() -> float:
        return clock["now"]

    class SlowHeaderStream(httpcore.NetworkStream):
        def __init__(self) -> None:
            self.read_count = 0

        def read(
            self,
            max_bytes: int,
            timeout: float | None = None,
        ) -> bytes:
            self.read_count += 1
            clock["now"] += 0.6

            if self.read_count == 1:
                return b"HTTP/1.1 200 OK\r\n"

            return b"Content-Length: 0\r\n\r\n"

        def write(
            self,
            buffer: bytes,
            timeout: float | None = None,
        ) -> None:
            return None

        def close(self) -> None:
            return None

        def start_tls(
            self,
            ssl_context,
            server_hostname: str | None = None,
            timeout: float | None = None,
        ) -> httpcore.NetworkStream:
            raise AssertionError("TLS is not expected in this test.")

        def get_extra_info(self, info: str):
            return None

    class FakeBackend(httpcore.NetworkBackend):
        def connect_tcp(
            self,
            host: str,
            port: int,
            timeout: float | None = None,
            local_address: str | None = None,
            socket_options=None,
        ) -> httpcore.NetworkStream:
            return SlowHeaderStream()

        def connect_unix_socket(
            self,
            path: str,
            timeout: float | None = None,
            socket_options=None,
        ) -> httpcore.NetworkStream:
            raise AssertionError("Unix sockets are not expected in this test.")

        def sleep(self, seconds: float) -> None:
            clock["now"] += seconds

    monkeypatch.setattr(
        "app.collection.deadline_transport.time.monotonic",
        fake_monotonic,
    )
    monkeypatch.setattr(
        httpcore,
        "SyncBackend",
        FakeBackend,
    )

    transport = DeadlineHTTPTransport(deadline=1.0)

    with httpx.Client(
        transport=transport,
        timeout=httpx.Timeout(5.0),
    ) as client, pytest.raises(TransportDeadlineExceededError):
        client.get("http://8.8.8.8/")
