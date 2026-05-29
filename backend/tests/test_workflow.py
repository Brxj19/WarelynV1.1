from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.models.workflow import WorkflowTask, WorkflowTaskStatus


def _create_tenant(db: Session) -> Tenant:
    tenant = Tenant(company_name="Workflow Corp", contact_email="wf@test.com", status=TenantStatus.ACTIVE)
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


def _register_and_login(client: TestClient, email: str = "admin@wf.com") -> str:
    resp = client.post("/api/auth/register", json={"company_name": "WF Co", "name": "Admin", "email": email, "password": "StrongPass123!"})
    assert resp.status_code == 201
    return _login(client, email)


def _setup_dimension(client: TestClient, token: str) -> dict:
    h = _headers(token)
    customer = client.post("/api/catalog/customers", json={"name": "WF Cust", "email": "wfc@test.com"}, headers=h)
    product = client.post("/api/catalog/products", json={"name": "WF Prod", "sku": "WF-T1"}, headers=h)
    warehouse = client.post("/api/warehouses", json={"name": "WF WH", "code": "WFT"}, headers=h)
    assert customer.status_code == 201
    assert product.status_code == 201
    assert warehouse.status_code == 201
    loc = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Stor", "code": "WFS", "location_type": "STORAGE"}, headers=h)
    assert loc.status_code == 201
    client.post("/api/inventory/stock-in", json={
        "product_id": product.json()["id"],
        "warehouse_id": warehouse.json()["id"],
        "location_id": loc.json()["id"],
        "quantity": "50",
        "idempotency_key": "wf-test-stock",
    }, headers=h)
    return {
        "customer_id": customer.json()["id"],
        "product_id": product.json()["id"],
        "warehouse_id": warehouse.json()["id"],
        "location_id": loc.json()["id"],
    }


class TestConfirmSalesOrderWorkflow:
    def test_confirm_creates_exactly_one_pick_task(self, client: TestClient, db_session: Session):
        token = _register_and_login(client)
        dim = _setup_dimension(client, token)
        h = _headers(token)

        order = client.post("/api/sales-orders", json={
            "customer_id": dim["customer_id"],
            "order_number": "SO-WFT-1",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "3", "unit_price": "10.00"}],
        }, headers=h)
        assert order.status_code == 201
        so = order.json()

        confirm = client.post(f"/api/sales-orders/{so['id']}/confirm", json={
            "idempotency_key": "wft-confirm-1",
            "allocations": [{"sales_order_item_id": so["items"][0]["id"], "warehouse_id": dim["warehouse_id"], "location_id": dim["location_id"], "quantity": "3"}],
        }, headers=h)
        assert confirm.status_code == 200

        tenant = db_session.query(Tenant).filter(Tenant.company_name == "WF Co").one()
        tasks = db_session.query(WorkflowTask).filter(
            WorkflowTask.tenant_id == tenant.id,
            WorkflowTask.entity_type == "sales_order",
            WorkflowTask.entity_id == so["id"],
            WorkflowTask.step_key == "PICK_ORDER",
            WorkflowTask.status == "OPEN",
        ).all()
        assert len(tasks) == 1
        assert tasks[0].assigned_role == "INVENTORY_MANAGER"

    def test_confirm_twice_no_duplicate(self, client: TestClient, db_session: Session):
        token = _register_and_login(client)
        dim = _setup_dimension(client, token)
        h = _headers(token)

        order = client.post("/api/sales-orders", json={
            "customer_id": dim["customer_id"],
            "order_number": "SO-WFT-2",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "2", "unit_price": "10.00"}],
        }, headers=h)
        so = order.json()

        client.post(f"/api/sales-orders/{so['id']}/confirm", json={
            "idempotency_key": "wft-confirm-2a",
            "allocations": [{"sales_order_item_id": so["items"][0]["id"], "warehouse_id": dim["warehouse_id"], "location_id": dim["location_id"], "quantity": "2"}],
        }, headers=h)

        client.post(f"/api/sales-orders/{so['id']}/confirm", json={
            "idempotency_key": "wft-confirm-2b",
            "allocations": [{"sales_order_item_id": so["items"][0]["id"], "warehouse_id": dim["warehouse_id"], "location_id": dim["location_id"], "quantity": "2"}],
        }, headers=h)

        tenant = db_session.query(Tenant).filter(Tenant.company_name == "WF Co").one()
        open_tasks = db_session.query(WorkflowTask).filter(
            WorkflowTask.tenant_id == tenant.id,
            WorkflowTask.entity_type == "sales_order",
            WorkflowTask.entity_id == so["id"],
            WorkflowTask.step_key == "PICK_ORDER",
            WorkflowTask.status == "OPEN",
        ).all()
        assert len(open_tasks) == 1

    def test_cancel_order_cancels_all_tasks(self, client: TestClient, db_session: Session):
        token = _register_and_login(client)
        dim = _setup_dimension(client, token)
        h = _headers(token)

        order = client.post("/api/sales-orders", json={
            "customer_id": dim["customer_id"],
            "order_number": "SO-WFT-3",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "2", "unit_price": "10.00"}],
        }, headers=h)
        so = order.json()

        client.post(f"/api/sales-orders/{so['id']}/confirm", json={
            "idempotency_key": "wft-confirm-3",
            "allocations": [{"sales_order_item_id": so["items"][0]["id"], "warehouse_id": dim["warehouse_id"], "location_id": dim["location_id"], "quantity": "2"}],
        }, headers=h)

        cancel = client.post(f"/api/sales-orders/{so['id']}/cancel", json={"idempotency_key": "wft-cancel-3"}, headers=h)
        assert cancel.status_code == 200

        tenant = db_session.query(Tenant).filter(Tenant.company_name == "WF Co").one()
        tasks = db_session.query(WorkflowTask).filter(
            WorkflowTask.tenant_id == tenant.id,
            WorkflowTask.entity_type == "sales_order",
            WorkflowTask.entity_id == so["id"],
        ).all()
        assert all(t.status == "CANCELLED" for t in tasks)


