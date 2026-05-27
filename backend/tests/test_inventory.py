from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.inventory import MovementType, StockLedgerEntry, WarehouseStock


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
    user = User(
        tenant_id=tenant.id,
        name=role.value,
        email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=role,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"]


def setup_dimension(client: TestClient, token: str) -> dict[str, int]:
    headers = auth_headers(token)
    product = client.post("/api/catalog/products", json={"name": "Widget", "sku": f"W-{token[:6]}"}, headers=headers)
    warehouse = client.post("/api/warehouses", json={"name": "Main", "code": f"M{token[:6]}"}, headers=headers)
    assert product.status_code == 201
    assert warehouse.status_code == 201
    location = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Aisle 1", "code": "A1"}, headers=headers)
    assert location.status_code == 201
    return {"product_id": product.json()["id"], "warehouse_id": warehouse.json()["id"], "location_id": location.json()["id"]}


def stock_in_payload(dimension: dict[str, int], quantity: str = "10", key: str = "in-1") -> dict[str, object]:
    return {**dimension, "quantity": quantity, "idempotency_key": key, "note": "initial stock"}


def stock_in(client: TestClient, token: str, dimension: dict[str, int], quantity: str = "10", key: str = "in-1") -> dict[str, object]:
    response = client.post("/api/inventory/stock-in", json=stock_in_payload(dimension, quantity, key), headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def test_stock_in_creates_warehouse_stock_and_ledger(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_dimension(client, login["access_token"])

    response = stock_in(client, login["access_token"], dimension, "10")

    assert Decimal(response["stock"]["quantity_on_hand"]) == Decimal("10")
    assert Decimal(response["stock"]["quantity_available"]) == Decimal("10")
    assert response["ledger_entries"][0]["movement_type"] == "STOCK_IN"
    assert db_session.query(WarehouseStock).count() == 1
    assert db_session.query(StockLedgerEntry).count() == 1


def test_stock_out_blocks_insufficient_stock(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "5")

    response = client.post("/api/inventory/stock-out", json={**dimension, "quantity": "6", "idempotency_key": "out-1"}, headers=auth_headers(login["access_token"]))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INSUFFICIENT_STOCK"


def test_adjustment_in_and_out_work_and_block_overdraw(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_dimension(client, login["access_token"])

    adjust_in = client.post("/api/inventory/adjust", json={**dimension, "delta": "7", "note": "count gain", "idempotency_key": "adj-1"}, headers=auth_headers(login["access_token"]))
    adjust_out = client.post("/api/inventory/adjust", json={**dimension, "delta": "-2", "note": "count loss", "idempotency_key": "adj-2"}, headers=auth_headers(login["access_token"]))
    overdraw = client.post("/api/inventory/adjust", json={**dimension, "delta": "-6", "note": "too much", "idempotency_key": "adj-3"}, headers=auth_headers(login["access_token"]))

    assert adjust_in.status_code == 200
    assert adjust_in.json()["ledger_entries"][0]["movement_type"] == "ADJUSTMENT_IN"
    assert adjust_out.status_code == 200
    assert adjust_out.json()["stock"]["quantity_on_hand"] == "5.000"
    assert overdraw.status_code == 409


def test_reserve_release_and_deduct_reserved_stock(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "10")

    reserve = client.post("/api/inventory/reserve", json={**dimension, "quantity": "4", "reference_id": "SO-1", "idempotency_key": "res-1"}, headers=auth_headers(login["access_token"]))
    assert reserve.status_code == 200
    assert reserve.json()["stock"]["quantity_reserved"] == "4.000"
    assert reserve.json()["stock"]["quantity_available"] == "6.000"

    release = client.post(f"/api/inventory/reservations/{reserve.json()['reservation']['id']}/release", json={"idempotency_key": "rel-1"}, headers=auth_headers(login["access_token"]))
    assert release.status_code == 200
    assert release.json()["stock"]["quantity_reserved"] == "0.000"
    assert release.json()["stock"]["quantity_available"] == "10.000"

    reserve_2 = client.post("/api/inventory/reserve", json={**dimension, "quantity": "3", "reference_id": "SO-2", "idempotency_key": "res-2"}, headers=auth_headers(login["access_token"]))
    deduct = client.post(f"/api/inventory/reservations/{reserve_2.json()['reservation']['id']}/deduct", json={"idempotency_key": "ded-1"}, headers=auth_headers(login["access_token"]))
    assert deduct.status_code == 200
    assert deduct.json()["stock"]["quantity_on_hand"] == "7.000"
    assert deduct.json()["stock"]["quantity_reserved"] == "0.000"
    assert deduct.json()["stock"]["quantity_available"] == "7.000"


def test_transfer_creates_balanced_ledger_entries(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_dimension(client, login["access_token"])
    headers = auth_headers(login["access_token"])
    location_2 = client.post(f"/api/warehouses/{dimension['warehouse_id']}/locations", json={"name": "Aisle 2", "code": "A2"}, headers=headers).json()
    stock_in(client, login["access_token"], dimension, "8")

    transfer = client.post(
        "/api/inventory/transfer",
        json={"product_id": dimension["product_id"], "source_warehouse_id": dimension["warehouse_id"], "source_location_id": dimension["location_id"], "destination_warehouse_id": dimension["warehouse_id"], "destination_location_id": location_2["id"], "quantity": "3", "idempotency_key": "tr-1"},
        headers=headers,
    )

    assert transfer.status_code == 200
    movements = [entry.movement_type for entry in db_session.query(StockLedgerEntry).filter(StockLedgerEntry.idempotency_key == "tr-1").all()]
    assert movements == [MovementType.TRANSFER_OUT, MovementType.TRANSFER_IN]


def test_tenant_cannot_access_other_tenant_stock(client: TestClient) -> None:
    login_a = register_and_login(client, "a@example.com")
    dimension_a = setup_dimension(client, login_a["access_token"])
    stock_in(client, login_a["access_token"], dimension_a, "5")
    login_b = register_and_login(client, "b@example.com")

    read = client.get("/api/inventory/stock", headers=auth_headers(login_b["access_token"]))
    mutate = client.post("/api/inventory/stock-out", json={**dimension_a, "quantity": "1", "idempotency_key": "b-out"}, headers=auth_headers(login_b["access_token"]))

    assert read.status_code == 200
    assert read.json() == []
    assert mutate.status_code == 404
    assert mutate.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_idempotency_prevents_duplicate_and_detects_conflict(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_dimension(client, login["access_token"])
    headers = auth_headers(login["access_token"])
    payload = stock_in_payload(dimension, "5", "idem-1")

    first = client.post("/api/inventory/stock-in", json=payload, headers=headers)
    second = client.post("/api/inventory/stock-in", json=payload, headers=headers)
    conflict = client.post("/api/inventory/stock-in", json={**payload, "quantity": "6"}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert Decimal(second.json()["stock"]["quantity_on_hand"]) == Decimal("5")
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert db_session.query(StockLedgerEntry).count() == 1


def test_ledger_has_no_update_or_delete_endpoint(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "5")

    patch = client.patch("/api/inventory/ledger/1", json={}, headers=auth_headers(login["access_token"]))
    delete = client.delete("/api/inventory/ledger/1", headers=auth_headers(login["access_token"]))

    assert patch.status_code == 404
    assert delete.status_code == 404


def test_reconciliation_dry_run_reports_match_and_mismatch(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_dimension(client, login["access_token"])
    stock_in(client, login["access_token"], dimension, "5")
    headers = auth_headers(login["access_token"])

    clean = client.get("/api/inventory/reconciliation/dry-run", headers=headers)
    stock = db_session.query(WarehouseStock).one()
    stock.quantity_available = Decimal("4")
    db_session.commit()
    mismatch = client.get("/api/inventory/reconciliation/dry-run", headers=headers)

    assert clean.status_code == 200
    assert clean.json()["mismatch_count"] == 0
    assert mismatch.status_code == 200
    assert mismatch.json()["mismatch_count"] == 1


def test_role_access_for_inventory(client: TestClient, db_session: Session) -> None:
    admin = register_and_login(client)
    dimension = setup_dimension(client, admin["access_token"])
    stock_in(client, admin["access_token"], dimension, "5")
    viewer_token = create_role_user(client, db_session, UserRole.VIEWER, "viewer-inv@example.com")
    sales_token = create_role_user(client, db_session, UserRole.SALES_STAFF, "sales-inv@example.com")

    assert client.get("/api/inventory/stock", headers=auth_headers(viewer_token)).status_code == 200
    assert client.post("/api/inventory/stock-in", json=stock_in_payload(dimension, "1", "viewer-in"), headers=auth_headers(viewer_token)).status_code == 403
    reserve = client.post("/api/inventory/reserve", json={**dimension, "quantity": "1", "idempotency_key": "sales-res"}, headers=auth_headers(sales_token))
    assert reserve.status_code == 200
    assert client.post("/api/inventory/stock-out", json={**dimension, "quantity": "1", "idempotency_key": "sales-out"}, headers=auth_headers(sales_token)).status_code == 403
