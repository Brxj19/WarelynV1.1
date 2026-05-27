import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ImportJobStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    HAS_ERRORS = "HAS_ERRORS"
    COMMITTED = "COMMITTED"
    CANCELLED = "CANCELLED"


class ImportRowStatus(str, enum.Enum):
    PENDING = "PENDING"
    VALID = "VALID"
    ERROR = "ERROR"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"
    CREATED = "CREATED"
    UPDATED = "UPDATED"


class ProductImportMode(str, enum.Enum):
    create_only = "create_only"
    update_existing = "update_existing"
    upsert = "upsert"


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (Index("ix_import_jobs_tenant_status", "tenant_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    import_type: Mapped[str] = mapped_column(String(80), nullable=False, default="products", index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[ProductImportMode] = mapped_column(Enum(ProductImportMode, name="product_import_mode", native_enum=False), nullable=False, index=True)
    status: Mapped[ImportJobStatus] = mapped_column(Enum(ImportJobStatus, name="import_job_status", native_enum=False), nullable=False, default=ImportJobStatus.UPLOADED, index=True)
    total_rows: Mapped[int] = mapped_column(nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(nullable=False, default=0)
    error_rows: Mapped[int] = mapped_column(nullable=False, default=0)
    warning_rows: Mapped[int] = mapped_column(nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImportJobRow(Base):
    __tablename__ = "import_job_rows"
    __table_args__ = (
        UniqueConstraint("tenant_id", "job_id", "row_number", name="uq_import_rows_tenant_job_row"),
        Index("ix_import_rows_tenant_job_status", "tenant_id", "job_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    normalized_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[ImportRowStatus] = mapped_column(Enum(ImportRowStatus, name="import_row_status", native_enum=False), nullable=False, default=ImportRowStatus.PENDING, index=True)
    errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    warnings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    existing_product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    created_product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
