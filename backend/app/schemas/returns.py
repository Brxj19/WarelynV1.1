from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.returns import BlockedReturnStockStatus, SalesReturnItemStatus, SalesReturnStatus


class SalesReturnItemCreate(BaseModel):
    sales_order_item_id: int
    warehouse_id: int
    location_id: int
    returned_quantity: Decimal = Field(gt=0)
    batch_id: int | None = None
    serial_id: int | None = None
    reason: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class SalesReturnCreate(BaseModel):
    sales_order_id: int
    return_number: str = Field(min_length=1, max_length=120)
    reason: str | None = Field(default=None, max_length=255)
    notes: str | None = None
    items: list[SalesReturnItemCreate] = Field(default_factory=list)


class SalesReturnUpdate(BaseModel):
    reason: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class SalesReturnItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    sales_return_id: int
    sales_order_item_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    batch_id: int | None = None
    serial_id: int | None = None
    returned_quantity: Decimal
    accepted_quantity: Decimal
    rejected_quantity: Decimal
    qc_status: SalesReturnItemStatus
    reason: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ReturnQCInspectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    sales_return_id: int
    inspected_by: int | None = None
    inspected_at: datetime
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class BlockedReturnStockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    sales_return_id: int
    sales_return_item_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    batch_id: int | None = None
    serial_id: int | None = None
    quantity: Decimal
    status: BlockedReturnStockStatus
    reason: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class SalesReturnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    sales_order_id: int
    return_number: str
    status: SalesReturnStatus
    reason: str | None = None
    notes: str | None = None
    created_by: int
    submitted_at: datetime | None = None
    inspected_at: datetime | None = None
    processed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    items: list[SalesReturnItemRead] = []
    inspections: list[ReturnQCInspectionRead] = []
    blocked_stock: list[BlockedReturnStockRead] = []


class ReturnInspectionItem(BaseModel):
    sales_return_item_id: int
    qc_status: SalesReturnItemStatus
    accepted_quantity: Decimal = Field(ge=0)
    rejected_quantity: Decimal = Field(ge=0)
    reason: str | None = Field(default=None, max_length=255)
    notes: str | None = None


class ReturnInspectionRequest(BaseModel):
    notes: str | None = None
    items: list[ReturnInspectionItem] = Field(default_factory=list)


class ReturnProcessRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=120)
    note: str | None = None


class ReturnWorkflowSummary(BaseModel):
    sales_return: SalesReturnRead
    stock_results: list[dict] = []
