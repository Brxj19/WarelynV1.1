from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.auth import UserRole
from app.models.inventory import InventorySerial, InventorySerialStatus, MovementType, StockLedgerEntry, WarehouseStock
from app.models.returns import BlockedReturnStock, ReturnQCInspection, SalesReturn, SalesReturnStatus
from app.models.workflow import WorkflowEvent
from test_sales import auth_headers, confirm_sales_order, create_fulfillment, create_role_user, create_sales_order, register_and_login, setup_sales_dimension, stock_in


def fulfilled_order(client: TestClient, token: str, dimension: dict[str, int], quantity: str = "2", order_number: str = "SO-RET", fulfillment_number: str = "FUL-RET") -> dict:
    order = create_sales_order(client, token, dimension, quantity, order_number)
    confirm_sales_order(client, token, order, dimension, quantity, f"confirm-{order_number}")
    # Pick the auto-created task; auto-pack-and-fulfill runs after pick
    tasks = client.get(f"/api/sales-orders/{order['id']}/pick-tasks", headers=auth_headers(token))
    assert tasks.status_code == 200
    pick_task = tasks.json()[0]
    pick_response = client.post(
        f"/api/pick-tasks/{pick_task['id']}/pick",
        json={"items": [{"pick_task_item_id": item["id"], "picked_quantity": item["required_quantity"]} for item in pick_task["items"]]},
        headers=auth_headers(token),
    )
    assert pick_response.status_code == 200
    # Reload the order after auto-fulfill
    order_response = client.get(f"/api/sales-orders/{order['id']}", headers=auth_headers(token))
    assert order_response.status_code == 200
    return order_response.json()


def create_return(client: TestClient, token: str, order: dict, dimension: dict[str, int], quantity: str = "1", number: str = "RET-1", serial_id: int | None = None) -> dict:
    response = client.post(
        "/api/sales-returns",
        json={
            "sales_order_id": order["id"],
            "return_number": number,
            "reason": "Customer return",
            "items": [
                {
                    "sales_order_item_id": order["items"][0]["id"],
                    "warehouse_id": dimension["warehouse_id"],
                    "location_id": dimension["location_id"],
                    "returned_quantity": quantity,
                    "serial_id": serial_id,
                }
            ],
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()


def inspect_and_process(client: TestClient, token: str, sales_return: dict, status: str, accepted: str, rejected: str = "0", key: str = "process-return") -> dict:
    inspect = client.post(
        f"/api/sales-returns/{sales_return['id']}/inspect",
        json={"items": [{"sales_return_item_id": sales_return["items"][0]["id"], "qc_status": status, "accepted_quantity": accepted, "rejected_quantity": rejected}]},
        headers=auth_headers(token),
    )
    assert inspect.status_code == 200
    process = client.post(f"/api/sales-returns/{sales_return['id']}/process", json={"idempotency_key": key}, headers=auth_headers(token))
    assert process.status_code == 200
    return process.json()


def test_sellable_return_restocks_through_inventory_engine(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "RET")
    stock_in(client, token, dimension, "5", "ret-stock-in")
    order = fulfilled_order(client, token, dimension, "2")
    sales_return = create_return(client, token, order, dimension, "1")
    submitted = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers=auth_headers(token))

    result = inspect_and_process(client, token, submitted.json(), "ACCEPTED_RESTOCK", "1")

    assert result["sales_return"]["status"] == "PROCESSED"
    stock = db_session.query(WarehouseStock).one()
    assert stock.quantity_on_hand == Decimal("4.000")
    assert stock.quantity_available == Decimal("4.000")
    assert db_session.query(StockLedgerEntry).filter(StockLedgerEntry.movement_type == MovementType.RETURN_RESTOCK).count() == 1
    assert client.get("/api/inventory/reconciliation/dry-run", headers=auth_headers(token)).json()["mismatch_count"] == 0


def test_blocked_return_does_not_increase_sellable_stock_or_ledger(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "BLOCK")
    stock_in(client, token, dimension, "5", "block-stock-in")
    order = fulfilled_order(client, token, dimension, "2", "SO-BLOCK", "FUL-BLOCK")
    sales_return = create_return(client, token, order, dimension, "1", "RET-BLOCK")
    submitted = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers=auth_headers(token))

    inspect_and_process(client, token, submitted.json(), "ACCEPTED_BLOCKED", "1", key="process-block")

    stock = db_session.query(WarehouseStock).one()
    assert stock.quantity_on_hand == Decimal("3.000")
    assert stock.quantity_available == Decimal("3.000")
    assert db_session.query(BlockedReturnStock).one().quantity == Decimal("1.000")
    assert db_session.query(StockLedgerEntry).filter(StockLedgerEntry.movement_type == MovementType.RETURN_RESTOCK).count() == 0
    assert client.get("/api/inventory/reconciliation/dry-run", headers=auth_headers(token)).json()["mismatch_count"] == 0


