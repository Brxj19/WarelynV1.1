from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus


def create_super_admin(db_session: Session, client: TestClient, email: str = "super@example.com") -> str:
    sa = User(
        name="Super",
        email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        tenant_id=None,
    )
    db_session.add(sa)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"]


def create_tenant_admin(db_session: Session, client: TestClient, email: str = "admin@example.com") -> str:
    tenant = Tenant(company_name="Acme", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id,
        name="Admin",
        email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_super_admin_can_list_tenants(db_session: Session, client: TestClient) -> None:
    token = create_super_admin(db_session, client)
    response = client.get("/api/admin/tenants", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tenant_admin_cannot_list_tenants(db_session: Session, client: TestClient) -> None:
    token = create_tenant_admin(db_session, client)
    response = client.get("/api/admin/tenants", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_viewer_cannot_list_tenants(db_session: Session, client: TestClient) -> None:
    tenant = Tenant(company_name="Co", contact_email="co@x.com")
    db_session.add(tenant)
    db_session.flush()
    viewer = User(
        tenant_id=tenant.id,
        name="Viewer",
        email="viewer@x.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.VIEWER,
        status=UserStatus.ACTIVE,
    )
    db_session.add(viewer)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": "viewer@x.com", "password": "StrongPass123!"})
    token = login.json()["access_token"]
    response = client.get("/api/admin/tenants", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_super_admin_can_get_platform_summary(db_session: Session, client: TestClient) -> None:
    token = create_super_admin(db_session, client)
    response = client.get("/api/admin/platform/summary", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "total_tenants" in data
    assert "active_tenants" in data
    assert "total_users" in data


def test_super_admin_can_get_tenant_detail(db_session: Session, client: TestClient) -> None:
    tenant = Tenant(company_name="DetailCo", contact_email="detail@x.com")
    db_session.add(tenant)
    db_session.flush()
    sa_token = create_super_admin(db_session, client, "sa@x.com")
    response = client.get(f"/api/admin/tenants/{tenant.id}", headers={"Authorization": f"Bearer {sa_token}"})
    assert response.status_code == 200
    assert response.json()["company_name"] == "DetailCo"


def test_super_admin_can_enable_tenant(db_session: Session, client: TestClient) -> None:
    tenant = Tenant(company_name="DisCo", contact_email="dis@x.com", status=TenantStatus.DISABLED)
    db_session.add(tenant)
    db_session.flush()
    sa_token = create_super_admin(db_session, client, "sa-enable@x.com")
    response = client.post(f"/api/admin/tenants/{tenant.id}/enable", headers={"Authorization": f"Bearer {sa_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"
    db_session.refresh(tenant)
    assert tenant.status == TenantStatus.ACTIVE


def test_super_admin_can_disable_tenant(db_session: Session, client: TestClient) -> None:
    tenant = Tenant(company_name="ActCo", contact_email="act@x.com", status=TenantStatus.ACTIVE)
    db_session.add(tenant)
    db_session.flush()
    sa_token = create_super_admin(db_session, client, "sa-disable@x.com")
    response = client.post(f"/api/admin/tenants/{tenant.id}/disable", headers={"Authorization": f"Bearer {sa_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "DISABLED"


def test_enable_disable_creates_audit_log(db_session: Session, client: TestClient) -> None:
    tenant = Tenant(company_name="AudCo", contact_email="aud@x.com", status=TenantStatus.DISABLED)
    db_session.add(tenant)
    db_session.flush()
    sa_token = create_super_admin(db_session, client, "sa-audit@x.com")
    client.post(f"/api/admin/tenants/{tenant.id}/enable", headers={"Authorization": f"Bearer {sa_token}"})
    from app.models.audit import AuditLog
    logs = db_session.query(AuditLog).filter(AuditLog.action == "TENANT_ENABLE").all()
    assert len(logs) == 1
    assert logs[0].entity_id == str(tenant.id)
    client.post(f"/api/admin/tenants/{tenant.id}/disable", headers={"Authorization": f"Bearer {sa_token}"})
    dis_logs = db_session.query(AuditLog).filter(AuditLog.action == "TENANT_DISABLE").all()
    assert len(dis_logs) == 1
