from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.auth import TenantStatus


class PlatformSummary(BaseModel):
    total_tenants: int
    active_tenants: int
    disabled_tenants: int
    total_users: int
    total_products: int
    stock_ledger_count: int
    recent_audit_events: int


class PlatformHealth(BaseModel):
    database_status: str
    app_status: str
    timestamp: datetime


class TenantAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    contact_email: str
    phone: str | None = None
    address: str | None = None
    gst_number: str | None = None
    business_type: str | None = None
    status: TenantStatus
    created_at: datetime
    updated_at: datetime


class TenantAdminListRow(BaseModel):
    id: int
    company_name: str
    contact_email: str
    status: TenantStatus
    users_count: int = 0
    products_count: int = 0
    created_at: datetime


class TenantAdminDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    contact_email: str
    phone: str | None = None
    address: str | None = None
    gst_number: str | None = None
    business_type: str | None = None
    status: TenantStatus
    users_count: int = 0
    products_count: int = 0
    warehouses_count: int = 0
    created_at: datetime
    updated_at: datetime


class TenantEnableDisableResponse(BaseModel):
    success: bool
    tenant_id: int
    status: TenantStatus