def test_return_quantity_cannot_exceed_fulfilled_quantity(client: TestClient) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "OVER")
    stock_in(client, token, dimension, "5", "over-stock-in")
    order = fulfilled_order(client, token, dimension, "1", "SO-OVER", "FUL-OVER")

    response = client.post(
        "/api/sales-returns",
        json={"sales_order_id": order["id"], "return_number": "RET-OVER", "items": [{"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "returned_quantity": "2"}]},
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RETURN_QUANTITY_EXCEEDS_FULFILLED"


def test_serial_sellable_return_updates_existing_sold_serial(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "SER-RET", {"name": "Serial Return", "sku": "SER-RET", "track_serial": True})
    stock = client.post("/api/inventory/stock-in", json={"product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "1", "serial_numbers": ["SER-RET-1"], "idempotency_key": "ser-ret-in"}, headers=auth_headers(token))
    assert stock.status_code == 200
    serial = db_session.query(InventorySerial).one()
    order = create_sales_order(client, token, dimension, "1", "SO-SER-RET")
    confirm_sales_order(client, token, order, dimension, "1", "confirm-ser-ret")
    pick_tasks = client.get(f"/api/sales-orders/{order['id']}/pick-tasks", headers=auth_headers(token))
    assert pick_tasks.status_code == 200
    pick = pick_tasks.json()[0]
    picked = client.post(f"/api/pick-tasks/{pick['id']}/pick", json={"items": [{"pick_task_item_id": pick["items"][0]["id"], "picked_quantity": "1", "serial_id": serial.id}]}, headers=auth_headers(token))
    assert picked.status_code == 200
    # Auto-pack-and-fulfill runs after pick; serial should be SOLD
    db_session.refresh(serial)
    assert serial.status == InventorySerialStatus.SOLD
    # Reload order after auto-fulfill
    order_response = client.get(f"/api/sales-orders/{order['id']}", headers=auth_headers(token))
    assert order_response.status_code == 200
    fulfilled_order_data = order_response.json()
    sales_return = create_return(client, token, fulfilled_order_data, dimension, "1", "RET-SER", serial.id)
    submitted = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers=auth_headers(token))

    inspect_and_process(client, token, submitted.json(), "ACCEPTED_RESTOCK", "1", key="process-ser-ret")

    db_session.refresh(serial)
    assert serial.status == InventorySerialStatus.IN_STOCK
    assert db_session.query(InventorySerial).count() == 1
    assert db_session.query(StockLedgerEntry).filter(StockLedgerEntry.movement_type == MovementType.RETURN_RESTOCK, StockLedgerEntry.serial_id == serial.id).count() == 1


def test_return_roles_and_tenant_isolation(client: TestClient, db_session: Session) -> None:
    login_a = register_and_login(client, "return-a@example.com")
    token_a = login_a["access_token"]
    dimension_a = setup_sales_dimension(client, token_a, "RA")
    stock_in(client, token_a, dimension_a, "3", "return-a-in")
    order_a = fulfilled_order(client, token_a, dimension_a, "1", "SO-RA", "FUL-RA")
    sales_return = create_return(client, token_a, order_a, dimension_a, "1", "RET-RA")
    viewer_token = create_role_user(client, db_session, UserRole.VIEWER, "viewer-return@example.com")
    purchase_token = create_role_user(client, db_session, UserRole.PURCHASE_STAFF, "purchase-return@example.com")
    sales_token = create_role_user(client, db_session, UserRole.SALES_STAFF, "sales-return@example.com")
    login_b = register_and_login(client, "return-b@example.com")

    viewer_read = client.get(f"/api/sales-returns/{sales_return['id']}", headers=auth_headers(viewer_token))
    viewer_create = client.post("/api/sales-returns", json={"sales_order_id": order_a["id"], "return_number": "RET-VIEW", "items": []}, headers=auth_headers(viewer_token))
    purchase_read = client.get(f"/api/sales-returns/{sales_return['id']}", headers=auth_headers(purchase_token))
    sales_submit = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers=auth_headers(sales_token))
    sales_inspect = client.post(f"/api/sales-returns/{sales_return['id']}/inspect", json={"items": []}, headers=auth_headers(sales_token))
    cross_tenant = client.get(f"/api/sales-returns/{sales_return['id']}", headers=auth_headers(login_b["access_token"]))

    assert viewer_read.status_code == 200
    assert viewer_create.status_code == 403
    assert purchase_read.status_code == 403
    assert sales_submit.status_code == 200
    assert sales_inspect.status_code == 403
    assert cross_tenant.status_code == 404
    assert db_session.query(SalesReturn).one().status == SalesReturnStatus.SUBMITTED


def test_sales_staff_cannot_inspect_return(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client, "return-rbac@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "RR")
    stock_in(client, token, dimension, "3", "return-rbac-in")
    order = fulfilled_order(client, token, dimension, "1", "SO-RR", "FUL-RR")
    sales_return = create_return(client, token, order, dimension, "1", "RET-RR")
    submitted = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers=auth_headers(token))
    assert submitted.status_code == 200

    sales_token = create_role_user(client, db_session, UserRole.SALES_STAFF, "return-rbac-sales@example.com")
    inspect = client.post(
        f"/api/sales-returns/{sales_return['id']}/inspect",
        json={"items": [{"sales_return_item_id": submitted.json()["items"][0]["id"], "qc_status": "ACCEPTED_RESTOCK", "accepted_quantity": "1", "rejected_quantity": "0"}]},
        headers=auth_headers(sales_token),
    )

    assert inspect.status_code == 403


def test_inspect_return_twice_creates_only_one_inspection_record(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client, "return-inspection@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "RI")
    stock_in(client, token, dimension, "3", "return-inspection-in")
    order = fulfilled_order(client, token, dimension, "1", "SO-RI", "FUL-RI")
    sales_return = create_return(client, token, order, dimension, "1", "RET-RI")
    submitted = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers=auth_headers(token))
    assert submitted.status_code == 200
    payload = {"items": [{"sales_return_item_id": submitted.json()["items"][0]["id"], "qc_status": "ACCEPTED_RESTOCK", "accepted_quantity": "1", "rejected_quantity": "0"}]}

    first = client.post(f"/api/sales-returns/{sales_return['id']}/inspect", json=payload, headers=auth_headers(token))
    second = client.post(f"/api/sales-returns/{sales_return['id']}/inspect", json=payload, headers=auth_headers(token))

    assert first.status_code == 200
    assert second.status_code == 200
    assert db_session.query(ReturnQCInspection).filter(ReturnQCInspection.sales_return_id == sales_return["id"]).count() == 1


def test_submit_return_workflow_event_has_actor_user_id(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client, "return-workflow@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "RW")
    stock_in(client, token, dimension, "3", "return-workflow-in")
    order = fulfilled_order(client, token, dimension, "1", "SO-RW", "FUL-RW")
    sales_return = create_return(client, token, order, dimension, "1", "RET-RW")

    submitted = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers=auth_headers(token))
    assert submitted.status_code == 200

    event = db_session.query(WorkflowEvent).filter(
        WorkflowEvent.entity_type == "sales_return",
        WorkflowEvent.entity_id == sales_return["id"],
        WorkflowEvent.event_type == "RETURN_SUBMITTED",
    ).one()
    assert event.actor_user_id is not None


def test_process_return_succeeds_after_inspection_pending_state(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client, "return-process@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "RP")
    stock_in(client, token, dimension, "5", "return-process-in")
    order = fulfilled_order(client, token, dimension, "2", "SO-RP", "FUL-RP")
    sales_return = create_return(client, token, order, dimension, "1", "RET-RP")
    submitted = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers=auth_headers(token))
    assert submitted.status_code == 200

    inspect = client.post(
        f"/api/sales-returns/{sales_return['id']}/inspect",
        json={"items": [{"sales_return_item_id": submitted.json()["items"][0]["id"], "qc_status": "ACCEPTED_RESTOCK", "accepted_quantity": "1", "rejected_quantity": "0"}]},
        headers=auth_headers(token),
    )
    assert inspect.status_code == 200
    assert inspect.json()["status"] == "INSPECTION_PENDING"

    process = client.post(
        f"/api/sales-returns/{sales_return['id']}/process",
        json={"idempotency_key": "return-process-happy"},
        headers=auth_headers(token),
    )

    assert process.status_code == 200
    assert process.json()["sales_return"]["status"] == "PROCESSED"
    stock = db_session.query(WarehouseStock).one()
    assert stock.quantity_on_hand == Decimal("4.000")
