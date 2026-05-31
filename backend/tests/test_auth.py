from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import get_password_hash
from app.dependencies.auth import require_roles, require_tenant_user
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.services.auth import UserContext


def register_payload(email: str = "admin@example.com") -> dict[str, str]:
    return {
        "company_name": "Acme Warehousing",
        "name": "Acme Admin",
        "email": email,
        "phone": "+15550100",
        "password": "StrongPass123!",
    }


def register_user(client: TestClient, email: str = "admin@example.com") -> dict[str, object]:
    response = client.post("/api/auth/register", json=register_payload(email))
    assert response.status_code == 201
    return response.json()


def login_user(client: TestClient, email: str = "admin@example.com", password: str = "StrongPass123!") -> dict[str, object]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()


def test_register_tenant_admin(client: TestClient) -> None:
    data = register_user(client)

    assert data["tenant"]["company_name"] == "Acme Warehousing"
    assert data["user"]["role"] == "TENANT_ADMIN"
    assert "password_hash" not in data["user"]


def test_duplicate_email_blocked(client: TestClient) -> None:
    register_user(client)

    response = client.post("/api/auth/register", json=register_payload())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_EMAIL"


def test_login_success(client: TestClient) -> None:
    register_user(client)

    data = login_user(client)

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["user"]["email"] == "admin@example.com"


def test_login_wrong_password(client: TestClient) -> None:
    register_user(client)

    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_auth_me_works_with_token(client: TestClient) -> None:
    register_user(client)
    login = login_user(client)

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})

    assert response.status_code == 200
    assert response.json()["role"] == "TENANT_ADMIN"
    assert response.json()["tenant"]["company_name"] == "Acme Warehousing"


def test_auth_me_fails_without_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "MISSING_TOKEN"


def test_auth_me_fails_with_invalid_token_and_error_envelope(client: TestClient) -> None:
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-valid-token"})

    body = response.json()
    assert response.status_code == 401
    assert body["error"]["code"] == "INVALID_TOKEN"
    assert body["error"]["message"]
    assert "request_id" in body["error"]


