"""batch expiry serial foundation

Revision ID: 20260521_0006
Revises: 20260521_0005
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260521_0006"
down_revision: str | None = "20260521_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

inventory_batch_status = sa.Enum("ACTIVE", "QC_HOLD", "DAMAGED", "EXPIRED", "QUARANTINE", "SCRAPPED", name="inventory_batch_status", native_enum=False)
inventory_serial_status = sa.Enum("IN_STOCK", "RESERVED", "SOLD", "DAMAGED", "SCRAPPED", "RETURNED", "QC_HOLD", name="inventory_serial_status", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "inventory_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("batch_number", sa.String(length=120), nullable=False),
        sa.Column("supplier_batch_number", sa.String(length=120), nullable=True),
        sa.Column("manufacture_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("warranty_until", sa.Date(), nullable=True),
        sa.Column("quantity_on_hand", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("quantity_available", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("quantity_reserved", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("status", inventory_batch_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_inventory_batches_on_hand_non_negative"),
        sa.CheckConstraint("quantity_available >= 0", name="ck_inventory_batches_available_non_negative"),
        sa.CheckConstraint("quantity_reserved >= 0", name="ck_inventory_batches_reserved_non_negative"),
        sa.CheckConstraint("quantity_reserved <= quantity_on_hand", name="ck_inventory_batches_reserved_lte_on_hand"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "product_id", "warehouse_id", "location_id", "batch_number", name="uq_inventory_batches_dimension_number"),
    )
    for column in ["id", "tenant_id", "product_id", "warehouse_id", "location_id", "batch_number", "expiry_date", "status", "created_at"]:
        op.create_index(op.f(f"ix_inventory_batches_{column}"), "inventory_batches", [column], unique=False)
    op.create_index("ix_inventory_batches_tenant_product", "inventory_batches", ["tenant_id", "product_id"], unique=False)

    op.create_table(
        "inventory_serials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=True),
        sa.Column("serial_number", sa.String(length=120), nullable=False),
        sa.Column("status", inventory_serial_status, nullable=False),
        sa.Column("warranty_until", sa.Date(), nullable=True),
        sa.Column("expires_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["inventory_batches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "product_id", "serial_number", name="uq_inventory_serials_tenant_product_number"),
    )
    for column in ["id", "tenant_id", "product_id", "warehouse_id", "location_id", "batch_id", "serial_number", "status", "created_at"]:
        op.create_index(op.f(f"ix_inventory_serials_{column}"), "inventory_serials", [column], unique=False)
    op.create_index("ix_inventory_serials_tenant_product", "inventory_serials", ["tenant_id", "product_id"], unique=False)

    op.add_column("stock_ledger_entries", sa.Column("batch_id", sa.Integer(), nullable=True))
    op.add_column("stock_ledger_entries", sa.Column("serial_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_stock_ledger_entries_batch_id_inventory_batches", "stock_ledger_entries", "inventory_batches", ["batch_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_stock_ledger_entries_serial_id_inventory_serials", "stock_ledger_entries", "inventory_serials", ["serial_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_stock_ledger_entries_batch_id"), "stock_ledger_entries", ["batch_id"], unique=False)
    op.create_index(op.f("ix_stock_ledger_entries_serial_id"), "stock_ledger_entries", ["serial_id"], unique=False)

    for column, type_ in [
        ("batch_number", sa.String(length=120)),
        ("supplier_batch_number", sa.String(length=120)),
        ("manufacture_date", sa.Date()),
        ("expiry_date", sa.Date()),
        ("warranty_until", sa.Date()),
        ("serial_numbers", sa.JSON()),
    ]:
        op.add_column("purchase_receipt_items", sa.Column(column, type_, nullable=True))


def downgrade() -> None:
    for column in ["serial_numbers", "warranty_until", "expiry_date", "manufacture_date", "supplier_batch_number", "batch_number"]:
        op.drop_column("purchase_receipt_items", column)
    op.drop_index(op.f("ix_stock_ledger_entries_serial_id"), table_name="stock_ledger_entries")
    op.drop_index(op.f("ix_stock_ledger_entries_batch_id"), table_name="stock_ledger_entries")
    op.drop_constraint("fk_stock_ledger_entries_serial_id_inventory_serials", "stock_ledger_entries", type_="foreignkey")
    op.drop_constraint("fk_stock_ledger_entries_batch_id_inventory_batches", "stock_ledger_entries", type_="foreignkey")
    op.drop_column("stock_ledger_entries", "serial_id")
    op.drop_column("stock_ledger_entries", "batch_id")
    op.drop_index("ix_inventory_serials_tenant_product", table_name="inventory_serials")
    for column in ["created_at", "status", "serial_number", "batch_id", "location_id", "warehouse_id", "product_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_inventory_serials_{column}"), table_name="inventory_serials")
    op.drop_table("inventory_serials")
    op.drop_index("ix_inventory_batches_tenant_product", table_name="inventory_batches")
    for column in ["created_at", "status", "expiry_date", "batch_number", "location_id", "warehouse_id", "product_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_inventory_batches_{column}"), table_name="inventory_batches")
    op.drop_table("inventory_batches")
