"""sales reservation fulfillment foundation

Revision ID: 20260521_0007
Revises: 20260521_0006
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260521_0007"
down_revision: str | None = "20260521_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

sales_order_status = sa.Enum("DRAFT", "CONFIRMED", "PARTIALLY_FULFILLED", "FULFILLED", "CANCELLED", "CLOSED", name="sales_order_status", native_enum=False)
sales_fulfillment_status = sa.Enum("DRAFT", "COMMITTED", "CANCELLED", name="sales_fulfillment_status", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "sales_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("order_number", sa.String(length=120), nullable=False),
        sa.Column("status", sales_order_status, nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("expected_ship_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "order_number", name="uq_sales_orders_tenant_order_number"),
    )
    for column in ["id", "tenant_id", "customer_id", "order_number", "status", "created_by", "created_at"]:
        op.create_index(op.f(f"ix_sales_orders_{column}"), "sales_orders", [column], unique=False)

    op.create_table(
        "sales_order_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("ordered_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("reserved_quantity", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("fulfilled_quantity", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("ordered_quantity > 0", name="ck_sales_order_items_ordered_positive"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_sales_order_items_reserved_non_negative"),
        sa.CheckConstraint("fulfilled_quantity >= 0", name="ck_sales_order_items_fulfilled_non_negative"),
        sa.CheckConstraint("unit_price >= 0", name="ck_sales_order_items_unit_price_non_negative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "sales_order_id", "product_id", "created_at"]:
        op.create_index(op.f(f"ix_sales_order_items_{column}"), "sales_order_items", [column], unique=False)

    op.create_table(
        "sales_fulfillments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=False),
        sa.Column("fulfillment_number", sa.String(length=120), nullable=False),
        sa.Column("status", sales_fulfillment_status, nullable=False),
        sa.Column("fulfilled_by", sa.Integer(), nullable=False),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["fulfilled_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "fulfillment_number", name="uq_sales_fulfillments_tenant_number"),
    )
    for column in ["id", "tenant_id", "sales_order_id", "fulfillment_number", "status", "fulfilled_by", "created_at"]:
        op.create_index(op.f(f"ix_sales_fulfillments_{column}"), "sales_fulfillments", [column], unique=False)

    op.create_table(
        "sales_fulfillment_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("fulfillment_id", sa.Integer(), nullable=False),
        sa.Column("sales_order_item_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("reservation_id", sa.Integer(), nullable=False),
        sa.Column("fulfilled_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("fulfilled_quantity > 0", name="ck_sales_fulfillment_items_quantity_positive"),
        sa.ForeignKeyConstraint(["fulfillment_id"], ["sales_fulfillments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reservation_id"], ["stock_reservations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_order_item_id"], ["sales_order_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "fulfillment_id", "sales_order_item_id", "product_id", "warehouse_id", "location_id", "reservation_id", "created_at"]:
        op.create_index(op.f(f"ix_sales_fulfillment_items_{column}"), "sales_fulfillment_items", [column], unique=False)


def downgrade() -> None:
    for column in ["created_at", "reservation_id", "location_id", "warehouse_id", "product_id", "sales_order_item_id", "fulfillment_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_sales_fulfillment_items_{column}"), table_name="sales_fulfillment_items")
    op.drop_table("sales_fulfillment_items")
    for column in ["created_at", "fulfilled_by", "status", "fulfillment_number", "sales_order_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_sales_fulfillments_{column}"), table_name="sales_fulfillments")
    op.drop_table("sales_fulfillments")
    for column in ["created_at", "product_id", "sales_order_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_sales_order_items_{column}"), table_name="sales_order_items")
    op.drop_table("sales_order_items")
    for column in ["created_at", "created_by", "status", "order_number", "customer_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_sales_orders_{column}"), table_name="sales_orders")
    op.drop_table("sales_orders")
