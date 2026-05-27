from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.dependencies.auth import require_tenant_user
from app.models.auth import UserRole, UserStatus
from app.schemas.users import UserCreate, UserRead, UserResetPassword, UserUpdate
from app.services.auth import UserContext
from app.services.users import UsersService

router = APIRouter(prefix="/users", tags=["users"])


def require_tenant_admin(context: UserContext = Depends(require_tenant_user)) -> UserContext:
    if context.role != UserRole.TENANT_ADMIN:
        raise AppError("FORBIDDEN", "Only tenant admins can manage users.", 403)
    return context


@router.get("", response_model=list[UserRead])
def list_users(
    search: str | None = Query(None),
    role: UserRole | None = Query(None),
    status: UserStatus | None = Query(None),
    context: UserContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    service = UsersService(db)
    users = service.list_users(context.tenant_id, search=search, role=role, status=status)
    return [UserRead.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    context: UserContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UsersService(db)
    user = service.get_user(context.tenant_id, user_id)
    return UserRead.model_validate(user)


@router.post("", response_model=UserRead, status_code=201)
def create_user(
    data: UserCreate,
    context: UserContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UsersService(db)
    user = service.create_user(context.tenant_id, context.user.id, data)
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    context: UserContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UsersService(db)
    user = service.update_user(context.tenant_id, context.user.id, user_id, data)
    return UserRead.model_validate(user)


@router.delete("/{user_id}", response_model=UserRead)
def delete_user(
    user_id: int,
    context: UserContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UsersService(db)
    user = service.disable_user(context.tenant_id, context.user.id, user_id)
    return UserRead.model_validate(user)


@router.post("/{user_id}/enable", response_model=UserRead)
def enable_user(
    user_id: int,
    context: UserContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UsersService(db)
    user = service.enable_user(context.tenant_id, context.user.id, user_id)
    return UserRead.model_validate(user)


@router.post("/{user_id}/disable", response_model=UserRead)
def disable_user(
    user_id: int,
    context: UserContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UsersService(db)
    user = service.disable_user(context.tenant_id, context.user.id, user_id)
    return UserRead.model_validate(user)


@router.post("/{user_id}/reset-password", response_model=UserRead)
def reset_password(
    user_id: int,
    data: UserResetPassword,
    context: UserContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    service = UsersService(db)
    user = service.reset_password(context.tenant_id, context.user.id, user_id, data.new_password)
    return UserRead.model_validate(user)
