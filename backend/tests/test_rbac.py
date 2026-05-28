from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.models.workflow import WorkflowTask, WorkflowTaskStatus


def _create_tenant(db: Session) -> Tenant:
    tenant = Tenant(company_name="RBAC Corp", contact_email="rbac@test.com", status=TenantStatus.ACTIVE)
    db.add(tenant)
    db.flush()
    return tenant


def _create_user(db: Session, tenant_id: int, email: str, role: UserRole) -> User:
    user = User(
        tenant_id=tenant_id,
        name=f"{role.value} User",
        email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=role,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    return user


def _login(client: TestClient, email: str) -> str:
    resp = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup_sales_dimension(client: TestClient, token: str) -> dict:
    h = _headers(token)
    customer = client.post("/api/catalog/customers", json={"name": "C1", "email": "c1@rbac.com"}, headers=h)
    product = client.post("/api/catalog/products", json={"name": "P1", "sku": "RBAC-1"}, headers=h)
    assert customer.status_code == 201
    assert product.status_code == 201
    return {"customer_id": customer.json()["id"], "product_id": product.json()["id"]}


def _setup_purchase_dimension(client: TestClient, token: str) -> dict:
    h = _headers(token)
    vendor = client.post("/api/catalog/vendors", json={"name": "V1"}, headers=h)
    product = client.post("/api/catalog/products", json={"name": "P2", "sku": "RBAC-2"}, headers=h)
    assert vendor.status_code == 201
    assert product.status_code == 201
    return {"vendor_id": vendor.json()["id"], "product_id": product.json()["id"]}


class TestSalesOrderRBAC:
    def test_viewer_cannot_create_sales_order(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id, "admin@rbac.com", UserRole.TENANT_ADMIN)
        viewer = _create_user(db_session, tenant.id, "viewer@rbac.com", UserRole.VIEWER)
        db_session.commit()

        admin_token = _login(client, "admin@rbac.com")
        dim = _setup_sales_dimension(client, admin_token)

        viewer_token = _login(client, "viewer@rbac.com")
        resp = client.post("/api/sales-orders", json={
            "customer_id": dim["customer_id"],
            "order_number": "SO-RBAC-1",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "1", "unit_price": "10.00"}],
        }, headers=_headers(viewer_token))
        assert resp.status_code == 403

    def test_purchase_staff_cannot_create_sales_order(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id, "admin@rbac.com", UserRole.TENANT_ADMIN)
        purchase = _create_user(db_session, tenant.id, "purchase@rbac.com", UserRole.PURCHASE_STAFF)
        db_session.commit()

        admin_token = _login(client, "admin@rbac.com")
        dim = _setup_sales_dimension(client, admin_token)

        purchase_token = _login(client, "purchase@rbac.com")
        resp = client.post("/api/sales-orders", json={
            "customer_id": dim["customer_id"],
            "order_number": "SO-RBAC-2",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "1", "unit_price": "10.00"}],
        }, headers=_headers(purchase_token))
        assert resp.status_code == 403

    def test_sales_staff_can_create_sales_order(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id, "admin@rbac.com", UserRole.TENANT_ADMIN)
        sales = _create_user(db_session, tenant.id, "sales@rbac.com", UserRole.SALES_STAFF)
        db_session.commit()

        admin_token = _login(client, "admin@rbac.com")
        dim = _setup_sales_dimension(client, admin_token)

        sales_token = _login(client, "sales@rbac.com")
        resp = client.post("/api/sales-orders", json={
            "customer_id": dim["customer_id"],
            "order_number": "SO-RBAC-3",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "1", "unit_price": "10.00"}],
        }, headers=_headers(sales_token))
        assert resp.status_code == 201


class TestPurchaseOrderRBAC:
    def test_viewer_cannot_create_purchase_order(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id, "admin@rbac.com", UserRole.TENANT_ADMIN)
        viewer = _create_user(db_session, tenant.id, "viewer@rbac.com", UserRole.VIEWER)
        db_session.commit()

        admin_token = _login(client, "admin@rbac.com")
        dim = _setup_purchase_dimension(client, admin_token)

        viewer_token = _login(client, "viewer@rbac.com")
        resp = client.post("/api/purchase-orders", json={
            "vendor_id": dim["vendor_id"],
            "po_number": "PO-RBAC-1",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "5", "unit_cost": "4.50"}],
        }, headers=_headers(viewer_token))
        assert resp.status_code == 403

    def test_sales_staff_cannot_create_purchase_order(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id, "admin@rbac.com", UserRole.TENANT_ADMIN)
        sales = _create_user(db_session, tenant.id, "sales@rbac.com", UserRole.SALES_STAFF)
        db_session.commit()

        admin_token = _login(client, "admin@rbac.com")
        dim = _setup_purchase_dimension(client, admin_token)

        sales_token = _login(client, "sales@rbac.com")
        resp = client.post("/api/purchase-orders", json={
            "vendor_id": dim["vendor_id"],
            "po_number": "PO-RBAC-2",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "5", "unit_cost": "4.50"}],
        }, headers=_headers(sales_token))
        assert resp.status_code == 403

    def test_purchase_staff_can_create_purchase_order(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id, "admin@rbac.com", UserRole.TENANT_ADMIN)
        purchase = _create_user(db_session, tenant.id, "purchase@rbac.com", UserRole.PURCHASE_STAFF)
        db_session.commit()

        admin_token = _login(client, "admin@rbac.com")
        dim = _setup_purchase_dimension(client, admin_token)

        purchase_token = _login(client, "purchase@rbac.com")
        resp = client.post("/api/purchase-orders", json={
            "vendor_id": dim["vendor_id"],
            "po_number": "PO-RBAC-3",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "5", "unit_cost": "4.50"}],
        }, headers=_headers(purchase_token))
        assert resp.status_code == 201


