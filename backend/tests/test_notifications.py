from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.communication import Notification
from app.services.notification import NotificationService
from test_returns import create_return, fulfilled_order
from test_sales import confirm_sales_order, create_role_user, create_sales_order, register_and_login, setup_sales_dimension, stock_in


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
    db_session.rollback()
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


def test_clear_all_persists_cleared_at_in_db(db_session: Session, client: TestClient) -> None:
    token_a, token_b, uid_a, uid_b, tid, n1, n2, n3 = create_users(db_session, client)
    clear = client.post("/api/notifications/clear-all", headers={"Authorization": f"Bearer {token_a}"})
    assert clear.status_code == 200

    db_session.rollback()
    user_a_notifications = (
        db_session.query(Notification)
        .filter(Notification.user_id == uid_a)
        .all()
    )
    assert len(user_a_notifications) == 2
    assert all(notification.cleared_at is not None for notification in user_a_notifications)

    default_list = client.get("/api/notifications", headers={"Authorization": f"Bearer {token_a}"})
    assert default_list.status_code == 200
    assert default_list.json() == []


def test_confirm_sales_order_creates_inventory_manager_notifications(db_session: Session, client: TestClient) -> None:
    login = register_and_login(client, "notif-sales-admin@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "NOTIF-SALES")
    stock_in(client, token, dimension, "10", "notif-sales-stock")
    create_role_user(client, db_session, UserRole.INVENTORY_MANAGER, "notif-inv-1@example.com")
    create_role_user(client, db_session, UserRole.INVENTORY_MANAGER, "notif-inv-2@example.com")
    order = create_sales_order(client, token, dimension, "2", "SO-NOTIFY-1")

    confirm = confirm_sales_order(client, token, order, dimension, "2", "notif-confirm-1")
    assert confirm["sales_order"]["status"] == "CONFIRMED"

    tenant_id = db_session.query(Tenant).one().id
    inventory_manager_ids = {
        user.id
        for user in db_session.query(User).filter(
            User.tenant_id == tenant_id,
            User.role == UserRole.INVENTORY_MANAGER,
        )
    }
    rows = (
        db_session.query(Notification)
        .filter(
            Notification.tenant_id == tenant_id,
            Notification.entity_type == "sales_order",
            Notification.entity_id == str(order["id"]),
            Notification.category == "SALES",
            Notification.type == "INFO",
        )
        .all()
    )
    notified_ids = {row.user_id for row in rows}
    assert inventory_manager_ids.issubset(notified_ids)
    assert all("New order to pick" in row.title for row in rows)


def test_submit_return_creates_warning_notification_for_inventory_managers(db_session: Session, client: TestClient) -> None:
    login = register_and_login(client, "notif-return-admin@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "NOTIF-RET")
    stock_in(client, token, dimension, "5", "notif-ret-stock")
    create_role_user(client, db_session, UserRole.INVENTORY_MANAGER, "notif-ret-inv-1@example.com")
    create_role_user(client, db_session, UserRole.INVENTORY_MANAGER, "notif-ret-inv-2@example.com")

    order = fulfilled_order(client, token, dimension, "1", "SO-NOTIF-RET", "FUL-NOTIF-RET")
    sales_return = create_return(client, token, order, dimension, "1", "RET-NOTIF-1")
    submit = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers={"Authorization": f"Bearer {token}"})
    assert submit.status_code == 200

    tenant_id = db_session.query(Tenant).one().id
    inventory_manager_ids = {
        user.id
        for user in db_session.query(User).filter(
            User.tenant_id == tenant_id,
            User.role == UserRole.INVENTORY_MANAGER,
        )
    }
    rows = (
        db_session.query(Notification)
        .filter(
            Notification.tenant_id == tenant_id,
            Notification.entity_type == "sales_return",
            Notification.entity_id == str(sales_return["id"]),
            Notification.category == "RETURNS",
            Notification.type == "WARNING",
        )
        .all()
    )
    notified_ids = {row.user_id for row in rows}
    assert inventory_manager_ids.issubset(notified_ids)
    assert all("QC required" in row.title for row in rows)


def test_notify_role_exclude_user_id_skips_excluded_user(db_session: Session, client: TestClient) -> None:
    login = register_and_login(client, "notif-exclude-admin@example.com")
    create_role_user(client, db_session, UserRole.INVENTORY_MANAGER, "notif-exclude-inv-1@example.com")
    create_role_user(client, db_session, UserRole.INVENTORY_MANAGER, "notif-exclude-inv-2@example.com")
    tenant_id = db_session.query(Tenant).one().id
    excluded_user = db_session.query(User).filter(User.role == UserRole.INVENTORY_MANAGER).first()
    assert excluded_user is not None

    NotificationService(db_session).notify_role(
        tenant_id=tenant_id,
        role="INVENTORY_MANAGER",
        title="Exclude test",
        message="Should skip one user.",
        type="INFO",
        category="SYSTEM",
        entity_type="test",
        entity_id="exclude",
        exclude_user_id=excluded_user.id,
    )

    rows = (
        db_session.query(Notification)
        .filter(
            Notification.tenant_id == tenant_id,
            Notification.title == "Exclude test",
        )
        .all()
    )
    notified_ids = {row.user_id for row in rows}
    assert excluded_user.id not in notified_ids
    assert len(rows) >= 1


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
