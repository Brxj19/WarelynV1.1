"""phase 18 operational completion tables

Revision ID: 20260525_0014
Revises: 20260525_0013
Create Date: 2026-05-25 14:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260525_0014"
down_revision: str | None = "20260525_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 18.1 Stock State Expansion
    op.add_column("warehouse_stock", sa.Column("quantity_in_transit", sa.Numeric(15, 4), server_default="0.0000", nullable=False))
    op.add_column("warehouse_stock", sa.Column("quantity_qc_hold", sa.Numeric(15, 4), server_default="0.0000", nullable=False))
    op.add_column("warehouse_stock", sa.Column("quantity_damaged", sa.Numeric(15, 4), server_default="0.0000", nullable=False))
    op.add_column("warehouse_stock", sa.Column("quantity_expired", sa.Numeric(15, 4), server_default="0.0000", nullable=False))
    op.add_column("warehouse_stock", sa.Column("quantity_quarantine", sa.Numeric(15, 4), server_default="0.0000", nullable=False))

    # 18.2 Reorder Rules
    op.create_table(
        "reorder_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("min_quantity", sa.Numeric(15, 4), nullable=False),
        sa.Column("max_quantity", sa.Numeric(15, 4), nullable=False),
        sa.Column("safety_stock", sa.Numeric(15, 4), server_default="0.0000", nullable=False),
        sa.Column("lead_time_days", sa.Integer(), server_default="0", nullable=False),
        sa.Column("auto_create_po", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "product_id", "warehouse_id", name="uq_reorder_rules_dimension"),
    )
    op.create_index("ix_reorder_rules_tenant", "reorder_rules", ["tenant_id"])

    # 18.3 Putaway Tasks
    op.create_table(
        "putaway_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("from_location_id", sa.Integer(), nullable=False),
        sa.Column("to_location_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(15, 4), nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("receipt_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["from_location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["to_location_id"], ["warehouse_locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["receipt_id"], ["purchase_receipts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_putaway_tasks_tenant", "putaway_tasks", ["tenant_id"])
    op.create_index("ix_putaway_tasks_status", "putaway_tasks", ["tenant_id", "status"])

    # 18.4 Cycle Counts
    op.create_table(
        "stock_count_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("session_number", sa.String(120), nullable=False),
        sa.Column("status", sa.String(20), server_default="DRAFT", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "session_number", name="uq_stock_count_sessions_number"),
    )
    op.create_index("ix_stock_count_sessions_tenant", "stock_count_sessions", ["tenant_id"])

    op.create_table(
        "stock_count_lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("system_quantity", sa.Numeric(15, 4), nullable=False),
        sa.Column("counted_quantity", sa.Numeric(15, 4), nullable=True),
        sa.Column("variance", sa.Numeric(15, 4), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["stock_count_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_count_lines_session", "stock_count_lines", ["session_id"])

    # 18.6 Outbox Events
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(120), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), server_default="PENDING", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbox_events_status", "outbox_events", ["status"])


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("stock_count_lines")
    op.drop_table("stock_count_sessions")
    op.drop_table("putaway_tasks")
    op.drop_table("reorder_rules")
    op.drop_column("warehouse_stock", "quantity_quarantine")
    op.drop_column("warehouse_stock", "quantity_expired")
    op.drop_column("warehouse_stock", "quantity_damaged")
    op.drop_column("warehouse_stock", "quantity_qc_hold")
    op.drop_column("warehouse_stock", "quantity_in_transit")
