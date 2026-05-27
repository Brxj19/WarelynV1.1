import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus


def _create_tenant(db: Session, company_name: str = "Test Corp") -> Tenant:
    tenant = Tenant(company_name=company_name, contact_email="corp@test.com", status=TenantStatus.ACTIVE)
    db.add(tenant)
    db.flush()
    return tenant


def _create_user(
    db: Session,
    tenant_id: int,
    email: str = "admin@test.com",
    role: UserRole = UserRole.TENANT_ADMIN,
    status: UserStatus = UserStatus.ACTIVE,
    name: str = "Admin User",
) -> User:
    user = User(
        tenant_id=tenant_id,
        name=name,
        email=email,
        phone=None,
        password_hash=get_password_hash("password123"),
        role=role,
        status=status,
    )
    db.add(user)
    db.flush()
    return user


def _auth_header(user: User) -> dict[str, str]:
    token = create_access_token(str(user.id), {"tenant_id": user.tenant_id, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}


class TestListUsers:
    def test_tenant_admin_can_list_users(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff")
        db_session.commit()

        resp = client.get("/api/users", headers=_auth_header(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_list_users_does_not_show_other_tenant(self, client: TestClient, db_session: Session):
        tenant1 = _create_tenant(db_session, "Tenant 1")
        tenant2 = _create_tenant(db_session, "Tenant 2")
        admin1 = _create_user(db_session, tenant1.id, email="admin1@test.com")
        _create_user(db_session, tenant2.id, email="admin2@test.com")
        db_session.commit()

        resp = client.get("/api/users", headers=_auth_header(admin1))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["email"] == "admin1@test.com"

    def test_search_filter(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        _create_user(db_session, tenant.id, email="john@test.com", role=UserRole.VIEWER, name="John Doe")
        db_session.commit()

        resp = client.get("/api/users?search=john", headers=_auth_header(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "John Doe"

    def test_role_filter(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        _create_user(db_session, tenant.id, email="viewer@test.com", role=UserRole.VIEWER, name="Viewer")
        db_session.commit()

        resp = client.get("/api/users?role=VIEWER", headers=_auth_header(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["role"] == "VIEWER"

    def test_status_filter(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        _create_user(db_session, tenant.id, email="disabled@test.com", role=UserRole.VIEWER, status=UserStatus.DISABLED, name="Disabled")
        db_session.commit()

        resp = client.get("/api/users?status=DISABLED", headers=_auth_header(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "DISABLED"


class TestCreateUser:
    def test_tenant_admin_can_create_user(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        db_session.commit()

        resp = client.post(
            "/api/users",
            headers=_auth_header(admin),
            json={
                "name": "New Staff",
                "email": "newstaff@test.com",
                "role": "SALES_STAFF",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Staff"
        assert data["email"] == "newstaff@test.com"
        assert data["role"] == "SALES_STAFF"
        assert data["status"] == "ACTIVE"
        assert data["tenant_id"] == tenant.id

    def test_cannot_create_super_admin(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        db_session.commit()

        resp = client.post(
            "/api/users",
            headers=_auth_header(admin),
            json={
                "name": "Hacker",
                "email": "hacker@test.com",
                "role": "SUPER_ADMIN",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_email_uniqueness_enforced(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        _create_user(db_session, tenant.id, email="existing@test.com", role=UserRole.VIEWER, name="Existing")
        db_session.commit()

        resp = client.post(
            "/api/users",
            headers=_auth_header(admin),
            json={
                "name": "Duplicate",
                "email": "existing@test.com",
                "role": "VIEWER",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "DUPLICATE_EMAIL"

    def test_can_create_all_allowed_roles(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        db_session.commit()

        for i, role in enumerate(["TENANT_ADMIN", "INVENTORY_MANAGER", "SALES_STAFF", "PURCHASE_STAFF", "VIEWER"]):
            resp = client.post(
                "/api/users",
                headers=_auth_header(admin),
                json={
                    "name": f"User {role}",
                    "email": f"user{i}@test.com",
                    "role": role,
                    "password": "securepass123",
                },
            )
            assert resp.status_code == 201, f"Failed to create user with role {role}"


class TestUpdateUser:
    def test_tenant_admin_can_update_user(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff")
        db_session.commit()

        resp = client.patch(
            f"/api/users/{staff.id}",
            headers=_auth_header(admin),
            json={"name": "Updated Staff", "role": "INVENTORY_MANAGER"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Staff"
        assert data["role"] == "INVENTORY_MANAGER"

    def test_cannot_update_user_in_another_tenant(self, client: TestClient, db_session: Session):
        tenant1 = _create_tenant(db_session, "Tenant 1")
        tenant2 = _create_tenant(db_session, "Tenant 2")
        admin1 = _create_user(db_session, tenant1.id, email="admin1@test.com")
        user2 = _create_user(db_session, tenant2.id, email="user2@test.com", role=UserRole.VIEWER, name="Other")
        db_session.commit()

        resp = client.patch(
            f"/api/users/{user2.id}",
            headers=_auth_header(admin1),
            json={"name": "Hacked"},
        )
        assert resp.status_code == 404

    def test_cannot_assign_super_admin_role(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff")
        db_session.commit()

        resp = client.patch(
            f"/api/users/{staff.id}",
            headers=_auth_header(admin),
            json={"role": "SUPER_ADMIN"},
        )
        assert resp.status_code == 403

    def test_cannot_change_own_role(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        db_session.commit()

        resp = client.patch(
            f"/api/users/{admin.id}",
            headers=_auth_header(admin),
            json={"role": "VIEWER"},
        )
        assert resp.status_code == 403


class TestDisableUser:
    def test_tenant_admin_can_disable_user(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff")
        db_session.commit()

        resp = client.post(f"/api/users/{staff.id}/disable", headers=_auth_header(admin))
        assert resp.status_code == 200
        assert resp.json()["status"] == "DISABLED"

    def test_cannot_disable_self(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        db_session.commit()

        resp = client.post(f"/api/users/{admin.id}/disable", headers=_auth_header(admin))
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_delete_endpoint_disables_user(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff")
        db_session.commit()

        resp = client.delete(f"/api/users/{staff.id}", headers=_auth_header(admin))
        assert resp.status_code == 200
        assert resp.json()["status"] == "DISABLED"


class TestEnableUser:
    def test_tenant_admin_can_enable_user(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, status=UserStatus.DISABLED, name="Staff")
        db_session.commit()

        resp = client.post(f"/api/users/{staff.id}/enable", headers=_auth_header(admin))
        assert resp.status_code == 200
        assert resp.json()["status"] == "ACTIVE"


class TestResetPassword:
    def test_tenant_admin_can_reset_password(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff")
        db_session.commit()

        resp = client.post(
            f"/api/users/{staff.id}/reset-password",
            headers=_auth_header(admin),
            json={"new_password": "newpassword123"},
        )
        assert resp.status_code == 200

        # Verify new password works by logging in
        login_resp = client.post("/api/auth/login", json={"email": "staff@test.com", "password": "newpassword123"})
        assert login_resp.status_code == 200


class TestNonAdminAccess:
    def test_non_admin_gets_403_on_list(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff")
        db_session.commit()

        resp = client.get("/api/users", headers=_auth_header(staff))
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_create(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff")
        db_session.commit()

        resp = client.post(
            "/api/users",
            headers=_auth_header(staff),
            json={"name": "X", "email": "x@test.com", "role": "VIEWER", "password": "securepass123"},
        )
        assert resp.status_code == 403

    def test_non_admin_gets_403_on_disable(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff")
        db_session.commit()

        resp = client.post("/api/users/1/disable", headers=_auth_header(staff))
        assert resp.status_code == 403

    def test_viewer_gets_403(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        viewer = _create_user(db_session, tenant.id, email="viewer@test.com", role=UserRole.VIEWER, name="Viewer")
        db_session.commit()

        resp = client.get("/api/users", headers=_auth_header(viewer))
        assert resp.status_code == 403


class TestDisabledUserLogin:
    def test_disabled_user_cannot_login(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        _create_user(db_session, tenant.id, email="disabled@test.com", role=UserRole.SALES_STAFF, status=UserStatus.DISABLED, name="Disabled")
        db_session.commit()

        resp = client.post("/api/auth/login", json={"email": "disabled@test.com", "password": "password123"})
        assert resp.status_code == 403


class TestGetUser:
    def test_get_user_detail(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id)
        staff = _create_user(db_session, tenant.id, email="staff@test.com", role=UserRole.SALES_STAFF, name="Staff User")
        db_session.commit()

        resp = client.get(f"/api/users/{staff.id}", headers=_auth_header(admin))
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Staff User"
        assert data["email"] == "staff@test.com"

    def test_get_user_from_other_tenant_returns_404(self, client: TestClient, db_session: Session):
        tenant1 = _create_tenant(db_session, "Tenant 1")
        tenant2 = _create_tenant(db_session, "Tenant 2")
        admin1 = _create_user(db_session, tenant1.id, email="admin1@test.com")
        user2 = _create_user(db_session, tenant2.id, email="user2@test.com", role=UserRole.VIEWER, name="Other")
        db_session.commit()

        resp = client.get(f"/api/users/{user2.id}", headers=_auth_header(admin1))
        assert resp.status_code == 404
