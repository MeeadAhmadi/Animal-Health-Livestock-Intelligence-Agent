from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.collection_attempt import CollectionAttempt


def start_collection_attempt(
    db: Session,
    *,
    source_id: int,
) -> CollectionAttempt:
    attempt = CollectionAttempt(
        source_id=source_id,
        status="running",
    )

    db.add(attempt)
    db.flush()

    return attempt


def mark_collection_succeeded(
    db: Session,
    *,
    attempt: CollectionAttempt,
) -> None:
    attempt.status = "succeeded"
    attempt.completed_at = datetime.now(UTC)
    attempt.failure_code = None
    db.flush()


def mark_collection_no_usable_item(
    db: Session,
    *,
    attempt: CollectionAttempt,
) -> None:
    attempt.status = "no_usable_item"
    attempt.completed_at = datetime.now(UTC)
    attempt.failure_code = None
    db.flush()


def mark_collection_failed(
    db: Session,
    *,
    attempt: CollectionAttempt,
    failure_code: str,
) -> None:
    if not failure_code:
        raise ValueError("failure_code must be non-empty.")

    attempt.status = "failed"
    attempt.completed_at = datetime.now(UTC)
    attempt.failure_code = failure_code
    db.flush()
