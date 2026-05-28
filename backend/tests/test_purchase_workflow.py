from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.auth import Tenant
from app.models.operations import PutawayTask, PutawayTaskStatus
from app.models.workflow import WorkflowTask


def register_and_login(client: TestClient) -> dict[str, object]:
    response = client.post("/api/auth/register", json={"company_name": "Acme", "name": "Admin", "email": "admin@example.com", "password": "StrongPass123!"})
    assert response.status_code == 201
    login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def setup_purchase_dimension(client: TestClient, token: str) -> dict[str, int]:
    headers = auth_headers(token)
    vendor = client.post("/api/catalog/vendors", json={"name": "Vendor PW"}, headers=headers)
    product = client.post("/api/catalog/products", json={"name": "Widget PW", "sku": "PW-1"}, headers=headers)
    warehouse = client.post("/api/warehouses", json={"name": "Main PW", "code": "PW1"}, headers=headers)
    assert vendor.status_code == 201
    assert product.status_code == 201
    assert warehouse.status_code == 201
    location = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Receiving", "code": "RPW", "location_type": "RECEIVING"}, headers=headers)
    assert location.status_code == 201
    return {"vendor_id": vendor.json()["id"], "product_id": product.json()["id"], "warehouse_id": warehouse.json()["id"], "location_id": location.json()["id"]}


