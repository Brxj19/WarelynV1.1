"""inventory engine foundation

Revision ID: 20260521_0003
Revises: 20260521_0002
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260521_0003"
down_revision: str | None = "20260521_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

movement_type = sa.Enum("STOCK_IN", "STOCK_OUT", "ADJUSTMENT_IN", "ADJUSTMENT_OUT", "SALES_RESERVE", "SALES_RELEASE", "SALES_DEDUCT", "TRANSFER_OUT", "TRANSFER_IN", "CYCLE_COUNT_ADJUSTMENT", name="movement_type", native_enum=False)
reference_type = sa.Enum("MANUAL", "SALES_ORDER", "TRANSFER", "ADJUSTMENT", "RECONCILIATION", name="reference_type", native_enum=False)
reservation_reference_type = sa.Enum("MANUAL", "SALES_ORDER", "TRANSFER", "ADJUSTMENT", "RECONCILIATION", name="reservation_reference_type", native_enum=False)
reservation_status = sa.Enum("ACTIVE", "RELEASED", "DEDUCTED", "CANCELLED", name="reservation_status", native_enum=False)
idempotency_status = sa.Enum("COMPLETED", name="idempotency_status", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "warehouse_stock",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("quantity_on_hand", sa.Numeric(14, 3), nullable=False),
        sa.Column("quantity_reserved", sa.Numeric(14, 3), nullable=False),
        sa.Column("quantity_available", sa.Numeric(14, 3), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "product_id", "warehouse_id", "location_id", name="uq_warehouse_stock_dimension"),
    )
    op.create_index(op.f("ix_warehouse_stock_id"), "warehouse_stock", ["id"], unique=False)
    op.create_index(op.f("ix_warehouse_stock_location_id"), "warehouse_stock", ["location_id"], unique=False)
    op.create_index(op.f("ix_warehouse_stock_product_id"), "warehouse_stock", ["product_id"], unique=False)
    op.create_index(op.f("ix_warehouse_stock_tenant_id"), "warehouse_stock", ["tenant_id"], unique=False)
    op.create_index("ix_warehouse_stock_tenant_product", "warehouse_stock", ["tenant_id", "product_id"], unique=False)
    op.create_index(op.f("ix_warehouse_stock_warehouse_id"), "warehouse_stock", ["warehouse_id"], unique=False)

    op.create_table(
        "stock_ledger_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("movement_type", movement_type, nullable=False),
        sa.Column("quantity_delta", sa.Numeric(14, 3), nullable=False),
        sa.Column("reserved_delta", sa.Numeric(14, 3), nullable=False),
        sa.Column("available_delta", sa.Numeric(14, 3), nullable=False),
        sa.Column("reference_type", reference_type, nullable=False),
        sa.Column("reference_id", sa.String(length=120), nullable=True),
        sa.Column("idempotency_key", sa.String(length=120), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "product_id", "warehouse_id", "location_id", "movement_type", "reference_type", "reference_id", "idempotency_key", "created_by", "created_at"]:
        op.create_index(op.f(f"ix_stock_ledger_entries_{column}"), "stock_ledger_entries", [column], unique=False)
    op.create_index("ix_stock_ledger_tenant_created", "stock_ledger_entries", ["tenant_id", "created_at"], unique=False)
    op.create_index("ix_stock_ledger_tenant_reference", "stock_ledger_entries", ["tenant_id", "reference_type", "reference_id"], unique=False)

    op.create_table(
        "stock_reservations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("status", reservation_status, nullable=False),
        sa.Column("reference_type", reservation_reference_type, nullable=False),
        sa.Column("reference_id", sa.String(length=120), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deducted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["location_id"], ["warehouse_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["id", "tenant_id", "product_id", "warehouse_id", "location_id", "status", "reference_type", "reference_id", "created_by"]:
        op.create_index(op.f(f"ix_stock_reservations_{column}"), "stock_reservations", [column], unique=False)
    op.create_index("ix_stock_reservations_tenant_reference", "stock_reservations", ["tenant_id", "reference_type", "reference_id"], unique=False)

    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("operation", sa.String(length=80), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=False),
        sa.Column("status", idempotency_status, nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "key", "operation", name="uq_idempotency_tenant_key_operation"),
    )
    for column in ["id", "tenant_id", "key", "operation", "created_by", "expires_at"]:
        op.create_index(op.f(f"ix_idempotency_keys_{column}"), "idempotency_keys", [column], unique=False)


def downgrade() -> None:
    for column in ["expires_at", "created_by", "operation", "key", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_idempotency_keys_{column}"), table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
    op.drop_index("ix_stock_reservations_tenant_reference", table_name="stock_reservations")
    for column in ["created_by", "reference_id", "reference_type", "status", "location_id", "warehouse_id", "product_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_stock_reservations_{column}"), table_name="stock_reservations")
    op.drop_table("stock_reservations")
    op.drop_index("ix_stock_ledger_tenant_reference", table_name="stock_ledger_entries")
    op.drop_index("ix_stock_ledger_tenant_created", table_name="stock_ledger_entries")
    for column in ["created_at", "created_by", "idempotency_key", "reference_id", "reference_type", "movement_type", "location_id", "warehouse_id", "product_id", "tenant_id", "id"]:
        op.drop_index(op.f(f"ix_stock_ledger_entries_{column}"), table_name="stock_ledger_entries")
    op.drop_table("stock_ledger_entries")
    op.drop_index(op.f("ix_warehouse_stock_warehouse_id"), table_name="warehouse_stock")
    op.drop_index("ix_warehouse_stock_tenant_product", table_name="warehouse_stock")
    op.drop_index(op.f("ix_warehouse_stock_tenant_id"), table_name="warehouse_stock")
    op.drop_index(op.f("ix_warehouse_stock_product_id"), table_name="warehouse_stock")
    op.drop_index(op.f("ix_warehouse_stock_location_id"), table_name="warehouse_stock")
    op.drop_index(op.f("ix_warehouse_stock_id"), table_name="warehouse_stock")
    op.drop_table("warehouse_stock")
