"""add pdf_bytes column to invoices and bills

Revision ID: 20260525_0015
Revises: 20260525_0014
Create Date: 2026-05-25 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260525_0015"
down_revision: str | None = "20260525_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("pdf_bytes", sa.LargeBinary(), nullable=True))
    op.add_column("bills", sa.Column("pdf_bytes", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("bills", "pdf_bytes")
    op.drop_column("invoices", "pdf_bytes")
