"""phase1 database baseline

Revision ID: e067b5c4eb30
Revises:
Create Date: 2026-09-23 15:57:27.459768

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'e067b5c4eb30'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
