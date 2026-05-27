import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PickTaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PICKED = "PICKED"
    CANCELLED = "CANCELLED"


class PickTaskItemStatus(str, enum.Enum):
    PENDING = "PENDING"
    PICKED = "PICKED"
    CANCELLED = "CANCELLED"


class PackageStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PACKED = "PACKED"
    CANCELLED = "CANCELLED"


class PickTask(Base):
    __tablename__ = "pick_tasks"
    __table_args__ = (UniqueConstraint("tenant_id", "pick_number", name="uq_pick_tasks_tenant_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    pick_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[PickTaskStatus] = mapped_column(Enum(PickTaskStatus, name="pick_task_status", native_enum=False), default=PickTaskStatus.PENDING, nullable=False, index=True)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    picked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    items: Mapped[list["PickTaskItem"]] = relationship(cascade="all, delete-orphan")


class PickTaskItem(Base):
    __tablename__ = "pick_task_items"
    __table_args__ = (
        CheckConstraint("required_quantity > 0", name="ck_pick_task_items_required_positive"),
        CheckConstraint("picked_quantity >= 0", name="ck_pick_task_items_picked_non_negative"),
        CheckConstraint("picked_quantity <= required_quantity", name="ck_pick_task_items_picked_lte_required"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    pick_task_id: Mapped[int] = mapped_column(ForeignKey("pick_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_item_id: Mapped[int] = mapped_column(ForeignKey("sales_order_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    reservation_id: Mapped[int] = mapped_column(ForeignKey("stock_reservations.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_serials.id", ondelete="SET NULL"), nullable=True, index=True)
    required_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    picked_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False, default=0)
    status: Mapped[PickTaskItemStatus] = mapped_column(Enum(PickTaskItemStatus, name="pick_task_item_status", native_enum=False), default=PickTaskItemStatus.PENDING, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Package(Base):
    __tablename__ = "packages"
    __table_args__ = (UniqueConstraint("tenant_id", "package_number", name="uq_packages_tenant_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_id: Mapped[int] = mapped_column(ForeignKey("sales_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    package_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[PackageStatus] = mapped_column(Enum(PackageStatus, name="package_status", native_enum=False), default=PackageStatus.DRAFT, nullable=False, index=True)
    packed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    packed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    items: Mapped[list["PackageItem"]] = relationship(cascade="all, delete-orphan")


class PackageItem(Base):
    __tablename__ = "package_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_package_items_quantity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True)
    pick_task_item_id: Mapped[int] = mapped_column(ForeignKey("pick_task_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    sales_order_item_id: Mapped[int] = mapped_column(ForeignKey("sales_order_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    serial_id: Mapped[int | None] = mapped_column(ForeignKey("inventory_serials.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
