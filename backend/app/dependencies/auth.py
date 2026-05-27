from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.auth import User, UserRole
from app.services.auth import AuthService, UserContext

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if credentials is None or not credentials.credentials:
        raise AppError("MISSING_TOKEN", "Authentication token is required.", 401)
    return credentials.credentials


def get_current_user_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserContext:
    token = _extract_bearer_token(credentials)
    return AuthService(db).get_current_user_context(token)


def get_current_user(context: UserContext = Depends(get_current_user_context)) -> User:
    return context.user


def require_roles(*allowed_roles: UserRole) -> Callable[[UserContext], UserContext]:
    def dependency(context: UserContext = Depends(get_current_user_context)) -> UserContext:
        if context.role not in allowed_roles:
            raise AppError("FORBIDDEN_ROLE", "Your role is not allowed to perform this action.", 403)
        return context

    return dependency


def require_tenant_user(context: UserContext = Depends(get_current_user_context)) -> UserContext:
    if context.role == UserRole.SUPER_ADMIN or context.tenant_id is None:
        raise AppError("TENANT_ACCESS_DENIED", "Tenant user context is required.", 403)
    return context


def require_super_admin(context: UserContext = Depends(require_roles(UserRole.SUPER_ADMIN))) -> UserContext:
    return context
