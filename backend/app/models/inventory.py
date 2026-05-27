import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MovementType(str, enum.Enum):
    STOCK_IN = "STOCK_IN"
    STOCK_OUT = "STOCK_OUT"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"
    SALES_RESERVE = "SALES_RESERVE"
    SALES_RELEASE = "SALES_RELEASE"
    SALES_DEDUCT = "SALES_DEDUCT"
    RETURN_RESTOCK = "RETURN_RESTOCK"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    CYCLE_COUNT_ADJUSTMENT = "CYCLE_COUNT_ADJUSTMENT"


class ReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    DEDUCTED = "DEDUCTED"
    CANCELLED = "CANCELLED"


class ReferenceType(str, enum.Enum):
    MANUAL = "MANUAL"
    PURCHASE_RECEIPT = "PURCHASE_RECEIPT"
    SALES_ORDER = "SALES_ORDER"
    SALES_RETURN = "SALES_RETURN"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"
    RECONCILIATION = "RECONCILIATION"


class InventoryBatchStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    QC_HOLD = "QC_HOLD"
    DAMAGED = "DAMAGED"
    EXPIRED = "EXPIRED"
    QUARANTINE = "QUARANTINE"
    SCRAPPED = "SCRAPPED"


class InventorySerialStatus(str, enum.Enum):
    IN_STOCK = "IN_STOCK"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    DAMAGED = "DAMAGED"
    SCRAPPED = "SCRAPPED"
    RETURNED = "RETURNED"
    QC_HOLD = "QC_HOLD"


class IdempotencyStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"


class WarehouseStock(Base):
    __tablename__ = "warehouse_stock"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "warehouse_id", "location_id", name="uq_warehouse_stock_dimension"),
        Index("ix_warehouse_stock_tenant_product", "tenant_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    quantity_reserved: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    quantity_available: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    quantity_in_transit: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    quantity_qc_hold: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    quantity_damaged: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    quantity_expired: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    quantity_quarantine: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class StockLedgerEntry(Base):
    __tablename__ = "stock_ledger_entries"
    __table_args__ = (
        Index("ix_stock_ledger_tenant_reference", "tenant_id", "reference_type", "reference_id"),
        Index("ix_stock_ledger_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_serials.id", ondelete="SET NULL"), nullable=True, index=True)
    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType, name="movement_type", native_enum=False), nullable=False, index=True)
    quantity_delta: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    reserved_delta: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    available_delta: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    reference_type: Mapped[ReferenceType] = mapped_column(Enum(ReferenceType, name="reference_type", native_enum=False), nullable=False, index=True)
    reference_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "warehouse_id", "location_id", "batch_number", name="uq_inventory_batches_dimension_number"),
        Index("ix_inventory_batches_tenant_product", "tenant_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    supplier_batch_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    manufacture_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    warranty_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    quantity_available: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    quantity_reserved: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    status: Mapped[InventoryBatchStatus] = mapped_column(Enum(InventoryBatchStatus, name="inventory_batch_status", native_enum=False), default=InventoryBatchStatus.ACTIVE, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class InventorySerial(Base):
    __tablename__ = "inventory_serials"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "serial_number", name="uq_inventory_serials_tenant_product_number"),
        Index("ix_inventory_serials_tenant_product", "tenant_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[InventorySerialStatus] = mapped_column(Enum(InventorySerialStatus, name="inventory_serial_status", native_enum=False), default=InventorySerialStatus.IN_STOCK, nullable=False, index=True)
    warranty_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class StockReservation(Base):
    __tablename__ = "stock_reservations"
    __table_args__ = (Index("ix_stock_reservations_tenant_reference", "tenant_id", "reference_type", "reference_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus, name="reservation_status", native_enum=False), nullable=False, default=ReservationStatus.ACTIVE, index=True)
    reference_type: Mapped[ReferenceType] = mapped_column(Enum(ReferenceType, name="reservation_reference_type", native_enum=False), nullable=False, index=True)
    reference_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deducted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("tenant_id", "key", "operation", name="uq_idempotency_tenant_key_operation"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[IdempotencyStatus] = mapped_column(Enum(IdempotencyStatus, name="idempotency_status", native_enum=False), nullable=False, default=IdempotencyStatus.COMPLETED)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
