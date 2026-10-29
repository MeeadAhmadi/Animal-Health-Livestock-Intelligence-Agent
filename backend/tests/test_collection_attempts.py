from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.collection_attempts import (
    mark_collection_failed,
    mark_collection_no_usable_item,
    mark_collection_succeeded,
    start_collection_attempt,
)
from app.db_base import APP_SCHEMA, Base
from app.models.source import Source


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:").execution_options(
        schema_translate_map={APP_SCHEMA: None},
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def create_source(db: Session) -> Source:
    source = Source(
        name="Example Source",
        entry_url="https://example.com/feed",
        collector_type="http",
    )
    db.add(source)
    db.flush()
    return source


def test_start_collection_attempt() -> None:
    with build_session() as db:
        source = create_source(db)

        attempt = start_collection_attempt(
            db,
            source_id=source.id,
        )

        assert attempt.id is not None
        assert attempt.status == "running"
        assert attempt.completed_at is None
        assert attempt.failure_code is None


def test_mark_collection_succeeded() -> None:
    with build_session() as db:
        source = create_source(db)
        attempt = start_collection_attempt(db, source_id=source.id)

        mark_collection_succeeded(
            db,
            attempt=attempt,
        )

        assert attempt.status == "succeeded"
        assert attempt.completed_at is not None
        assert attempt.failure_code is None


def test_mark_collection_no_usable_item() -> None:
    with build_session() as db:
        source = create_source(db)
        attempt = start_collection_attempt(db, source_id=source.id)

        mark_collection_no_usable_item(
            db,
            attempt=attempt,
        )

        assert attempt.status == "no_usable_item"
        assert attempt.completed_at is not None
        assert attempt.failure_code is None


def test_mark_collection_failed() -> None:
    with build_session() as db:
        source = create_source(db)
        attempt = start_collection_attempt(db, source_id=source.id)

        mark_collection_failed(
            db,
            attempt=attempt,
            failure_code="http_timeout",
        )

        assert attempt.status == "failed"
        assert attempt.completed_at is not None
        assert attempt.failure_code == "http_timeout"


def test_mark_collection_failed_requires_failure_code() -> None:
    with build_session() as db:
        source = create_source(db)
        attempt = start_collection_attempt(db, source_id=source.id)

        try:
            mark_collection_failed(
                db,
                attempt=attempt,
                failure_code="",
            )
        except ValueError as exc:
            assert str(exc) == "failure_code must be non-empty."
        else:
            raise AssertionError("Expected ValueError.")
