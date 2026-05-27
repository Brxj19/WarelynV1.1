import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecordStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class LocationType(str, enum.Enum):
    STORAGE = "STORAGE"
    PICKING = "PICKING"
    RECEIVING = "RECEIVING"
    PACKING = "PACKING"
    SHIPPING = "SHIPPING"
    RETURN = "RETURN"
    DAMAGED = "DAMAGED"
    EXPIRED = "EXPIRED"
    QUARANTINE = "QUARANTINE"
    QC = "QC"
    SCRAP = "SCRAP"
    VIRTUAL = "VIRTUAL"


class TenantRecordMixin:
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[RecordStatus] = mapped_column(Enum(RecordStatus, name="record_status", native_enum=False), default=RecordStatus.ACTIVE, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Category(TenantRecordMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_categories_tenant_name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Brand(TenantRecordMixin, Base):
    __tablename__ = "brands"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_brands_tenant_name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Vendor(TenantRecordMixin, Base):
    __tablename__ = "vendors"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_vendors_tenant_name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Customer(TenantRecordMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_customers_tenant_email"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Product(TenantRecordMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_products_tenant_sku"),
        UniqueConstraint("tenant_id", "barcode", name="uq_products_tenant_barcode"),
    )

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[str] = mapped_column(String(120), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="pcs")
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    selling_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    reorder_level: Mapped[int | None] = mapped_column(nullable=True)
    track_batch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    track_expiry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    track_serial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Warehouse(TenantRecordMixin, Base):
    __tablename__ = "warehouses"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_warehouses_tenant_code"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    locations: Mapped[list["WarehouseLocation"]] = relationship(back_populates="warehouse")


class WarehouseLocation(TenantRecordMixin, Base):
    __tablename__ = "warehouse_locations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "warehouse_id", "code", name="uq_locations_tenant_warehouse_code"),
        UniqueConstraint("tenant_id", "warehouse_id", "barcode", name="uq_locations_tenant_warehouse_barcode"),
    )

    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_location_id: Mapped[int | None] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="SET NULL"), nullable=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(120), nullable=True)
    location_type: Mapped[LocationType] = mapped_column(Enum(LocationType, name="location_type", native_enum=False), nullable=False, default=LocationType.STORAGE)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)
    warehouse: Mapped[Warehouse] = relationship(back_populates="locations")
