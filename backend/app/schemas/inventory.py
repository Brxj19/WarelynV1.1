from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory import InventoryBatchStatus, InventorySerialStatus, MovementType, ReferenceType, ReservationStatus


class StockMutationBase(BaseModel):
    product_id: int
    warehouse_id: int
    location_id: int
    quantity: Decimal = Field(gt=0)
    reference_type: ReferenceType = ReferenceType.MANUAL
    reference_id: str | None = Field(default=None, max_length=120)
    note: str | None = None
    idempotency_key: str = Field(min_length=1, max_length=120)


class StockInRequest(StockMutationBase):
    batch_number: str | None = Field(default=None, max_length=120)
    supplier_batch_number: str | None = Field(default=None, max_length=120)
    manufacture_date: date | None = None
    expiry_date: date | None = None
    warranty_until: date | None = None
    serial_numbers: list[str] | None = None


class StockOutRequest(StockMutationBase):
    pass


class StockAdjustRequest(BaseModel):
    product_id: int
    warehouse_id: int
    location_id: int
    delta: Decimal
    reference_type: ReferenceType = ReferenceType.ADJUSTMENT
    reference_id: str | None = Field(default=None, max_length=120)
    note: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=120)


class ReserveStockRequest(StockMutationBase):
    reference_type: ReferenceType = ReferenceType.SALES_ORDER


class ReleaseReservationRequest(BaseModel):
    note: str | None = None
    idempotency_key: str = Field(min_length=1, max_length=120)


class DeductReservationRequest(BaseModel):
    note: str | None = None
    idempotency_key: str = Field(min_length=1, max_length=120)


class TransferStockRequest(BaseModel):
    product_id: int
    source_warehouse_id: int
    source_location_id: int
    destination_warehouse_id: int
    destination_location_id: int
    quantity: Decimal = Field(gt=0)
    reference_type: ReferenceType = ReferenceType.TRANSFER
    reference_id: str | None = Field(default=None, max_length=120)
    note: str | None = None
    idempotency_key: str = Field(min_length=1, max_length=120)


class WarehouseStockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal
    quantity_in_transit: Decimal = Decimal("0")
    quantity_qc_hold: Decimal = Decimal("0")
    quantity_damaged: Decimal = Decimal("0")
    quantity_expired: Decimal = Decimal("0")
    quantity_quarantine: Decimal = Decimal("0")
    updated_at: datetime


class StockLedgerEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    batch_id: int | None = None
    serial_id: int | None = None
    movement_type: MovementType
    quantity_delta: Decimal
    reserved_delta: Decimal
    available_delta: Decimal
    reference_type: ReferenceType
    reference_id: str | None = None
    idempotency_key: str
    note: str | None = None
    created_by: int
    created_at: datetime


class StockReservationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    quantity: Decimal
    status: ReservationStatus
    reference_type: ReferenceType
    reference_id: str | None = None
    created_by: int
    released_at: datetime | None = None
    deducted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class InventoryMutationResponse(BaseModel):
    stock: WarehouseStockRead | list[WarehouseStockRead]
    ledger_entries: list[StockLedgerEntryRead]
    reservation: StockReservationRead | None = None
    idempotency_key: str


class InventoryBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    batch_number: str
    supplier_batch_number: str | None = None
    manufacture_date: date | None = None
    expiry_date: date | None = None
    warranty_until: date | None = None
    quantity_on_hand: Decimal
    quantity_available: Decimal
    quantity_reserved: Decimal
    status: InventoryBatchStatus
    created_at: datetime
    updated_at: datetime


class InventorySerialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    product_id: int
    warehouse_id: int
    location_id: int
    batch_id: int | None = None
    serial_number: str
    status: InventorySerialStatus
    warranty_until: date | None = None
    expires_on: date | None = None
    created_at: datetime
    updated_at: datetime


class ReconciliationMismatch(BaseModel):
    product_id: int
    warehouse_id: int
    location_id: int
    expected_on_hand: Decimal
    actual_on_hand: Decimal
    expected_reserved: Decimal
    actual_reserved: Decimal
    expected_available: Decimal
    actual_available: Decimal


class ReconciliationDryRunResponse(BaseModel):
    tenant_id: int
    mismatch_count: int
    mismatches: list[ReconciliationMismatch]
