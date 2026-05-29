from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.inventory import ReferenceType, StockLedgerEntry
from app.models.master_data import Category, LocationType, Product, RecordStatus, Warehouse, WarehouseLocation
from app.models.operations import StockCountSession, StockCountSessionStatus


def _setup(db_session: Session, client: TestClient, email: str = "cycle-counts@example.com"):
    tenant = Tenant(company_name="CycleCountCo", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id,
        name="Cycle Count User",
        email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    category = Category(tenant_id=tenant.id, name="Cycle Count Cat", status=RecordStatus.ACTIVE)
    db_session.add(category)
    db_session.flush()
    product = Product(
        tenant_id=tenant.id,
        name="Cycle Count Product",
        sku="CC-001",
        unit="pcs",
        category_id=category.id,
        status=RecordStatus.ACTIVE,
    )
    db_session.add(product)
    db_session.flush()
    warehouse = Warehouse(tenant_id=tenant.id, name="Cycle Count WH", code="CCWH", status=RecordStatus.ACTIVE)
    db_session.add(warehouse)
    db_session.flush()
    location = WarehouseLocation(
        tenant_id=tenant.id,
        warehouse_id=warehouse.id,
        name="Cycle Count Loc",
        code="CCLOC",
        location_type=LocationType.STORAGE,
        status=RecordStatus.ACTIVE,
    )
    db_session.add(location)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id, product.id, warehouse.id, location.id


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _stock_quantity(client: TestClient, token: str, product_id: int, warehouse_id: int, location_id: int) -> Decimal:
    response = client.get("/api/inventory/stock", headers=_auth_headers(token))
    assert response.status_code == 200
    rows = response.json()
    match = next(
        (
            row for row in rows
            if row["product_id"] == product_id and row["warehouse_id"] == warehouse_id and row["location_id"] == location_id
        ),
        None,
    )
    return Decimal(match["quantity_on_hand"]) if match else Decimal("0")


def _prepare_submitted_session(
    client: TestClient,
    token: str,
    product_id: int,
    warehouse_id: int,
    location_id: int,
    counted_quantity: str,
    stock_in_quantity: str,
    key_prefix: str,
) -> tuple[int, str]:
    stock_in = client.post(
        "/api/inventory/stock-in",
        json={
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "location_id": location_id,
            "quantity": stock_in_quantity,
            "reference_type": "MANUAL",
            "idempotency_key": f"{key_prefix}-stock-in",
        },
        headers=_auth_headers(token),
    )
    assert stock_in.status_code == 200
    session = client.post("/api/cycle-counts", json={"warehouse_id": warehouse_id}, headers=_auth_headers(token))
    assert session.status_code == 201
    session_id = session.json()["id"]
    line = client.post(
        f"/api/cycle-counts/{session_id}/lines",
        json={"product_id": product_id, "location_id": location_id},
        headers=_auth_headers(token),
    )
    assert line.status_code == 201
    line_id = line.json()["id"]
    update = client.patch(
        f"/api/cycle-counts/{session_id}/lines/{line_id}",
        json={"counted_quantity": counted_quantity},
        headers=_auth_headers(token),
    )
    assert update.status_code == 200
    submit = client.post(f"/api/cycle-counts/{session_id}/submit", headers=_auth_headers(token))
    assert submit.status_code == 200
    return session_id, session.json()["session_number"]


def test_duplicate_cycle_count_line_returns_conflict(client: TestClient, db_session: Session) -> None:
    token, tenant_id, product_id, warehouse_id, location_id = _setup(db_session, client, "cycle-count-dup@example.com")
    session = client.post("/api/cycle-counts", json={"warehouse_id": warehouse_id}, headers=_auth_headers(token))
    assert session.status_code == 201
    session_id = session.json()["id"]
    first = client.post(
        f"/api/cycle-counts/{session_id}/lines",
        json={"product_id": product_id, "location_id": location_id},
        headers=_auth_headers(token),
    )
    assert first.status_code == 201
    duplicate = client.post(
        f"/api/cycle-counts/{session_id}/lines",
        json={"product_id": product_id, "location_id": location_id},
        headers=_auth_headers(token),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_COUNT_LINE"


def test_reconcile_retry_only_applies_adjustment_once(client: TestClient, db_session: Session) -> None:
    token, tenant_id, product_id, warehouse_id, location_id = _setup(db_session, client, "cycle-count-retry@example.com")
    session_id, session_number = _prepare_submitted_session(
        client, token, product_id, warehouse_id, location_id, counted_quantity="95", stock_in_quantity="100", key_prefix="cc-retry"
    )

    first = client.post(f"/api/cycle-counts/{session_id}/reconcile", headers=_auth_headers(token))
    assert first.status_code == 200
    assert _stock_quantity(client, token, product_id, warehouse_id, location_id) == Decimal("95")

    db_session.expire_all()
    session = db_session.get(StockCountSession, session_id)
    assert session is not None
    session.status = StockCountSessionStatus.SUBMITTED
    db_session.commit()

    second = client.post(f"/api/cycle-counts/{session_id}/reconcile", headers=_auth_headers(token))
    assert second.status_code == 200
    assert _stock_quantity(client, token, product_id, warehouse_id, location_id) == Decimal("95")

    db_session.expire_all()
    entries = (
        db_session.query(StockLedgerEntry)
        .filter(
            StockLedgerEntry.tenant_id == tenant_id,
            StockLedgerEntry.reference_type == ReferenceType.RECONCILIATION,
            StockLedgerEntry.reference_id == session_number,
        )
        .all()
    )
    assert len(entries) == 1


def test_second_reconcile_request_is_blocked_after_first_success(client: TestClient, db_session: Session) -> None:
    token, tenant_id, product_id, warehouse_id, location_id = _setup(db_session, client, "cycle-count-double@example.com")
    session_id, session_number = _prepare_submitted_session(
        client, token, product_id, warehouse_id, location_id, counted_quantity="45", stock_in_quantity="50", key_prefix="cc-double"
    )

    first = client.post(f"/api/cycle-counts/{session_id}/reconcile", headers=_auth_headers(token))
    assert first.status_code == 200
    second = client.post(f"/api/cycle-counts/{session_id}/reconcile", headers=_auth_headers(token))
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "INVALID_SESSION_STATE"
    assert _stock_quantity(client, token, product_id, warehouse_id, location_id) == Decimal("45")

    entries = (
        db_session.query(StockLedgerEntry)
        .filter(
            StockLedgerEntry.tenant_id == tenant_id,
            StockLedgerEntry.reference_type == ReferenceType.RECONCILIATION,
            StockLedgerEntry.reference_id == session_number,
        )
        .all()
    )
    assert len(entries) == 1


def test_cancel_session_prevents_reconcile(client: TestClient, db_session: Session) -> None:
    token, tenant_id, product_id, warehouse_id, location_id = _setup(db_session, client, "cycle-count-cancel@example.com")
    session = client.post("/api/cycle-counts", json={"warehouse_id": warehouse_id}, headers=_auth_headers(token))
    assert session.status_code == 201
    session_id = session.json()["id"]

    cancel = client.post(f"/api/cycle-counts/{session_id}/cancel", headers=_auth_headers(token))
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "CANCELLED"

    reconcile = client.post(f"/api/cycle-counts/{session_id}/reconcile", headers=_auth_headers(token))
    assert reconcile.status_code == 409
    assert reconcile.json()["error"]["code"] == "INVALID_SESSION_STATE"


def test_reconcile_resnapshots_system_quantity_before_adjusting(client: TestClient, db_session: Session) -> None:
    token, tenant_id, product_id, warehouse_id, location_id = _setup(db_session, client, "cycle-count-resnapshot@example.com")
    initial_stock = client.post(
        "/api/inventory/stock-in",
        json={
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "location_id": location_id,
            "quantity": "10",
            "reference_type": "MANUAL",
            "idempotency_key": "cc-resnapshot-initial",
        },
        headers=_auth_headers(token),
    )
    assert initial_stock.status_code == 200

    session = client.post("/api/cycle-counts", json={"warehouse_id": warehouse_id}, headers=_auth_headers(token))
    assert session.status_code == 201
    session_id = session.json()["id"]
    line = client.post(
        f"/api/cycle-counts/{session_id}/lines",
        json={"product_id": product_id, "location_id": location_id},
        headers=_auth_headers(token),
    )
    assert line.status_code == 201
    assert Decimal(line.json()["system_quantity"]) == Decimal("10")
    line_id = line.json()["id"]

    extra_stock = client.post(
        "/api/inventory/stock-in",
        json={
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "location_id": location_id,
            "quantity": "5",
            "reference_type": "MANUAL",
            "idempotency_key": "cc-resnapshot-extra",
        },
        headers=_auth_headers(token),
    )
    assert extra_stock.status_code == 200

    update = client.patch(
        f"/api/cycle-counts/{session_id}/lines/{line_id}",
        json={"counted_quantity": "8"},
        headers=_auth_headers(token),
    )
    assert update.status_code == 200
    assert Decimal(update.json()["variance"]) == Decimal("-2")

    submit = client.post(f"/api/cycle-counts/{session_id}/submit", headers=_auth_headers(token))
    assert submit.status_code == 200
    reconcile = client.post(f"/api/cycle-counts/{session_id}/reconcile", headers=_auth_headers(token))
    assert reconcile.status_code == 200

    detail = client.get(f"/api/cycle-counts/{session_id}", headers=_auth_headers(token))
    assert detail.status_code == 200
    assert len(detail.json()["lines"]) == 1
    saved_line = detail.json()["lines"][0]
    assert Decimal(saved_line["system_quantity"]) == Decimal("15")
    assert Decimal(saved_line["variance"]) == Decimal("-7")
    assert _stock_quantity(client, token, product_id, warehouse_id, location_id) == Decimal("8")
