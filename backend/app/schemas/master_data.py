import enum
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.master_data import LocationType, RecordStatus


class TenantReadMixin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


class NamedCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE


class NamedUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: RecordStatus | None = None


class CategoryCreate(NamedCreate):
    pass


class CategoryUpdate(NamedUpdate):
    pass


class CategoryRead(TenantReadMixin):
    name: str
    description: str | None = None


class BrandCreate(NamedCreate):
    pass


class BrandUpdate(NamedUpdate):
    pass


class BrandRead(TenantReadMixin):
    name: str
    description: str | None = None


class PartyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    gst_number: str | None = Field(default=None, max_length=64)
    status: RecordStatus = RecordStatus.ACTIVE


class PartyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    gst_number: str | None = Field(default=None, max_length=64)
    status: RecordStatus | None = None


class VendorCreate(PartyCreate):
    pass


class VendorUpdate(PartyUpdate):
    pass


class VendorRead(TenantReadMixin):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    gst_number: str | None = None


class CustomerCreate(PartyCreate):
    pass


class CustomerUpdate(PartyUpdate):
    pass


class CustomerRead(VendorRead):
    pass


class ProductBase(BaseModel):
    category_id: int | None = None
    brand_id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    sku: str = Field(min_length=1, max_length=120)
    barcode: str | None = Field(default=None, max_length=120)
    description: str | None = None
    unit: str = Field(default="pcs", min_length=1, max_length=50)
    cost_price: Decimal | None = Field(default=None, ge=0)
    selling_price: Decimal | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    track_batch: bool = False
    track_expiry: bool = False
    track_serial: bool = False
    status: RecordStatus = RecordStatus.ACTIVE

    @field_validator("barcode", mode="before")
    @classmethod
    def blank_barcode_to_none(cls, value: str | None) -> str | None:
        return value or None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    category_id: int | None = None
    brand_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=120)
    barcode: str | None = Field(default=None, max_length=120)
    description: str | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=50)
    cost_price: Decimal | None = Field(default=None, ge=0)
    selling_price: Decimal | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    track_batch: bool | None = None
    track_expiry: bool | None = None
    track_serial: bool | None = None
    status: RecordStatus | None = None

    @field_validator("barcode", mode="before")
    @classmethod
    def blank_barcode_to_none(cls, value: str | None) -> str | None:
        return value or None


class ProductRead(TenantReadMixin):
    category_id: int | None = None
    brand_id: int | None = None
    name: str
    sku: str
    barcode: str | None = None
    description: str | None = None
    unit: str
    cost_price: Decimal | None = None
    selling_price: Decimal | None = None
    reorder_level: int | None = None
    track_batch: bool
    track_expiry: bool
    track_serial: bool


class ProductStockLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    warehouse_id: int
    warehouse_name: str
    location_id: int
    location_name: str
    quantity_on_hand: Decimal
    quantity_available: Decimal
    quantity_reserved: Decimal


class ProductBatchDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_number: str
    supplier_batch_number: str | None = None
    manufacture_date: date | None = None
    expiry_date: date | None = None
    warranty_until: date | None = None
    warehouse_id: int
    warehouse_name: str
    location_id: int
    location_name: str
    quantity_on_hand: Decimal
    quantity_available: Decimal
    quantity_reserved: Decimal
    status: str
    qr_payload: str
    qr_matrix: list[list[bool]]


class ProductSerialDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    serial_number: str
    batch_id: int | None = None
    batch_number: str | None = None
    warranty_until: date | None = None
    expires_on: date | None = None
    warehouse_id: int
    warehouse_name: str
    location_id: int
    location_name: str
    status: str
    qr_payload: str
    qr_matrix: list[list[bool]]


class ProductDetailRead(ProductRead):
    category_name: str | None = None
    brand_name: str | None = None
    available_quantity: Decimal
    qr_payload: str
    qr_matrix: list[list[bool]]
    stock_rows: list[ProductStockLocationRead] = Field(default_factory=list)
    batches: list[ProductBatchDetailRead] = Field(default_factory=list)
    serials: list[ProductSerialDetailRead] = Field(default_factory=list)


class ProductLabelTrackingMode(str, enum.Enum):
    ALL = "ALL"
    TRACKED = "TRACKED"
    STANDARD = "STANDARD"
    BATCH = "BATCH"
    EXPIRY = "EXPIRY"
    SERIAL = "SERIAL"


class ProductLabelPrintRequest(BaseModel):
    product_ids: list[int] = Field(min_length=1)
    tracking_mode: ProductLabelTrackingMode = ProductLabelTrackingMode.ALL


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64)
    address: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=64)
    address: str | None = None
    status: RecordStatus | None = None


class WarehouseRead(TenantReadMixin):
    name: str
    code: str
    address: str | None = None


class WarehouseLocationCreate(BaseModel):
    parent_location_id: int | None = None
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    barcode: str | None = Field(default=None, max_length=120)
    location_type: LocationType = LocationType.STORAGE
    status: RecordStatus = RecordStatus.ACTIVE
    sort_order: int = 0

    @field_validator("barcode", mode="before")
    @classmethod
    def blank_barcode_to_none(cls, value: str | None) -> str | None:
        return value or None


class WarehouseLocationUpdate(BaseModel):
    parent_location_id: int | None = None
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    barcode: str | None = Field(default=None, max_length=120)
    location_type: LocationType | None = None
    status: RecordStatus | None = None
    sort_order: int | None = None


class WarehouseLocationRead(TenantReadMixin):
    warehouse_id: int
    parent_location_id: int | None = None
    code: str
    name: str
    barcode: str | None = None
    location_type: LocationType
    sort_order: int
