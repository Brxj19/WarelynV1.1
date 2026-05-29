from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.inventory import InventoryBatch, InventorySerial, StockLedgerEntry, WarehouseStock


def register_and_login(client: TestClient, email: str = "admin@example.com") -> dict[str, object]:
    response = client.post("/api/auth/register", json={"company_name": "Acme", "name": "Admin", "email": email, "password": "StrongPass123!"})
    assert response.status_code == 201
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def setup_dimension(client: TestClient, token: str, product_payload: dict[str, object]) -> dict[str, int]:
    headers = auth_headers(token)
    product = client.post("/api/catalog/products", json=product_payload, headers=headers)
    warehouse = client.post("/api/warehouses", json={"name": "Main", "code": f"M{product_payload['sku']}"}, headers=headers)
    assert product.status_code == 201
    assert warehouse.status_code == 201
    location = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Receiving", "code": f"R{product_payload['sku']}"}, headers=headers)
    assert location.status_code == 201
    return {"product_id": product.json()["id"], "warehouse_id": warehouse.json()["id"], "location_id": location.json()["id"]}


def test_batch_stock_in_creates_batch_and_ledger_reference(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_dimension(client, token, {"name": "Lot Item", "sku": "LOT-1", "track_batch": True, "track_expiry": True})

    response = client.post(
        "/api/inventory/stock-in",
        json={**dimension, "quantity": "5", "batch_number": "B-100", "expiry_date": "2026-12-31", "idempotency_key": "batch-in-1"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    batch = db_session.query(InventoryBatch).one()
    ledger = db_session.query(StockLedgerEntry).one()
    assert batch.batch_number == "B-100"
    assert batch.quantity_on_hand == Decimal("5.000")
    assert ledger.batch_id == batch.id
    assert response.json()["ledger_entries"][0]["batch_id"] == batch.id


def test_serial_stock_in_creates_one_serial_and_ledger_per_unit(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_dimension(client, token, {"name": "Serialized Item", "sku": "SER-1", "track_serial": True})

    response = client.post(
        "/api/inventory/stock-in",
        json={**dimension, "quantity": "2", "serial_numbers": ["SN-001", "SN-002"], "idempotency_key": "serial-in-1"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert db_session.query(WarehouseStock).one().quantity_on_hand == Decimal("2.000")
    assert db_session.query(InventorySerial).count() == 2
    ledgers = db_session.query(StockLedgerEntry).order_by(StockLedgerEntry.id).all()
    assert len(ledgers) == 2
    assert {entry.quantity_delta for entry in ledgers} == {Decimal("1.000")}
    assert all(entry.serial_id is not None for entry in ledgers)


def test_serial_stock_in_requires_quantity_match(client: TestClient) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_dimension(client, token, {"name": "Serialized Item", "sku": "SER-2", "track_serial": True})

    response = client.post(
        "/api/inventory/stock-in",
        json={**dimension, "quantity": "2", "serial_numbers": ["SN-003"], "idempotency_key": "serial-bad-1"},
        headers=auth_headers(token),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SERIAL_QUANTITY_MISMATCH"


def test_purchase_receipt_commit_creates_batch_and_serial_records(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    headers = auth_headers(token)
    vendor = client.post("/api/catalog/vendors", json={"name": "Vendor"}, headers=headers).json()
    dimension = setup_dimension(client, token, {"name": "Tracked Purchase", "sku": "TP-1", "track_batch": True, "track_serial": True})
    po = client.post(
        "/api/purchase-orders",
        json={"vendor_id": vendor["id"], "po_number": "PO-TRACK", "order_date": "2026-05-21", "items": [{"product_id": dimension["product_id"], "ordered_quantity": "2", "unit_cost": "1.00"}]},
        headers=headers,
    ).json()
    submitted = client.post(f"/api/purchase-orders/{po['id']}/submit", json={}, headers=headers).json()
    approved = client.post(f"/api/purchase-orders/{submitted['id']}/approve", json={}, headers=headers).json()
    receipt = client.post(
        f"/api/purchase-orders/{approved['id']}/receipts",
        json={
            "receipt_number": "GRN-TRACK",
            "items": [
                {
                    "purchase_order_item_id": submitted["items"][0]["id"],
                    "product_id": dimension["product_id"],
                    "warehouse_id": dimension["warehouse_id"],
                    "location_id": dimension["location_id"],
                    "received_quantity": "2",
                    "batch_number": "B-PO-1",
                    "serial_numbers": ["PO-SN-1", "PO-SN-2"],
                }
            ],
        },
        headers=headers,
    ).json()

    commit = client.post(f"/api/purchase-receipts/{receipt['id']}/commit", json={"idempotency_key": "po-track"}, headers=headers)

    assert commit.status_code == 200
    assert db_session.query(InventoryBatch).one().batch_number == "B-PO-1"
    assert db_session.query(InventorySerial).count() == 2
    assert db_session.query(StockLedgerEntry).count() == 2
    assert client.get("/api/inventory/batches", headers=headers).json()[0]["batch_number"] == "B-PO-1"
    assert len(client.get("/api/inventory/serials", headers=headers).json()) == 2
