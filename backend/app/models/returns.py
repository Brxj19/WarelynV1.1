import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SalesReturnStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    INSPECTION_PENDING = "INSPECTION_PENDING"
    PARTIALLY_PROCESSED = "PARTIALLY_PROCESSED"
    PROCESSED = "PROCESSED"
    CANCELLED = "CANCELLED"


class SalesReturnItemStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED_RESTOCK = "ACCEPTED_RESTOCK"
    ACCEPTED_BLOCKED = "ACCEPTED_BLOCKED"
    DAMAGED = "DAMAGED"
    SCRAPPED = "SCRAPPED"
    REJECTED = "REJECTED"


class BlockedReturnStockStatus(str, enum.Enum):
    QC_HOLD = "QC_HOLD"
    QUARANTINE = "QUARANTINE"
    DAMAGED = "DAMAGED"
    SCRAPPED = "SCRAPPED"


class SalesReturn(Base):
    __tablename__ = "sales_returns"
    __table_args__ = (UniqueConstraint("tenant_id", "return_number", name="uq_sales_returns_tenant_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    return_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[SalesReturnStatus] = mapped_column(Enum(SalesReturnStatus, name="sales_return_status", native_enum=False), default=SalesReturnStatus.DRAFT, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    inspected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    items: Mapped[list["SalesReturnItem"]] = relationship(cascade="all, delete-orphan")
    inspections: Mapped[list["ReturnQCInspection"]] = relationship(cascade="all, delete-orphan")
    blocked_stock: Mapped[list["BlockedReturnStock"]] = relationship(cascade="all, delete-orphan")


class SalesReturnItem(Base):
    __tablename__ = "sales_return_items"
    __table_args__ = (
        CheckConstraint("returned_quantity > 0", name="ck_sales_return_items_returned_positive"),
        CheckConstraint("accepted_quantity >= 0", name="ck_sales_return_items_accepted_non_negative"),
        CheckConstraint("rejected_quantity >= 0", name="ck_sales_return_items_rejected_non_negative"),
        CheckConstraint("accepted_quantity + rejected_quantity <= returned_quantity", name="ck_sales_return_items_qc_lte_returned"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_return_id: Mapped[int] = mapped_column(ForeignKey("sales_returns.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_item_id: Mapped[int] = mapped_column(ForeignKey("sales_order_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_serials.id", ondelete="SET NULL"), nullable=True, index=True)
    returned_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    accepted_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    rejected_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    qc_status: Mapped[SalesReturnItemStatus] = mapped_column(Enum(SalesReturnItemStatus, name="sales_return_item_status", native_enum=False), default=SalesReturnItemStatus.PENDING, nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ReturnQCInspection(Base):
    __tablename__ = "return_qc_inspections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_return_id: Mapped[int] = mapped_column(ForeignKey("sales_returns.id", ondelete="CASCADE"), nullable=False, index=True)
    inspected_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    inspected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BlockedReturnStock(Base):
    __tablename__ = "blocked_return_stock"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_blocked_return_stock_quantity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_return_id: Mapped[int] = mapped_column(ForeignKey("sales_returns.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_return_item_id: Mapped[int] = mapped_column(ForeignKey("sales_return_items.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_serials.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    status: Mapped[BlockedReturnStockStatus] = mapped_column(Enum(BlockedReturnStockStatus, name="blocked_return_stock_status", native_enum=False), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
