"""picking packing serial allocation foundation

Revision ID: 20260521_0008
Revises: 20260521_0007
Create Date: 2026-05-21 00:08:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260521_0008"
down_revision: str | None = "20260521_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pick_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=False),
        sa.Column("pick_number", sa.String(length=120), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "IN_PROGRESS", "PICKED", "CANCELLED", name="pick_task_status", native_enum=False), nullable=False),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("picked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "pick_number", name="uq_pick_tasks_tenant_number"),
    )
    for column in ["id", "tenant_id", "sales_order_id", "pick_number", "status", "assigned_to", "created_by", "created_at"]:
        op.create_index(op.f(f"ix_pick_tasks_{column}"), "pick_tasks", [column])

    op.create_table(
        "pick_task_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("pick_task_id", sa.Integer(), nullable=False),
        sa.Column("sales_order_item_id", sa.Integer(), nullable=False),
        sa.Column("reservation_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("serial_id", sa.Integer(), nullable=True),
        sa.Column("required_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("picked_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "PICKED", "CANCELLED", name="pick_task_item_status", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("picked_quantity >= 0", name="ck_pick_task_items_picked_non_negative"),
        sa.CheckConstraint("picked_quantity <= required_quantity", name="ck_pick_task_items_picked_lte_required"),
        sa.CheckConstraint("required_quantity > 0", name="ck_pick_task_items_required_positive"),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["pick_task_id"], ["pick_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reservation_id"], ["stock_reservations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_order_item_id"], ["sales_order_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["serial_id"], ["inventory_serials.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "pick_task_id", "sales_order_item_id", "reservation_id", "product_id", "warehouse_id", "location_id", "batch_id", "serial_id", "status", "created_at"]:
        op.create_index(op.f(f"ix_pick_task_items_{column}"), "pick_task_items", [column])

    op.create_table(
        "packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("sales_order_id", sa.Integer(), nullable=False),
        sa.Column("package_number", sa.String(length=120), nullable=False),
        sa.Column("status", sa.Enum("DRAFT", "PACKED", "CANCELLED", name="package_status", native_enum=False), nullable=False),
        sa.Column("packed_by", sa.Integer(), nullable=True),
        sa.Column("packed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["packed_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sales_order_id"], ["sales_orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "package_number", name="uq_packages_tenant_number"),
    )
    for column in ["id", "tenant_id", "sales_order_id", "package_number", "status", "packed_by", "created_at"]:
        op.create_index(op.f(f"ix_packages_{column}"), "packages", [column])

    op.create_table(
        "package_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("pick_task_item_id", sa.Integer(), nullable=False),
        sa.Column("sales_order_item_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("serial_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_package_items_quantity_positive"),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pick_task_item_id"], ["pick_task_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sales_order_item_id"], ["sales_order_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["serial_id"], ["inventory_serials.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "package_id", "pick_task_item_id", "sales_order_item_id", "product_id", "batch_id", "serial_id", "created_at"]:
        op.create_index(op.f(f"ix_package_items_{column}"), "package_items", [column])


def downgrade() -> None:
    op.drop_table("package_items")
    op.drop_table("packages")
    op.drop_table("pick_task_items")
    op.drop_table("pick_tasks")
