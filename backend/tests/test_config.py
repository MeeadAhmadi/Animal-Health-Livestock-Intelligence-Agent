import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_fail_when_database_config_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required_database_env_vars = (
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    )

    for env_var in required_database_env_vars:
        monkeypatch.delenv(env_var, raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_collection_safety_defaults() -> None:
    settings = Settings(
        _env_file=None,
        db_host="127.0.0.1",
        db_name="li_core",
        db_user="li_app",
        db_password="test-password",
    )

    assert settings.collection_connect_timeout_seconds == 10.0
    assert settings.collection_read_timeout_seconds == 15.0
    assert settings.collection_total_timeout_seconds == 60.0
    assert settings.collection_max_redirects == 5
    assert settings.collection_max_response_bytes == 5_242_880


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("collection_connect_timeout_seconds", 0),
        ("collection_read_timeout_seconds", 0),
        ("collection_total_timeout_seconds", 0),
        ("collection_max_redirects", -1),
        ("collection_max_response_bytes", 0),
    ],
)
def test_collection_safety_limits_reject_invalid_values(
    field_name: str,
    invalid_value: int,
) -> None:
    values = {
        "db_host": "127.0.0.1",
        "db_name": "li_core",
        "db_user": "li_app",
        "db_password": "test-password",
        field_name: invalid_value,
    }

    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)
