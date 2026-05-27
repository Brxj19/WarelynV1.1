from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth import RefreshToken, Tenant, TenantStatus, User, UserRole, UserStatus


class TenantRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, tenant_id: int) -> Tenant | None:
        return self.db.get(Tenant, tenant_id)

    def create(self, *, company_name: str, contact_email: str, phone: str | None = None) -> Tenant:
        tenant = Tenant(company_name=company_name, contact_email=contact_email.lower(), phone=phone, status=TenantStatus.ACTIVE)
        self.db.add(tenant)
        self.db.flush()
        return tenant

    def update(self, tenant: Tenant, **values: object) -> Tenant:
        for key, value in values.items():
            setattr(tenant, key, value)
        self.db.flush()
        return tenant


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def create(
        self,
        *,
        name: str,
        email: str,
        password_hash: str,
        role: UserRole,
        tenant_id: int | None = None,
        phone: str | None = None,
        status: UserStatus = UserStatus.ACTIVE,
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            name=name,
            email=email.lower(),
            phone=phone,
            password_hash=password_hash,
            role=role,
            status=status,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_last_login(self, user: User) -> User:
        user.last_login_at = datetime.now(UTC)
        self.db.flush()
        return user


class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, *, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        refresh_token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.db.add(refresh_token)
        self.db.flush()
        return refresh_token

    def find_by_hash(self, token_hash: str) -> RefreshToken | None:
        return self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))

    def revoke(self, refresh_token: RefreshToken) -> RefreshToken:
        refresh_token.revoked_at = datetime.now(UTC)
        self.db.flush()
        return refresh_token
