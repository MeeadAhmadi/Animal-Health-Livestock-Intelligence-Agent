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
