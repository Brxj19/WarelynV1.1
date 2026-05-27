from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.inventory import MovementType, StockLedgerEntry, WarehouseStock
from app.models.sales import SalesFulfillment, SalesFulfillmentStatus, SalesOrder, SalesOrderStatus


def register_and_login(client: TestClient, email: str = "admin@example.com") -> dict[str, object]:
    response = client.post("/api/auth/register", json={"company_name": "Acme", "name": "Admin", "email": email, "password": "StrongPass123!"})
    assert response.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_role_user(client: TestClient, db_session: Session, role: UserRole, email: str) -> str:
    tenant = db_session.query(Tenant).one()
    user = User(tenant_id=tenant.id, name=role.value, email=email, password_hash=get_password_hash("StrongPass123!"), role=role, status=UserStatus.ACTIVE)
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"]


def setup_sales_dimension(client: TestClient, token: str, suffix: str = "1", product_payload: dict[str, object] | None = None) -> dict[str, int]:
    headers = auth_headers(token)
    customer = client.post("/api/catalog/customers", json={"name": f"Customer {suffix}", "email": f"customer-{suffix}@example.com"}, headers=headers)
    payload = product_payload or {"name": f"Widget {suffix}", "sku": f"S-{suffix}"}
    product = client.post("/api/catalog/products", json=payload, headers=headers)
    warehouse = client.post("/api/warehouses", json={"name": f"Main {suffix}", "code": f"SM{suffix}"}, headers=headers)
    assert customer.status_code == 201
    assert product.status_code == 201
    assert warehouse.status_code == 201
    location = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Storage", "code": f"SS{suffix}", "location_type": "STORAGE"}, headers=headers)
    assert location.status_code == 201
    return {"customer_id": customer.json()["id"], "product_id": product.json()["id"], "warehouse_id": warehouse.json()["id"], "location_id": location.json()["id"]}


def stock_in(client: TestClient, token: str, dimension: dict[str, int], quantity: str = "10", key: str = "stock-in") -> None:
    response = client.post("/api/inventory/stock-in", json={"product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": quantity, "idempotency_key": key}, headers=auth_headers(token))
    assert response.status_code == 200


def sales_order_payload(dimension: dict[str, int], quantity: str = "4", order_number: str = "SO-1") -> dict[str, object]:
    return {"customer_id": dimension["customer_id"], "order_number": order_number, "order_date": "2026-05-22", "items": [{"product_id": dimension["product_id"], "ordered_quantity": quantity, "unit_price": "9.99"}]}


