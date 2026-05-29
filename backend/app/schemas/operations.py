from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.operations import OutboxEventStatus, PutawayTaskStatus, StockCountSessionStatus


class ReorderRuleCreate(BaseModel):
    product_id: int
    warehouse_id: int
    min_quantity: Decimal = Field(ge=0)
    max_quantity: Decimal = Field(gt=0)
    safety_stock: Decimal = Field(default=Decimal("0"), ge=0)
    lead_time_days: int = Field(default=0, ge=0)
    auto_create_po: bool = False
    is_active: bool = True


class ReorderRuleUpdate(BaseModel):
    min_quantity: Decimal | None = Field(default=None, ge=0)
    max_quantity: Decimal | None = Field(default=None, gt=0)
    safety_stock: Decimal | None = Field(default=None, ge=0)
    lead_time_days: int | None = Field(default=None, ge=0)
    auto_create_po: bool | None = None
    is_active: bool | None = None


class ReorderRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    product_id: int
    warehouse_id: int
    min_quantity: Decimal
    max_quantity: Decimal
    safety_stock: Decimal
    lead_time_days: int
    auto_create_po: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PutawayTaskCreate(BaseModel):
    product_id: int
    warehouse_id: int
    from_location_id: int
    to_location_id: int | None = None
    quantity: Decimal = Field(gt=0)
    receipt_id: int | None = None
    assigned_to: int | None = None


class PutawayTaskUpdate(BaseModel):
    to_location_id: int | None = None
    assigned_to: int | None = None
    status: PutawayTaskStatus | None = None


class PutawayTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    product_id: int
    warehouse_id: int
    from_location_id: int
    to_location_id: int | None
    quantity: Decimal
    status: PutawayTaskStatus
    receipt_id: int | None
    assigned_to: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StockCountSessionCreate(BaseModel):
    warehouse_id: int
    notes: str | None = None


class StockCountSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    warehouse_id: int
    session_number: str
    status: StockCountSessionStatus
    notes: str | None
    created_by: int
    submitted_at: datetime | None
    reconciled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    lines: list["StockCountLineRead"] = []


class StockCountLineCreate(BaseModel):
    product_id: int
    location_id: int


class StockCountLineUpdate(BaseModel):
    counted_quantity: Decimal = Field(ge=0)
    notes: str | None = None


class StockCountLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    session_id: int
    product_id: int
    location_id: int
    system_quantity: Decimal
    counted_quantity: Decimal | None
    variance: Decimal | None
    notes: str | None
    created_at: datetime


class OutboxEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int | None
    event_type: str
    payload_json: dict
    status: OutboxEventStatus
    attempts: int
    last_error: str | None
    processed_at: datetime | None
    created_at: datetime


class ExpireBatchesResponse(BaseModel):
    expired_count: int
    batch_ids: list[int]
