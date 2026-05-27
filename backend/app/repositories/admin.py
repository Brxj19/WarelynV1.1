from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.auth import Tenant, TenantStatus, User
from app.models.inventory import StockLedgerEntry
from app.models.master_data import Product


class AdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def count_tenants(self) -> int:
        return self.db.scalar(select(func.count(Tenant.id))) or 0

    def count_tenants_by_status(self, status: TenantStatus) -> int:
        return self.db.scalar(select(func.count(Tenant.id)).where(Tenant.status == status)) or 0

    def count_users(self) -> int:
        return self.db.scalar(select(func.count(User.id))) or 0

    def count_products(self) -> int:
        return self.db.scalar(select(func.count(Product.id))) or 0

    def count_ledger_entries(self) -> int:
        return self.db.scalar(select(func.count(StockLedgerEntry.id))) or 0

    def list_tenants(self, search: str | None = None, status: str | None = None) -> list[Tenant]:
        query = select(Tenant)
        if status:
            query = query.where(Tenant.status == TenantStatus(status))
        if search:
            term = f"%{search.strip()}%"
            query = query.where(Tenant.company_name.ilike(term) | Tenant.contact_email.ilike(term))
        query = query.order_by(Tenant.created_at.desc())
        return list(self.db.scalars(query))

    def get_tenant(self, tenant_id: int) -> Tenant | None:
        return self.db.get(Tenant, tenant_id)

    def count_users_for_tenant(self, tenant_id: int) -> int:
        return self.db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id)) or 0

    def count_products_for_tenant(self, tenant_id: int) -> int:
        return self.db.scalar(select(func.count(Product.id)).where(Product.tenant_id == tenant_id)) or 0

    def is_super_admin_only_tenant_admin(self, tenant_id: int) -> bool:
        active_super_admins = self.db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id, User.role == "SUPER_ADMIN"))
        return (active_super_admins or 0) > 0
