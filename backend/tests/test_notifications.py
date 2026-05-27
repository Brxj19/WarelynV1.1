from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.communication import Notification


def create_users(db_session, client):
    tenant = Tenant(company_name="NotifCo", contact_email="n@x.com")
    db_session.add(tenant)
    db_session.flush()
    user_a = User(
        tenant_id=tenant.id, name="UserA", email="a@x.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    user_b = User(
        tenant_id=tenant.id, name="UserB", email="b@x.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.VIEWER, status=UserStatus.ACTIVE,
    )
    db_session.add(user_a)
    db_session.add(user_b)
    db_session.flush()
    notif1 = Notification(user_id=user_a.id, tenant_id=tenant.id, title="Test 1", type="INFO", category="SYSTEM", priority="normal")
    notif2 = Notification(user_id=user_a.id, tenant_id=tenant.id, title="Test 2", type="WARNING", category="AUTH", priority="normal")
    notif3 = Notification(user_id=user_b.id, tenant_id=tenant.id, title="B Notif", type="INFO", category="SYSTEM", priority="normal")
    db_session.add(notif1)
    db_session.add(notif2)
    db_session.add(notif3)
    db_session.commit()
    login_a = client.post("/api/auth/login", json={"email": "a@x.com", "password": "StrongPass123!"})
    login_b = client.post("/api/auth/login", json={"email": "b@x.com", "password": "StrongPass123!"})
    return login_a.json()["access_token"], login_b.json()["access_token"], user_a.id, user_b.id, tenant.id, notif1.id, notif2.id, notif3.id


def test_list_notifications_tenant_scoped(db_session: Session, client: TestClient) -> None:
    token_a, token_b, uid_a, uid_b, tid, n1, n2, n3 = create_users(db_session, client)
    resp = client.get("/api/notifications", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    titles = [n["title"] for n in data]
    assert "Test 1" in titles
    assert "Test 2" in titles
    assert "B Notif" not in titles


def test_unread_count_excludes_cleared(db_session: Session, client: TestClient) -> None:
    token_a, token_b, uid_a, uid_b, tid, n1, n2, n3 = create_users(db_session, client)

    # Initially 2 unread for user A
    resp = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.json()["count"] == 2

    # Clear one notification directly in DB
    notif = db_session.get(Notification, n1)
    notif.cleared_at = datetime.now(timezone.utc)
    db_session.commit()

    # Unread count should now be 1 (cleared excluded)
    resp2 = client.get("/api/notifications/unread-count", headers={"Authorization": f"Bearer {token_a}"})
    assert resp2.json()["count"] == 1


def test_mark_read(db_session: Session, client: TestClient) -> None:
    token_a, token_b, uid_a, uid_b, tid, n1, n2, n3 = create_users(db_session, client)
    resp = client.post(f"/api/notifications/{n1}/read", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True
    notif = db_session.get(Notification, n1)
    assert notif.is_read is True


def test_mark_all_read(db_session: Session, client: TestClient) -> None:
    token_a, token_b, uid_a, uid_b, tid, n1, n2, n3 = create_users(db_session, client)
    resp = client.post("/api/notifications/read-all", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    unread = db_session.query(Notification).filter(Notification.user_id == uid_a, Notification.is_read == False).count()
    assert unread == 0


def test_clear_one(db_session: Session, client: TestClient) -> None:
    token_a, token_b, uid_a, uid_b, tid, n1, n2, n3 = create_users(db_session, client)

    resp = client.post(f"/api/notifications/{n1}/clear", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    assert resp.json()["cleared_at"] is not None

    # Should not appear in default list
    list_resp = client.get("/api/notifications", headers={"Authorization": f"Bearer {token_a}"})
    ids = [item["id"] for item in list_resp.json()]
    assert n1 not in ids

    # Should appear in cleared tab
    cleared_resp = client.get("/api/notifications?status=cleared", headers={"Authorization": f"Bearer {token_a}"})
    cleared_ids = [item["id"] for item in cleared_resp.json()]
    assert n1 in cleared_ids


def test_clear_all(db_session: Session, client: TestClient) -> None:
    token_a, token_b, uid_a, uid_b, tid, n1, n2, n3 = create_users(db_session, client)

    resp = client.post("/api/notifications/clear-all", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Default list should be empty for user A
    list_resp = client.get("/api/notifications", headers={"Authorization": f"Bearer {token_a}"})
    assert list_resp.json() == []

    # Cleared list should have them
    cleared_resp = client.get("/api/notifications?status=cleared", headers={"Authorization": f"Bearer {token_a}"})
    assert len(cleared_resp.json()) == 2

    # User B's notification should be unaffected
    list_b = client.get("/api/notifications", headers={"Authorization": f"Bearer {token_b}"})
    assert len(list_b.json()) == 1


def test_cross_tenant_isolation(db_session: Session, client: TestClient) -> None:
    tenant_a = Tenant(company_name="TenA", contact_email="ta@x.com")
    tenant_b = Tenant(company_name="TenB", contact_email="tb@x.com")
    db_session.add(tenant_a)
    db_session.add(tenant_b)
    db_session.flush()
    user_a = User(tenant_id=tenant_a.id, name="A", email="aa@x.com", password_hash=get_password_hash("StrongPass123!"), role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE)
    user_b = User(tenant_id=tenant_b.id, name="B", email="bb@x.com", password_hash=get_password_hash("StrongPass123!"), role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE)
    db_session.add(user_a)
    db_session.add(user_b)
    db_session.flush()
    n_a = Notification(user_id=user_a.id, tenant_id=tenant_a.id, title="Secret A", type="INFO", category="SYSTEM", priority="normal")
    n_b = Notification(user_id=user_b.id, tenant_id=tenant_b.id, title="Secret B", type="INFO", category="SYSTEM", priority="normal")
    db_session.add(n_a)
    db_session.add(n_b)
    db_session.commit()

    login_a = client.post("/api/auth/login", json={"email": "aa@x.com", "password": "StrongPass123!"})
    login_b = client.post("/api/auth/login", json={"email": "bb@x.com", "password": "StrongPass123!"})
    token_a = login_a.json()["access_token"]
    token_b = login_b.json()["access_token"]

    # User A sees only their notification
    resp_a = client.get("/api/notifications", headers={"Authorization": f"Bearer {token_a}"})
    assert resp_a.status_code == 200
    titles_a = [n["title"] for n in resp_a.json()]
    assert "Secret A" in titles_a
    assert "Secret B" not in titles_a

    # User B sees only their notification
    resp_b = client.get("/api/notifications", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b.status_code == 200
    titles_b = [n["title"] for n in resp_b.json()]
    assert "Secret B" in titles_b
    assert "Secret A" not in titles_b

    # User B cannot mark A's notification as read
    cross_read = client.post(f"/api/notifications/{n_a.id}/read", headers={"Authorization": f"Bearer {token_b}"})
    assert cross_read.status_code == 404

    # User B cannot clear A's notification
    cross_clear = client.post(f"/api/notifications/{n_a.id}/clear", headers={"Authorization": f"Bearer {token_b}"})
    assert cross_clear.status_code == 404
