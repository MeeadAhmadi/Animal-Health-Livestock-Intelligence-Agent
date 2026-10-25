from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.collection.http_fetcher import FetchLimits
from app.collection.orchestrator import CollectionResult
from app.collection.runner import collect_enabled_sources
from app.db_base import APP_SCHEMA, Base
from app.models.source import Source


def build_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:").execution_options(
        schema_translate_map={APP_SCHEMA: None},
    )
    Base.metadata.create_all(engine)
    return Session(engine)


def build_limits() -> FetchLimits:
    return FetchLimits(
        connect_timeout_seconds=10,
        read_timeout_seconds=15,
        max_redirects=5,
        max_response_bytes=5_242_880,
    )


def create_source(
    db: Session,
    *,
    name: str,
    is_enabled: bool = True,
) -> Source:
    source = Source(
        name=name,
        entry_url=f"https://example.com/{name}",
        collector_type="http",
        is_enabled=is_enabled,
    )
    db.add(source)
    db.flush()
    return source


def test_collect_enabled_sources_isolates_failures(
    monkeypatch,
) -> None:
    with build_session() as db:
        first = create_source(db, name="first")
        second = create_source(db, name="second")
        disabled = create_source(
            db,
            name="disabled",
            is_enabled=False,
        )
        db.commit()

        called_source_ids: list[int] = []

        def fake_collect_source(
            db: Session,
            *,
            source: Source,
            limits: FetchLimits,
        ) -> CollectionResult:
            called_source_ids.append(source.id)

            if source.id == first.id:
                raise RuntimeError("simulated failure")

            return CollectionResult(
                attempt_id=200,
                evidence_id=300,
                evidence_created=True,
                status="succeeded",
            )

        monkeypatch.setattr(
            "app.collection.runner.collect_source",
            fake_collect_source,
        )

        result = collect_enabled_sources(
            db,
            limits=build_limits(),
        )

        assert called_source_ids == [first.id, second.id]
        assert disabled.id not in called_source_ids

        assert result.total_sources == 2
        assert result.succeeded == 1
        assert result.failed == 1
        assert len(result.results) == 1
        assert result.results[0].status == "succeeded"


def test_collect_enabled_sources_returns_empty_result_when_none_enabled(
    monkeypatch,
) -> None:
    with build_session() as db:
        create_source(
            db,
            name="disabled",
            is_enabled=False,
        )
        db.commit()

        def fail_if_called(*args, **kwargs):
            raise AssertionError("collect_source must not be called.")

        monkeypatch.setattr(
            "app.collection.runner.collect_source",
            fail_if_called,
        )

        result = collect_enabled_sources(
            db,
            limits=build_limits(),
        )

        assert result.total_sources == 0
        assert result.succeeded == 0
        assert result.failed == 0
        assert result.results == ()
