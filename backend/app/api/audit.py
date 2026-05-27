from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles, require_super_admin, require_tenant_user
from app.models.auth import UserRole
from app.services.audit import AuditService
from app.services.auth import UserContext

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])
tenant_admin_roles = (UserRole.TENANT_ADMIN,)


@router.get("")
def list_audit_logs(
    tenant_id: int | None = Query(default=None),
    actor_user_id: int | None = Query(default=None),
    action: str | None = Query(default=None, max_length=120),
    entity_type: str | None = Query(default=None, max_length=120),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    context: UserContext = Depends(require_super_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    return AuditService(db).list_logs(tenant_id, actor_user_id, action, entity_type, date_from, date_to, limit, offset)


@router.get("/tenant")
def list_tenant_audit_logs(
    action: str | None = Query(default=None, max_length=120),
    entity_type: str | None = Query(default=None, max_length=120),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    context: UserContext = Depends(require_tenant_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return AuditService(db).list_logs(context.tenant_id, None, action, entity_type, date_from, date_to, limit, offset)
