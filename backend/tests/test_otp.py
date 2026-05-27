from datetime import UTC, datetime, timedelta

from app.core.security import hash_token
from app.models.communication import OTPPurpose, OTPSource
from app.repositories.otp import OTPRepository
from app.services.otp_service import OTPService


def test_create_otp_stores_hashed_code(db_session):
    repo = OTPRepository(db_session)
    svc = OTPService(repo)
    code = svc.create_otp(user_id=1, tenant_id=1, destination="test@x.com", destination_type=OTPSource.EMAIL, purpose=OTPPurpose.EMAIL_VERIFICATION)
    stored = repo.get_active_by_user_and_purpose(1, OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    assert stored is not None
    assert stored.code_hash == hash_token(code)
    assert stored.code_hash != code


def test_verify_valid_otp_succeeds(db_session):
    repo = OTPRepository(db_session)
    svc = OTPService(repo)
    code = svc.create_otp(user_id=1, tenant_id=1, destination="test@x.com", destination_type=OTPSource.EMAIL, purpose=OTPPurpose.EMAIL_VERIFICATION)
    svc.verify_otp(1, code, OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    stored = repo.get_active_by_user_and_purpose(1, OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    assert stored is None  # consumed, no longer active


def test_expired_otp_fails(db_session):
    repo = OTPRepository(db_session)
    otp = repo.create({
        "user_id": 1, "tenant_id": 1, "destination": "test@x.com",
        "destination_type": OTPSource.EMAIL, "purpose": OTPPurpose.EMAIL_VERIFICATION,
        "code_hash": hash_token("123456"), "expires_at": datetime.now(UTC) - timedelta(minutes=1),
        "max_attempts": 5,
    })
    svc = OTPService(repo)
    try:
        svc.verify_otp(1, "123456", OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    except Exception as exc:
        assert exc.code == "OTP_NOT_FOUND"
    else:
        raise AssertionError("Expected error")


def test_consumed_otp_cannot_be_reused(db_session):
    repo = OTPRepository(db_session)
    svc = OTPService(repo)
    code = svc.create_otp(user_id=1, tenant_id=1, destination="test@x.com", destination_type=OTPSource.EMAIL, purpose=OTPPurpose.EMAIL_VERIFICATION)
    svc.verify_otp(1, code, OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    try:
        svc.verify_otp(1, code, OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    except Exception as exc:
        assert exc.code == "OTP_NOT_FOUND"
    else:
        raise AssertionError("Expected error")


def test_wrong_otp_increments_attempts(db_session):
    repo = OTPRepository(db_session)
    svc = OTPService(repo)
    code = svc.create_otp(user_id=1, tenant_id=1, destination="test@x.com", destination_type=OTPSource.EMAIL, purpose=OTPPurpose.EMAIL_VERIFICATION)
    try:
        svc.verify_otp(1, "000000", OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    except Exception as exc:
        assert exc.code == "OTP_INVALID"
        assert "remaining" in exc.message
    else:
        raise AssertionError("Expected error")
    stored = repo.get_active_by_user_and_purpose(1, OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    assert stored is not None
    assert stored.attempt_count == 1


def test_resend_invalidates_previous_otp(db_session):
    repo = OTPRepository(db_session)
    svc = OTPService(repo)
    code1 = svc.create_otp(user_id=1, tenant_id=1, destination="test@x.com", destination_type=OTPSource.EMAIL, purpose=OTPPurpose.EMAIL_VERIFICATION)
    code2 = svc.create_otp(user_id=1, tenant_id=1, destination="test@x.com", destination_type=OTPSource.EMAIL, purpose=OTPPurpose.EMAIL_VERIFICATION)
    try:
        svc.verify_otp(1, code1, OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
    except Exception as exc:
        assert exc.code in ("OTP_INVALID", "OTP_NOT_FOUND")
    else:
        raise AssertionError("Expected error")
    svc.verify_otp(1, code2, OTPPurpose.EMAIL_VERIFICATION, OTPSource.EMAIL)