def test_auth_me_fails_with_expired_token(client: TestClient) -> None:
    settings = get_settings()
    token = jwt.encode({"sub": "1", "type": "access", "exp": datetime.now(UTC) - timedelta(minutes=1), "iat": datetime.now(UTC) - timedelta(minutes=2)}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "EXPIRED_TOKEN"


def test_disabled_user_cannot_login(client: TestClient, db_session: Session) -> None:
    register_user(client)
    user = db_session.query(User).filter(User.email == "admin@example.com").one()
    user.status = UserStatus.DISABLED
    db_session.commit()

    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "StrongPass123!"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "DISABLED_USER"


def test_disabled_user_existing_token_is_rejected(client: TestClient, db_session: Session) -> None:
    register_user(client)
    login = login_user(client)
    user = db_session.query(User).filter(User.email == "admin@example.com").one()
    user.status = UserStatus.DISABLED
    db_session.commit()

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "DISABLED_USER"


def test_disabled_tenant_user_cannot_login(client: TestClient, db_session: Session) -> None:
    register_user(client)
    tenant = db_session.query(Tenant).one()
    tenant.status = TenantStatus.DISABLED
    db_session.commit()

    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "StrongPass123!"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "DISABLED_TENANT"


def test_disabled_tenant_existing_token_is_rejected(client: TestClient, db_session: Session) -> None:
    register_user(client)
    login = login_user(client)
    tenant = db_session.query(Tenant).one()
    tenant.status = TenantStatus.DISABLED
    db_session.commit()

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "DISABLED_TENANT"


def test_refresh_token_works(client: TestClient) -> None:
    register_user(client)
    login = login_user(client)

    response = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["token_type"] == "bearer"


def test_refresh_rejects_access_token_type(client: TestClient) -> None:
    register_user(client)
    login = login_user(client)

    response = client.post("/api/auth/refresh", json={"refresh_token": login["access_token"]})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    register_user(client)
    login = login_user(client)

    logout = client.post("/api/auth/logout", json={"refresh_token": login["refresh_token"]})
    refresh = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert logout.status_code == 200
    assert logout.json() == {"success": True}
    assert refresh.status_code == 401
    assert refresh.json()["error"]["code"] == "INVALID_TOKEN"


def test_role_dependency_blocks_unauthorized_role(db_session: Session) -> None:
    user = User(
        name="Viewer",
        email="viewer@example.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.VIEWER,
        status=UserStatus.ACTIVE,
    )
    context = UserContext(user=user, tenant=None, tenant_id=None, role=UserRole.VIEWER)
    dependency = require_roles(UserRole.SUPER_ADMIN)

    try:
        dependency(context)
    except AppError as exc:
        assert exc.code == "FORBIDDEN_ROLE"
        assert exc.status_code == 403
    else:
        raise AssertionError("Expected AppError")


def test_tenant_user_context_resolves_tenant_id(client: TestClient, db_session: Session) -> None:
    register_user(client)
    login = login_user(client)

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"}).json()

    assert me["user"]["tenant_id"] == me["tenant"]["id"]


def test_require_tenant_user_rejects_super_admin() -> None:
    user = User(
        name="Super",
        email="super@example.com",
        password_hash="hash",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
    )
    context = UserContext(user=user, tenant=None, tenant_id=None, role=UserRole.SUPER_ADMIN)

    try:
        require_tenant_user(context)
    except AppError as exc:
        assert exc.code == "TENANT_ACCESS_DENIED"
    else:
        raise AssertionError("Expected AppError")


def test_forgot_password_unknown_email_returns_204(client: TestClient) -> None:
    response = client.post("/api/auth/forgot-password", json={"email": "unknown@example.com"})
    assert response.status_code == 204
    assert response.content == b""


def test_verify_reset_code_returns_token_for_valid_email(client: TestClient, monkeypatch) -> None:
    register_user(client, "reset-user@example.com")
    captured = {"code": None}

    def fake_send_password_reset_email(to_email: str, code: str) -> None:
        assert to_email == "reset-user@example.com"
        captured["code"] = code

    monkeypatch.setattr("app.services.auth.send_password_reset_email", fake_send_password_reset_email)

    forgot = client.post("/api/auth/forgot-password", json={"email": "reset-user@example.com"})
    assert forgot.status_code == 204
    assert captured["code"] is not None

    verify = client.post(
        "/api/auth/verify-reset-code",
        json={"email": "reset-user@example.com", "code": captured["code"]},
    )
    assert verify.status_code == 200
    assert verify.json()["reset_token"]


def test_reset_password_changes_credentials(client: TestClient, monkeypatch) -> None:
    register_user(client, "reset-password@example.com")
    captured = {"code": None}

    def fake_send_password_reset_email(to_email: str, code: str) -> None:
        assert to_email == "reset-password@example.com"
        captured["code"] = code

    monkeypatch.setattr("app.services.auth.send_password_reset_email", fake_send_password_reset_email)

    forgot = client.post("/api/auth/forgot-password", json={"email": "reset-password@example.com"})
    assert forgot.status_code == 204
    verify = client.post(
        "/api/auth/verify-reset-code",
        json={"email": "reset-password@example.com", "code": captured["code"]},
    )
    assert verify.status_code == 200
    reset_token = verify.json()["reset_token"]

    reset = client.post(
        "/api/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "NewStrongPass123!"},
    )
    assert reset.status_code == 204

    old_login = client.post("/api/auth/login", json={"email": "reset-password@example.com", "password": "StrongPass123!"})
    assert old_login.status_code == 401
    assert old_login.json()["error"]["code"] == "INVALID_CREDENTIALS"

    new_login = client.post("/api/auth/login", json={"email": "reset-password@example.com", "password": "NewStrongPass123!"})
    assert new_login.status_code == 200
    assert new_login.json()["access_token"]


def test_reset_token_cannot_be_used_twice(client: TestClient, monkeypatch) -> None:
    register_user(client, "reset-twice@example.com")
    captured = {"code": None}

    def fake_send_password_reset_email(to_email: str, code: str) -> None:
        assert to_email == "reset-twice@example.com"
        captured["code"] = code

    monkeypatch.setattr("app.services.auth.send_password_reset_email", fake_send_password_reset_email)

    forgot = client.post("/api/auth/forgot-password", json={"email": "reset-twice@example.com"})
    assert forgot.status_code == 204
    verify = client.post(
        "/api/auth/verify-reset-code",
        json={"email": "reset-twice@example.com", "code": captured["code"]},
    )
    assert verify.status_code == 200
    reset_token = verify.json()["reset_token"]

    first = client.post(
        "/api/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "NewStrongPass123!"},
    )
    second = client.post(
        "/api/auth/reset-password",
        json={"reset_token": reset_token, "new_password": "AnotherStrongPass123!"},
    )

    assert first.status_code == 204
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "RESET_TOKEN_ALREADY_USED"
