from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db_base import Base


class CollectionAttempt(Base):
    __tablename__ = "collection_attempts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('running', 'succeeded', 'no_usable_item', 'failed')",
            name="ck_collection_attempts_status",
        ),
        CheckConstraint(
            "(status = 'running' AND completed_at IS NULL) "
            "OR (status <> 'running' AND completed_at IS NOT NULL)",
            name="ck_collection_attempts_completion_state",
        ),
        CheckConstraint(
            "(status = 'failed' AND failure_code IS NOT NULL) "
            "OR (status <> 'failed' AND failure_code IS NULL)",
            name="ck_collection_attempts_failure_state",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("app.sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="running",
        server_default="running",
    )
    failure_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
