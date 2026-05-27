from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.auth import Tenant, TenantStatus, UserRole
from app.repositories.admin import AdminRepository
from app.repositories.audit import AuditLogRepository
from app.schemas.admin import PlatformSummary, TenantAdminDetail, TenantAdminListRow


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
            "timestamp": datetime.now(UTC),
        }

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
