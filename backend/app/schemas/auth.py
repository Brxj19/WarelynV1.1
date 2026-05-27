from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.auth import TenantStatus, UserRole, UserStatus


class TenantCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    contact_email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    gst_number: str | None = Field(default=None, max_length=64)
    business_type: str | None = Field(default=None, max_length=120)
    status: TenantStatus = TenantStatus.ACTIVE


class TenantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_name: str
    contact_email: EmailStr
    phone: str | None = None
    address: str | None = None
    gst_number: str | None = None
    business_type: str | None = None
    status: TenantStatus
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    tenant_id: int | None = None
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int | None = None
    name: str
    email: EmailStr
    phone: str | None = None
    role: UserRole
    status: UserStatus
    email_verified_at: datetime | None = None
    phone_verified_at: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    tenant: TenantRead
    user: UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead
    tenant: TenantRead | None = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthMeResponse(BaseModel):
    user: UserRead
    tenant: TenantRead | None = None
    role: UserRole


class LogoutResponse(BaseModel):
    success: bool
