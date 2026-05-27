from datetime import datetime

from pydantic import BaseModel, Field


class VerificationSendRequest(BaseModel):
    pass


class VerificationSendResponse(BaseModel):
    success: bool = True
    message: str = "Verification code sent."
    development_code: str | None = None
    destination_hint: str | None = None


class VerificationConfirmRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=10)


class VerificationConfirmResponse(BaseModel):
    success: bool = True
    message: str = "Verification successful."


class VerificationStatusResponse(BaseModel):
    email: str | None = None
    phone: str | None = None
    email_verified: bool = False
    phone_verified: bool = False


class NotificationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    tenant_id: int | None = None
    user_id: int | None = None
    title: str
    message: str | None = None
    type: str = "INFO"
    category: str = "SYSTEM"
    entity_type: str | None = None
    entity_id: str | None = None
    action_url: str | None = None
    priority: str = "normal"
    is_read: bool = False
    read_at: datetime | None = None
    cleared_at: datetime | None = None
    created_at: datetime
