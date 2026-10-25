from app.collection.runtime import build_fetch_limits
from app.config import Settings


def test_build_fetch_limits_from_settings() -> None:
    settings = Settings(
        _env_file=None,
        db_host="127.0.0.1",
        db_name="li_core",
        db_user="li_app",
        db_password="test-password",
        collection_connect_timeout_seconds=10,
        collection_read_timeout_seconds=15,
        collection_max_redirects=5,
        collection_max_response_bytes=5_242_880,
    )

    limits = build_fetch_limits(settings)

    assert limits.connect_timeout_seconds == 10
    assert limits.read_timeout_seconds == 15
    assert limits.max_redirects == 5
    assert limits.max_response_bytes == 5_242_880
