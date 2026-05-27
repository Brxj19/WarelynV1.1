from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_super_admin
from app.models.auth import UserRole
from app.schemas.admin import PlatformSummary, TenantAdminDetail, TenantAdminListRow, TenantEnableDisableResponse
from app.services.admin import AdminService
from app.services.auth import UserContext

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/platform/summary", response_model=PlatformSummary)
def platform_summary(context: UserContext = Depends(require_super_admin), db: Session = Depends(get_db)) -> PlatformSummary:
    return AdminService(db).get_platform_summary()


@router.get("/platform/health")
def platform_health(context: UserContext = Depends(require_super_admin), db: Session = Depends(get_db)) -> dict:
    return AdminService(db).get_platform_health()


@router.get("/tenants", response_model=list[TenantAdminListRow])
def list_tenants(
    search: str | None = Query(default=None, max_length=255),
    status: str | None = Query(default=None),
    context: UserContext = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> list[TenantAdminListRow]:
    return AdminService(db).list_tenants(search, status)


@router.get("/tenants/{tenant_id}", response_model=TenantAdminDetail)
def get_tenant(tenant_id: int, context: UserContext = Depends(require_super_admin), db: Session = Depends(get_db)) -> TenantAdminDetail:
    return AdminService(db).get_tenant_detail(tenant_id)


@router.post("/tenants/{tenant_id}/enable", response_model=TenantEnableDisableResponse)
def enable_tenant(tenant_id: int, context: UserContext = Depends(require_super_admin), db: Session = Depends(get_db)) -> TenantEnableDisableResponse:
    return AdminService(db).enable_tenant(tenant_id, context.user.id, context.role.value)


@router.post("/tenants/{tenant_id}/disable", response_model=TenantEnableDisableResponse)
def disable_tenant(tenant_id: int, context: UserContext = Depends(require_super_admin), db: Session = Depends(get_db)) -> TenantEnableDisableResponse:
    return AdminService(db).disable_tenant(tenant_id, context.user.id, context.role.value)
