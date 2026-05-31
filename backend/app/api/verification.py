from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.limiter import limiter
from app.db.session import get_db
from app.dependencies.auth import require_tenant_user
from app.models.communication import OTPPurpose, OTPSource
from app.models.documents import DocumentTemplateChannel, DocumentTemplateKey
from app.repositories.audit import AuditLogRepository
from app.repositories.settings import TenantSettingsRepository
from app.services.documents import DocumentTemplateService
from app.repositories.notification import NotificationRepository
from app.repositories.otp import OTPRepository
from app.schemas.communication import VerificationConfirmRequest, VerificationConfirmResponse, VerificationSendResponse, VerificationStatusResponse
from app.services.auth import UserContext
from app.services.email_service import EmailDeliveryError, send_email
from app.services.otp_service import OTPError, OTPService
from app.services.sms_service import SMSDevOutboxService

router = APIRouter(prefix="/verification", tags=["verification"])


def _otp_service(db: Session) -> OTPService:
    return OTPService(OTPRepository(db))


def _notify(db: Session, user_id: int, tenant_id: int | None, title: str, message: str, category: str) -> None:
    NotificationRepository(db).create_notification(
        user_id=user_id,
        tenant_id=tenant_id,
        title=title,
        message=message,
        type="SUCCESS",
        category=category,
    )


def _mask_destination(value: str | None) -> str | None:
    if not value:
        return None
    if "@" in value:
        name, domain = value.split("@", 1)
        masked_name = (name[:2] + "***") if len(name) > 2 else "***"
        return f"{masked_name}@{domain}"
    cleaned = value.strip()
    if len(cleaned) <= 4:
        return cleaned
    return f"{'*' * max(len(cleaned) - 4, 0)}{cleaned[-4:]}"


@router.post("/email/send", response_model=VerificationSendResponse)
@limiter.limit("5/minute")
def send_email_verification(request: Request, context: UserContext = Depends(require_tenant_user), db: Session = Depends(get_db)) -> VerificationSendResponse:
    if context.user.email_verified_at is not None:
        raise AppError("ALREADY_VERIFIED", "Email is already verified.", 409)
    svc = _otp_service(db)
    code = svc.create_otp(context.user.id, context.tenant_id, context.user.email, OTPSource.EMAIL, OTPPurpose.EMAIL_VERIFICATION)
    db.commit()
    try:
        preferred_id = None
        tenant_settings = TenantSettingsRepository(db).get_by_tenant(context.tenant_id)
        if tenant_settings:
            preferred_id = tenant_settings.preferred_verification_template_id
        rendered = DocumentTemplateService(db).render_by_key(
            context.tenant_id,
            DocumentTemplateChannel.EMAIL,
            DocumentTemplateKey.EMAIL_VERIFICATION,
            {
                "code": code,
                "purpose": "email verification",
                "ttl_minutes": 10,
                "expiry_minutes": 10,
                "user_name": context.user.name or context.user.email,
            },
            preferred_template_id=preferred_id,
        )
        send_email(
            context.user.email,
            rendered["subject"] or "Verify your Warelyn email",
            body_text=rendered.get("text") or rendered["body"],
            body_html=rendered["body"] if "<html" in rendered["body"].lower() else None,
        )
    except (OSError, EmailDeliveryError) as exc:
        raise AppError("EMAIL_DELIVERY_FAILED", f"Failed to send verification email: {exc}", 502) from exc
    settings = get_settings()
    development_code = code if settings.debug else None
    return VerificationSendResponse(
        message="Verification code sent to your email.",
        development_code=development_code,
        destination_hint=_mask_destination(context.user.email),
    )


@router.post("/email/confirm", response_model=VerificationConfirmResponse)
def confirm_email_verification(request: VerificationConfirmRequest, context: UserContext = Depends(require_tenant_user), db: Session = Depends(get_db)) -> VerificationConfirmResponse:
    svc = _otp_service(db)
    try:
        svc.verify_otp(context.user.id, request.code, OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    except OTPError as exc:
        raise AppError(exc.code, exc.message, 400) from exc
    context.user.email_verified_at = datetime.now(UTC)
    db.flush()
    AuditLogRepository(db).create(
        {"tenant_id": context.tenant_id, "actor_user_id": context.user.id, "actor_role": context.role.value, "action": "EMAIL_VERIFIED", "entity_type": "user", "entity_id": str(context.user.id)}
    )
    _notify(db, context.user.id, context.tenant_id, "Email Verified", "Your email address has been verified successfully.", "VERIFICATION")
    db.commit()
    return VerificationConfirmResponse(message="Email verified successfully.")


@router.post("/phone/send", response_model=VerificationSendResponse)
def send_phone_verification(context: UserContext = Depends(require_tenant_user), db: Session = Depends(get_db)) -> VerificationSendResponse:
    if context.user.phone_verified_at is not None:
        raise AppError("ALREADY_VERIFIED", "Phone is already verified.", 409)
    if not context.user.phone:
        raise AppError("NO_PHONE", "User has no phone number to verify.", 400)
    svc = _otp_service(db)
    code = svc.create_otp(context.user.id, context.tenant_id, context.user.phone, OTPSource.PHONE, OTPPurpose.PHONE_VERIFICATION)
    sms = SMSDevOutboxService(db)
    sms.send(phone=context.user.phone, message=f"Your Warelyn verification code is: {code}", purpose="PHONE_VERIFICATION", tenant_id=context.tenant_id, user_id=context.user.id)
    db.commit()
    settings = get_settings()
    development_code = code if settings.debug else None
    return VerificationSendResponse(
        message="Verification code sent to your phone.",
        development_code=development_code,
        destination_hint=_mask_destination(context.user.phone),
    )


@router.post("/phone/confirm", response_model=VerificationConfirmResponse)
def confirm_phone_verification(request: VerificationConfirmRequest, context: UserContext = Depends(require_tenant_user), db: Session = Depends(get_db)) -> VerificationConfirmResponse:
    svc = _otp_service(db)
    try:
        svc.verify_otp(context.user.id, request.code, OTPPurpose.PHONE_VERIFICATION, OTPSource.PHONE)
    except OTPError as exc:
        raise AppError(exc.code, exc.message, 400) from exc
    context.user.phone_verified_at = datetime.now(UTC)
    db.flush()
    AuditLogRepository(db).create(
        {"tenant_id": context.tenant_id, "actor_user_id": context.user.id, "actor_role": context.role.value, "action": "PHONE_VERIFIED", "entity_type": "user", "entity_id": str(context.user.id)}
    )
    _notify(db, context.user.id, context.tenant_id, "Phone Verified", "Your phone number has been verified successfully.", "VERIFICATION")
    db.commit()
    return VerificationConfirmResponse(message="Phone verified successfully.")


@router.get("/status", response_model=VerificationStatusResponse)
def verification_status(context: UserContext = Depends(require_tenant_user), db: Session = Depends(get_db)) -> VerificationStatusResponse:
    return VerificationStatusResponse(
        email=context.user.email,
        phone=context.user.phone,
        email_verified=context.user.email_verified_at is not None,
        phone_verified=context.user.phone_verified_at is not None,
    )
