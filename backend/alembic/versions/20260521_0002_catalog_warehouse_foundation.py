"""catalog warehouse foundation

Revision ID: 20260521_0002
Revises: 20260521_0001
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260521_0002"
down_revision: str | None = "20260521_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

record_status = sa.Enum("ACTIVE", "INACTIVE", "ARCHIVED", name="record_status", native_enum=False)
location_type = sa.Enum("STORAGE", "PICKING", "RECEIVING", "PACKING", "SHIPPING", "RETURN", "DAMAGED", "EXPIRED", "QUARANTINE", "QC", "SCRAP", "VIRTUAL", name="location_type", native_enum=False)


def tenant_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("status", record_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def add_common_indexes(table_name: str) -> None:
    op.create_index(op.f(f"ix_{table_name}_id"), table_name, ["id"], unique=False)
    op.create_index(op.f(f"ix_{table_name}_tenant_id"), table_name, ["tenant_id"], unique=False)
    op.create_index(op.f(f"ix_{table_name}_status"), table_name, ["status"], unique=False)


def upgrade() -> None:
    op.create_table(
        "categories",
        *tenant_columns(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_categories_tenant_name"),
    )
    add_common_indexes("categories")

    op.create_table(
        "brands",
        *tenant_columns(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_brands_tenant_name"),
    )
    add_common_indexes("brands")

    op.create_table(
        "vendors",
        *tenant_columns(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("gst_number", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_vendors_tenant_name"),
    )
    add_common_indexes("vendors")

    op.create_table(
        "customers",
        *tenant_columns(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("gst_number", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_customers_tenant_email"),
    )
    add_common_indexes("customers")

    op.create_table(
        "products",
        *tenant_columns(),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("brand_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=120), nullable=False),
        sa.Column("barcode", sa.String(length=120), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("cost_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("selling_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("reorder_level", sa.Integer(), nullable=True),
        sa.Column("track_batch", sa.Boolean(), nullable=False),
        sa.Column("track_expiry", sa.Boolean(), nullable=False),
        sa.Column("track_serial", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "barcode", name="uq_products_tenant_barcode"),
        sa.UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),
    )
    add_common_indexes("products")
    op.create_index(op.f("ix_products_brand_id"), "products", ["brand_id"], unique=False)
    op.create_index(op.f("ix_products_category_id"), "products", ["category_id"], unique=False)

    op.create_table(
        "warehouses",
        *tenant_columns(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_warehouses_tenant_code"),
    )
    add_common_indexes("warehouses")

    op.create_table(
        "warehouse_locations",
        *tenant_columns(),
        sa.Column("warehouse_id", sa.Integer(), nullable=False),
        sa.Column("parent_location_id", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("barcode", sa.String(length=120), nullable=True),
        sa.Column("location_type", location_type, nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["parent_location_id"], ["warehouse_locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "warehouse_id", "barcode", name="uq_locations_tenant_warehouse_barcode"),
        sa.UniqueConstraint("tenant_id", "warehouse_id", "code", name="uq_locations_tenant_warehouse_code"),
    )
    add_common_indexes("warehouse_locations")
    op.create_index(op.f("ix_warehouse_locations_warehouse_id"), "warehouse_locations", ["warehouse_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_warehouse_locations_warehouse_id"), table_name="warehouse_locations")
    op.drop_index(op.f("ix_warehouse_locations_status"), table_name="warehouse_locations")
    op.drop_index(op.f("ix_warehouse_locations_tenant_id"), table_name="warehouse_locations")
    op.drop_index(op.f("ix_warehouse_locations_id"), table_name="warehouse_locations")
    op.drop_table("warehouse_locations")
    op.drop_index(op.f("ix_warehouses_status"), table_name="warehouses")
    op.drop_index(op.f("ix_warehouses_tenant_id"), table_name="warehouses")
    op.drop_index(op.f("ix_warehouses_id"), table_name="warehouses")
    op.drop_table("warehouses")
    op.drop_index(op.f("ix_products_category_id"), table_name="products")
    op.drop_index(op.f("ix_products_brand_id"), table_name="products")
    op.drop_index(op.f("ix_products_status"), table_name="products")
    op.drop_index(op.f("ix_products_tenant_id"), table_name="products")
    op.drop_index(op.f("ix_products_id"), table_name="products")
    op.drop_table("products")
    op.drop_index(op.f("ix_customers_status"), table_name="customers")
    op.drop_index(op.f("ix_customers_tenant_id"), table_name="customers")
    op.drop_index(op.f("ix_customers_id"), table_name="customers")
    op.drop_table("customers")
    op.drop_index(op.f("ix_vendors_status"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_tenant_id"), table_name="vendors")
    op.drop_index(op.f("ix_vendors_id"), table_name="vendors")
    op.drop_table("vendors")
    op.drop_index(op.f("ix_brands_status"), table_name="brands")
    op.drop_index(op.f("ix_brands_tenant_id"), table_name="brands")
    op.drop_index(op.f("ix_brands_id"), table_name="brands")
    op.drop_table("brands")
    op.drop_index(op.f("ix_categories_status"), table_name="categories")
    op.drop_index(op.f("ix_categories_tenant_id"), table_name="categories")
    op.drop_index(op.f("ix_categories_id"), table_name="categories")
    op.drop_table("categories")
