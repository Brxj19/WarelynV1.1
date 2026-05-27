from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, hash_token
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.communication import OTPPurpose, OTPSource, OTPVerification


def create_tenant_user(db_session, client, email="v@x.com", phone="+15550101"):
    tenant = Tenant(company_name="VerCo", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="User", email=email, phone=phone,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    return login.json()["access_token"], user.id


def test_send_email_verification_creates_otp(db_session, client):
    token, uid = create_tenant_user(db_session, client)
    resp = client.post("/api/verification/email/send", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code in (200, 502)
    if resp.status_code == 200:
        assert len(resp.json()["development_code"]) == 6
        assert resp.json()["destination_hint"]
    otps = db_session.query(OTPVerification).filter(OTPVerification.user_id == uid).all()
    assert len(otps) == 1
    assert otps[0].purpose == "EMAIL_VERIFICATION"


def test_confirm_email_verification_marks_user_verified(db_session, client):
    token, uid = create_tenant_user(db_session, client)
    code = "123456"
    otp = OTPVerification(
        user_id=uid, tenant_id=1, destination="v@x.com",
        destination_type=OTPSource.EMAIL, purpose=OTPPurpose.EMAIL_VERIFICATION,
        code_hash=hash_token(code),
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=10),
        max_attempts=5,
    )
    db_session.add(otp)
    db_session.commit()
    resp = client.post("/api/verification/email/confirm", json={"code": code}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    user = db_session.query(User).filter(User.id == uid).one()
    assert user.email_verified_at is not None


def test_invalid_code_returns_structured_error(db_session, client):
    token, uid = create_tenant_user(db_session, client)
    otp = OTPVerification(
        user_id=uid, tenant_id=1, destination="v@x.com",
        destination_type=OTPSource.EMAIL, purpose=OTPPurpose.EMAIL_VERIFICATION,
        code_hash=hash_token("123456"),
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=10),
        max_attempts=5,
    )
    db_session.add(otp)
    db_session.commit()
    resp = client.post("/api/verification/email/confirm", json={"code": "000000"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert "error" in resp.json()
    assert resp.json()["error"]["code"] == "OTP_INVALID"


def test_send_phone_verification_creates_sms_outbox(db_session, client):
    token, uid = create_tenant_user(db_session, client)
    resp = client.post("/api/verification/phone/send", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert len(resp.json()["development_code"]) == 6
    from app.models.communication import SMSOutbox
    sms = db_session.query(SMSOutbox).filter(SMSOutbox.user_id == uid).all()
    assert len(sms) >= 1
    assert sms[0].purpose == "PHONE_VERIFICATION"


def test_phone_verification_rejects_no_phone(db_session, client):
    token, uid = create_tenant_user(db_session, client, email="nophone@x.com", phone=None)
    resp = client.post("/api/verification/phone/send", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "NO_PHONE"


def test_verification_status_returns_correctly(db_session, client):
    token, uid = create_tenant_user(db_session, client)
    resp = client.get("/api/verification/status", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email_verified"] is False
    assert data["phone_verified"] is False
    assert data["email"] is not None


def test_verification_endpoints_require_auth(db_session, client):
    resp = client.post("/api/verification/email/send")
    assert resp.status_code == 401
    resp = client.post("/api/verification/email/confirm", json={"code": "123456"})
    assert resp.status_code == 401
    resp = client.get("/api/verification/status")
    assert resp.status_code == 401


def test_verified_action_creates_audit_log(db_session, client):
    token, uid = create_tenant_user(db_session, client)
    code = "654321"
    otp = OTPVerification(
        user_id=uid, tenant_id=1, destination="v@x.com",
        destination_type=OTPSource.EMAIL, purpose=OTPPurpose.EMAIL_VERIFICATION,
        code_hash=hash_token(code),
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=10),
        max_attempts=5,
    )
    db_session.add(otp)
    db_session.commit()
    client.post("/api/verification/email/confirm", json={"code": code}, headers={"Authorization": f"Bearer {token}"})
    from app.models.audit import AuditLog
    logs = db_session.query(AuditLog).filter(AuditLog.action == "EMAIL_VERIFIED").all()
    assert len(logs) == 1


def test_confirm_phone_verification_works(db_session, client):
    token, uid = create_tenant_user(db_session, client)
    code = "999999"
    otp = OTPVerification(
        user_id=uid, tenant_id=1, destination="+15550101",
        destination_type=OTPSource.PHONE, purpose=OTPPurpose.PHONE_VERIFICATION,
        code_hash=hash_token(code),
        expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=10),
        max_attempts=5,
    )
    db_session.add(otp)
    db_session.commit()
    resp = client.post("/api/verification/phone/confirm", json={"code": code}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    user = db_session.query(User).filter(User.id == uid).one()
    assert user.phone_verified_at is not None


def test_already_verified_email_returns_409(db_session, client):
    token, uid = create_tenant_user(db_session, client)
    user = db_session.query(User).filter(User.id == uid).one()
    user.email_verified_at = datetime.now(UTC).replace(tzinfo=None)
    db_session.commit()
    resp = client.post("/api/verification/email/send", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ALREADY_VERIFIED"


def test_already_verified_phone_returns_409(db_session, client):
    token, uid = create_tenant_user(db_session, client)
    user = db_session.query(User).filter(User.id == uid).one()
    user.phone_verified_at = datetime.now(UTC).replace(tzinfo=None)
    db_session.commit()
    resp = client.post("/api/verification/phone/send", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "ALREADY_VERIFIED"


def test_development_code_not_in_production(db_session, client, monkeypatch):
    from app.core.config import Settings
    import app.api.verification as verification_module

    # Create a settings instance with debug=False
    prod_settings = Settings(debug=False, environment="production")
    monkeypatch.setattr(verification_module, "get_settings", lambda: prod_settings)

    token, uid = create_tenant_user(db_session, client)
    resp = client.post("/api/verification/phone/send", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json().get("development_code") is None
