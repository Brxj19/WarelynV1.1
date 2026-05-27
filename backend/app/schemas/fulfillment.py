from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.fulfillment import PackageStatus, PickTaskItemStatus, PickTaskStatus


class PickTaskCreate(BaseModel):
    pick_number: str = Field(min_length=1, max_length=120)
    assigned_to: int | None = None
    notes: str | None = None


class PickTaskUpdate(BaseModel):
    pick_number: str | None = Field(default=None, min_length=1, max_length=120)
    assigned_to: int | None = None
    notes: str | None = None


class PickTaskPickItemRequest(BaseModel):
    pick_task_item_id: int
    picked_quantity: Decimal = Field(ge=0)
    batch_id: int | None = None
    serial_id: int | None = None


class PickTaskPickRequest(BaseModel):
    items: list[PickTaskPickItemRequest] = Field(default_factory=list)


class PickTaskItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    pick_task_id: int
    sales_order_item_id: int
    reservation_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    batch_id: int | None = None
    serial_id: int | None = None
    required_quantity: Decimal
    picked_quantity: Decimal
    status: PickTaskItemStatus
    created_at: datetime
    updated_at: datetime


class PickTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    sales_order_id: int
    pick_number: str
    status: PickTaskStatus
    assigned_to: int | None = None
    started_at: datetime | None = None
    picked_at: datetime | None = None
    cancelled_at: datetime | None = None
    notes: str | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    items: list[PickTaskItemRead] = []


class PackageCreate(BaseModel):
    package_number: str = Field(min_length=1, max_length=120)
    pick_task_item_ids: list[int] = Field(default_factory=list)
    notes: str | None = None


class PackageUpdate(BaseModel):
    package_number: str | None = Field(default=None, min_length=1, max_length=120)
    notes: str | None = None


class PackagePackRequest(BaseModel):
    notes: str | None = None


class PackageItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    package_id: int
    pick_task_item_id: int
    sales_order_item_id: int
    product_id: int
    batch_id: int | None = None
    serial_id: int | None = None
    quantity: Decimal
    created_at: datetime
    updated_at: datetime


class PackageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    sales_order_id: int
    package_number: str
    status: PackageStatus
    packed_by: int | None = None
    packed_at: datetime | None = None
    cancelled_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[PackageItemRead] = []
