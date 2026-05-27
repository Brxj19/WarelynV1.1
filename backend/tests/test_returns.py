from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.auth import UserRole
from app.models.inventory import InventorySerial, InventorySerialStatus, MovementType, StockLedgerEntry, WarehouseStock
from app.models.returns import BlockedReturnStock, SalesReturn, SalesReturnStatus
from test_sales import auth_headers, confirm_sales_order, create_fulfillment, create_role_user, create_sales_order, register_and_login, setup_sales_dimension, stock_in


def fulfilled_order(client: TestClient, token: str, dimension: dict[str, int], quantity: str = "2", order_number: str = "SO-RET", fulfillment_number: str = "FUL-RET") -> dict:
    order = create_sales_order(client, token, dimension, quantity, order_number)
    confirmed = confirm_sales_order(client, token, order, dimension, quantity, f"confirm-{order_number}")
    fulfillment = create_fulfillment(client, token, order, dimension, confirmed["stock_results"][0]["reservation"]["id"], quantity, fulfillment_number)
    commit = client.post(f"/api/sales-fulfillments/{fulfillment['id']}/commit", json={"idempotency_key": f"fulfill-{order_number}"}, headers=auth_headers(token))
    assert commit.status_code == 200
    return commit.json()["sales_order"]


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
    confirmed = confirm_sales_order(client, token, order, dimension, "1", "confirm-ser-ret")
    pick = client.post(f"/api/sales-orders/{order['id']}/pick-tasks", json={"pick_number": "PICK-SER-RET"}, headers=auth_headers(token))
    assert pick.status_code == 201
    picked = client.post(f"/api/pick-tasks/{pick.json()['id']}/pick", json={"items": [{"pick_task_item_id": pick.json()["items"][0]["id"], "picked_quantity": "1", "serial_id": serial.id}]}, headers=auth_headers(token))
    assert picked.status_code == 200
    fulfillment = create_fulfillment(client, token, order, dimension, confirmed["stock_results"][0]["reservation"]["id"], "1", "FUL-SER-RET")
    commit = client.post(f"/api/sales-fulfillments/{fulfillment['id']}/commit", json={"idempotency_key": "fulfill-ser-ret"}, headers=auth_headers(token))
    assert commit.status_code == 200
    db_session.refresh(serial)
    assert serial.status == InventorySerialStatus.SOLD
    sales_return = create_return(client, token, commit.json()["sales_order"], dimension, "1", "RET-SER", serial.id)
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
