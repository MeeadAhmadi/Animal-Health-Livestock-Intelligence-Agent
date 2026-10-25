from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.collection.http_fetcher import (
    FetchLimits,
    HttpStatusError,
    RedirectLocationError,
    ResponseTooLargeError,
    TooManyRedirectsError,
    fetch_url,
)
from app.collection.url_safety import UnsafeUrlError
from app.collection_attempts import (
    mark_collection_failed,
    mark_collection_no_usable_item,
    mark_collection_succeeded,
    start_collection_attempt,
)
from app.evidence import store_evidence
from app.models.collection_attempt import CollectionAttempt
from app.models.source import Source
from app.source_registry import (
    UnsupportedCollectorTypeError,
    validate_collector_type,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CollectionResult:
    attempt_id: int
    evidence_id: int | None
    evidence_created: bool
    status: str


def _failure_code(exc: Exception) -> str:
    if isinstance(exc, UnsupportedCollectorTypeError):
        return "unsupported_collector_type"

    if isinstance(exc, UnsafeUrlError):
        return "unsafe_url"

    if isinstance(exc, TooManyRedirectsError):
        return "too_many_redirects"

    if isinstance(exc, ResponseTooLargeError):
        return "response_too_large"

    if isinstance(exc, RedirectLocationError):
        return "invalid_redirect"

    if isinstance(exc, HttpStatusError):
        return "http_status"

    if isinstance(exc, httpx.TimeoutException):
        return "http_timeout"

    if isinstance(exc, httpx.RequestError):
        return "http_request_error"

    return "unexpected_error"


def _decode_content(content: bytes, content_type: str | None) -> str:
    charset = "utf-8"

    if content_type:
        for part in content_type.split(";")[1:]:
            key, separator, value = part.strip().partition("=")

            if separator and key.lower() == "charset":
                candidate = value.strip().strip("\"'")

                if candidate:
                    charset = candidate
                break

    try:
        return content.decode(charset)
    except (LookupError, UnicodeDecodeError):
        return content.decode("utf-8", errors="replace")


def _record_failure(
    db: Session,
    *,
    attempt_id: int,
    failure_code: str,
) -> None:
    db.rollback()

    attempt = db.get(CollectionAttempt, attempt_id)

    if attempt is None:
        raise RuntimeError(
            f"Collection attempt {attempt_id} could not be reloaded after failure."
        )

    mark_collection_failed(
        db,
        attempt=attempt,
        failure_code=failure_code,
    )
    db.commit()


def collect_source(
    db: Session,
    *,
    source: Source,
    limits: FetchLimits,
) -> CollectionResult:
    if not source.is_enabled:
        raise ValueError("Disabled sources cannot be collected.")

    attempt = start_collection_attempt(
        db,
        source_id=source.id,
    )

    db.commit()
    attempt_id = attempt.id

    logger.info(
        "Collection started",
        extra={
            "source_id": source.id,
            "collection_attempt_id": attempt_id,
            "collection_status": "running",
        },
    )

    try:
        validate_collector_type(source.collector_type)

        fetch_result = fetch_url(
            source.entry_url,
            limits=limits,
        )

        raw_content = _decode_content(
            fetch_result.content,
            fetch_result.content_type,
        )

        if not raw_content.strip():
            attempt = db.get(CollectionAttempt, attempt_id)

            if attempt is None:
                raise RuntimeError(
                    f"Collection attempt {attempt_id} could not be reloaded."
                )

            mark_collection_no_usable_item(
                db,
                attempt=attempt,
            )
            db.commit()

            logger.info(
                "Collection completed with no usable item",
                extra={
                    "source_id": source.id,
                    "collection_attempt_id": attempt_id,
                    "collection_status": "no_usable_item",
                },
            )

            return CollectionResult(
                attempt_id=attempt_id,
                evidence_id=None,
                evidence_created=False,
                status="no_usable_item",
            )

        record, created = store_evidence(
            db,
            source_id=source.id,
            collection_attempt_id=attempt_id,
            source_url=fetch_result.final_url,
            raw_content=raw_content,
            content_type=fetch_result.content_type,
        )

        attempt = db.get(CollectionAttempt, attempt_id)

        if attempt is None:
            raise RuntimeError(
                f"Collection attempt {attempt_id} could not be reloaded."
            )

        mark_collection_succeeded(
            db,
            attempt=attempt,
        )
        db.commit()

        logger.info(
            "Collection succeeded",
            extra={
                "source_id": source.id,
                "collection_attempt_id": attempt_id,
                "evidence_id": record.id,
                "collection_status": "succeeded",
                "evidence_created": created,
            },
        )

        return CollectionResult(
            attempt_id=attempt_id,
            evidence_id=record.id,
            evidence_created=created,
            status="succeeded",
        )

    except Exception as exc:
        failure_code = _failure_code(exc)

        _record_failure(
            db,
            attempt_id=attempt_id,
            failure_code=failure_code,
        )

        logger.error(
            "Collection failed",
            extra={
                "source_id": source.id,
                "collection_attempt_id": attempt_id,
                "collection_status": "failed",
                "failure_code": failure_code,
            },
        )

        raise
