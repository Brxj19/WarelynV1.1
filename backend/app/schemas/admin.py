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


class TenantGrowthMonth(BaseModel):
    month: str
    new_tenants: int
    cumulative: int


class AuditActivityDay(BaseModel):
    date: str
    event_count: int


class ActiveTenantRow(BaseModel):
    tenant_id: int
    company_name: str
    event_count: int
    user_count: int
    product_count: int
    status: str


class RecentTenantRow(BaseModel):
    tenant_id: int
    company_name: str
    contact_email: str
    status: str
    created_at: datetime
    has_users: bool
    has_products: bool
    has_warehouse: bool
    has_orders: bool


class PlatformDashboard(BaseModel):
    total_tenants: int
    active_tenants: int
    disabled_tenants: int
    new_tenants_mtd: int
    new_tenants_prev_month: int
    total_users: int
    new_users_mtd: int
    total_products: int
    stock_ledger_count: int
    recent_audit_events: int
    audit_events_7d: int
    tenant_growth_by_month: list[TenantGrowthMonth]
    audit_activity_by_day: list[AuditActivityDay]
    most_active_tenants: list[ActiveTenantRow]
    recent_tenants: list[RecentTenantRow]
    platform_health: dict


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
