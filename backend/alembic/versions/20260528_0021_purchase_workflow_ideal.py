"""Add APPROVED status, approved_at, grn_number, GRN sequence key

Revision ID: 20260528_0021
Revises: 20260528_0020
Create Date: 2026-05-28
"""
import sqlalchemy as sa
from alembic import op

revision = "20260528_0021"
down_revision = "20260528_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("purchase_orders", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("purchase_receipts", sa.Column("grn_number", sa.String(120), nullable=True, index=True))


def downgrade() -> None:
    op.drop_column("purchase_receipts", "grn_number")
    op.drop_column("purchase_orders", "approved_at")
