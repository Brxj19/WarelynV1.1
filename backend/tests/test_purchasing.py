from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.inventory import ReferenceType, StockLedgerEntry, WarehouseStock
from app.models.purchasing import PurchaseOrder, PurchaseOrderStatus, PurchaseReceipt, PurchaseReceiptStatus


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


def setup_purchase_dimension(client: TestClient, token: str, suffix: str = "1") -> dict[str, int]:
    headers = auth_headers(token)
    vendor = client.post("/api/catalog/vendors", json={"name": f"Vendor {suffix}"}, headers=headers)
    product = client.post("/api/catalog/products", json={"name": f"Widget {suffix}", "sku": f"W-{suffix}"}, headers=headers)
    warehouse = client.post("/api/warehouses", json={"name": f"Main {suffix}", "code": f"M{suffix}"}, headers=headers)
    assert vendor.status_code == 201
    assert product.status_code == 201
    assert warehouse.status_code == 201
    location = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Receiving", "code": f"R{suffix}", "location_type": "RECEIVING"}, headers=headers)
    assert location.status_code == 201
    return {"vendor_id": vendor.json()["id"], "product_id": product.json()["id"], "warehouse_id": warehouse.json()["id"], "location_id": location.json()["id"]}


def po_payload(dimension: dict[str, int], quantity: str = "10", po_number: str = "PO-1") -> dict[str, object]:
    return {
        "vendor_id": dimension["vendor_id"],
        "po_number": po_number,
        "order_date": "2026-05-21",
        "items": [{"product_id": dimension["product_id"], "ordered_quantity": quantity, "unit_cost": "4.50"}],
    }


