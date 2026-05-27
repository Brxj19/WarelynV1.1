from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.imports import ImportJobStatus, ImportRowStatus, ProductImportMode


class ImportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    created_by: int
    import_type: str
    filename: str
    mode: ProductImportMode
    status: ImportJobStatus
    total_rows: int
    valid_rows: int
    error_rows: int
    warning_rows: int
    created_count: int
    updated_count: int
    skipped_count: int
    created_at: datetime
    updated_at: datetime
    validated_at: datetime | None = None
    committed_at: datetime | None = None
    cancelled_at: datetime | None = None


class ImportJobRowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    job_id: int
    row_number: int
    raw_data: dict
    normalized_data: dict | None = None
    status: ImportRowStatus
    errors: list
    warnings: list
    existing_product_id: int | None = None
    created_product_id: int | None = None
    created_at: datetime
    updated_at: datetime


class ImportJobSummary(BaseModel):
    job: ImportJobRead


class ProductImportUploadResponse(ImportJobSummary):
    pass


class ProductImportValidationResponse(ImportJobSummary):
    rows: list[ImportJobRowRead]


class ProductImportCommitResponse(ImportJobSummary):
    rows: list[ImportJobRowRead]


class ProductImportCancelRequest(BaseModel):
    reason: str | None = None
