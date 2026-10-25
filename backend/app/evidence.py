from __future__ import annotations

import hashlib
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.evidence_record import EvidenceRecord


def build_technical_dedup_key(
    *,
    external_id: str | None,
    source_url: str,
    raw_content: str,
) -> str:
    if external_id:
        identity = f"external_id:{external_id}"
    elif source_url:
        identity = f"source_url:{source_url}"
    else:
        identity = "content_only"

    payload = f"{identity}\0{raw_content}"

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def store_evidence(
    db: Session,
    *,
    source_id: int,
    collection_attempt_id: int,
    source_url: str,
    raw_content: str,
    external_id: str | None = None,
    title: str | None = None,
    content_type: str | None = None,
    source_published_at: datetime | None = None,
    source_updated_at: datetime | None = None,
) -> tuple[EvidenceRecord, bool]:
    technical_dedup_key = build_technical_dedup_key(
        external_id=external_id,
        source_url=source_url,
        raw_content=raw_content,
    )

    record = EvidenceRecord(
        source_id=source_id,
        collection_attempt_id=collection_attempt_id,
        external_id=external_id,
        source_url=source_url,
        title=title,
        raw_content=raw_content,
        content_type=content_type,
        source_published_at=source_published_at,
        source_updated_at=source_updated_at,
        technical_dedup_key=technical_dedup_key,
    )

    try:
        with db.begin_nested():
            db.add(record)
            db.flush()
    except IntegrityError:
        statement = select(EvidenceRecord).where(
            EvidenceRecord.source_id == source_id,
            EvidenceRecord.technical_dedup_key == technical_dedup_key,
        )
        existing = db.scalar(statement)

        if existing is None:
            raise

        return existing, False

    return record, True
