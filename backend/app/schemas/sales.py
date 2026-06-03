from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.sales import SalesFulfillmentStatus, SalesOrderStatus


class SalesOrderItemCreate(BaseModel):
    product_id: int
    ordered_quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(default=0, ge=0)
    notes: str | None = None


class SalesOrderCreate(BaseModel):
    customer_id: int
    order_number: str | None = Field(default=None, min_length=1, max_length=120)
    order_date: date
    expected_ship_date: date | None = None
    notes: str | None = None
    items: list[SalesOrderItemCreate] = Field(default_factory=list)


class SalesOrderUpdate(BaseModel):
    customer_id: int | None = None
    order_number: str | None = Field(default=None, min_length=1, max_length=120)
    order_date: date | None = None
    expected_ship_date: date | None = None
    notes: str | None = None
    items: list[SalesOrderItemCreate] | None = None


class SalesOrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    sales_order_id: int
    product_id: int
    ordered_quantity: Decimal
    reserved_quantity: Decimal
    fulfilled_quantity: Decimal
    unit_price: Decimal
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class SalesOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    customer_id: int
    order_number: str
    status: SalesOrderStatus
    order_date: date
    expected_ship_date: date | None = None
    notes: str | None = None
    created_by: int
    confirmed_at: datetime | None = None
    fulfilled_at: datetime | None = None
    cancelled_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    items: list[SalesOrderItemRead] = []


class SalesReservationAllocation(BaseModel):
    sales_order_item_id: int
    warehouse_id: int
    location_id: int
    quantity: Decimal = Field(gt=0)


class SalesOrderConfirmRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=120)
    note: str | None = None
    allocations: list[SalesReservationAllocation] = Field(default_factory=list)


class SalesFulfillmentItemCreate(BaseModel):
    sales_order_item_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    reservation_id: int
    fulfilled_quantity: Decimal = Field(gt=0)


class SalesFulfillmentCreate(BaseModel):
    fulfillment_number: str = Field(min_length=1, max_length=120)
    fulfilled_at: datetime | None = None
    notes: str | None = None
    items: list[SalesFulfillmentItemCreate] = Field(default_factory=list)


class SalesFulfillmentUpdate(BaseModel):
    fulfillment_number: str | None = Field(default=None, min_length=1, max_length=120)
    fulfilled_at: datetime | None = None
    notes: str | None = None
    items: list[SalesFulfillmentItemCreate] | None = None


class SalesFulfillmentItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    fulfillment_id: int
    sales_order_item_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    reservation_id: int
    fulfilled_quantity: Decimal
    created_at: datetime
    updated_at: datetime


class SalesFulfillmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    sales_order_id: int
    fulfillment_number: str
    status: SalesFulfillmentStatus
    fulfilled_by: int
    fulfilled_at: datetime | None = None
    committed_at: datetime | None = None
    cancelled_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[SalesFulfillmentItemRead] = []


class SalesFulfillmentCommitRequest(BaseModel):
    idempotency_key: str = Field(min_length=1, max_length=120)
    note: str | None = None


class SalesWorkflowSummary(BaseModel):
    sales_order: SalesOrderRead
    fulfillment: SalesFulfillmentRead | None = None
    stock_results: list[dict] = []
