import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PutawayTaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class StockCountSessionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    RECONCILED = "RECONCILED"
    CANCELLED = "CANCELLED"


class OutboxEventStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class ReorderRule(Base):
    __tablename__ = "reorder_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "warehouse_id", name="uq_reorder_rules_dimension"),
        Index("ix_reorder_rules_tenant", "tenant_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    min_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    max_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    safety_stock: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_create_po: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class PutawayTask(Base):
    __tablename__ = "putaway_tasks"
    __table_args__ = (
        Index("ix_putaway_tasks_tenant", "tenant_id"),
        Index("ix_putaway_tasks_status", "tenant_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    from_location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False)
    to_location_id: Mapped[int | None] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="SET NULL"), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    status: Mapped[PutawayTaskStatus] = mapped_column(Enum(PutawayTaskStatus, name="putaway_task_status", native_enum=False), default=PutawayTaskStatus.PENDING, nullable=False)
    receipt_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_receipts.id", ondelete="SET NULL"), nullable=True)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class StockCountSession(Base):
    __tablename__ = "stock_count_sessions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "session_number", name="uq_stock_count_sessions_number"),
        Index("ix_stock_count_sessions_tenant", "tenant_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    session_number: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[StockCountSessionStatus] = mapped_column(Enum(StockCountSessionStatus, name="stock_count_session_status", native_enum=False), default=StockCountSessionStatus.DRAFT, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    lines: Mapped[list["StockCountLine"]] = relationship("StockCountLine", cascade="all, delete-orphan", lazy="selectin")


class StockCountLine(Base):
    __tablename__ = "stock_count_lines"
    __table_args__ = (
        Index("ix_stock_count_lines_session", "session_id"),
        UniqueConstraint("tenant_id", "session_id", "product_id", "location_id", name="uq_stock_count_lines_session_product_location"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("stock_count_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("warehouse_locations.id", ondelete="RESTRICT"), nullable=False)
    system_quantity: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    counted_quantity: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    variance: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (Index("ix_outbox_events_status", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[OutboxEventStatus] = mapped_column(Enum(OutboxEventStatus, name="outbox_event_status", native_enum=False), default=OutboxEventStatus.PENDING, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
