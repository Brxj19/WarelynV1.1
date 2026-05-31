from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.auth import UserRole
from app.models.fulfillment import Package, PackageStatus, PickTask, PickTaskStatus
from app.models.inventory import InventorySerial, InventorySerialStatus, MovementType, StockLedgerEntry, WarehouseStock
from test_sales import auth_headers, confirm_sales_order, create_fulfillment, create_role_user, create_sales_order, register_and_login, setup_sales_dimension, stock_in


def create_pick_task(client: TestClient, token: str, order_id: int, number: str = "PICK-1") -> dict:
    response = client.post(f"/api/sales-orders/{order_id}/pick-tasks", json={"pick_number": number}, headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def get_auto_pick_task(client: TestClient, token: str, order_id: int) -> dict:
    response = client.get(f"/api/sales-orders/{order_id}/pick-tasks", headers=auth_headers(token))
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) >= 1
    return tasks[0]


def pick_all(client: TestClient, token: str, pick_task: dict) -> dict:
    response = client.post(
        f"/api/pick-tasks/{pick_task['id']}/pick",
        json={"items": [{"pick_task_item_id": item["id"], "picked_quantity": item["required_quantity"]} for item in pick_task["items"]]},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    return response.json()


def test_create_and_pick_task_from_confirmed_sales_order(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "10")
    order = create_sales_order(client, login["access_token"], dimension, "4")
    confirm_sales_order(client, login["access_token"], order, dimension, "4")

    # Pick task is auto-created on confirmation
    tasks_response = client.get(f"/api/sales-orders/{order['id']}/pick-tasks", headers=auth_headers(login["access_token"]))
    assert tasks_response.status_code == 200
    pick_tasks = tasks_response.json()
    assert len(pick_tasks) == 1
    pick_task = pick_tasks[0]
    picked = pick_all(client, login["access_token"], pick_task)

    assert pick_task["status"] == "PENDING"
    assert len(pick_task["items"]) == 1
    assert picked["status"] == "PICKED"
    assert picked["items"][0]["picked_quantity"] == "4.000"
    # After picking, auto-pack-and-fulfill runs: stock is deducted
    stock = db_session.query(WarehouseStock).one()
    assert stock.quantity_on_hand == Decimal("6.000")
    assert stock.quantity_reserved == Decimal("0.000")
    assert stock.quantity_available == Decimal("6.000")


def test_pick_task_creation_requires_pickable_order_and_active_reservations(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    draft = create_sales_order(client, login["access_token"], dimension, "1")

    draft_pick = client.post(f"/api/sales-orders/{draft['id']}/pick-tasks", json={"pick_number": "PICK-DRAFT"}, headers=auth_headers(login["access_token"]))
    cancel = client.post(f"/api/sales-orders/{draft['id']}/cancel", json={}, headers=auth_headers(login["access_token"]))
    cancelled_pick = client.post(f"/api/sales-orders/{draft['id']}/pick-tasks", json={"pick_number": "PICK-CANCEL"}, headers=auth_headers(login["access_token"]))

    assert draft_pick.status_code == 409
    assert cancel.status_code == 200
    assert cancelled_pick.status_code == 409


def test_picked_quantity_cannot_exceed_reserved_quantity(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "5")
    order = create_sales_order(client, login["access_token"], dimension, "2")
    confirm_sales_order(client, login["access_token"], order, dimension, "2")
    pick_task = get_auto_pick_task(client, login["access_token"], order["id"])

    response = client.post(f"/api/pick-tasks/{pick_task['id']}/pick", json={"items": [{"pick_task_item_id": pick_task["items"][0]["id"], "picked_quantity": "3"}]}, headers=auth_headers(login["access_token"]))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PICK_QUANTITY_INVALID"


def test_cancel_pick_task_does_not_mutate_stock_or_ledger(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "5")
    order = create_sales_order(client, login["access_token"], dimension, "2")
    confirm_sales_order(client, login["access_token"], order, dimension, "2")
    pick_task = get_auto_pick_task(client, login["access_token"], order["id"])
    ledger_count = db_session.query(StockLedgerEntry).count()

    cancel = client.post(f"/api/pick-tasks/{pick_task['id']}/cancel", json={}, headers=auth_headers(login["access_token"]))
    pick_again = client.post(f"/api/pick-tasks/{pick_task['id']}/pick", json={"items": [{"pick_task_item_id": pick_task["items"][0]["id"], "picked_quantity": "1"}]}, headers=auth_headers(login["access_token"]))

    assert cancel.status_code == 200
    assert cancel.json()["status"] == "CANCELLED"
    assert pick_again.status_code == 409
    assert db_session.query(WarehouseStock).one().quantity_reserved == Decimal("2.000")
    assert db_session.query(StockLedgerEntry).count() == ledger_count


def test_serial_picking_requires_valid_unique_serial_and_fulfillment_sells_serial(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"], "SER-PICK", {"name": "Serial Product", "sku": "SER-PICK", "track_serial": True})
    response = client.post("/api/inventory/stock-in", json={"product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "1", "serial_numbers": ["SER-PICK-1"], "idempotency_key": "serial-pick-in"}, headers=auth_headers(login["access_token"]))
    assert response.status_code == 200
    serial = db_session.query(InventorySerial).one()
    order = create_sales_order(client, login["access_token"], dimension, "1", "SO-SER-PICK")
    confirm_sales_order(client, login["access_token"], order, dimension, "1", "confirm-ser-pick")
    pick_task = get_auto_pick_task(client, login["access_token"], order["id"])

    missing_serial = client.post(f"/api/pick-tasks/{pick_task['id']}/pick", json={"items": [{"pick_task_item_id": pick_task["items"][0]["id"], "picked_quantity": "1"}]}, headers=auth_headers(login["access_token"]))
    picked = client.post(f"/api/pick-tasks/{pick_task['id']}/pick", json={"items": [{"pick_task_item_id": pick_task["items"][0]["id"], "picked_quantity": "1", "serial_id": serial.id}]}, headers=auth_headers(login["access_token"]))

    assert missing_serial.status_code == 400
    assert missing_serial.json()["error"]["code"] == "SERIAL_SELECTION_REQUIRED"
    assert picked.status_code == 200
    # Auto-pack-and-fulfill runs after pick, serial should be SOLD
    db_session.refresh(serial)
    assert serial.status == InventorySerialStatus.SOLD
    assert db_session.query(StockLedgerEntry).filter(StockLedgerEntry.movement_type == MovementType.SALES_DEDUCT, StockLedgerEntry.serial_id == serial.id).count() == 1


def test_serial_allocation_validation_and_duplicates(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"], "SER-DUP", {"name": "Serial Product", "sku": "SER-DUP", "track_serial": True})
    other_dimension = setup_sales_dimension(client, login["access_token"], "SER-OTHER", {"name": "Other Serial Product", "sku": "SER-OTHER", "track_serial": True})
    stock_one = client.post("/api/inventory/stock-in", json={"product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "2", "serial_numbers": ["SER-DUP-1", "SER-DUP-2"], "idempotency_key": "serial-dup-in"}, headers=auth_headers(login["access_token"]))
    stock_other = client.post("/api/inventory/stock-in", json={"product_id": other_dimension["product_id"], "warehouse_id": other_dimension["warehouse_id"], "location_id": other_dimension["location_id"], "quantity": "1", "serial_numbers": ["SER-OTHER-1"], "idempotency_key": "serial-other-in"}, headers=auth_headers(login["access_token"]))
    assert stock_one.status_code == 200
    assert stock_other.status_code == 200
    serials = {serial.serial_number: serial for serial in db_session.query(InventorySerial).all()}
    order = create_sales_order(client, login["access_token"], dimension, "2", "SO-SER-DUP")
    confirm = client.post(f"/api/sales-orders/{order['id']}/confirm", json={"idempotency_key": "confirm-ser-dup", "allocations": [{"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "1"}, {"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "1"}]}, headers=auth_headers(login["access_token"]))
    assert confirm.status_code == 200
    pick_task = get_auto_pick_task(client, login["access_token"], order["id"])

    product_mismatch = client.post(f"/api/pick-tasks/{pick_task['id']}/pick", json={"items": [{"pick_task_item_id": pick_task["items"][0]["id"], "picked_quantity": "1", "serial_id": serials["SER-OTHER-1"].id}]}, headers=auth_headers(login["access_token"]))
    duplicate_request = client.post(f"/api/pick-tasks/{pick_task['id']}/pick", json={"items": [{"pick_task_item_id": pick_task["items"][0]["id"], "picked_quantity": "1", "serial_id": serials["SER-DUP-1"].id}, {"pick_task_item_id": pick_task["items"][1]["id"], "picked_quantity": "1", "serial_id": serials["SER-DUP-1"].id}]}, headers=auth_headers(login["access_token"]))

    assert product_mismatch.status_code == 400
    assert product_mismatch.json()["error"]["code"] == "SERIAL_PRODUCT_MISMATCH"
    assert duplicate_request.status_code == 409
    assert duplicate_request.json()["error"]["code"] == "DUPLICATE_SERIAL_ALLOCATION"


def test_auto_pack_and_fulfill_creates_package_and_deducts_stock(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "10")
    order = create_sales_order(client, login["access_token"], dimension, "3")
    confirm_sales_order(client, login["access_token"], order, dimension, "3")
    pick_task = pick_all(client, login["access_token"], get_auto_pick_task(client, login["access_token"], order["id"]))

    # Auto-pack-and-fulfill runs after pick completes
    assert pick_task["status"] == "PICKED"
    package = db_session.query(Package).first()
    assert package is not None
    assert package.status == PackageStatus.PACKED
    stock = db_session.query(WarehouseStock).one()
    assert stock.quantity_on_hand == Decimal("7.000")
    assert stock.quantity_reserved == Decimal("0.000")
    assert stock.quantity_available == Decimal("7.000")


def test_pick_allows_resubmitting_stale_picked_lines_after_partial_fulfillment(client: TestClient) -> None:
    login = register_and_login(client, "pick-partial@example.com")
    dimension = setup_sales_dimension(client, login["access_token"], "PICK-PARTIAL")
    stock_in(client, login["access_token"], dimension, "10", "stock-in-pick-partial")
    order = create_sales_order(client, login["access_token"], dimension, "5", "SO-PICK-PARTIAL")
    confirm = client.post(
        f"/api/sales-orders/{order['id']}/confirm",
        json={
            "idempotency_key": "confirm-pick-partial",
            "allocations": [
                {
                    "sales_order_item_id": order["items"][0]["id"],
                    "warehouse_id": dimension["warehouse_id"],
                    "location_id": dimension["location_id"],
                    "quantity": "2",
                },
                {
                    "sales_order_item_id": order["items"][0]["id"],
                    "warehouse_id": dimension["warehouse_id"],
                    "location_id": dimension["location_id"],
                    "quantity": "3",
                },
            ],
        },
        headers=auth_headers(login["access_token"]),
    )
    assert confirm.status_code == 200
    first_reservation = confirm.json()["stock_results"][0]["reservation"]["id"]
    second_reservation = confirm.json()["stock_results"][1]["reservation"]["id"]

    pick_task = get_auto_pick_task(client, login["access_token"], order["id"])
    item_by_reservation = {item["reservation_id"]: item for item in pick_task["items"]}
    first_item = item_by_reservation[first_reservation]
    second_item = item_by_reservation[second_reservation]

    partial_pick = client.post(
        f"/api/pick-tasks/{pick_task['id']}/pick",
        json={
            "items": [
                {"pick_task_item_id": first_item["id"], "picked_quantity": first_item["required_quantity"]},
                {"pick_task_item_id": second_item["id"], "picked_quantity": "0"},
            ]
        },
        headers=auth_headers(login["access_token"]),
    )
    assert partial_pick.status_code == 200
    assert partial_pick.json()["status"] == "IN_PROGRESS"

    partial_fulfillment = create_fulfillment(
        client,
        login["access_token"],
        order,
        dimension,
        first_reservation,
        "2",
        "FUL-PICK-PARTIAL-1",
    )
    commit_partial = client.post(
        f"/api/sales-fulfillments/{partial_fulfillment['id']}/commit",
        json={"idempotency_key": "fulfill-pick-partial-1"},
        headers=auth_headers(login["access_token"]),
    )
    assert commit_partial.status_code == 200
    assert commit_partial.json()["sales_order"]["status"] == "PARTIALLY_FULFILLED"

    # Frontend submits all lines again. Previously picked lines may now point to
    # DEDUCTED reservations and should be treated as safe no-op lines.
    resume_pick = client.post(
        f"/api/pick-tasks/{pick_task['id']}/pick",
        json={
            "items": [
                {"pick_task_item_id": first_item["id"], "picked_quantity": first_item["required_quantity"]},
                {"pick_task_item_id": second_item["id"], "picked_quantity": second_item["required_quantity"]},
            ]
        },
        headers=auth_headers(login["access_token"]),
    )
    assert resume_pick.status_code == 200
    assert resume_pick.json()["status"] == "PICKED"


def test_cannot_pack_unpicked_items_and_auto_fulfill_deducts_stock_correctly(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "5")
    order = create_sales_order(client, login["access_token"], dimension, "2")
    confirm_sales_order(client, login["access_token"], order, dimension, "2")
    pick_task = get_auto_pick_task(client, login["access_token"], order["id"])

    # Cannot create package from unpicked items
    unpicked = client.post(f"/api/sales-orders/{order['id']}/packages", json={"package_number": "PKG-UNPICKED", "pick_task_item_ids": [pick_task["items"][0]["id"]]}, headers=auth_headers(login["access_token"]))
    assert unpicked.status_code == 409

    # After picking, auto-pack-and-fulfill runs
    picked = pick_all(client, login["access_token"], pick_task)
    assert picked["status"] == "PICKED"
    stock = db_session.query(WarehouseStock).one()
    assert stock.quantity_on_hand == Decimal("3.000")
    assert stock.quantity_reserved == Decimal("0.000")


def test_tenant_isolation_and_roles_for_picking_and_packing(client: TestClient, db_session: Session) -> None:
    login_a = register_and_login(client, "fulfill-a@example.com")
    dimension_a = setup_sales_dimension(client, login_a["access_token"], "FA")
    stock_in(client, login_a["access_token"], dimension_a, "5")
    order_a = create_sales_order(client, login_a["access_token"], dimension_a, "1", "SO-FA")
    confirm_sales_order(client, login_a["access_token"], order_a, dimension_a, "1", "confirm-fa")
    pick_a = get_auto_pick_task(client, login_a["access_token"], order_a["id"])
    viewer_token = create_role_user(client, db_session, UserRole.VIEWER, "viewer-fulfill@example.com")
    purchase_token = create_role_user(client, db_session, UserRole.PURCHASE_STAFF, "purchase-fulfill@example.com")
    sales_token = create_role_user(client, db_session, UserRole.SALES_STAFF, "sales-fulfill@example.com")
    login_b = register_and_login(client, "fulfill-b@example.com")

    cross_tenant = client.get(f"/api/pick-tasks/{pick_a['id']}", headers=auth_headers(login_b["access_token"]))
    viewer_mutate = client.post(f"/api/pick-tasks/{pick_a['id']}/start", json={}, headers=auth_headers(viewer_token))
    purchase_mutate = client.post(f"/api/pick-tasks/{pick_a['id']}/start", json={}, headers=auth_headers(purchase_token))
    sales_mutate = client.post(f"/api/pick-tasks/{pick_a['id']}/start", json={}, headers=auth_headers(sales_token))

    assert cross_tenant.status_code == 404
    assert viewer_mutate.status_code == 403
    assert purchase_mutate.status_code == 403
    assert sales_mutate.status_code == 200
    assert db_session.query(PickTask).one().status == PickTaskStatus.IN_PROGRESS
