from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.auth import UserRole, UserStatus


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = None
    role: UserRole
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    role: UserRole | None = None


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int | None
    name: str
    email: str
    phone: str | None
    role: UserRole
    status: UserStatus
    email_verified_at: datetime | None
    phone_verified_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime | None


class UserResetPassword(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=100)
