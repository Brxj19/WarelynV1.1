from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.models.workflow import WorkflowTask, WorkflowTaskStatus


def _create_tenant_with_admin(db: Session, company: str, email: str) -> tuple[Tenant, User]:
    tenant = Tenant(company_name=company, contact_email=email, status=TenantStatus.ACTIVE)
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        name=f"{company} Admin",
        email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    return tenant, user


def _login(client: TestClient, email: str) -> str:
    resp = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _setup_sales_for_tenant(client: TestClient, token: str, suffix: str) -> dict:
    h = _headers(token)
    customer = client.post("/api/catalog/customers", json={"name": f"Cust {suffix}", "email": f"c{suffix}@iso.com"}, headers=h)
    product = client.post("/api/catalog/products", json={"name": f"Prod {suffix}", "sku": f"ISO-{suffix}"}, headers=h)
    warehouse = client.post("/api/warehouses", json={"name": f"WH {suffix}", "code": f"I{suffix}"}, headers=h)
    assert customer.status_code == 201
    assert product.status_code == 201
    assert warehouse.status_code == 201
    loc = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "S", "code": f"S{suffix}", "location_type": "STORAGE"}, headers=h)
    assert loc.status_code == 201

    client.post("/api/inventory/stock-in", json={
        "product_id": product.json()["id"],
        "warehouse_id": warehouse.json()["id"],
        "location_id": loc.json()["id"],
        "quantity": "20",
        "idempotency_key": f"iso-stock-{suffix}",
    }, headers=h)

    order = client.post("/api/sales-orders", json={
        "customer_id": customer.json()["id"],
        "order_number": f"SO-ISO-{suffix}",
        "order_date": "2026-05-28",
        "items": [{"product_id": product.json()["id"], "ordered_quantity": "2", "unit_price": "10.00"}],
    }, headers=h)
    assert order.status_code == 201
    so = order.json()

    confirm = client.post(f"/api/sales-orders/{so['id']}/confirm", json={
        "idempotency_key": f"iso-confirm-{suffix}",
        "allocations": [{"sales_order_item_id": so["items"][0]["id"], "warehouse_id": warehouse.json()["id"], "location_id": loc.json()["id"], "quantity": "2"}],
    }, headers=h)
    assert confirm.status_code == 200

    return {"sales_order_id": so["id"]}


class TestTenantIsolation:
    def test_tenant_a_cannot_read_tenant_b_sales_orders(self, client: TestClient, db_session: Session):
        tenant_a, user_a = _create_tenant_with_admin(db_session, "Tenant A", "a@iso.com")
        tenant_b, user_b = _create_tenant_with_admin(db_session, "Tenant B", "b@iso.com")
        db_session.commit()

        token_a = _login(client, "a@iso.com")
        token_b = _login(client, "b@iso.com")

        data_b = _setup_sales_for_tenant(client, token_b, "B")

        resp = client.get(f"/api/sales-orders/{data_b['sales_order_id']}", headers=_headers(token_a))
        assert resp.status_code == 404

    def test_tenant_a_cannot_complete_tenant_b_workflow_tasks(self, client: TestClient, db_session: Session):
        tenant_a, user_a = _create_tenant_with_admin(db_session, "Tenant A", "a@iso.com")
        tenant_b, user_b = _create_tenant_with_admin(db_session, "Tenant B", "b@iso.com")
        db_session.flush()

        task_b = WorkflowTask(
            tenant_id=tenant_b.id,
            workflow_type="SALES",
            entity_type="sales_order",
            entity_id=999,
            step_key="PICK_ORDER",
            title="Pick order",
            assigned_role="TENANT_ADMIN",
            priority="NORMAL",
            status=WorkflowTaskStatus.OPEN,
        )
        db_session.add(task_b)
        db_session.commit()

        token_a = _login(client, "a@iso.com")
        resp = client.post(f"/api/workflow/tasks/{task_b.id}/complete", json={}, headers=_headers(token_a))
        assert resp.status_code == 404

    def test_tenant_a_cannot_read_tenant_b_invoices(self, client: TestClient, db_session: Session):
        tenant_a, user_a = _create_tenant_with_admin(db_session, "Tenant A", "a@iso.com")
        tenant_b, user_b = _create_tenant_with_admin(db_session, "Tenant B", "b@iso.com")
        db_session.commit()

        token_a = _login(client, "a@iso.com")
        token_b = _login(client, "b@iso.com")

        _setup_sales_for_tenant(client, token_b, "B2")

        # Tenant B's invoices list
        invoices_b = client.get("/api/invoices", headers=_headers(token_b))
        # Tenant A should see no invoices (they belong to B)
        invoices_a = client.get("/api/invoices", headers=_headers(token_a))
        assert invoices_a.status_code == 200
        assert len(invoices_a.json()) == 0

        if invoices_b.status_code == 200 and len(invoices_b.json()) > 0:
            inv_id = invoices_b.json()[0]["id"]
            detail = client.get(f"/api/invoices/{inv_id}", headers=_headers(token_a))
            assert detail.status_code == 404

    def test_tenant_a_cannot_read_tenant_b_workflow_events(self, client: TestClient, db_session: Session):
        tenant_a, user_a = _create_tenant_with_admin(db_session, "Tenant A", "a@iso.com")
        tenant_b, user_b = _create_tenant_with_admin(db_session, "Tenant B", "b@iso.com")
        db_session.commit()

        token_a = _login(client, "a@iso.com")
        token_b = _login(client, "b@iso.com")

        _setup_sales_for_tenant(client, token_b, "B3")

        # Tenant A queries events — should see nothing from B
        events_a = client.get("/api/workflow/events", headers=_headers(token_a))
        assert events_a.status_code == 200
        assert len(events_a.json()) == 0
