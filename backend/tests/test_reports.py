from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.auth import UserRole
from app.models.inventory import InventorySerial, StockLedgerEntry, WarehouseStock
from app.models.returns import BlockedReturnStock
from test_purchasing import approve_po, create_po, create_receipt, setup_purchase_dimension, submit_po
from test_returns import create_return, fulfilled_order, inspect_and_process
from test_sales import (
    auth_headers,
    confirm_sales_order,
    create_fulfillment,
    create_role_user,
    create_sales_order,
    register_and_login,
    setup_sales_dimension,
    stock_in,
)


def stock_out(client: TestClient, token: str, dimension: dict[str, int], quantity: str, key: str) -> None:
    response = client.post("/api/inventory/stock-out", json={"product_id": dimension["product_id"], "warehouse_id": dimension["warehouse_id"], "location_id": dimension["location_id"], "quantity": quantity, "idempotency_key": key}, headers=auth_headers(token))
    assert response.status_code == 200


def create_report_fixture(client: TestClient, token: str, suffix: str = "R") -> dict[str, int]:
    dimension = setup_sales_dimension(client, token, suffix, {"name": f"Report Widget {suffix}", "sku": f"REPORT-{suffix}", "cost_price": "12.50", "reorder_level": 10})
    stock_in(client, token, dimension, "5", f"report-stock-in-{suffix}")
    return dimension


