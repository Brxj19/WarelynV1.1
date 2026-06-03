from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.purchasing import PurchaseOrderStatus, PurchaseReceiptStatus


class PurchaseOrderItemCreate(BaseModel):
    product_id: int
    ordered_quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(default=0, ge=0)
    notes: str | None = None


class PurchaseOrderCreate(BaseModel):
    vendor_id: int
    po_number: str | None = Field(default=None, min_length=1, max_length=120)
    order_date: date
    expected_date: date | None = None
    notes: str | None = None
    items: list[PurchaseOrderItemCreate] = Field(default_factory=list)


class PurchaseOrderUpdate(BaseModel):
    vendor_id: int | None = None
    po_number: str | None = Field(default=None, min_length=1, max_length=120)
    order_date: date | None = None
    expected_date: date | None = None
    notes: str | None = None
    items: list[PurchaseOrderItemCreate] | None = None


class PurchaseOrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    purchase_order_id: int
    product_id: int
    ordered_quantity: Decimal
    received_quantity: Decimal
    unit_cost: Decimal
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class PurchaseOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    vendor_id: int
    po_number: str
    status: PurchaseOrderStatus
    order_date: date
    expected_date: date | None = None
    notes: str | None = None
    created_by: int
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    received_at: datetime | None = None
    cancelled_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseOrderItemRead] = []


class PurchaseReceiptItemCreate(BaseModel):
    purchase_order_item_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    received_quantity: Decimal = Field(gt=0)
    unit_cost: Decimal | None = Field(default=None, ge=0)
    batch_number: str | None = Field(default=None, max_length=120)
    supplier_batch_number: str | None = Field(default=None, max_length=120)
    manufacture_date: date | None = None
    expiry_date: date | None = None
    warranty_until: date | None = None
    serial_numbers: list[str] | None = None


class PurchaseReceiptCreate(BaseModel):
    receipt_number: str = Field(min_length=1, max_length=120)
    received_at: datetime | None = None
    notes: str | None = None
    items: list[PurchaseReceiptItemCreate] = Field(default_factory=list)


class PurchaseReceiptUpdate(BaseModel):
    receipt_number: str | None = Field(default=None, min_length=1, max_length=120)
    received_at: datetime | None = None
    notes: str | None = None
    items: list[PurchaseReceiptItemCreate] | None = None


class PurchaseReceiptItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    purchase_receipt_id: int
    purchase_order_item_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    received_quantity: Decimal
    unit_cost: Decimal
    batch_number: str | None = None
    supplier_batch_number: str | None = None
    manufacture_date: date | None = None
    expiry_date: date | None = None
    warranty_until: date | None = None
    serial_numbers: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class PurchaseReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    purchase_order_id: int
    receipt_number: str
    grn_number: str | None = None
    status: PurchaseReceiptStatus
    received_by: int
    received_at: datetime | None = None
    committed_at: datetime | None = None
    cancelled_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseReceiptItemRead] = []


class PurchaseReceiptCommitRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=120)
    note: str | None = None


class PurchaseWorkflowSummary(BaseModel):
    purchase_order: PurchaseOrderRead
    receipt: PurchaseReceiptRead | None = None
    stock_results: list[dict] = []
