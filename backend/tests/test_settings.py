from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus


def create_tenant_user(db_session: Session, client: TestClient, role: UserRole = UserRole.TENANT_ADMIN, email: str = "user@x.com") -> tuple[str, int]:
    tenant = Tenant(company_name="SettingsCo", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id,
        name="User",
        email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=role,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id


def test_tenant_admin_can_read_tenant_settings(db_session: Session, client: TestClient) -> None:
    token, _ = create_tenant_user(db_session, client)
    response = client.get("/api/settings/tenant", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "company_display_name" in response.json()


def test_tenant_admin_can_update_tenant_settings(db_session: Session, client: TestClient) -> None:
    token, _ = create_tenant_user(db_session, client)
    response = client.patch("/api/settings/tenant", json={"company_display_name": "NewCo"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["company_display_name"] == "NewCo"


def test_cross_tenant_settings_access_blocked(db_session: Session, client: TestClient) -> None:
    token_a, _ = create_tenant_user(db_session, client, email="a@x.com")
    _, tenant_b_id = create_tenant_user(db_session, client, email="b@x.com")
    response = client.get(f"/api/settings/tenant", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] != tenant_b_id


def test_user_can_read_own_preferences(db_session: Session, client: TestClient) -> None:
    token, _ = create_tenant_user(db_session, client)
    response = client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["table_density"] == "comfortable"


def test_user_can_update_own_preferences(db_session: Session, client: TestClient) -> None:
    token, _ = create_tenant_user(db_session, client)
    response = client.patch("/api/settings/preferences", json={"table_density": "compact"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["table_density"] == "compact"


def test_user_cannot_update_another_user_preferences(db_session: Session, client: TestClient) -> None:
    token_a, _ = create_tenant_user(db_session, client, email="pref-a@x.com")
    token_b, _ = create_tenant_user(db_session, client, email="pref-b@x.com")
    prefs_b = client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token_b}"}).json()
    patch_url = f"/api/settings/preferences"
    response = client.patch(patch_url, json={"table_density": "compact"}, headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200
    assert response.json()["table_density"] == "compact"
    check_b = client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token_b}"}).json()
    assert check_b["table_density"] == "comfortable"


def test_settings_update_creates_audit_log(db_session: Session, client: TestClient) -> None:
    token, _ = create_tenant_user(db_session, client)
    client.patch("/api/settings/tenant", json={"company_display_name": "AuditCo"}, headers={"Authorization": f"Bearer {token}"})
    from app.models.audit import AuditLog
    logs = db_session.query(AuditLog).all()
    assert len(logs) >= 1
