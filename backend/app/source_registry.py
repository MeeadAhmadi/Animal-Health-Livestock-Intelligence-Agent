from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source

SUPPORTED_COLLECTOR_TYPES = frozenset({"http"})


class UnsupportedCollectorTypeError(ValueError):
    pass


def validate_collector_type(collector_type: str) -> None:
    if collector_type not in SUPPORTED_COLLECTOR_TYPES:
        raise UnsupportedCollectorTypeError(
            f"Unsupported collector type: {collector_type!r}"
        )


def register_source(
    db: Session,
    *,
    name: str,
    entry_url: str,
    collector_type: str,
    is_enabled: bool = True,
) -> Source:
    validate_collector_type(collector_type)

    source = Source(
        name=name,
        entry_url=entry_url,
        collector_type=collector_type,
        is_enabled=is_enabled,
    )

    db.add(source)
    db.flush()

    return source


def get_source(db: Session, source_id: int) -> Source | None:
    return db.get(Source, source_id)


def list_enabled_sources(db: Session) -> list[Source]:
    statement = (
        select(Source)
        .where(Source.is_enabled.is_(True))
        .order_by(Source.id)
    )

    return list(db.scalars(statement))


def set_source_enabled(
    db: Session,
    *,
    source: Source,
    is_enabled: bool,
) -> None:
    source.is_enabled = is_enabled
    db.flush()
