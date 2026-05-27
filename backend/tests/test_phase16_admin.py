from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.communication import Notification
from app.repositories.notification import NotificationRepository


def _super_admin_token(db_session: Session, client: TestClient, email: str = "sa-p16@example.com") -> str:
    sa = User(
        name="SuperP16", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.SUPER_ADMIN, status=UserStatus.ACTIVE, tenant_id=None,
    )
    db_session.add(sa)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"]


def _tenant_user_token(db_session: Session, client: TestClient, email: str = "tu-p16@example.com") -> str:
    tenant = Tenant(company_name="P16Co", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="TenantUser", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_admin_route_requires_super_admin_role(client: TestClient, db_session: Session) -> None:
    token = _tenant_user_token(db_session, client, "nonadmin-p16@example.com")
    resp = client.get("/api/admin/tenants", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_tenant_user_cannot_access_admin_dashboard(client: TestClient, db_session: Session) -> None:
    token = _tenant_user_token(db_session, client, "nonadmin2-p16@example.com")
    resp = client.get("/api/admin/platform/summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_super_admin_can_access_admin_dashboard(client: TestClient, db_session: Session) -> None:
    token = _super_admin_token(db_session, client, "sa-dash-p16@example.com")
    resp = client.get("/api/admin/platform/summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "total_tenants" in data


def test_notification_repository_list_returns_for_user(db_session: Session) -> None:
    tenant = Tenant(company_name="NR-Co", contact_email="nr@x.com")
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="NRUser", email="nr-user@x.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    repo = NotificationRepository(db_session)
    repo.create_notification(user_id=user.id, tenant_id=tenant.id, title="Hello", message="World")
    repo.create_notification(user_id=user.id, tenant_id=tenant.id, title="Second", message="Msg")
    db_session.commit()
    results = repo.list_notifications(user.id, tenant.id)
    assert len(results) == 2
    titles = [r.title for r in results]
    assert "Hello" in titles
    assert "Second" in titles


def test_notification_repository_unread_count(db_session: Session) -> None:
    tenant = Tenant(company_name="UC-Co", contact_email="uc@x.com")
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="UCUser", email="uc-user@x.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    repo = NotificationRepository(db_session)
    repo.create_notification(user_id=user.id, tenant_id=tenant.id, title="N1")
    repo.create_notification(user_id=user.id, tenant_id=tenant.id, title="N2")
    repo.create_notification(user_id=user.id, tenant_id=tenant.id, title="N3")
    db_session.commit()
    assert repo.unread_count(user.id, tenant.id) == 3


def test_notification_mark_read(db_session: Session, client: TestClient) -> None:
    tenant = Tenant(company_name="MR-Co", contact_email="mr@x.com")
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="MRUser", email="mr-user@x.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    repo = NotificationRepository(db_session)
    repo.create_notification(user_id=user.id, tenant_id=tenant.id, title="ReadMe")
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": "mr-user@x.com", "password": "StrongPass123!"})
    token = login.json()["access_token"]
    notifs = client.get("/api/notifications", headers={"Authorization": f"Bearer {token}"})
    nid = notifs.json()[0]["id"]
    resp = client.post(f"/api/notifications/{nid}/read", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True


def test_notification_mark_all_read(db_session: Session, client: TestClient) -> None:
    tenant = Tenant(company_name="MA-Co", contact_email="ma@x.com")
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="MAUser", email="ma-user@x.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    repo = NotificationRepository(db_session)
    repo.create_notification(user_id=user.id, tenant_id=tenant.id, title="A1")
    repo.create_notification(user_id=user.id, tenant_id=tenant.id, title="A2")
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": "ma-user@x.com", "password": "StrongPass123!"})
    token = login.json()["access_token"]
    resp = client.post("/api/notifications/read-all", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    count_resp = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {token}"})
    assert count_resp.json()["count"] == 0


def test_tenant_list_is_accessible_to_super_admin(client: TestClient, db_session: Session) -> None:
    token = _super_admin_token(db_session, client, "sa-tenants-p16@example.com")
    tenant = Tenant(company_name="ListMe", contact_email="listme@x.com", status="ACTIVE")
    db_session.add(tenant)
    db_session.commit()
    resp = client.get("/api/admin/tenants", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    names = [t["company_name"] for t in resp.json()]
    assert "ListMe" in names
