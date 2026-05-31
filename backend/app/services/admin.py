from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.auth import TenantStatus
from app.repositories.admin import AdminRepository
from app.repositories.audit import AuditLogRepository
from app.schemas.admin import (
    PlatformDashboard,
    PlatformSummary,
    RecentTenantRow,
    TenantAdminDetail,
    TenantAdminListRow,
)


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AdminRepository(db)
        self.audit_logs = AuditLogRepository(db)

    def get_platform_summary(self) -> PlatformSummary:
        return PlatformSummary(
            total_tenants=self.repository.count_tenants(),
            active_tenants=self.repository.count_tenants_by_status(TenantStatus.ACTIVE),
            disabled_tenants=self.repository.count_tenants_by_status(TenantStatus.DISABLED),
            total_users=self.repository.count_users(),
            total_products=self.repository.count_products(),
            stock_ledger_count=self.repository.count_ledger_entries(),
            recent_audit_events=self.audit_logs.count_logs(),
        )

    def get_platform_health(self) -> dict:
        return {
            "database_status": "connected",
            "app_status": "healthy",
            "ledger_integrity_ok": True,
            "timestamp": datetime.now(UTC),
        }

    def get_platform_dashboard(self) -> PlatformDashboard:
        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_end = month_start - timedelta(microseconds=1)
        prev_month_start = prev_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        recent_tenants_raw = self.repository.recent_tenants(limit=10)
        recent_tenants = []
        for tenant in recent_tenants_raw:
            flags = self.repository.tenant_activation_flags(tenant.id)
            recent_tenants.append(
                RecentTenantRow(
                    tenant_id=tenant.id,
                    company_name=tenant.company_name,
                    contact_email=tenant.contact_email,
                    status=tenant.status.value,
                    created_at=tenant.created_at,
                    has_users=flags["has_users"],
                    has_products=flags["has_products"],
                    has_warehouse=flags["has_warehouse"],
                    has_orders=flags["has_orders"],
                )
            )

        health = self.get_platform_health()

        return PlatformDashboard(
            total_tenants=self.repository.count_tenants(),
            active_tenants=self.repository.count_tenants_by_status(TenantStatus.ACTIVE),
            disabled_tenants=self.repository.count_tenants_by_status(TenantStatus.DISABLED),
            new_tenants_mtd=self.repository.count_tenants_created_since(month_start),
            new_tenants_prev_month=self.repository.count_tenants_created_since(prev_month_start)
            - self.repository.count_tenants_created_since(month_start),
            total_users=self.repository.count_users(),
            new_users_mtd=self.repository.count_users_created_since(month_start),
            total_products=self.repository.count_products(),
            stock_ledger_count=self.repository.count_ledger_entries(),
            recent_audit_events=self.audit_logs.count_logs(since=now - timedelta(hours=24)),
            audit_events_7d=self.audit_logs.count_logs(since=now - timedelta(days=7)),
            tenant_growth_by_month=self.repository.tenant_growth_by_month(months=12),
            audit_activity_by_day=self.repository.audit_activity_by_day(days=30),
            most_active_tenants=self.repository.most_active_tenants(days=30, limit=10),
            recent_tenants=recent_tenants,
            platform_health=health,
        )

    def list_tenants(self, search: str | None = None, status: str | None = None) -> list[TenantAdminListRow]:
        tenants = self.repository.list_tenants(search, status)
        result = []
        for tenant in tenants:
            result.append(
                TenantAdminListRow(
                    id=tenant.id,
                    company_name=tenant.company_name,
                    contact_email=tenant.contact_email,
                    status=tenant.status,
                    users_count=self.repository.count_users_for_tenant(tenant.id),
                    products_count=self.repository.count_products_for_tenant(tenant.id),
                    created_at=tenant.created_at,
                )
            )
        return result

    def get_tenant_detail(self, tenant_id: int) -> TenantAdminDetail:
        tenant = self.repository.get_tenant(tenant_id)
        if tenant is None:
            raise AppError("TENANT_NOT_FOUND", "Tenant was not found.", 404)
        return TenantAdminDetail(
            id=tenant.id,
            company_name=tenant.company_name,
            contact_email=tenant.contact_email,
            phone=tenant.phone,
            address=tenant.address,
            gst_number=tenant.gst_number,
            business_type=tenant.business_type,
            status=tenant.status,
            users_count=self.repository.count_users_for_tenant(tenant.id),
            products_count=self.repository.count_products_for_tenant(tenant.id),
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )

    def enable_tenant(self, tenant_id: int, actor_user_id: int, actor_role: str) -> dict:
        tenant = self.repository.get_tenant(tenant_id)
        if tenant is None:
            raise AppError("TENANT_NOT_FOUND", "Tenant was not found.", 404)
        if tenant.status == TenantStatus.ACTIVE:
            return {"success": True, "tenant_id": tenant.id, "status": tenant.status.value}
        tenant.status = TenantStatus.ACTIVE
        self.db.flush()
        self.audit_logs.create(
            {
                "tenant_id": tenant_id,
                "actor_user_id": actor_user_id,
                "actor_role": actor_role,
                "action": "TENANT_ENABLE",
                "entity_type": "tenant",
                "entity_id": str(tenant_id),
            }
        )
        self.db.commit()
        return {"success": True, "tenant_id": tenant.id, "status": tenant.status.value}

    def disable_tenant(self, tenant_id: int, actor_user_id: int, actor_role: str) -> dict:
        tenant = self.repository.get_tenant(tenant_id)
        if tenant is None:
            raise AppError("TENANT_NOT_FOUND", "Tenant was not found.", 404)
        if tenant.status == TenantStatus.DISABLED:
            return {"success": True, "tenant_id": tenant.id, "status": tenant.status.value}
        if self.repository.is_super_admin_only_tenant_admin(tenant_id):
            raise AppError("TENANT_HAS_SUPER_ADMINS", "Tenant has super admin users and cannot be disabled through this API.", 409)
        tenant.status = TenantStatus.DISABLED
        self.db.flush()
        self.audit_logs.create(
            {
                "tenant_id": tenant_id,
                "actor_user_id": actor_user_id,
                "actor_role": actor_role,
                "action": "TENANT_DISABLE",
                "entity_type": "tenant",
                "entity_id": str(tenant_id),
            }
        )
        self.db.commit()
        return {"success": True, "tenant_id": tenant.id, "status": tenant.status.value}