def test_inventory_summary_and_stock_reports(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = create_report_fixture(client, token)

    summary = client.get("/api/reports/inventory-summary", headers=auth_headers(token))
    warehouse = client.get("/api/reports/warehouse-stock", headers=auth_headers(token))
    location = client.get("/api/reports/location-stock", headers=auth_headers(token))

    assert summary.status_code == 200
    assert summary.json()["total_products"] == 1
    assert summary.json()["total_available_quantity"] == "5.000"
    assert summary.json()["total_stock_value_cost"] == "62.50000"
    assert summary.json()["low_stock_count"] == 1
    assert warehouse.status_code == 200
    assert warehouse.json()[0]["stock_status"] == "LOW_STOCK"
    assert warehouse.json()[0]["stock_value"] == "62.50000"
    assert location.status_code == 200
    assert location.json()[0]["location_id"] == dimension["location_id"]
    assert db_session.query(StockLedgerEntry).count() == 1


def test_stock_movement_low_stock_reorder_and_valuation_reports(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = create_report_fixture(client, token, "MOVE")
    before_stock = db_session.query(WarehouseStock).one().quantity_available
    before_ledger = db_session.query(StockLedgerEntry).count()

    movements = client.get("/api/reports/stock-movements?movement_type=STOCK_IN", headers=auth_headers(token))
    low_stock = client.get("/api/reports/low-stock", headers=auth_headers(token))
    reorder = client.get("/api/reports/reorder-suggestions", headers=auth_headers(token))
    valuation = client.get("/api/reports/product-valuation", headers=auth_headers(token))

    assert movements.status_code == 200
    assert movements.json()[0]["movement_type"] == "STOCK_IN"
    assert low_stock.status_code == 200
    assert low_stock.json()[0]["suggested_reorder_quantity"] == "15.000"
    assert reorder.status_code == 200
    assert reorder.json()[0]["reason"] == "LOW_STOCK"
    assert reorder.json()[0]["default_vendor_id"] is None
    assert valuation.status_code == 200
    assert valuation.json()["total_stock_value"] == "62.50000"
    assert valuation.json()["total_units"] == "5.000"
    db_session.refresh(db_session.query(WarehouseStock).one())
    assert db_session.query(WarehouseStock).one().quantity_available == before_stock
    assert db_session.query(StockLedgerEntry).count() == before_ledger


def test_reconciliation_report_is_read_only(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    create_report_fixture(client, token, "READONLY")
    before_stock = db_session.query(WarehouseStock).count()
    before_ledger = db_session.query(StockLedgerEntry).count()

    first = client.get("/api/reports/reconciliation", headers=auth_headers(token))
    second = client.get("/api/reports/reconciliation", headers=auth_headers(token))

    assert first.status_code == 200
    assert second.status_code == 200
    assert db_session.query(WarehouseStock).count() == before_stock
    assert db_session.query(StockLedgerEntry).count() == before_ledger


def test_out_of_stock_report_uses_projection_available(client: TestClient) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "OUT", {"name": "Out Item", "sku": "OUT-1", "cost_price": "1.00", "reorder_level": 5})
    stock_in(client, token, dimension, "1", "out-in")
    stock_out(client, token, dimension, "1", "out-out")

    response = client.get("/api/reports/low-stock", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()[0]["status"] == "OUT_OF_STOCK"
    assert response.json()[0]["suggested_reorder_quantity"] == "10.000"


def test_batch_expiry_and_serial_status_reports(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    batch_dimension = setup_sales_dimension(client, token, "BATCH", {"name": "Expiry Item", "sku": "EXP-1", "track_batch": True, "track_expiry": True})
    serial_dimension = setup_sales_dimension(client, token, "SERIAL-REP", {"name": "Serial Report", "sku": "SER-REP", "track_serial": True})
    tomorrow = date.today() + timedelta(days=1)
    expired = date.today() - timedelta(days=1)
    batch_in = client.post("/api/inventory/stock-in", json={"product_id": batch_dimension["product_id"], "warehouse_id": batch_dimension["warehouse_id"], "location_id": batch_dimension["location_id"], "quantity": "2", "batch_number": "EXP-SOON", "expiry_date": tomorrow.isoformat(), "idempotency_key": "batch-soon"}, headers=auth_headers(token))
    batch_expired = client.post("/api/inventory/stock-in", json={"product_id": batch_dimension["product_id"], "warehouse_id": batch_dimension["warehouse_id"], "location_id": batch_dimension["location_id"], "quantity": "1", "batch_number": "EXP-OLD", "expiry_date": expired.isoformat(), "idempotency_key": "batch-old"}, headers=auth_headers(token))
    serial_in = client.post("/api/inventory/stock-in", json={"product_id": serial_dimension["product_id"], "warehouse_id": serial_dimension["warehouse_id"], "location_id": serial_dimension["location_id"], "quantity": "1", "serial_numbers": ["SER-REPORT-1"], "idempotency_key": "serial-report-in"}, headers=auth_headers(token))
    assert batch_in.status_code == 200
    assert batch_expired.status_code == 200
    assert serial_in.status_code == 200

    expiry_report = client.get("/api/reports/batch-expiry?expiry_within_days=30", headers=auth_headers(token))
    serial_report = client.get("/api/reports/serial-status", headers=auth_headers(token))

    assert expiry_report.status_code == 200
    statuses = {row["batch_number"]: row["expiry_status"] for row in expiry_report.json()}
    assert statuses["EXP-SOON"] == "EXPIRING_SOON"
    assert statuses["EXP-OLD"] == "EXPIRED"
    assert serial_report.status_code == 200
    assert serial_report.json()[0]["serial_number"] == "SER-REPORT-1"
    assert db_session.query(InventorySerial).count() == 1


def test_blocked_stock_and_reconciliation_reports(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "BLOCK-REPORT")
    stock_in(client, token, dimension, "3", "block-report-in")
    order = fulfilled_order(client, token, dimension, "1", "SO-BLOCK-REPORT", "FUL-BLOCK-REPORT")
    sales_return = create_return(client, token, order, dimension, "1", "RET-BLOCK-REPORT")
    submitted = client.post(f"/api/sales-returns/{sales_return['id']}/submit", json={}, headers=auth_headers(token))
    inspect_and_process(client, token, submitted.json(), "ACCEPTED_BLOCKED", "1", key="process-block-report")

    blocked = client.get("/api/reports/blocked-stock", headers=auth_headers(token))
    clean = client.get("/api/reports/reconciliation", headers=auth_headers(token))
    stock = db_session.query(WarehouseStock).one()
    stock.quantity_available = Decimal("999")
    db_session.commit()
    mismatch = client.get("/api/reports/reconciliation", headers=auth_headers(token))

    assert blocked.status_code == 200
    assert blocked.json()[0]["source_type"] == "RETURN_BLOCKED"
    assert db_session.query(BlockedReturnStock).count() == 1
    assert clean.status_code == 200
    assert clean.json()["mismatch_count"] == 0
    assert mismatch.status_code == 200
    assert mismatch.json()["mismatch_count"] == 1
    assert mismatch.json()["mismatches"][0]["actual_available"] == "999.000"


def test_dashboard_operations_and_report_roles(client: TestClient, db_session: Session) -> None:
    admin = register_and_login(client)
    token = admin["access_token"]
    create_report_fixture(client, token, "DASH")
    viewer_token = create_role_user(client, db_session, UserRole.VIEWER, "viewer-reports@example.com")
    sales_token = create_role_user(client, db_session, UserRole.SALES_STAFF, "sales-reports@example.com")
    purchase_token = create_role_user(client, db_session, UserRole.PURCHASE_STAFF, "purchase-reports@example.com")

    dashboard = client.get("/api/dashboard/operations", headers=auth_headers(token))
    viewer = client.get("/api/reports/inventory-summary", headers=auth_headers(viewer_token))
    sales = client.get("/api/reports/inventory-summary", headers=auth_headers(sales_token))
    purchase = client.get("/api/reports/inventory-summary", headers=auth_headers(purchase_token))

    assert dashboard.status_code == 200
    assert dashboard.json()["kpis"]["low_stock_count"] == 1
    assert len(dashboard.json()["recent_stock_movements"]) == 1
    assert viewer.status_code == 200
    assert sales.status_code == 403
    assert purchase.status_code == 403


def test_report_tenant_isolation(client: TestClient) -> None:
    login_a = register_and_login(client, "report-a@example.com")
    create_report_fixture(client, login_a["access_token"], "A")
    login_b = register_and_login(client, "report-b@example.com")

    stock_b = client.get("/api/reports/warehouse-stock", headers=auth_headers(login_b["access_token"]))
    movements_b = client.get("/api/reports/stock-movements", headers=auth_headers(login_b["access_token"]))

    assert stock_b.status_code == 200
    assert stock_b.json() == []
    assert movements_b.status_code == 200
    assert movements_b.json() == []


def test_report_csv_export_returns_text_csv(client: TestClient) -> None:
    login = register_and_login(client, "report-export@example.com")
    token = login["access_token"]
    create_report_fixture(client, token, "EXPORT")

    response = client.get("/api/reports/warehouse-stock/export.csv", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "warehouse_name" in response.text


def test_dashboard_charts_and_insights(client: TestClient) -> None:
    login = register_and_login(client, "charts-test@example.com")
    token = login["access_token"]
    create_report_fixture(client, token, "CHARTS")

    dashboard = client.get("/api/dashboard/operations?compare_previous=true", headers=auth_headers(token))

    assert dashboard.status_code == 200
    data = dashboard.json()
    # Charts field present with expected structure
    assert "charts" in data
    charts = data["charts"]
    assert "stock_movements_by_day" in charts
    assert "order_status_summary" in charts
    assert "low_stock_by_category" in charts
    assert isinstance(charts["stock_movements_by_day"], list)
    assert len(charts["stock_movements_by_day"]) == 30
    # Each day entry has the right shape
    day_entry = charts["stock_movements_by_day"][0]
    assert "date" in day_entry
    assert "inbound" in day_entry
    assert "outbound" in day_entry
    # Order status summary has correct keys
    assert "purchase_orders" in charts["order_status_summary"]
    assert "sales_orders" in charts["order_status_summary"]
    # Insights field present
    assert "insights" in data
    assert isinstance(data["insights"], list)
    # With only 1 low-stock item (count <= 5), no low-stock insight should fire
    low_stock_insights = [i for i in data["insights"] if "low-stock" in (i.get("title") or "").lower()]
    assert len(low_stock_insights) == 0
    # previous_kpis should be None when no historical ledger data exists for previous period
    assert data["previous_kpis"] is None


def test_sales_and_admin_dashboard_endpoints(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = register_and_login(client, "dashboard-sales-admin@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(
        client,
        token,
        "DASH-SALES",
        {"name": "Dashboard Sales", "sku": "DASH-SALES", "cost_price": "4.00", "selling_price": "10.00"},
    )
    stock_in(client, token, dimension, "6", "dash-sales-stock")
    order = create_sales_order(client, token, dimension, "3", "SO-DASH-SALES")
    confirmed = confirm_sales_order(client, token, order, dimension, "3", "dash-sales-confirm")
    reservation_id = confirmed["stock_results"][0]["reservation"]["id"]
    fulfillment = create_fulfillment(client, token, order, dimension, reservation_id, "3", "FUL-DASH-SALES")
    committed = client.post(
        f"/api/sales-fulfillments/{fulfillment['id']}/commit",
        json={"idempotency_key": "dash-sales-commit"},
        headers=auth_headers(token),
    )
    invoice_order = create_sales_order(client, token, dimension, "3", "SO-DASH-INVOICE")
    invoice = client.post("/api/invoices", json={"sales_order_id": invoice_order["id"]}, headers=auth_headers(token))
    sent = client.post(
        f"/api/invoices/{invoice.json()['id']}/send",
        json={"email": "customer@example.com"},
        headers=auth_headers(token),
    )
    sales_staff_token = create_role_user(client, db_session, UserRole.SALES_STAFF, "dash-sales-staff@example.com")
    inventory_token = create_role_user(client, db_session, UserRole.INVENTORY_MANAGER, "dash-sales-inventory@example.com")

    sales_dashboard = client.get("/api/dashboard/sales?days=30", headers=auth_headers(token))
    admin_dashboard = client.get("/api/dashboard/admin?days=30", headers=auth_headers(token))
    sales_staff_dashboard = client.get("/api/dashboard/sales?days=30", headers=auth_headers(sales_staff_token))
    inventory_forbidden = client.get("/api/dashboard/sales?days=30", headers=auth_headers(inventory_token))
    sales_staff_admin_forbidden = client.get("/api/dashboard/admin?days=30", headers=auth_headers(sales_staff_token))

    assert committed.status_code == 200
    assert invoice.status_code == 201
    assert sent.status_code == 200
    assert sales_dashboard.status_code == 200
    assert sales_dashboard.json()["total_revenue_mtd"] == "29.97"
    assert sales_dashboard.json()["overdue_invoices_count"] == 0
    assert sales_dashboard.json()["top_products_by_revenue"][0]["sku"] == "DASH-SALES"
    assert admin_dashboard.status_code == 200
    assert admin_dashboard.json()["revenue_mtd"] == "29.97"
    assert admin_dashboard.json()["order_health"]["open_so"] >= 0
    assert admin_dashboard.json()["stock_health"]["low_stock"] >= 0
    assert sales_staff_dashboard.status_code == 200
    assert inventory_forbidden.status_code == 403
    assert sales_staff_admin_forbidden.status_code == 403


def test_purchase_and_inventory_dashboard_endpoints(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = register_and_login(client, "dashboard-purchase-admin@example.com")
    token = login["access_token"]
    create_report_fixture(client, token, "INV-DASH")
    dimension = setup_purchase_dimension(client, token, "DASH-PURCHASE")
    po = approve_po(client, token, submit_po(client, token, create_po(client, token, dimension, "5", "PO-DASH")["id"])["id"])
    receipt = create_receipt(client, token, po, dimension, "5", "GRN-DASH")
    committed = client.post(
        f"/api/purchase-receipts/{receipt['id']}/commit",
        json={"idempotency_key": "dash-receipt-commit"},
        headers=auth_headers(token),
    )
    bill = client.post("/api/bills", json={"receipt_id": receipt["id"]}, headers=auth_headers(token))
    sent = client.post(
        f"/api/bills/{bill.json()['id']}/send",
        json={"email": "vendor@example.com"},
        headers=auth_headers(token),
    )
    purchase_token = create_role_user(client, db_session, UserRole.PURCHASE_STAFF, "dash-purchase-staff@example.com")
    inventory_token = create_role_user(client, db_session, UserRole.INVENTORY_MANAGER, "dash-purchase-inventory@example.com")
    viewer_token = create_role_user(client, db_session, UserRole.VIEWER, "dash-purchase-viewer@example.com")

    purchase_dashboard = client.get("/api/dashboard/purchasing?days=30", headers=auth_headers(token))
    purchase_staff_dashboard = client.get("/api/dashboard/purchasing?days=30", headers=auth_headers(purchase_token))
    inventory_dashboard = client.get("/api/dashboard/inventory?days=30", headers=auth_headers(inventory_token))
    viewer_purchase_forbidden = client.get("/api/dashboard/purchasing?days=30", headers=auth_headers(viewer_token))
    viewer_inventory_forbidden = client.get("/api/dashboard/inventory?days=30", headers=auth_headers(viewer_token))

    assert committed.status_code == 200
    assert bill.status_code == 201
    assert sent.status_code == 200
    assert purchase_dashboard.status_code == 200
    assert purchase_dashboard.json()["total_spend_mtd"] == "22.50"
    assert purchase_dashboard.json()["pending_bills_count"] == 0
    assert purchase_dashboard.json()["top_vendors_by_spend"][0]["vendor_name"].startswith("Vendor")
    assert purchase_staff_dashboard.status_code == 200
    assert inventory_dashboard.status_code == 200
    assert inventory_dashboard.json()["low_stock_count"] >= 1
    assert len(inventory_dashboard.json()["warehouse_utilization"]) >= 1
    assert viewer_purchase_forbidden.status_code == 403
    assert viewer_inventory_forbidden.status_code == 403
