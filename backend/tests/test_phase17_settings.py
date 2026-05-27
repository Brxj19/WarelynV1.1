from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.settings import TenantSettings, UserPreferences


def _setup_tenant_user(db_session: Session, client: TestClient, email: str = "p17@example.com"):
    tenant = Tenant(company_name="P17Co", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P17User", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id, user.id


def test_settings_update_saves_all_fields(client: TestClient, db_session: Session) -> None:
    token, tenant_id, _ = _setup_tenant_user(db_session, client, "settings-save@example.com")
    resp = client.patch(
        "/api/settings/tenant",
        json={"company_display_name": "Updated Co", "currency": "EUR", "phone": "+1234567890"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_display_name"] == "Updated Co"
    assert data["currency"] == "EUR"
    assert data["phone"] == "+1234567890"


def test_user_preferences_update_saves_theme(client: TestClient, db_session: Session) -> None:
    token, _, _ = _setup_tenant_user(db_session, client, "prefs-theme@example.com")
    resp = client.patch(
        "/api/settings/preferences",
        json={"theme_preference": "light", "table_density": "compact"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["theme_preference"] == "light"
    assert data["table_density"] == "compact"


def test_401_is_returned_for_expired_token(client: TestClient) -> None:
    resp = client.get("/api/settings/tenant", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401


def test_403_is_returned_for_wrong_role(client: TestClient, db_session: Session) -> None:
    tenant = Tenant(company_name="ViewerCo", contact_email="viewer-p17@example.com")
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="Viewer", email="viewer-p17@example.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.VIEWER, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": "viewer-p17@example.com", "password": "StrongPass123!"})
    token = login.json()["access_token"]
    resp = client.patch(
        "/api/settings/tenant",
        json={"company_display_name": "Hacked"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_settings_get_returns_defaults_for_new_tenant(client: TestClient, db_session: Session) -> None:
    token, _, _ = _setup_tenant_user(db_session, client, "defaults-tenant@example.com")
    resp = client.get("/api/settings/tenant", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["currency"] == "USD"


def test_preferences_get_returns_defaults_for_new_user(client: TestClient, db_session: Session) -> None:
    token, _, _ = _setup_tenant_user(db_session, client, "defaults-prefs@example.com")
    resp = client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["theme_preference"] == "light"
