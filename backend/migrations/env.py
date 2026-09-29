from logging.config import fileConfig
from pathlib import Path

from alembic import context
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine, pool, text
from sqlalchemy.engine import URL

from app.db_base import APP_SCHEMA, Base

BACKEND_DIR = Path(__file__).resolve().parents[1]

EXPECTED_MIGRATION_ROLE = "li_migrate"
EXPECTED_DATABASE = "li_core"
OWNER_ROLE = "li_owner"

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


class MigrationSettings(BaseSettings):
    db_host: str
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str
    db_user: str
    db_password: SecretStr

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env.migrate",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def include_name(
    name: str | None,
    type_: str,
    parent_names: dict[str, str | None],
) -> bool:
    if type_ == "schema":
        return name == APP_SCHEMA

    if type_ == "table":
        return parent_names.get("schema_name") == APP_SCHEMA

    return True


def run_migrations_offline() -> None:
    context.configure(
        url="postgresql+psycopg://",
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        version_table_schema=APP_SCHEMA,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    settings = MigrationSettings()

    if settings.db_user != EXPECTED_MIGRATION_ROLE:
        raise RuntimeError(
            f"Alembic must connect as {EXPECTED_MIGRATION_ROLE!r}, "
            f"not {settings.db_user!r}."
        )

    if settings.db_name != EXPECTED_DATABASE:
        raise RuntimeError(
            f"Alembic must target database {EXPECTED_DATABASE!r}, "
            f"not {settings.db_name!r}."
        )

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
    )

    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
        hide_parameters=True,
    )

    with connectable.connect() as connection:
        session_user, database_name = connection.execute(
            text("SELECT session_user, current_database()")
        ).one()

        if session_user != EXPECTED_MIGRATION_ROLE:
            raise RuntimeError(
                f"Unexpected migration session user: {session_user!r}."
            )

        if database_name != EXPECTED_DATABASE:
            raise RuntimeError(
                f"Unexpected migration database: {database_name!r}."
            )

        connection.exec_driver_sql("SET ROLE li_owner")

        current_user = connection.scalar(text("SELECT current_user"))

        if current_user != OWNER_ROLE:
            raise RuntimeError(
                f"Failed to activate migration owner role {OWNER_ROLE!r}."
            )

        # Persist the session-level SET ROLE before Alembic starts
        # its migration transaction.
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            version_table_schema=APP_SCHEMA,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()