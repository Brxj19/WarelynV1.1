import random
import string
from datetime import UTC, datetime, timedelta, timezone

from app.core.config import get_settings
from app.core.security import hash_token
from app.models.communication import OTPPurpose, OTPSource
from app.repositories.otp import OTPRepository


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (UTC). Handles SQLite returning naive datetimes."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class OTPError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


class OTPService:
    def __init__(self, repo: OTPRepository) -> None:
        self.repo = repo

    def _generate_code(self) -> str:
        settings = get_settings()
        return "".join(random.choices(string.digits, k=settings.otp_code_length))

    def create_otp(self, user_id: int, tenant_id: int | None, destination: str, destination_type: OTPSource, purpose: OTPPurpose) -> str:
        self.repo.supersede_active_for_user(user_id, purpose, destination_type)
        settings = get_settings()
        code = self._generate_code()
        code_hash = hash_token(code)
        expires_at = _utcnow() + timedelta(minutes=settings.otp_expire_minutes)
        self.repo.create(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "destination_type": destination_type,
                "destination": destination,
                "purpose": purpose,
                "code_hash": code_hash,
                "expires_at": expires_at,
                "max_attempts": settings.otp_max_attempts,
            }
        )
        return code

    def verify_otp(self, user_id: int, code: str, purpose: OTPPurpose, destination_type: OTPSource) -> None:
        otp = self.repo.get_active_by_user_and_purpose(user_id, purpose, destination_type)
        if otp is None:
            raise OTPError("OTP_NOT_FOUND", "Verification code is invalid or expired.")
        if otp.consumed_at is not None:
            raise OTPError("OTP_CONSUMED", "Verification code has already been used.")
        if otp.superseded_at is not None:
            raise OTPError("OTP_SUPERSEDED", "A newer verification code has been sent.")
        if _ensure_aware(otp.expires_at) < _utcnow():
            raise OTPError("OTP_EXPIRED", "Verification code has expired.")
        if otp.attempt_count >= otp.max_attempts:
            raise OTPError("OTP_MAX_ATTEMPTS", "Too many failed attempts. Please request a new code.")

        code_hash = hash_token(code)
        if otp.code_hash != code_hash:
            self.repo.increment_attempt(otp.id)
            remaining = otp.max_attempts - otp.attempt_count - 1
            if remaining <= 0:
                raise OTPError("OTP_MAX_ATTEMPTS", "Too many failed attempts. Please request a new code.")
            raise OTPError("OTP_INVALID", f"Invalid verification code. {remaining} attempt(s) remaining.")

        self.repo.mark_consumed(otp.id)
