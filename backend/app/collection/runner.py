from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.collection.http_fetcher import FetchLimits
from app.collection.orchestrator import CollectionResult, collect_source
from app.source_registry import list_enabled_sources

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CollectionBatchResult:
    total_sources: int
    succeeded: int
    failed: int
    results: tuple[CollectionResult, ...]


def collect_enabled_sources(
    db: Session,
    *,
    limits: FetchLimits,
) -> CollectionBatchResult:
    sources = list_enabled_sources(db)

    results: list[CollectionResult] = []
    failed = 0

    for source in sources:
        try:
            result = collect_source(
                db,
                source=source,
                limits=limits,
            )
        except Exception:
            failed += 1

            logger.exception(
                "Source collection failed during batch execution",
                extra={
                    "source_id": source.id,
                    "collection_status": "failed",
                },
            )

            continue

        results.append(result)

    return CollectionBatchResult(
        total_sources=len(sources),
        succeeded=len(results),
        failed=failed,
        results=tuple(results),
    )