class TestFulfillmentWorkflow:
    def test_commit_fulfillment_creates_invoice_task(self, client: TestClient, db_session: Session):
        token = _register_and_login(client)
        dim = _setup_dimension(client, token)
        h = _headers(token)

        order = client.post("/api/sales-orders", json={
            "customer_id": dim["customer_id"],
            "order_number": "SO-WFT-4",
            "order_date": "2026-05-28",
            "items": [{"product_id": dim["product_id"], "ordered_quantity": "2", "unit_price": "10.00"}],
        }, headers=h)
        so = order.json()

        confirm = client.post(f"/api/sales-orders/{so['id']}/confirm", json={
            "idempotency_key": "wft-confirm-4",
            "allocations": [{"sales_order_item_id": so["items"][0]["id"], "warehouse_id": dim["warehouse_id"], "location_id": dim["location_id"], "quantity": "2"}],
        }, headers=h)
        confirmed = confirm.json()
        reservation_id = confirmed["stock_results"][0]["reservation"]["id"]
        so = confirmed["sales_order"]

        ful = client.post(f"/api/sales-orders/{so['id']}/fulfillments", json={
            "fulfillment_number": "FUL-WFT-4",
            "items": [{"sales_order_item_id": so["items"][0]["id"], "product_id": dim["product_id"], "warehouse_id": dim["warehouse_id"], "location_id": dim["location_id"], "reservation_id": reservation_id, "fulfilled_quantity": "2"}],
        }, headers=h)
        assert ful.status_code == 201

        commit = client.post(f"/api/sales-fulfillments/{ful.json()['id']}/commit", json={"idempotency_key": "wft-commit-4"}, headers=h)
        assert commit.status_code == 200

        tenant = db_session.query(Tenant).filter(Tenant.company_name == "WF Co").one()
        tasks = db_session.query(WorkflowTask).filter(
            WorkflowTask.tenant_id == tenant.id,
            WorkflowTask.entity_type == "sales_order",
            WorkflowTask.entity_id == so["id"],
            WorkflowTask.step_key == "CREATE_INVOICE",
            WorkflowTask.status == "OPEN",
        ).all()
        assert len(tasks) == 1
        assert tasks[0].assigned_role == "SALES_STAFF"


