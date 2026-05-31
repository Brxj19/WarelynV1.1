import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

import jwt

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, hash_token, verify_password
from app.models.communication import OTPPurpose
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.repositories.auth import RefreshTokenRepository, TenantRepository, UserRepository
from app.schemas.auth import LoginResponse, RegisterRequest, RegisterResponse, TokenRefreshResponse
from app.services.email_service import send_password_reset_email, send_password_reset_link_email


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

    def request_password_reset(self, email: str) -> None:
        normalized_email = email.lower().strip()
        user = self.users.get_by_email(normalized_email)
        if user is None or user.status != UserStatus.ACTIVE:
            return

        code = f"{secrets.randbelow(900000) + 100000}"
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        self.users.create_password_reset_otp(user.id, user.tenant_id, user.email, code_hash)
        self.db.commit()
        try:
            send_password_reset_email(user.email, code)
        except Exception:
            pass

    def verify_reset_code(self, email: str, code: str) -> str:
        normalized_email = email.lower().strip()
        user = self.users.get_by_email(normalized_email)
        if user is None or user.status != UserStatus.ACTIVE:
            raise AppError("INVALID_RESET_CODE", "Invalid or expired reset code.", 400)

        otp = self.users.get_active_reset_otp(user.id)
        if otp is None:
            raise AppError("INVALID_RESET_CODE", "Invalid or expired reset code.", 400)

        otp.attempt_count += 1
        if otp.attempt_count > otp.max_attempts:
            self.db.commit()
            raise AppError("RESET_CODE_ATTEMPTS_EXCEEDED", "Too many attempts. Request a new reset code.", 429)

        code_hash = hashlib.sha256(code.encode()).hexdigest()
        if otp.code_hash != code_hash:
            self.db.commit()
            raise AppError("INVALID_RESET_CODE", "Invalid or expired reset code.", 400)

        reset_token = self._create_reset_token(user.id, otp.id)
        self.db.commit()
        return reset_token

    def reset_password(self, reset_token: str, new_password: str) -> None:
        payload = self._decode_reset_token(reset_token)

        try:
            user_id = int(str(payload["sub"]))
            otp_id = int(str(payload["otp_id"]))
        except Exception as exc:  # pragma: no cover - defensive guard
            raise AppError("INVALID_RESET_TOKEN", "Reset token is invalid or expired.", 400) from exc

        user = self.users.get_by_id(user_id)
        if user is None or user.status != UserStatus.ACTIVE:
            raise AppError("INVALID_RESET_TOKEN", "Reset token is invalid or expired.", 400)

        otp = self.users.get_otp_by_id(otp_id)
        if otp is None or otp.user_id != user.id or otp.purpose != OTPPurpose.PASSWORD_RESET:
            raise AppError("INVALID_RESET_TOKEN", "Reset token is invalid or expired.", 400)
        if otp.consumed_at is not None:
            raise AppError("RESET_TOKEN_ALREADY_USED", "This reset token has already been used.", 400)
        if otp.superseded_at is not None or self._ensure_aware(otp.expires_at) <= datetime.now(UTC):
            raise AppError("INVALID_RESET_TOKEN", "Reset token is invalid or expired.", 400)

        self._validate_password_strength(new_password)
        user.password_hash = get_password_hash(new_password)
        self.users.consume_reset_otp(otp_id)
        self.refresh_tokens.revoke_all_for_user(user.id)
        self.db.commit()

    def send_admin_password_reset_link(self, user: User) -> None:
        if user.status != UserStatus.ACTIVE:
            raise AppError("INACTIVE_USER", "Password reset link can only be sent to active users.", 400)

        one_time_secret = secrets.token_urlsafe(32)
        code_hash = hashlib.sha256(one_time_secret.encode()).hexdigest()
        otp = self.users.create_password_reset_otp(user.id, user.tenant_id, user.email, code_hash)
        reset_token = self._create_reset_token(user.id, otp.id)
        reset_url = self._build_password_reset_url(reset_token)
        self.db.commit()
        try:
            send_password_reset_link_email(user.email, reset_url)
        except Exception:
            pass

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

    def _create_reset_token(self, user_id: int, otp_id: int) -> str:
        settings = get_settings()
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        payload: dict[str, object] = {
            "sub": str(user_id),
            "otp_id": otp_id,
            "purpose": "password_reset",
            "type": "password_reset",
            "exp": expires_at,
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def _build_password_reset_url(self, reset_token: str) -> str:
        settings = get_settings()
        base_url = settings.cors_origins[0] if settings.cors_origins else "http://localhost:5173"
        return f"{base_url.rstrip('/')}/forgot-password?token={reset_token}"

    def _decode_reset_token(self, reset_token: str) -> dict[str, object]:
        settings = get_settings()
        try:
            payload = jwt.decode(reset_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        except jwt.ExpiredSignatureError as exc:
            raise AppError("INVALID_RESET_TOKEN", "Reset token is invalid or expired.", 400) from exc
        except jwt.PyJWTError as exc:
            raise AppError("INVALID_RESET_TOKEN", "Reset token is invalid or expired.", 400) from exc

        if payload.get("type") != "password_reset" or payload.get("purpose") != "password_reset":
            raise AppError("INVALID_RESET_TOKEN", "Reset token is invalid or expired.", 400)
        if payload.get("sub") is None or payload.get("otp_id") is None:
            raise AppError("INVALID_RESET_TOKEN", "Reset token is invalid or expired.", 400)
        return payload

    def _validate_password_strength(self, password: str) -> None:
        if len(password) < 8:
            raise AppError("WEAK_PASSWORD", "Password must be at least 8 characters long.", 400)

    def _ensure_aware(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt


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