class TestSettingsUsersRBAC:
    def test_inventory_manager_cannot_list_users(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        _create_user(db_session, tenant.id, "im@rbac.com", UserRole.INVENTORY_MANAGER)
        db_session.commit()

        token = _login(client, "im@rbac.com")
        resp = client.get("/api/users", headers=_headers(token))
        assert resp.status_code == 403

    def test_sales_staff_cannot_list_users(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        _create_user(db_session, tenant.id, "sales@rbac.com", UserRole.SALES_STAFF)
        db_session.commit()

        token = _login(client, "sales@rbac.com")
        resp = client.get("/api/users", headers=_headers(token))
        assert resp.status_code == 403

    def test_tenant_admin_can_list_users(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        _create_user(db_session, tenant.id, "admin@rbac.com", UserRole.TENANT_ADMIN)
        db_session.commit()

        token = _login(client, "admin@rbac.com")
        resp = client.get("/api/users", headers=_headers(token))
        assert resp.status_code == 200


class TestAdminRBAC:
    def test_tenant_admin_cannot_access_admin(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        _create_user(db_session, tenant.id, "admin@rbac.com", UserRole.TENANT_ADMIN)
        db_session.commit()

        token = _login(client, "admin@rbac.com")
        resp = client.get("/api/admin/tenants", headers=_headers(token))
        assert resp.status_code == 403

    def test_super_admin_can_access_admin(self, client: TestClient, db_session: Session):
        sa = User(
            name="Super",
            email="super@rbac.com",
            password_hash=get_password_hash("StrongPass123!"),
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE,
            tenant_id=None,
        )
        db_session.add(sa)
        db_session.commit()

        token = _login(client, "super@rbac.com")
        resp = client.get("/api/admin/tenants", headers=_headers(token))
        assert resp.status_code == 200


class TestWorkflowCompleteRBAC:
    def test_viewer_cannot_complete_task(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        _create_user(db_session, tenant.id, "viewer@rbac.com", UserRole.VIEWER)
        db_session.commit()

        token = _login(client, "viewer@rbac.com")
        resp = client.post("/api/workflow/tasks/1/complete", json={}, headers=_headers(token))
        assert resp.status_code == 403

    def test_matching_role_can_complete_task(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        im = _create_user(db_session, tenant.id, "im@rbac.com", UserRole.INVENTORY_MANAGER)
        db_session.flush()

        task = WorkflowTask(
            tenant_id=tenant.id,
            workflow_type="SALES",
            entity_type="sales_order",
            entity_id=999,
            step_key="PICK_ORDER",
            title="Pick order",
            assigned_role="INVENTORY_MANAGER",
            priority="NORMAL",
            status=WorkflowTaskStatus.OPEN,
        )
        db_session.add(task)
        db_session.commit()

        token = _login(client, "im@rbac.com")
        resp = client.post(f"/api/workflow/tasks/{task.id}/complete", json={}, headers=_headers(token))
        assert resp.status_code == 200

    def test_tenant_admin_override_can_complete_any_task(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        admin = _create_user(db_session, tenant.id, "admin@rbac.com", UserRole.TENANT_ADMIN)
        db_session.flush()

        task = WorkflowTask(
            tenant_id=tenant.id,
            workflow_type="PURCHASING",
            entity_type="purchase_order",
            entity_id=888,
            step_key="APPROVE_PO",
            title="Approve purchase order",
            assigned_role="PURCHASE_STAFF",
            priority="HIGH",
            status=WorkflowTaskStatus.OPEN,
        )
        db_session.add(task)
        db_session.commit()

        token = _login(client, "admin@rbac.com")
        resp = client.post(f"/api/workflow/tasks/{task.id}/complete", json={}, headers=_headers(token))
        assert resp.status_code == 200

    def test_wrong_role_cannot_complete_task(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        sales = _create_user(db_session, tenant.id, "sales@rbac.com", UserRole.SALES_STAFF)
        db_session.flush()

        task = WorkflowTask(
            tenant_id=tenant.id,
            workflow_type="PURCHASING",
            entity_type="purchase_order",
            entity_id=777,
            step_key="APPROVE_PO",
            title="Approve purchase order",
            assigned_role="PURCHASE_STAFF",
            priority="NORMAL",
            status=WorkflowTaskStatus.OPEN,
        )
        db_session.add(task)
        db_session.commit()

        token = _login(client, "sales@rbac.com")
        resp = client.post(f"/api/workflow/tasks/{task.id}/complete", json={}, headers=_headers(token))
        assert resp.status_code == 403
