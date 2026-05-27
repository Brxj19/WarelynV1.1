from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, hash_token, verify_password
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.repositories.auth import RefreshTokenRepository, TenantRepository, UserRepository
from app.schemas.auth import LoginResponse, RegisterRequest, RegisterResponse, TokenRefreshResponse


@dataclass(frozen=True)
class UserContext:
    user: User
    tenant: Tenant | None
    tenant_id: int | None
    role: UserRole


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tenants = TenantRepository(db)
        self.users = UserRepository(db)
        self.refresh_tokens = RefreshTokenRepository(db)

    def register_tenant_admin(self, request: RegisterRequest) -> RegisterResponse:
        if self.users.get_by_email(request.email):
            raise AppError("DUPLICATE_EMAIL", "A user with this email already exists.", 409)

        tenant = self.tenants.create(company_name=request.company_name, contact_email=str(request.email), phone=request.phone)
        user = self.users.create(
            tenant_id=tenant.id,
            name=request.name,
            email=str(request.email),
            phone=request.phone,
            password_hash=get_password_hash(request.password),
            role=UserRole.TENANT_ADMIN,
        )

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_EMAIL", "A user with this email already exists.", 409) from exc

        self.db.refresh(tenant)
        self.db.refresh(user)
        return RegisterResponse(tenant=tenant, user=user)

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Invalid email or password.", 401)

        self._validate_active_user(user)
        return user

    def login(self, email: str, password: str) -> LoginResponse:
        user = self.authenticate_user(email, password)
        self.users.update_last_login(user)
        access_token, refresh_token = self.issue_tokens(user)
        self.db.commit()
        self.db.refresh(user)
        return LoginResponse(access_token=access_token, refresh_token=refresh_token, user=user, tenant=user.tenant)

    def issue_tokens(self, user: User) -> tuple[str, str]:
        access_token = create_access_token(
            str(user.id),
            {"tenant_id": user.tenant_id, "role": user.role.value},
        )
        refresh_token, expires_at = create_refresh_token(str(user.id))
        self.refresh_tokens.create(user_id=user.id, token_hash=hash_token(refresh_token), expires_at=expires_at)
        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> TokenRefreshResponse:
        payload = decode_token(refresh_token, "refresh")
        user_id = int(str(payload["sub"]))
        stored_token = self.refresh_tokens.find_by_hash(hash_token(refresh_token))
        if not stored_token or stored_token.user_id != user_id:
            raise AppError("INVALID_TOKEN", "Refresh token is invalid.", 401)
        if stored_token.revoked_at is not None:
            raise AppError("INVALID_TOKEN", "Refresh token has been revoked.", 401)
        if stored_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            raise AppError("EXPIRED_TOKEN", "Refresh token has expired.", 401)

        user = self.users.get_by_id(user_id)
        if not user:
            raise AppError("INVALID_TOKEN", "Refresh token user is invalid.", 401)
        self._validate_active_user(user)

        access_token = create_access_token(str(user.id), {"tenant_id": user.tenant_id, "role": user.role.value})
        return TokenRefreshResponse(access_token=access_token)

    def logout(self, refresh_token: str | None) -> bool:
        if not refresh_token:
            return True
        stored_token = self.refresh_tokens.find_by_hash(hash_token(refresh_token))
        if stored_token and stored_token.revoked_at is None:
            self.refresh_tokens.revoke(stored_token)
            self.db.commit()
        return True

    def get_current_user_context(self, access_token: str) -> UserContext:
        payload = decode_token(access_token, "access")
        user = self.users.get_by_id(int(str(payload["sub"])))
        if not user:
            raise AppError("INVALID_TOKEN", "Token user is invalid.", 401)
        self._validate_active_user(user)
        return UserContext(user=user, tenant=user.tenant, tenant_id=user.tenant_id, role=user.role)

    def ensure_super_admin(self, *, email: str, password: str, name: str) -> User:
        existing = self.users.get_by_email(email)
        if existing:
            return existing
        user = self.users.create(
            tenant_id=None,
            name=name,
            email=email,
            password_hash=get_password_hash(password),
            role=UserRole.SUPER_ADMIN,
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def _validate_active_user(self, user: User) -> None:
        if user.status != UserStatus.ACTIVE:
            raise AppError("DISABLED_USER", "User is not active.", 403)
        if user.role != UserRole.SUPER_ADMIN:
            if not user.tenant:
                raise AppError("TENANT_ACCESS_DENIED", "Tenant context is required.", 403)
            if user.tenant.status != TenantStatus.ACTIVE:
                raise AppError("DISABLED_TENANT", "Tenant is not active.", 403)


class TenantService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tenants = TenantRepository(db)

    def get_active_tenant(self, tenant_id: int) -> Tenant:
        tenant = self.tenants.get_by_id(tenant_id)
        if not tenant:
            raise AppError("TENANT_NOT_FOUND", "Tenant was not found.", 404)
        if tenant.status != TenantStatus.ACTIVE:
            raise AppError("DISABLED_TENANT", "Tenant is not active.", 403)
        return tenant