def create_po(client: TestClient, token: str, dimension: dict[str, int], quantity: str = "10", po_number: str = "PO-1") -> dict[str, object]:
    response = client.post("/api/purchase-orders", json=po_payload(dimension, quantity, po_number), headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def submit_po(client: TestClient, token: str, po_id: int) -> dict[str, object]:
    response = client.post(f"/api/purchase-orders/{po_id}/submit", json={}, headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def receipt_payload(po: dict[str, object], dimension: dict[str, int], quantity: str = "4", receipt_number: str = "GRN-1") -> dict[str, object]:
    item = po["items"][0]
    return {
        "receipt_number": receipt_number,
        "items": [
            {
                "purchase_order_item_id": item["id"],
                "product_id": dimension["product_id"],
                "warehouse_id": dimension["warehouse_id"],
                "location_id": dimension["location_id"],
                "received_quantity": quantity,
            }
        ],
    }


def create_receipt(client: TestClient, token: str, po: dict[str, object], dimension: dict[str, int], quantity: str = "4", receipt_number: str = "GRN-1") -> dict[str, object]:
    response = client.post(f"/api/purchase-orders/{po['id']}/receipts", json=receipt_payload(po, dimension, quantity, receipt_number), headers=auth_headers(token))
    assert response.status_code == 201
    return response.json()


def test_create_and_submit_purchase_order_and_block_submit_without_items(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_purchase_dimension(client, login["access_token"])
    po = create_po(client, login["access_token"], dimension)
    empty_po = client.post("/api/purchase-orders", json={"vendor_id": dimension["vendor_id"], "po_number": "PO-EMPTY", "order_date": "2026-05-21", "items": []}, headers=auth_headers(login["access_token"])).json()

    submitted = client.post(f"/api/purchase-orders/{po['id']}/submit", json={}, headers=auth_headers(login["access_token"]))
    blocked = client.post(f"/api/purchase-orders/{empty_po['id']}/submit", json={}, headers=auth_headers(login["access_token"]))

    assert submitted.status_code == 200
    assert submitted.json()["status"] == "SUBMITTED"
    assert blocked.status_code == 400
    assert blocked.json()["error"]["code"] == "PURCHASE_ORDER_ITEMS_REQUIRED"


def test_cancel_draft_and_submitted_purchase_orders_and_cannot_receive_cancelled(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_purchase_dimension(client, login["access_token"])
    draft = create_po(client, login["access_token"], dimension, po_number="PO-DRAFT")
    submitted = submit_po(client, login["access_token"], create_po(client, login["access_token"], dimension, po_number="PO-SUB")["id"])

    cancel_draft = client.post(f"/api/purchase-orders/{draft['id']}/cancel", json={}, headers=auth_headers(login["access_token"]))
    cancel_submitted = client.post(f"/api/purchase-orders/{submitted['id']}/cancel", json={}, headers=auth_headers(login["access_token"]))
    receive = client.post(f"/api/purchase-orders/{submitted['id']}/receipts", json=receipt_payload(submitted, dimension), headers=auth_headers(login["access_token"]))

    assert cancel_draft.json()["status"] == "CANCELLED"
    assert cancel_submitted.json()["status"] == "CANCELLED"
    assert receive.status_code == 409


def test_partial_and_full_receipt_commit_updates_stock_ledger_and_status(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_purchase_dimension(client, login["access_token"])
    po = submit_po(client, login["access_token"], create_po(client, login["access_token"], dimension, "10")["id"])
    receipt = create_receipt(client, login["access_token"], po, dimension, "4")

    partial = client.post(f"/api/purchase-receipts/{receipt['id']}/commit", json={"idempotency_key": "receive-1"}, headers=auth_headers(login["access_token"]))
    po_after_partial = client.get(f"/api/purchase-orders/{po['id']}", headers=auth_headers(login["access_token"])).json()
    receipt_2 = create_receipt(client, login["access_token"], po_after_partial, dimension, "6", "GRN-2")
    full = client.post(f"/api/purchase-receipts/{receipt_2['id']}/commit", json={"idempotency_key": "receive-2"}, headers=auth_headers(login["access_token"]))

    assert partial.status_code == 200
    assert partial.json()["purchase_order"]["status"] == "PARTIALLY_RECEIVED"
    assert Decimal(po_after_partial["items"][0]["received_quantity"]) == Decimal("4")
    assert full.status_code == 200
    assert full.json()["purchase_order"]["status"] == "RECEIVED"
    assert db_session.query(WarehouseStock).one().quantity_on_hand == Decimal("10.000")
    assert db_session.query(StockLedgerEntry).count() == 2
    assert {entry.reference_type for entry in db_session.query(StockLedgerEntry).all()} == {ReferenceType.PURCHASE_RECEIPT}
    assert client.get("/api/inventory/reconciliation/dry-run", headers=auth_headers(login["access_token"])).json()["mismatch_count"] == 0


def test_over_receiving_is_blocked(client: TestClient) -> None:
    login = register_and_login(client)
    dimension = setup_purchase_dimension(client, login["access_token"])
    po = submit_po(client, login["access_token"], create_po(client, login["access_token"], dimension, "5")["id"])

    response = client.post(f"/api/purchase-orders/{po['id']}/receipts", json=receipt_payload(po, dimension, "6"), headers=auth_headers(login["access_token"]))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "OVER_RECEIVING_NOT_ALLOWED"


def test_committed_receipt_cannot_be_edited_and_replay_does_not_duplicate_stock(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_purchase_dimension(client, login["access_token"])
    po = submit_po(client, login["access_token"], create_po(client, login["access_token"], dimension, "2")["id"])
    receipt = create_receipt(client, login["access_token"], po, dimension, "2")
    commit = client.post(f"/api/purchase-receipts/{receipt['id']}/commit", json={"idempotency_key": "receive-once"}, headers=auth_headers(login["access_token"]))
    replay = client.post(f"/api/purchase-receipts/{receipt['id']}/commit", json={"idempotency_key": "receive-once"}, headers=auth_headers(login["access_token"]))
    edit = client.patch(f"/api/purchase-receipts/{receipt['id']}", json={"notes": "edit"}, headers=auth_headers(login["access_token"]))

    assert commit.status_code == 200
    assert replay.status_code == 200
    assert edit.status_code == 409
    assert db_session.query(WarehouseStock).one().quantity_on_hand == Decimal("2.000")
    assert db_session.query(StockLedgerEntry).count() == 1


def test_cancelled_receipt_does_not_mutate_stock(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_purchase_dimension(client, login["access_token"])
    po = submit_po(client, login["access_token"], create_po(client, login["access_token"], dimension, "3")["id"])
    receipt = create_receipt(client, login["access_token"], po, dimension, "3")

    cancel = client.post(f"/api/purchase-receipts/{receipt['id']}/cancel", json={}, headers=auth_headers(login["access_token"]))
    commit = client.post(f"/api/purchase-receipts/{receipt['id']}/commit", json={"idempotency_key": "cancelled"}, headers=auth_headers(login["access_token"]))

    assert cancel.json()["status"] == "CANCELLED"
    assert commit.status_code == 409
    assert db_session.query(WarehouseStock).count() == 0
    assert db_session.query(StockLedgerEntry).count() == 0


def test_tenant_isolation_for_purchase_orders_receipts_and_locations(client: TestClient) -> None:
    login_a = register_and_login(client, "a@example.com")
    dimension_a = setup_purchase_dimension(client, login_a["access_token"], "A")
    po_a = submit_po(client, login_a["access_token"], create_po(client, login_a["access_token"], dimension_a, po_number="PO-A")["id"])
    receipt_a = create_receipt(client, login_a["access_token"], po_a, dimension_a)
    login_b = register_and_login(client, "b@example.com")
    dimension_b = setup_purchase_dimension(client, login_b["access_token"], "B")
    po_b = submit_po(client, login_b["access_token"], create_po(client, login_b["access_token"], dimension_b, po_number="PO-B")["id"])
    bad_payload = receipt_payload(po_b, {**dimension_b, "warehouse_id": dimension_a["warehouse_id"], "location_id": dimension_a["location_id"]})

    order_read = client.get(f"/api/purchase-orders/{po_a['id']}", headers=auth_headers(login_b["access_token"]))
    receipt_read = client.get(f"/api/purchase-receipts/{receipt_a['id']}", headers=auth_headers(login_b["access_token"]))
    receive_other_location = client.post(f"/api/purchase-orders/{po_b['id']}/receipts", json=bad_payload, headers=auth_headers(login_b["access_token"]))

    assert order_read.status_code == 404
    assert receipt_read.status_code == 404
    assert receive_other_location.status_code == 404


def test_purchase_roles(client: TestClient, db_session: Session) -> None:
    admin = register_and_login(client)
    dimension = setup_purchase_dimension(client, admin["access_token"])
    viewer_token = create_role_user(client, db_session, UserRole.VIEWER, "viewer-po@example.com")
    sales_token = create_role_user(client, db_session, UserRole.SALES_STAFF, "sales-po@example.com")
    purchase_token = create_role_user(client, db_session, UserRole.PURCHASE_STAFF, "purchase-po@example.com")

    viewer_create = client.post("/api/purchase-orders", json=po_payload(dimension, po_number="PO-VIEW"), headers=auth_headers(viewer_token))
    sales_create = client.post("/api/purchase-orders", json=po_payload(dimension, po_number="PO-SALES"), headers=auth_headers(sales_token))
    purchase_po = create_po(client, purchase_token, dimension, po_number="PO-PURCHASE")
    submitted = submit_po(client, purchase_token, purchase_po["id"])
    receipt = create_receipt(client, purchase_token, submitted, dimension, "1")
    commit = client.post(f"/api/purchase-receipts/{receipt['id']}/commit", json={"idempotency_key": "purchase-staff"}, headers=auth_headers(purchase_token))

    assert viewer_create.status_code == 403
    assert sales_create.status_code == 403
    assert purchase_po["status"] == "DRAFT"
    assert commit.status_code == 200


def test_purchase_models_statuses_persist(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    dimension = setup_purchase_dimension(client, login["access_token"])
    po = submit_po(client, login["access_token"], create_po(client, login["access_token"], dimension, "1")["id"])
    receipt = create_receipt(client, login["access_token"], po, dimension, "1")

    assert db_session.query(PurchaseOrder).one().status == PurchaseOrderStatus.SUBMITTED
    assert db_session.query(PurchaseReceipt).one().status == PurchaseReceiptStatus.DRAFT
    assert receipt["status"] == "DRAFT"
