"""Grant Phase 2 runtime permissions

Revision ID: 3c5ef3b52d3a
Revises: 24bdc9be06f6
Create Date: 2026-10-25 10:07:22.787501

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c5ef3b52d3a"
down_revision: str | Sequence[str] | None = "24bdc9be06f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Grant the runtime role the minimum Phase 2 data privileges."""
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE
        ON TABLE
            app.sources,
            app.collection_attempts,
            app.evidence_records
        TO li_app
        """
    )

    op.execute(
        """
        GRANT USAGE, SELECT
        ON SEQUENCE
            app.sources_id_seq,
            app.collection_attempts_id_seq,
            app.evidence_records_id_seq
        TO li_app
        """
    )


def downgrade() -> None:
    """Revoke the Phase 2 runtime privileges."""
    op.execute(
        """
        REVOKE USAGE, SELECT
        ON SEQUENCE
            app.sources_id_seq,
            app.collection_attempts_id_seq,
            app.evidence_records_id_seq
        FROM li_app
        """
    )

    op.execute(
        """
        REVOKE SELECT, INSERT, UPDATE
        ON TABLE
            app.sources,
            app.collection_attempts,
            app.evidence_records
        FROM li_app
        """
    )
