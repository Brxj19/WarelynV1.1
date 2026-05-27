from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles, require_tenant_user
from app.models.auth import UserRole
from app.schemas.settings import TenantSettingsRead, TenantSettingsUpdate, UserPreferencesRead, UserPreferencesUpdate
from app.services.auth import UserContext
from app.services.settings import TenantSettingsService, UserPreferencesService
from app.utils.currency import SUPPORTED_CURRENCIES

router = APIRouter(prefix="/settings", tags=["settings"])
tenant_admin_roles = (UserRole.TENANT_ADMIN,)
read_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PURCHASE_STAFF, UserRole.SALES_STAFF, UserRole.VIEWER)


@router.get("/currencies")
def list_currencies(context: UserContext = Depends(require_roles(*read_roles))) -> list[dict]:
    return [{"code": code, **info} for code, info in SUPPORTED_CURRENCIES.items()]


@router.get("/tenant", response_model=TenantSettingsRead)
def get_tenant_settings(context: UserContext = Depends(require_roles(*tenant_admin_roles)), db: Session = Depends(get_db)) -> TenantSettingsRead:
    return TenantSettingsService(db).get_settings(context.tenant_id)


@router.patch("/tenant", response_model=TenantSettingsRead)
def update_tenant_settings(
    request: TenantSettingsUpdate,
    context: UserContext = Depends(require_roles(*tenant_admin_roles)),
    db: Session = Depends(get_db),
) -> TenantSettingsRead:
    return TenantSettingsService(db).update_settings(context.tenant_id, request.model_dump(exclude_unset=True), actor_user_id=context.user.id, actor_role=context.role.value)


@router.get("/preferences", response_model=UserPreferencesRead)
def get_preferences(context: UserContext = Depends(require_tenant_user), db: Session = Depends(get_db)) -> UserPreferencesRead:
    return UserPreferencesService(db).get_preferences(context.user.id)


@router.patch("/preferences", response_model=UserPreferencesRead)
def update_preferences(
    request: UserPreferencesUpdate,
    context: UserContext = Depends(require_tenant_user),
    db: Session = Depends(get_db),
) -> UserPreferencesRead:
    return UserPreferencesService(db).update_preferences(context.user.id, request.model_dump(exclude_unset=True), actor_role=context.role.value, tenant_id=context.tenant_id)
