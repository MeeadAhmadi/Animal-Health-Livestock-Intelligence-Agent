from app.collection.http_fetcher import FetchLimits
from app.config import Settings


def build_fetch_limits(settings: Settings) -> FetchLimits:
    return FetchLimits(
        connect_timeout_seconds=settings.collection_connect_timeout_seconds,
        read_timeout_seconds=settings.collection_read_timeout_seconds,
        max_redirects=settings.collection_max_redirects,
        max_response_bytes=settings.collection_max_response_bytes,
    )
