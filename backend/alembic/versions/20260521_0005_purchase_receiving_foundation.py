"""purchase receiving foundation

Revision ID: 20260521_0005
Revises: 20260521_0004
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260521_0005"
down_revision: str | None = "20260521_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

purchase_order_status = sa.Enum("DRAFT", "SUBMITTED", "PARTIALLY_RECEIVED", "RECEIVED", "CANCELLED", "CLOSED", name="purchase_order_status", native_enum=False)
purchase_receipt_status = sa.Enum("DRAFT", "COMMITTED", "CANCELLED", name="purchase_receipt_status", native_enum=False)


def upgrade() -> None:
    op.alter_column("stock_ledger_entries", "reference_type", existing_type=sa.String(length=14), type_=sa.String(length=16), existing_nullable=False)
    op.alter_column("stock_reservations", "reference_type", existing_type=sa.String(length=14), type_=sa.String(length=16), existing_nullable=False)

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("po_number", sa.String(length=120), nullable=False),
        sa.Column("status", purchase_order_status, nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("expected_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "po_number", name="uq_purchase_orders_tenant_po_number"),
    )
    for column in ["id", "tenant_id", "vendor_id", "po_number", "status", "created_by", "created_at"]:
        op.create_index(op.f(f"ix_purchase_orders_{column}"), "purchase_orders", [column], unique=False)
    op.create_index("ix_purchase_orders_tenant_status", "purchase_orders", ["tenant_id", "status"], unique=False)

    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("ordered_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("received_quantity", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("ordered_quantity > 0", name="ck_purchase_order_items_ordered_positive"),
        sa.CheckConstraint("received_quantity >= 0", name="ck_purchase_order_items_received_non_negative"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_purchase_order_items_unit_cost_non_negative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "purchase_order_id", "product_id", "created_at"]:
        op.create_index(op.f(f"ix_purchase_order_items_{column}"), "purchase_order_items", [column], unique=False)

    op.create_table(
        "purchase_receipts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("receipt_number", sa.String(length=120), nullable=False),
        sa.Column("status", purchase_receipt_status, nullable=False),
        sa.Column("received_by", sa.Integer(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["received_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "receipt_number", name="uq_purchase_receipts_tenant_receipt_number"),
    )
    for column in ["id", "tenant_id", "purchase_order_id", "receipt_number", "status", "received_by", "created_at"]:
        op.create_index(op.f(f"ix_purchase_receipts_{column}"), "purchase_receipts", [column], unique=False)
    op.create_index("ix_purchase_receipts_tenant_status", "purchase_receipts", ["tenant_id", "status"], unique=False)

    op.create_table(
        "purchase_receipt_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("purchase_receipt_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_item_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("received_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("received_quantity > 0", name="ck_purchase_receipt_items_received_positive"),
        sa.CheckConstraint("unit_cost >= 0", name="ck_purchase_receipt_items_unit_cost_non_negative"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["purchase_order_item_id"], ["purchase_order_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["purchase_receipt_id"], ["purchase_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "purchase_receipt_id", "purchase_order_item_id", "product_id", "warehouse_id", "location_id", "created_at"]:
        op.create_index(op.f(f"ix_purchase_receipt_items_{column}"), "purchase_receipt_items", [column], unique=False)


def downgrade() -> None:
    for column in ["created_at", "location_id", "warehouse_id", "product_id", "purchase_order_item_id", "purchase_receipt_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_purchase_receipt_items_{column}"), table_name="purchase_receipt_items")
    op.drop_table("purchase_receipt_items")
    op.drop_index("ix_purchase_receipts_tenant_status", table_name="purchase_receipts")
    for column in ["created_at", "received_by", "status", "receipt_number", "purchase_order_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_purchase_receipts_{column}"), table_name="purchase_receipts")
    op.drop_table("purchase_receipts")
    for column in ["created_at", "product_id", "purchase_order_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_purchase_order_items_{column}"), table_name="purchase_order_items")
    op.drop_table("purchase_order_items")
    op.drop_index("ix_purchase_orders_tenant_status", table_name="purchase_orders")
    for column in ["created_at", "created_by", "status", "po_number", "vendor_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_purchase_orders_{column}"), table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.alter_column("stock_reservations", "reference_type", existing_type=sa.String(length=16), type_=sa.String(length=14), existing_nullable=False)
    op.alter_column("stock_ledger_entries", "reference_type", existing_type=sa.String(length=16), type_=sa.String(length=14), existing_nullable=False)
