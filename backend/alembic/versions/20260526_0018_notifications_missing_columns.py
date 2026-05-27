"""Add action_url, priority, cleared_at to notifications table

Revision ID: 20260526_0018
Revises: 20260526_0017
Create Date: 2026-05-26
"""
import sqlalchemy as sa
from alembic import op

revision = "20260526_0018"
down_revision = "20260526_0017"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("notifications", sa.Column("action_url", sa.String(500), nullable=True))
    op.add_column("notifications", sa.Column("priority", sa.String(50), nullable=False, server_default="normal"))
    op.add_column("notifications", sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("notifications", "cleared_at")
    op.drop_column("notifications", "priority")
    op.drop_column("notifications", "action_url")
