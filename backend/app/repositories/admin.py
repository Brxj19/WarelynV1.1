from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.auth import Tenant, TenantStatus, User
from app.models.inventory import StockLedgerEntry
from app.models.master_data import Product
from app.models.master_data import Warehouse
from app.models.purchasing import PurchaseOrder
from app.models.sales import SalesOrder


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

    def count_tenants_created_since(self, since: datetime) -> int:
        return self.db.scalar(select(func.count(Tenant.id)).where(Tenant.created_at >= since)) or 0

    def count_users_created_since(self, since: datetime) -> int:
        return self.db.scalar(select(func.count(User.id)).where(User.created_at >= since)) or 0

    def tenant_growth_by_month(self, months: int = 12) -> list[dict]:
        tenant_rows = list(self.db.scalars(select(Tenant).order_by(Tenant.created_at.asc())))
        if not tenant_rows:
            return []
        counts_by_month: dict[str, int] = {}
        for tenant in tenant_rows:
            month_key = tenant.created_at.astimezone(UTC).strftime("%Y-%m")
            counts_by_month[month_key] = counts_by_month.get(month_key, 0) + 1
        all_months = sorted(counts_by_month.keys())
        cumulative_by_month: dict[str, int] = {}
        cumulative = 0
        for month in all_months:
            cumulative += counts_by_month[month]
            cumulative_by_month[month] = cumulative
        window_months = all_months[-months:]
        return [
            {"month": month, "new_tenants": counts_by_month[month], "cumulative": cumulative_by_month[month]}
            for month in window_months
        ]

    def audit_activity_by_day(self, days: int = 30) -> list[dict]:
        since = datetime.now(UTC) - timedelta(days=max(days, 1) - 1)
        rows = self.db.execute(
            select(func.date(AuditLog.created_at), func.count(AuditLog.id))
            .where(AuditLog.created_at >= since)
            .group_by(func.date(AuditLog.created_at))
            .order_by(func.date(AuditLog.created_at).asc())
        ).all()
        values = {str(row[0]): int(row[1]) for row in rows}
        result = []
        cursor = since.date()
        today = datetime.now(UTC).date()
        while cursor <= today:
            key = cursor.isoformat()
            result.append({"date": key, "event_count": values.get(key, 0)})
            cursor += timedelta(days=1)
        return result

    def most_active_tenants(self, days: int = 30, limit: int = 10) -> list[dict]:
        since = datetime.now(UTC) - timedelta(days=max(days, 1))
        rows = self.db.execute(
            select(AuditLog.tenant_id, func.count(AuditLog.id))
            .where(AuditLog.tenant_id.is_not(None), AuditLog.created_at >= since)
            .group_by(AuditLog.tenant_id)
            .order_by(func.count(AuditLog.id).desc())
            .limit(limit)
        ).all()
        if not rows:
            return []
        tenant_ids = [int(row[0]) for row in rows if row[0] is not None]
        tenants = {row.id: row for row in self.db.scalars(select(Tenant).where(Tenant.id.in_(tenant_ids))).all()}
        user_counts = {
            int(row[0]): int(row[1])
            for row in self.db.execute(
                select(User.tenant_id, func.count(User.id))
                .where(User.tenant_id.in_(tenant_ids))
                .group_by(User.tenant_id)
            ).all()
        }
        product_counts = {
            int(row[0]): int(row[1])
            for row in self.db.execute(
                select(Product.tenant_id, func.count(Product.id))
                .where(Product.tenant_id.in_(tenant_ids))
                .group_by(Product.tenant_id)
            ).all()
        }
        result = []
        for tenant_id, event_count in rows:
            if tenant_id is None:
                continue
            tenant = tenants.get(int(tenant_id))
            if not tenant:
                continue
            result.append(
                {
                    "tenant_id": tenant.id,
                    "company_name": tenant.company_name,
                    "event_count": int(event_count),
                    "user_count": user_counts.get(tenant.id, 0),
                    "product_count": product_counts.get(tenant.id, 0),
                    "status": tenant.status.value,
                }
            )
        return result

    def recent_tenants(self, limit: int = 10) -> list[Tenant]:
        return list(self.db.scalars(select(Tenant).order_by(Tenant.created_at.desc()).limit(limit)))

    def tenant_activation_flags(self, tenant_id: int) -> dict[str, bool]:
        has_users = (self.db.scalar(select(func.count(User.id)).where(User.tenant_id == tenant_id)) or 0) > 0
        has_products = (self.db.scalar(select(func.count(Product.id)).where(Product.tenant_id == tenant_id)) or 0) > 0
        has_warehouse = (self.db.scalar(select(func.count(Warehouse.id)).where(Warehouse.tenant_id == tenant_id)) or 0) > 0
        has_orders = (
            (self.db.scalar(select(func.count(SalesOrder.id)).where(SalesOrder.tenant_id == tenant_id)) or 0)
            + (self.db.scalar(select(func.count(PurchaseOrder.id)).where(PurchaseOrder.tenant_id == tenant_id)) or 0)
        ) > 0
        return {
            "has_users": has_users,
            "has_products": has_products,
            "has_warehouse": has_warehouse,
            "has_orders": has_orders,
        }
