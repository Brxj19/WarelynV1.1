"""return qc blocked stock foundation

Revision ID: 20260521_0009
Revises: 20260521_0008
Create Date: 2026-05-21 00:09:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260521_0009"
down_revision: str | None = "20260521_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sales_returns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=False),
        sa.Column("return_number", sa.String(length=120), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "SUBMITTED", "INSPECTION_PENDING", "PARTIALLY_PROCESSED", "PROCESSED", "CANCELLED", name="sales_return_status", native_enum=False), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "return_number", name="uq_sales_returns_tenant_number"),
    )
    for column in ["id", "tenant_id", "sales_order_id", "return_number", "status", "created_by", "created_at"]:
        op.create_index(op.f(f"ix_sales_returns_{column}"), "sales_returns", [column])

    op.create_table(
        "sales_return_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sales_return_id", sa.Integer(), nullable=False),
        sa.Column("sales_order_item_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("serial_id", sa.Integer(), nullable=True),
        sa.Column("returned_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("accepted_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("rejected_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("qc_status", sa.Enum("PENDING", "ACCEPTED_RESTOCK", "ACCEPTED_BLOCKED", "DAMAGED", "SCRAPPED", "REJECTED", name="sales_return_item_status", native_enum=False), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("accepted_quantity >= 0", name="ck_sales_return_items_accepted_non_negative"),
        sa.CheckConstraint("accepted_quantity + rejected_quantity <= returned_quantity", name="ck_sales_return_items_qc_lte_returned"),
        sa.CheckConstraint("rejected_quantity >= 0", name="ck_sales_return_items_rejected_non_negative"),
        sa.CheckConstraint("returned_quantity > 0", name="ck_sales_return_items_returned_positive"),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_order_item_id"], ["sales_order_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_return_id"], ["sales_returns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["serial_id"], ["inventory_serials.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "sales_return_id", "sales_order_item_id", "product_id", "warehouse_id", "location_id", "batch_id", "serial_id", "qc_status", "created_at"]:
        op.create_index(op.f(f"ix_sales_return_items_{column}"), "sales_return_items", [column])

    op.create_table(
        "return_qc_inspections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sales_return_id", sa.Integer(), nullable=False),
        sa.Column("inspected_by", sa.Integer(), nullable=True),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["inspected_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sales_return_id"], ["sales_returns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "sales_return_id", "inspected_by", "inspected_at", "created_at"]:
        op.create_index(op.f(f"ix_return_qc_inspections_{column}"), "return_qc_inspections", [column])

    op.create_table(
        "blocked_return_stock",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sales_return_id", sa.Integer(), nullable=False),
        sa.Column("sales_return_item_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("serial_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("status", sa.Enum("QC_HOLD", "QUARANTINE", "DAMAGED", "SCRAPPED", name="blocked_return_stock_status", native_enum=False), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_blocked_return_stock_quantity_positive"),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_return_id"], ["sales_returns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sales_return_item_id"], ["sales_return_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["serial_id"], ["inventory_serials.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "sales_return_id", "sales_return_item_id", "product_id", "warehouse_id", "location_id", "batch_id", "serial_id", "status", "created_at"]:
        op.create_index(op.f(f"ix_blocked_return_stock_{column}"), "blocked_return_stock", [column])


def downgrade() -> None:
    op.drop_table("blocked_return_stock")
    op.drop_table("return_qc_inspections")
    op.drop_table("sales_return_items")
    op.drop_table("sales_returns")