def create_sales_order(client: TestClient, token: str, dimension: dict[str, int], quantity: str = "4", order_number: str = "SO-1") -> dict[str, object]:
    response = client.post("/api/sales-orders", json=sales_order_payload(dimension, quantity, order_number), headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def confirm_sales_order(client: TestClient, token: str, order: dict[str, object], dimension: dict[str, int], quantity: str = "4", key: str = "confirm-1") -> dict[str, object]:
    response = client.post(
        f"/api/sales-orders/{order['id']}/confirm",
        json={"idempotency_key": key, "allocations": [{"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": quantity}]},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    return response.json()


def create_fulfillment(client: TestClient, token: str, order: dict[str, object], dimension: dict[str, int], reservation_id: int, quantity: str = "4", number: str = "FUL-1") -> dict[str, object]:
    response = client.post(
        f"/api/sales-orders/{order['id']}/fulfillments",
        json={"fulfillment_number": number, "items": [{"sales_order_item_id": order["items"][0]["id"], "product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "reservation_id": reservation_id, "fulfilled_quantity": quantity}]},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    return response.json()


def test_create_and_confirm_sales_order_reserves_stock(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "10")
    order = create_sales_order(client, login["access_token"], dimension, "4")

    confirmed = confirm_sales_order(client, login["access_token"], order, dimension, "4")

    assert confirmed["sales_order"]["status"] == "CONFIRMED"
    assert Decimal(confirmed["sales_order"]["items"][0]["reserved_quantity"]) == Decimal("4")
    stock = db_session.query(WarehouseStock).one()
    assert stock.quantity_on_hand == Decimal("10.000")
    assert stock.quantity_reserved == Decimal("4.000")
    assert stock.quantity_available == Decimal("6.000")
    assert db_session.query(StockLedgerEntry).filter(StockLedgerEntry.movement_type == MovementType.SALES_RESERVE).count() == 1


def test_insufficient_stock_blocks_confirmation(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "2")
    order = create_sales_order(client, login["access_token"], dimension, "4")

    response = client.post(f"/api/sales-orders/{order['id']}/confirm", json={"idempotency_key": "confirm-low", "allocations": [{"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "4"}]}, headers=auth_headers(login["access_token"]))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_cancel_draft_and_confirmed_sales_orders(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "10")
    draft = create_sales_order(client, login["access_token"], dimension, "1", "SO-DRAFT")
    confirmed_order = create_sales_order(client, login["access_token"], dimension, "3", "SO-CONF")
    confirm_sales_order(client, login["access_token"], confirmed_order, dimension, "3", "confirm-cancel")

    cancel_draft = client.post(f"/api/sales-orders/{draft['id']}/cancel", json={}, headers=auth_headers(login["access_token"]))
    cancel_confirmed = client.post(f"/api/sales-orders/{confirmed_order['id']}/cancel", json={}, headers=auth_headers(login["access_token"]))

    assert cancel_draft.status_code == 200
    assert cancel_draft.json()["status"] == "CANCELLED"
    assert cancel_confirmed.status_code == 200
    assert cancel_confirmed.json()["status"] == "CANCELLED"
    stock = db_session.query(WarehouseStock).one()
    assert stock.quantity_reserved == Decimal("0.000")
    assert stock.quantity_available == Decimal("10.000")
    assert db_session.query(StockLedgerEntry).filter(StockLedgerEntry.movement_type == MovementType.SALES_RELEASE).count() == 1


def test_fulfillment_commit_deducts_reserved_stock_and_reconciles(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "10")
    order = create_sales_order(client, login["access_token"], dimension, "4")
    confirmed = confirm_sales_order(client, login["access_token"], order, dimension, "4")
    reservation_id = confirmed["stock_results"][0]["reservation"]["id"]
    fulfillment = create_fulfillment(client, login["access_token"], order, dimension, reservation_id, "4")

    commit = client.post(f"/api/sales-fulfillments/{fulfillment['id']}/commit", json={"idempotency_key": "fulfill-1"}, headers=auth_headers(login["access_token"]))
    replay = client.post(f"/api/sales-fulfillments/{fulfillment['id']}/commit", json={"idempotency_key": "fulfill-1"}, headers=auth_headers(login["access_token"]))

    assert commit.status_code == 200
    assert replay.status_code == 200
    assert commit.json()["sales_order"]["status"] == "FULFILLED"
    stock = db_session.query(WarehouseStock).one()
    assert stock.quantity_on_hand == Decimal("6.000")
    assert stock.quantity_reserved == Decimal("0.000")
    assert stock.quantity_available == Decimal("6.000")
    assert db_session.query(StockLedgerEntry).filter(StockLedgerEntry.movement_type == MovementType.SALES_DEDUCT).count() == 1
    assert client.get("/api/inventory/reconciliation/dry-run", headers=auth_headers(login["access_token"])).json()["mismatch_count"] == 0


def test_partial_and_full_fulfillment_statuses(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "10")
    order = create_sales_order(client, login["access_token"], dimension, "5")
    confirm = client.post(
        f"/api/sales-orders/{order['id']}/confirm",
        json={"idempotency_key": "confirm-split", "allocations": [{"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "2"}, {"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "3"}]},
        headers=auth_headers(login["access_token"]),
    )
    assert confirm.status_code == 200
    first_reservation = confirm.json()["stock_results"][0]["reservation"]["id"]
    second_reservation = confirm.json()["stock_results"][1]["reservation"]["id"]
    partial_fulfillment = create_fulfillment(client, login["access_token"], order, dimension, first_reservation, "2", "FUL-PART")
    partial = client.post(f"/api/sales-fulfillments/{partial_fulfillment['id']}/commit", json={"idempotency_key": "fulfill-part"}, headers=auth_headers(login["access_token"]))
    full_fulfillment = create_fulfillment(client, login["access_token"], order, dimension, second_reservation, "3", "FUL-FULL")
    full = client.post(f"/api/sales-fulfillments/{full_fulfillment['id']}/commit", json={"idempotency_key": "fulfill-full"}, headers=auth_headers(login["access_token"]))

    assert partial.json()["sales_order"]["status"] == "PARTIALLY_FULFILLED"
    assert full.json()["sales_order"]["status"] == "FULFILLED"


def test_over_fulfillment_and_committed_edit_are_blocked(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "10")
    order = create_sales_order(client, login["access_token"], dimension, "2")
    confirmed = confirm_sales_order(client, login["access_token"], order, dimension, "2")
    reservation_id = confirmed["stock_results"][0]["reservation"]["id"]

    over = client.post(f"/api/sales-orders/{order['id']}/fulfillments", json={"fulfillment_number": "FUL-OVER", "items": [{"sales_order_item_id": order["items"][0]["id"], "product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "reservation_id": reservation_id, "fulfilled_quantity": "3"}]}, headers=auth_headers(login["access_token"]))
    fulfillment = create_fulfillment(client, login["access_token"], order, dimension, reservation_id, "2")
    commit = client.post(f"/api/sales-fulfillments/{fulfillment['id']}/commit", json={"idempotency_key": "fulfill-edit"}, headers=auth_headers(login["access_token"]))
    edit = client.patch(f"/api/sales-fulfillments/{fulfillment['id']}", json={"notes": "edit"}, headers=auth_headers(login["access_token"]))

    assert over.status_code == 400
    assert over.json()["error"]["code"] == "SALES_FULFILLMENT_RESERVATION_QUANTITY"
    assert commit.status_code == 200
    assert edit.status_code == 409


def test_cancelled_fulfillment_does_not_mutate_stock(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "5")
    order = create_sales_order(client, login["access_token"], dimension, "2")
    confirmed = confirm_sales_order(client, login["access_token"], order, dimension, "2")
    fulfillment = create_fulfillment(client, login["access_token"], order, dimension, confirmed["stock_results"][0]["reservation"]["id"], "2")

    cancel = client.post(f"/api/sales-fulfillments/{fulfillment['id']}/cancel", json={}, headers=auth_headers(login["access_token"]))
    commit = client.post(f"/api/sales-fulfillments/{fulfillment['id']}/commit", json={"idempotency_key": "cancelled-fulfill"}, headers=auth_headers(login["access_token"]))

    assert cancel.json()["status"] == "CANCELLED"
    assert commit.status_code == 409
    assert db_session.query(WarehouseStock).one().quantity_on_hand == Decimal("5.000")
    assert db_session.query(WarehouseStock).one().quantity_reserved == Decimal("2.000")
    assert db_session.query(StockLedgerEntry).filter(StockLedgerEntry.movement_type == MovementType.SALES_DEDUCT).count() == 0


def test_tenant_isolation_for_sales_orders_fulfillments_and_locations(client: TestClient) -> None:
    login_a = register_and_login(client, "a@example.com")
    dimension_a = setup_sales_dimension(client, login_a["access_token"], "A")
    stock_in(client, login_a["access_token"], dimension_a, "5")
    order_a = create_sales_order(client, login_a["access_token"], dimension_a, "1", "SO-A")
    confirmed_a = confirm_sales_order(client, login_a["access_token"], order_a, dimension_a, "1", "confirm-a")
    fulfillment_a = create_fulfillment(client, login_a["access_token"], order_a, dimension_a, confirmed_a["stock_results"][0]["reservation"]["id"], "1", "FUL-A")
    login_b = register_and_login(client, "b@example.com")
    dimension_b = setup_sales_dimension(client, login_b["access_token"], "B")
    stock_in(client, login_b["access_token"], dimension_b, "5", "stock-b")
    order_b = create_sales_order(client, login_b["access_token"], dimension_b, "1", "SO-B")
    confirmed_b = confirm_sales_order(client, login_b["access_token"], order_b, dimension_b, "1", "confirm-b")
    bad_fulfillment = {"fulfillment_number": "FUL-BAD", "items": [{"sales_order_item_id": order_b["items"][0]["id"], "product_id": dimension_b["product_id"], "warehouse_id": dimension_a["warehouse_id"], "location_id": dimension_a["location_id"], "reservation_id": confirmed_b["stock_results"][0]["reservation"]["id"], "fulfilled_quantity": "1"}]}

    assert client.get(f"/api/sales-orders/{order_a['id']}", headers=auth_headers(login_b["access_token"])).status_code == 404
    assert client.get(f"/api/sales-fulfillments/{fulfillment_a['id']}", headers=auth_headers(login_b["access_token"])).status_code == 404
    assert client.post(f"/api/sales-orders/{order_b['id']}/fulfillments", json=bad_fulfillment, headers=auth_headers(login_b["access_token"])).status_code in {400, 404}


def test_sales_roles(client: TestClient, db_session: Session) -> None:
    admin = register_and_login(client)
    dimension = setup_sales_dimension(client, admin["access_token"])
    stock_in(client, admin["access_token"], dimension, "5")
    viewer_token = create_role_user(client, db_session, UserRole.VIEWER, "viewer-sales@example.com")
    purchase_token = create_role_user(client, db_session, UserRole.PURCHASE_STAFF, "purchase-sales@example.com")
    sales_token = create_role_user(client, db_session, UserRole.SALES_STAFF, "sales-user@example.com")

    viewer_create = client.post("/api/sales-orders", json=sales_order_payload(dimension, order_number="SO-VIEW"), headers=auth_headers(viewer_token))
    purchase_create = client.post("/api/sales-orders", json=sales_order_payload(dimension, order_number="SO-PUR"), headers=auth_headers(purchase_token))
    sales_order = create_sales_order(client, sales_token, dimension, "1", "SO-SALES")
    confirmed = confirm_sales_order(client, sales_token, sales_order, dimension, "1", "confirm-sales-user")
    fulfillment = create_fulfillment(client, sales_token, sales_order, dimension, confirmed["stock_results"][0]["reservation"]["id"], "1", "FUL-SALES")
    commit = client.post(f"/api/sales-fulfillments/{fulfillment['id']}/commit", json={"idempotency_key": "fulfill-sales-user"}, headers=auth_headers(sales_token))

    assert viewer_create.status_code == 403
    assert purchase_create.status_code == 403
    assert commit.status_code == 200


def test_serial_tracked_product_confirmation_requires_unit_allocations(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"], "SER", {"name": "Serial Product", "sku": "SER-SALES", "track_serial": True})
    response = client.post("/api/inventory/stock-in", json={"product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "1", "serial_numbers": ["SER-SALES-1"], "idempotency_key": "serial-sales-in"}, headers=auth_headers(login["access_token"]))
    assert response.status_code == 200
    order = create_sales_order(client, login["access_token"], dimension, "1", "SO-SERIAL")

    confirm = client.post(f"/api/sales-orders/{order['id']}/confirm", json={"idempotency_key": "confirm-serial", "allocations": [{"sales_order_item_id": order["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "1"}]}, headers=auth_headers(login["access_token"]))

    assert confirm.status_code == 200

    order_two = create_sales_order(client, login["access_token"], dimension, "2", "SO-SERIAL-2")
    invalid = client.post(f"/api/sales-orders/{order_two['id']}/confirm", json={"idempotency_key": "confirm-serial-two", "allocations": [{"sales_order_item_id": order_two["items"][0]["id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": "2"}]}, headers=auth_headers(login["access_token"]))
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "SERIAL_ALLOCATION_MUST_BE_UNIT"


def test_sales_models_statuses_persist(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_sales_dimension(client, login["access_token"])
    order = create_sales_order(client, login["access_token"], dimension, "1")

    assert db_session.query(SalesOrder).one().status == SalesOrderStatus.DRAFT
    assert order["status"] == "DRAFT"
    assert db_session.query(SalesFulfillment).count() == 0
    assert SalesFulfillmentStatus.DRAFT.value == "DRAFT"