class TestPurchaseWorkflow:
    def test_commit_receipt_creates_putaway_task(self, client: TestClient, db_session: Session):
        token = _register_and_login(client)
        h = _headers(token)

        vendor = client.post("/api/catalog/vendors", json={"name": "V WFT"}, headers=h)
        product = client.post("/api/catalog/products", json={"name": "P WFT", "sku": "WFT-P"}, headers=h)
        warehouse = client.post("/api/warehouses", json={"name": "WH WFT", "code": "WFP"}, headers=h)
        loc = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Recv", "code": "WFR", "location_type": "RECEIVING"}, headers=h)

        po = client.post("/api/purchase-orders", json={
            "vendor_id": vendor.json()["id"],
            "po_number": "PO-WFT-1",
            "order_date": "2026-05-28",
            "items": [{"product_id": product.json()["id"], "ordered_quantity": "5", "unit_cost": "3.00"}],
        }, headers=h)
        assert po.status_code == 201
        po_data = po.json()

        client.post(f"/api/purchase-orders/{po_data['id']}/submit", json={}, headers=h)
        client.post(f"/api/purchase-orders/{po_data['id']}/approve", json={}, headers=h)

        receipt = client.post(f"/api/purchase-orders/{po_data['id']}/receipts", json={
            "receipt_number": "GRN-WFT-1",
            "items": [{"purchase_order_item_id": po_data["items"][0]["id"], "product_id": product.json()["id"], "warehouse_id": warehouse.json()["id"], "location_id": loc.json()["id"], "received_quantity": "5"}],
        }, headers=h)
        assert receipt.status_code == 201

        commit = client.post(f"/api/purchase-receipts/{receipt.json()['id']}/commit", json={"idempotency_key": "wft-rcpt-1"}, headers=h)
        assert commit.status_code == 200

        tenant = db_session.query(Tenant).filter(Tenant.company_name == "WF Co").one()
        tasks = db_session.query(WorkflowTask).filter(
            WorkflowTask.tenant_id == tenant.id,
            WorkflowTask.entity_type == "purchase_receipt",
            WorkflowTask.entity_id == receipt.json()["id"],
            WorkflowTask.step_key == "PUTAWAY_STOCK",
            WorkflowTask.status == "OPEN",
        ).all()
        assert len(tasks) == 1
        assert tasks[0].assigned_role == "INVENTORY_MANAGER"


class TestMyTasksFiltering:
    def test_inventory_manager_sees_own_tasks(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        im = _create_user(db_session, tenant.id, "im@wf.com", UserRole.INVENTORY_MANAGER)
        sales = _create_user(db_session, tenant.id, "sales@wf.com", UserRole.SALES_STAFF)
        db_session.flush()

        im_task = WorkflowTask(tenant_id=tenant.id, workflow_type="SALES", entity_type="sales_order", entity_id=1, step_key="PICK_ORDER", title="Pick order", assigned_role="INVENTORY_MANAGER", priority="NORMAL", status=WorkflowTaskStatus.OPEN)
        sales_task = WorkflowTask(tenant_id=tenant.id, workflow_type="SALES", entity_type="sales_order", entity_id=2, step_key="CREATE_INVOICE", title="Create invoice", assigned_role="SALES_STAFF", priority="NORMAL", status=WorkflowTaskStatus.OPEN)
        db_session.add_all([im_task, sales_task])
        db_session.commit()

        token = _login(client, "im@wf.com")
        resp = client.get("/api/workflow/my-tasks", headers=_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert all(t["assigned_role"] == "INVENTORY_MANAGER" for t in data)
        assert len(data) == 1

    def test_sales_staff_does_not_see_im_tasks(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        _create_user(db_session, tenant.id, "im@wf.com", UserRole.INVENTORY_MANAGER)
        _create_user(db_session, tenant.id, "sales@wf.com", UserRole.SALES_STAFF)
        db_session.flush()

        im_task = WorkflowTask(tenant_id=tenant.id, workflow_type="SALES", entity_type="sales_order", entity_id=1, step_key="PICK_ORDER", title="Pick order", assigned_role="INVENTORY_MANAGER", priority="NORMAL", status=WorkflowTaskStatus.OPEN)
        db_session.add(im_task)
        db_session.commit()

        token = _login(client, "sales@wf.com")
        resp = client.get("/api/workflow/my-tasks", headers=_headers(token))
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_viewer_cannot_access_my_tasks(self, client: TestClient, db_session: Session):
        tenant = _create_tenant(db_session)
        _create_user(db_session, tenant.id, "viewer@wf.com", UserRole.VIEWER)
        db_session.commit()

        token = _login(client, "viewer@wf.com")
        resp = client.get("/api/workflow/my-tasks", headers=_headers(token))
        assert resp.status_code == 403
