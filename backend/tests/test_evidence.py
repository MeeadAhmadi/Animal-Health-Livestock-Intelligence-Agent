from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.collection_attempts import start_collection_attempt
from app.db_base import APP_SCHEMA, Base
from app.evidence import build_technical_dedup_key, store_evidence
from app.models.evidence_record import EvidenceRecord
from app.models.source import Source


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:").execution_options(
        schema_translate_map={APP_SCHEMA: None},
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def create_source(
    db: Session,
    *,
    name: str,
    entry_url: str,
) -> Source:
    source = Source(
        name=name,
        entry_url=entry_url,
        collector_type="http",
    )
    db.add(source)
    db.flush()
    return source


def test_build_technical_dedup_key_changes_when_content_changes() -> None:
    first = build_technical_dedup_key(
        external_id="article-123",
        source_url="https://example.com/a",
        raw_content="first version",
    )
    second = build_technical_dedup_key(
        external_id="article-123",
        source_url="https://example.com/a",
        raw_content="second version",
    )

    assert first != second


def test_store_evidence_creates_new_record() -> None:
    with build_session() as db:
        source = create_source(
            db,
            name="Example Source",
            entry_url="https://example.com/feed",
        )
        attempt = start_collection_attempt(db, source_id=source.id)

        record, created = store_evidence(
            db,
            source_id=source.id,
            collection_attempt_id=attempt.id,
            external_id="article-1",
            source_url="https://example.com/article-1",
            raw_content="Original content",
            title="Example Article",
            content_type="text/html",
        )

        assert created is True
        assert record.id is not None
        assert record.source_id == source.id
        assert record.external_id == "article-1"


def test_same_source_exact_duplicate_is_not_inserted_twice() -> None:
    with build_session() as db:
        source = create_source(
            db,
            name="Example Source",
            entry_url="https://example.com/feed",
        )
        first_attempt = start_collection_attempt(db, source_id=source.id)
        second_attempt = start_collection_attempt(db, source_id=source.id)

        first_record, first_created = store_evidence(
            db,
            source_id=source.id,
            collection_attempt_id=first_attempt.id,
            external_id="article-1",
            source_url="https://example.com/article-1",
            raw_content="Same collected version",
        )

        second_record, second_created = store_evidence(
            db,
            source_id=source.id,
            collection_attempt_id=second_attempt.id,
            external_id="article-1",
            source_url="https://example.com/article-1",
            raw_content="Same collected version",
        )

        records = list(db.scalars(select(EvidenceRecord)))

        assert first_created is True
        assert second_created is False
        assert second_record.id == first_record.id
        assert len(records) == 1


def test_same_source_updated_content_is_preserved_as_new_evidence() -> None:
    with build_session() as db:
        source = create_source(
            db,
            name="Example Source",
            entry_url="https://example.com/feed",
        )
        first_attempt = start_collection_attempt(db, source_id=source.id)
        second_attempt = start_collection_attempt(db, source_id=source.id)

        first_record, first_created = store_evidence(
            db,
            source_id=source.id,
            collection_attempt_id=first_attempt.id,
            external_id="article-1",
            source_url="https://example.com/article-1",
            raw_content="First collected version",
        )

        second_record, second_created = store_evidence(
            db,
            source_id=source.id,
            collection_attempt_id=second_attempt.id,
            external_id="article-1",
            source_url="https://example.com/article-1",
            raw_content="Updated collected version",
        )

        records = list(db.scalars(select(EvidenceRecord)))

        assert first_created is True
        assert second_created is True
        assert first_record.id != second_record.id
        assert len(records) == 2


def test_same_evidence_from_different_sources_is_preserved() -> None:
    with build_session() as db:
        source_a = create_source(
            db,
            name="Source A",
            entry_url="https://a.example.com/feed",
        )
        source_b = create_source(
            db,
            name="Source B",
            entry_url="https://b.example.com/feed",
        )

        attempt_a = start_collection_attempt(db, source_id=source_a.id)
        attempt_b = start_collection_attempt(db, source_id=source_b.id)

        record_a, created_a = store_evidence(
            db,
            source_id=source_a.id,
            collection_attempt_id=attempt_a.id,
            external_id="shared-article",
            source_url="https://a.example.com/article",
            raw_content="Shared story",
        )

        record_b, created_b = store_evidence(
            db,
            source_id=source_b.id,
            collection_attempt_id=attempt_b.id,
            external_id="shared-article",
            source_url="https://b.example.com/article",
            raw_content="Shared story",
        )

        records = list(db.scalars(select(EvidenceRecord)))

        assert created_a is True
        assert created_b is True
        assert record_a.id != record_b.id
        assert len(records) == 2


def test_source_url_identity_still_tracks_content_changes() -> None:
    first = build_technical_dedup_key(
        external_id=None,
        source_url="https://example.com/article",
        raw_content="first version",
    )
    second = build_technical_dedup_key(
        external_id=None,
        source_url="https://example.com/article",
        raw_content="updated version",
    )

    assert first != second
