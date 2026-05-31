from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.communication import OTPPurpose, OTPSource, OTPVerification
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

    def create_password_reset_otp(self, user_id: int, tenant_id: int | None, email: str, code_hash: str) -> OTPVerification:
        self.db.execute(
            update(OTPVerification)
            .where(
                OTPVerification.user_id == user_id,
                OTPVerification.purpose == OTPPurpose.PASSWORD_RESET,
                OTPVerification.consumed_at == None,
                OTPVerification.superseded_at == None,
            )
            .values(superseded_at=datetime.now(timezone.utc))
        )
        otp = OTPVerification(
            tenant_id=tenant_id,
            user_id=user_id,
            destination_type=OTPSource.EMAIL,
            destination=email,
            purpose=OTPPurpose.PASSWORD_RESET,
            code_hash=code_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            max_attempts=5,
        )
        self.db.add(otp)
        self.db.flush()
        return otp

    def get_active_reset_otp(self, user_id: int) -> OTPVerification | None:
        return self.db.scalar(
            select(OTPVerification)
            .where(
                OTPVerification.user_id == user_id,
                OTPVerification.purpose == OTPPurpose.PASSWORD_RESET,
                OTPVerification.consumed_at == None,
                OTPVerification.superseded_at == None,
                OTPVerification.expires_at > datetime.now(timezone.utc),
            )
            .order_by(OTPVerification.created_at.desc())
            .limit(1)
        )

    def get_otp_by_id(self, otp_id: int) -> OTPVerification | None:
        return self.db.get(OTPVerification, otp_id)

    def consume_reset_otp(self, otp_id: int) -> None:
        self.db.execute(
            update(OTPVerification).where(OTPVerification.id == otp_id).values(consumed_at=datetime.now(timezone.utc))
        )
        self.db.flush()


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

    def revoke_all_for_user(self, user_id: int) -> None:
        self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at == None,
            )
            .values(revoked_at=datetime.now(UTC))
        )
        self.db.flush()
