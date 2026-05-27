from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.auth import User, UserRole, UserStatus


class UsersRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_users(
        self,
        tenant_id: int,
        search: str | None = None,
        role: UserRole | None = None,
        status: UserStatus | None = None,
    ) -> list[User]:
        query = select(User).where(User.tenant_id == tenant_id)
        if search:
            pattern = f"%{search}%"
            query = query.where(or_(User.name.ilike(pattern), User.email.ilike(pattern)))
        if role is not None:
            query = query.where(User.role == role)
        if status is not None:
            query = query.where(User.status == status)
        query = query.order_by(User.created_at.desc())
        return list(self.db.scalars(query))

    def get_user(self, tenant_id: int, user_id: int) -> User | None:
        return self.db.scalar(
            select(User).where(User.id == user_id, User.tenant_id == tenant_id)
        )

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def create_user(
        self,
        tenant_id: int,
        name: str,
        email: str,
        phone: str | None,
        password_hash: str,
        role: UserRole,
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            name=name,
            email=email.lower(),
            phone=phone,
            password_hash=password_hash,
            role=role,
            status=UserStatus.ACTIVE,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_user(self, user: User, **values: object) -> User:
        for key, value in values.items():
            if value is not None:
                setattr(user, key, value)
        self.db.flush()
        return user

    def disable_user(self, user: User) -> User:
        user.status = UserStatus.DISABLED
        self.db.flush()
        return user

    def enable_user(self, user: User) -> User:
        user.status = UserStatus.ACTIVE
        self.db.flush()
        return user

    def count_users(self, tenant_id: int) -> int:
        result = self.db.scalar(
            select(func.count(User.id)).where(User.tenant_id == tenant_id)
        )
        return result or 0
