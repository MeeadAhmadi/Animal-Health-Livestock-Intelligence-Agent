import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db_base import APP_SCHEMA, Base
from app.source_registry import (
    UnsupportedCollectorTypeError,
    get_source,
    list_enabled_sources,
    register_source,
    set_source_enabled,
)


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:").execution_options(
        schema_translate_map={APP_SCHEMA: None},
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def test_register_and_get_source() -> None:
    with build_session() as db:
        source = register_source(
            db,
            name="Example Source",
            entry_url="https://example.com/feed",
            collector_type="http",
        )
        db.commit()

        loaded = get_source(db, source.id)

        assert loaded is not None
        assert loaded.name == "Example Source"
        assert loaded.entry_url == "https://example.com/feed"
        assert loaded.collector_type == "http"
        assert loaded.is_enabled is True


def test_list_enabled_sources_only_returns_enabled() -> None:
    with build_session() as db:
        first = register_source(
            db,
            name="Enabled Source",
            entry_url="https://example.com/enabled",
            collector_type="http",
        )
        second = register_source(
            db,
            name="Disabled Source",
            entry_url="https://example.com/disabled",
            collector_type="http",
            is_enabled=False,
        )
        db.commit()

        sources = list_enabled_sources(db)

        assert [source.id for source in sources] == [first.id]
        assert second.id not in [source.id for source in sources]


def test_set_source_enabled_updates_state() -> None:
    with build_session() as db:
        source = register_source(
            db,
            name="Example Source",
            entry_url="https://example.com/feed",
            collector_type="http",
        )

        set_source_enabled(
            db,
            source=source,
            is_enabled=False,
        )
        db.commit()

        loaded = get_source(db, source.id)

        assert loaded is not None
        assert loaded.is_enabled is False



def test_register_source_rejects_unsupported_collector_type() -> None:
    with build_session() as db, pytest.raises(UnsupportedCollectorTypeError):
        register_source(
            db,
            name="Unsupported Source",
            entry_url="https://example.com/feed",
            collector_type="rss",
        )