def create_and_commit_receipt(client: TestClient, token: str, dimension: dict[str, int]) -> dict[str, object]:
    headers = auth_headers(token)
    po_resp = client.post("/api/purchase-orders", json={
        "vendor_id": dimension["vendor_id"],
        "po_number": "PO-PW-1",
        "order_date": "2026-05-28",
        "items": [{"product_id": dimension["product_id"], "ordered_quantity": "5", "unit_cost": "4.50"}],
    }, headers=headers)
    assert po_resp.status_code == 201
    po = po_resp.json()

    submit_resp = client.post(f"/api/purchase-orders/{po['id']}/submit", json={}, headers=headers)
    assert submit_resp.status_code == 200

    receipt_resp = client.post(f"/api/purchase-orders/{po['id']}/receipts", json={
        "receipt_number": "GRN-PW-1",
        "items": [{"purchase_order_item_id": po["items"][0]["id"], "product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "received_quantity": "5"}],
    }, headers=headers)
    assert receipt_resp.status_code == 201
    receipt = receipt_resp.json()

    commit_resp = client.post(f"/api/purchase-receipts/{receipt['id']}/commit", json={"idempotency_key": "pw-commit-1"}, headers=headers)
    assert commit_resp.status_code == 200
    return {"po": po, "receipt": receipt, "commit": commit_resp.json()}


def test_commit_receipt_creates_putaway_task(client: TestClient, db_session: Session):
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_purchase_dimension(client, token)
    result = create_and_commit_receipt(client, token, dimension)

    tenant = db_session.query(Tenant).one()
    tasks = db_session.query(WorkflowTask).filter(
        WorkflowTask.tenant_id == tenant.id,
        WorkflowTask.entity_type == "purchase_receipt",
        WorkflowTask.entity_id == result["receipt"]["id"],
        WorkflowTask.step_key == "PUTAWAY_STOCK",
        WorkflowTask.status == "OPEN",
    ).all()
    assert len(tasks) == 1
    assert tasks[0].assigned_role == "INVENTORY_MANAGER"


def test_complete_putaway_creates_record_bill_task(client: TestClient, db_session: Session):
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_purchase_dimension(client, token)
    result = create_and_commit_receipt(client, token, dimension)
    headers = auth_headers(token)

    # Create a putaway task linked to the receipt
    putaway_resp = client.post("/api/putaway-tasks", json={
        "product_id": dimension["product_id"],
        "warehouse_id": dimension["warehouse_id"],
        "from_location_id": dimension["location_id"],
        "to_location_id": dimension["location_id"],
        "quantity": "5",
        "receipt_id": result["receipt"]["id"],
    }, headers=headers)
    assert putaway_resp.status_code == 201
    putaway = putaway_resp.json()

    # Complete the putaway task
    complete_resp = client.post(f"/api/putaway-tasks/{putaway['id']}/complete", json={}, headers=headers)
    assert complete_resp.status_code == 200

    tenant = db_session.query(Tenant).one()
    po = result["po"]
    tasks = db_session.query(WorkflowTask).filter(
        WorkflowTask.tenant_id == tenant.id,
        WorkflowTask.entity_type == "purchase_order",
        WorkflowTask.entity_id == po["id"],
        WorkflowTask.step_key == "RECORD_BILL",
        WorkflowTask.status == "OPEN",
    ).all()
    assert len(tasks) == 1
    assert tasks[0].assigned_role == "PURCHASE_STAFF"


def test_record_bill_completes_record_bill_task(client: TestClient, db_session: Session):
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_purchase_dimension(client, token)
    result = create_and_commit_receipt(client, token, dimension)
    headers = auth_headers(token)

    # Create a putaway task and complete it to generate RECORD_BILL task
    putaway_resp = client.post("/api/putaway-tasks", json={
        "product_id": dimension["product_id"],
        "warehouse_id": dimension["warehouse_id"],
        "from_location_id": dimension["location_id"],
        "to_location_id": dimension["location_id"],
        "quantity": "5",
        "receipt_id": result["receipt"]["id"],
    }, headers=headers)
    assert putaway_resp.status_code == 201
    complete_resp = client.post(f"/api/putaway-tasks/{putaway_resp.json()['id']}/complete", json={}, headers=headers)
    assert complete_resp.status_code == 200

    po = result["po"]
    # Verify RECORD_BILL task exists
    tenant = db_session.query(Tenant).one()
    open_tasks = db_session.query(WorkflowTask).filter(
        WorkflowTask.tenant_id == tenant.id,
        WorkflowTask.entity_type == "purchase_order",
        WorkflowTask.entity_id == po["id"],
        WorkflowTask.step_key == "RECORD_BILL",
        WorkflowTask.status == "OPEN",
    ).all()
    assert len(open_tasks) == 1

    # Record a bill for this PO
    bill_resp = client.post("/api/bills", json={
        "purchase_order_id": po["id"],
        "receipt_id": result["receipt"]["id"],
    }, headers=headers)
    assert bill_resp.status_code == 201

    # RECORD_BILL task should now be cancelled
    db_session.expire_all()
    remaining = db_session.query(WorkflowTask).filter(
        WorkflowTask.tenant_id == tenant.id,
        WorkflowTask.entity_type == "purchase_order",
        WorkflowTask.entity_id == po["id"],
        WorkflowTask.step_key == "RECORD_BILL",
        WorkflowTask.status == "OPEN",
    ).all()
    assert len(remaining) == 0


def test_low_stock_no_duplicate_reorder_task(client: TestClient, db_session: Session):
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_purchase_dimension(client, token)

    tenant = db_session.query(Tenant).one()

    # Create a reorder rule with min_quantity > 0 (product has no stock)
    from app.models.operations import ReorderRule
    rule = ReorderRule(
        tenant_id=tenant.id,
        product_id=dimension["product_id"],
        warehouse_id=dimension["warehouse_id"],
        min_quantity=Decimal("10"),
        max_quantity=Decimal("100"),
        safety_stock=Decimal("5"),
        is_active=True,
    )
    db_session.add(rule)
    db_session.commit()

    # Run low stock check
    from app.jobs.low_stock_check import run_low_stock_check
    result1 = run_low_stock_check(db_session, tenant.id)
    assert result1["tasks_created"] == 1

    # Run again — should NOT create a duplicate
    result2 = run_low_stock_check(db_session, tenant.id)
    assert result2["tasks_created"] == 0

    # Verify only one REORDER_STOCK task exists
    tasks = db_session.query(WorkflowTask).filter(
        WorkflowTask.tenant_id == tenant.id,
        WorkflowTask.entity_type == "product",
        WorkflowTask.entity_id == dimension["product_id"],
        WorkflowTask.step_key == "REORDER_STOCK",
    ).all()
    open_tasks = [t for t in tasks if t.status == "OPEN"]
    assert len(open_tasks) == 1
