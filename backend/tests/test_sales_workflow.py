from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.auth import Tenant, UserRole
from app.models.workflow import WorkflowTask


def register_and_login(client: TestClient, email: str = "admin@example.com") -> dict[str, object]:
    response = client.post("/api/auth/register", json={"company_name": "Acme", "name": "Admin", "email": email, "password": "StrongPass123!"})
    assert response.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def setup_sales_dimension(client: TestClient, token: str) -> dict[str, int]:
    headers = auth_headers(token)
    customer = client.post("/api/catalog/customers", json={"name": "Customer 1", "email": "c1@example.com"}, headers=headers)
    product = client.post("/api/catalog/products", json={"name": "Widget", "sku": "WF-1"}, headers=headers)
    warehouse = client.post("/api/warehouses", json={"name": "Main", "code": "WF1"}, headers=headers)
    assert customer.status_code == 201
    assert product.status_code == 201
    assert warehouse.status_code == 201
    location = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Storage", "code": "WFS", "location_type": "STORAGE"}, headers=headers)
    assert location.status_code == 201
    return {"customer_id": customer.json()["id"], "product_id": product.json()["id"], "warehouse_id": warehouse.json()["id"], "location_id": location.json()["id"]}


def stock_in(client: TestClient, token: str, dimension: dict[str, int], quantity: str = "10") -> None:
    response = client.post("/api/inventory/stock-in", json={"product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": quantity, "idempotency_key": "wf-stock-in"}, headers=auth_headers(token))
    assert response.status_code == 200


def create_and_confirm_order(client: TestClient, token: str, dimension: dict[str, int]) -> dict[str, object]:
    order_resp = client.post("/api/sales-orders", json={
        "customer_id": dimension["customer_id"],
        "order_number": "SO-WF-1",
        "order_date": "2026-05-28",
        "items": [{"product_id": dimension["product_id"], "ordered_quantity": "4", "unit_price": "9.99"}],
    }, headers=auth_headers(token))
    assert order_resp.status_code == 201
    order = order_resp.json()
    confirm_resp = client.post(f"/api/sales-orders/{order['id']}/confirm", json={
        "idempotency_key": "wf-confirm-1",
        "allocations": [{"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "4"}],
    }, headers=auth_headers(token))
    assert confirm_resp.status_code == 200
    return confirm_resp.json()["sales_order"]


def test_confirm_creates_pick_task(client: TestClient, db_session: Session):
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token)
    stock_in(client, token, dimension)
    order = create_and_confirm_order(client, token, dimension)

    tenant = db_session.query(Tenant).one()
    tasks = db_session.query(WorkflowTask).filter(
        WorkflowTask.tenant_id == tenant.id,
        WorkflowTask.entity_type == "sales_order",
        WorkflowTask.entity_id == order["id"],
        WorkflowTask.step_key == "PICK_ORDER",
        WorkflowTask.status == "OPEN",
    ).all()
    assert len(tasks) == 1
    assert tasks[0].assigned_role == "INVENTORY_MANAGER"
    assert tasks[0].workflow_type == "SALES"


def test_confirm_twice_no_duplicate_task(client: TestClient, db_session: Session):
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token)
    stock_in(client, token, dimension)
    order = create_and_confirm_order(client, token, dimension)

    # Confirming again should be idempotent (returns same order, no new task)
    confirm_resp = client.post(f"/api/sales-orders/{order['id']}/confirm", json={
        "idempotency_key": "wf-confirm-2",
        "allocations": [{"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "4"}],
    }, headers=auth_headers(token))
    assert confirm_resp.status_code == 200

    tenant = db_session.query(Tenant).one()
    tasks = db_session.query(WorkflowTask).filter(
        WorkflowTask.tenant_id == tenant.id,
        WorkflowTask.entity_type == "sales_order",
        WorkflowTask.entity_id == order["id"],
        WorkflowTask.step_key == "PICK_ORDER",
    ).all()
    open_tasks = [t for t in tasks if t.status == "OPEN"]
    assert len(open_tasks) == 1


def test_cancel_order_cancels_tasks(client: TestClient, db_session: Session):
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token)
    stock_in(client, token, dimension)
    order = create_and_confirm_order(client, token, dimension)

    cancel_resp = client.post(f"/api/sales-orders/{order['id']}/cancel", json={"idempotency_key": "wf-cancel-1"}, headers=auth_headers(token))
    assert cancel_resp.status_code == 200

    tenant = db_session.query(Tenant).one()
    tasks = db_session.query(WorkflowTask).filter(
        WorkflowTask.tenant_id == tenant.id,
        WorkflowTask.entity_type == "sales_order",
        WorkflowTask.entity_id == order["id"],
    ).all()
    assert all(t.status == "CANCELLED" for t in tasks)


def test_commit_fulfillment_creates_invoice_task(client: TestClient, db_session: Session):
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token)
    stock_in(client, token, dimension)

    # Create and confirm order (get reservation from confirm response)
    order_resp = client.post("/api/sales-orders", json={
        "customer_id": dimension["customer_id"],
        "order_number": "SO-WF-1",
        "order_date": "2026-05-28",
        "items": [{"product_id": dimension["product_id"], "ordered_quantity": "4", "unit_price": "9.99"}],
    }, headers=auth_headers(token))
    assert order_resp.status_code == 201
    order = order_resp.json()

    confirm_resp = client.post(f"/api/sales-orders/{order['id']}/confirm", json={
        "idempotency_key": "wf-confirm-ful",
        "allocations": [{"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "4"}],
    }, headers=auth_headers(token))
    assert confirm_resp.status_code == 200
    confirmed = confirm_resp.json()
    reservation_id = confirmed["stock_results"][0]["reservation"]["id"]
    order = confirmed["sales_order"]

    # Create fulfillment
    ful_resp = client.post(f"/api/sales-orders/{order['id']}/fulfillments", json={
        "fulfillment_number": "FUL-WF-1",
        "items": [{"sales_order_item_id": order["items"][0]["id"], "product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "reservation_id": reservation_id, "fulfilled_quantity": "4"}],
    }, headers=auth_headers(token))
    assert ful_resp.status_code == 201
    fulfillment = ful_resp.json()

    # Commit fulfillment
    commit_resp = client.post(f"/api/sales-fulfillments/{fulfillment['id']}/commit", json={"idempotency_key": "wf-commit-1"}, headers=auth_headers(token))
    assert commit_resp.status_code == 200

    tenant = db_session.query(Tenant).one()
    tasks = db_session.query(WorkflowTask).filter(
        WorkflowTask.tenant_id == tenant.id,
        WorkflowTask.entity_type == "sales_order",
        WorkflowTask.entity_id == order["id"],
        WorkflowTask.step_key == "CREATE_INVOICE",
        WorkflowTask.status == "OPEN",
    ).all()
    assert len(tasks) == 1
    assert tasks[0].assigned_role == "SALES_STAFF"
