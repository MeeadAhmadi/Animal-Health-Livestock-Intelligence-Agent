from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db_base import Base


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "technical_dedup_key",
            name="uq_evidence_records_source_dedup_key",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    source_id: Mapped[int] = mapped_column(
        ForeignKey("app.sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    collection_attempt_id: Mapped[int] = mapped_column(
        ForeignKey("app.collection_attempts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    raw_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    content_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    technical_dedup_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
