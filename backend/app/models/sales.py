import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SalesOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"


class SalesFulfillmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    COMMITTED = "COMMITTED"
    CANCELLED = "CANCELLED"


class SalesOrder(Base):
    __tablename__ = "sales_orders"
    __table_args__ = (UniqueConstraint("tenant_id", "order_number", name="uq_sales_orders_tenant_order_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[SalesOrderStatus] = mapped_column(Enum(SalesOrderStatus, name="sales_order_status", native_enum=False), default=SalesOrderStatus.DRAFT, nullable=False, index=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_ship_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    items: Mapped[list["SalesOrderItem"]] = relationship(back_populates="sales_order", cascade="all, delete-orphan")
    fulfillments: Mapped[list["SalesFulfillment"]] = relationship(back_populates="sales_order")


class SalesOrderItem(Base):
    __tablename__ = "sales_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    ordered_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    fulfilled_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sales_order: Mapped[SalesOrder] = relationship(back_populates="items")


class SalesFulfillment(Base):
    __tablename__ = "sales_fulfillments"
    __table_args__ = (UniqueConstraint("tenant_id", "fulfillment_number", name="uq_sales_fulfillments_tenant_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    fulfillment_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[SalesFulfillmentStatus] = mapped_column(Enum(SalesFulfillmentStatus, name="sales_fulfillment_status", native_enum=False), default=SalesFulfillmentStatus.DRAFT, nullable=False, index=True)
    fulfilled_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sales_order: Mapped[SalesOrder] = relationship(back_populates="fulfillments")
    items: Mapped[list["SalesFulfillmentItem"]] = relationship(cascade="all, delete-orphan")


class SalesFulfillmentItem(Base):
    __tablename__ = "sales_fulfillment_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    fulfillment_id: Mapped[int] = mapped_column(ForeignKey("sales_fulfillments.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_item_id: Mapped[int] = mapped_column(ForeignKey("sales_order_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("stock_reservations.id", ondelete="RESTRICT"), nullable=False, index=True)
    fulfilled_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
