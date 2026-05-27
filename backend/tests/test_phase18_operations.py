from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.master_data import Category, LocationType, Product, RecordStatus, Warehouse, WarehouseLocation


def _setup(db_session: Session, client: TestClient, email: str = "p18@example.com"):
    tenant = Tenant(company_name="P18Co", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P18User", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.flush()
    cat = Category(tenant_id=tenant.id, name="P18Cat", status=RecordStatus.ACTIVE)
    db_session.add(cat)
    db_session.flush()
    product = Product(tenant_id=tenant.id, name="P18Prod", sku="P18-001", unit="pcs", category_id=cat.id, status=RecordStatus.ACTIVE)
    db_session.add(product)
    db_session.flush()
    wh = Warehouse(tenant_id=tenant.id, name="P18WH", code="P18W", status=RecordStatus.ACTIVE)
    db_session.add(wh)
    db_session.flush()
    loc = WarehouseLocation(tenant_id=tenant.id, warehouse_id=wh.id, name="P18Loc", code="P18L", location_type=LocationType.STORAGE, status=RecordStatus.ACTIVE)
    db_session.add(loc)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return token, tenant.id, product.id, wh.id, loc.id, user.id


# ─── Reorder Rules ───────────────────────────────────────────────────────────

def test_reorder_rule_create(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "rr-create@example.com")
    resp = client.post("/api/reorder-rules", json={
        "product_id": pid, "warehouse_id": wid,
        "min_quantity": "10", "max_quantity": "100",
        "safety_stock": "5", "lead_time_days": 7,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["product_id"] == pid
    assert Decimal(data["min_quantity"]) == Decimal("10")


def test_reorder_rule_list(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "rr-list@example.com")
    client.post("/api/reorder-rules", json={
        "product_id": pid, "warehouse_id": wid,
        "min_quantity": "5", "max_quantity": "50",
    }, headers={"Authorization": f"Bearer {token}"})
    resp = client.get("/api/reorder-rules", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_reorder_rule_update(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "rr-update@example.com")
    create = client.post("/api/reorder-rules", json={
        "product_id": pid, "warehouse_id": wid,
        "min_quantity": "10", "max_quantity": "100",
    }, headers={"Authorization": f"Bearer {token}"})
    rule_id = create.json()["id"]
    resp = client.patch(f"/api/reorder-rules/{rule_id}", json={"min_quantity": "20"}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert Decimal(resp.json()["min_quantity"]) == Decimal("20")


def test_reorder_rule_delete(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "rr-delete@example.com")
    create = client.post("/api/reorder-rules", json={
        "product_id": pid, "warehouse_id": wid,
        "min_quantity": "10", "max_quantity": "100",
    }, headers={"Authorization": f"Bearer {token}"})
    rule_id = create.json()["id"]
    resp = client.delete(f"/api/reorder-rules/{rule_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204


def test_reorder_rule_get(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "rr-get@example.com")
    create = client.post("/api/reorder-rules", json={
        "product_id": pid, "warehouse_id": wid,
        "min_quantity": "10", "max_quantity": "100",
    }, headers={"Authorization": f"Bearer {token}"})
    rule_id = create.json()["id"]
    resp = client.get(f"/api/reorder-rules/{rule_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == rule_id


# ─── Putaway Tasks ───────────────────────────────────────────────────────────

def test_putaway_task_create(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "pt-create@example.com")
    resp = client.post("/api/putaway-tasks", json={
        "product_id": pid, "warehouse_id": wid,
        "from_location_id": lid, "quantity": "25",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "PENDING"


def test_putaway_task_list(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "pt-list@example.com")
    client.post("/api/putaway-tasks", json={
        "product_id": pid, "warehouse_id": wid,
        "from_location_id": lid, "quantity": "10",
    }, headers={"Authorization": f"Bearer {token}"})
    resp = client.get("/api/putaway-tasks", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_putaway_task_start(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "pt-start@example.com")
    create = client.post("/api/putaway-tasks", json={
        "product_id": pid, "warehouse_id": wid,
        "from_location_id": lid, "quantity": "10",
    }, headers={"Authorization": f"Bearer {token}"})
    task_id = create.json()["id"]
    resp = client.post(f"/api/putaway-tasks/{task_id}/start", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"
    assert resp.json()["started_at"] is not None


def test_putaway_task_complete(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "pt-complete@example.com")
    create = client.post("/api/putaway-tasks", json={
        "product_id": pid, "warehouse_id": wid,
        "from_location_id": lid, "quantity": "10",
    }, headers={"Authorization": f"Bearer {token}"})
    task_id = create.json()["id"]
    resp = client.post(f"/api/putaway-tasks/{task_id}/complete", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETED"
    assert resp.json()["completed_at"] is not None


def test_putaway_task_cancel(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "pt-cancel@example.com")
    create = client.post("/api/putaway-tasks", json={
        "product_id": pid, "warehouse_id": wid,
        "from_location_id": lid, "quantity": "10",
    }, headers={"Authorization": f"Bearer {token}"})
    task_id = create.json()["id"]
    resp = client.post(f"/api/putaway-tasks/{task_id}/cancel", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


# ─── Cycle Counts ────────────────────────────────────────────────────────────

def test_cycle_count_create_session(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "cc-create@example.com")
    resp = client.post("/api/cycle-counts", json={
        "warehouse_id": wid, "notes": "Monthly count",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "DRAFT"
    assert resp.json()["session_number"].startswith("CC-")


def test_cycle_count_list_sessions(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "cc-list@example.com")
    client.post("/api/cycle-counts", json={"warehouse_id": wid}, headers={"Authorization": f"Bearer {token}"})
    resp = client.get("/api/cycle-counts", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_cycle_count_add_line(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "cc-addline@example.com")
    session = client.post("/api/cycle-counts", json={"warehouse_id": wid}, headers={"Authorization": f"Bearer {token}"})
    sid = session.json()["id"]
    resp = client.post(f"/api/cycle-counts/{sid}/lines", json={
        "product_id": pid, "location_id": lid,
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    assert resp.json()["system_quantity"] is not None


def test_cycle_count_update_line(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "cc-updline@example.com")
    session = client.post("/api/cycle-counts", json={"warehouse_id": wid}, headers={"Authorization": f"Bearer {token}"})
    sid = session.json()["id"]
    line = client.post(f"/api/cycle-counts/{sid}/lines", json={
        "product_id": pid, "location_id": lid,
    }, headers={"Authorization": f"Bearer {token}"})
    line_id = line.json()["id"]
    resp = client.patch(f"/api/cycle-counts/{sid}/lines/{line_id}", json={
        "counted_quantity": "42",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert Decimal(resp.json()["counted_quantity"]) == Decimal("42")
    assert resp.json()["variance"] is not None


def test_cycle_count_submit(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "cc-submit@example.com")
    session = client.post("/api/cycle-counts", json={"warehouse_id": wid}, headers={"Authorization": f"Bearer {token}"})
    sid = session.json()["id"]
    resp = client.post(f"/api/cycle-counts/{sid}/submit", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUBMITTED"
    assert resp.json()["submitted_at"] is not None


def test_cycle_count_reconcile_adjusts_stock(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "cc-recon@example.com")
    # Stock in first
    client.post("/api/inventory/stock-in", json={
        "product_id": pid, "warehouse_id": wid, "location_id": lid,
        "quantity": "100", "reference_type": "MANUAL", "idempotency_key": "cc-recon-setup",
    }, headers={"Authorization": f"Bearer {token}"})
    # Create session, add line, count, submit, reconcile
    session = client.post("/api/cycle-counts", json={"warehouse_id": wid}, headers={"Authorization": f"Bearer {token}"})
    sid = session.json()["id"]
    line = client.post(f"/api/cycle-counts/{sid}/lines", json={
        "product_id": pid, "location_id": lid,
    }, headers={"Authorization": f"Bearer {token}"})
    line_id = line.json()["id"]
    assert Decimal(line.json()["system_quantity"]) == Decimal("100")
    client.patch(f"/api/cycle-counts/{sid}/lines/{line_id}", json={"counted_quantity": "95"}, headers={"Authorization": f"Bearer {token}"})
    client.post(f"/api/cycle-counts/{sid}/submit", headers={"Authorization": f"Bearer {token}"})
    resp = client.post(f"/api/cycle-counts/{sid}/reconcile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "RECONCILED"
    # Verify stock was adjusted
    stock_resp = client.get("/api/inventory/stock", headers={"Authorization": f"Bearer {token}"})
    stocks = stock_resp.json()
    matching = [s for s in stocks if s["product_id"] == pid and s["warehouse_id"] == wid]
    assert len(matching) == 1
    assert Decimal(matching[0]["quantity_on_hand"]) == Decimal("95")


def test_cycle_count_reconcile_requires_submitted_state(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "cc-recon-fail@example.com")
    session = client.post("/api/cycle-counts", json={"warehouse_id": wid}, headers={"Authorization": f"Bearer {token}"})
    sid = session.json()["id"]
    resp = client.post(f"/api/cycle-counts/{sid}/reconcile", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409


# ─── Expire Batches ──────────────────────────────────────────────────────────

def test_expire_batches_marks_expired(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "exp-batch@example.com")
    # Enable expiry tracking on the product
    from app.models.master_data import Product
    prod = db_session.get(Product, pid)
    prod.track_expiry = True
    db_session.commit()
    # Stock in with a batch that has past expiry
    client.post("/api/inventory/stock-in", json={
        "product_id": pid, "warehouse_id": wid, "location_id": lid,
        "quantity": "50", "reference_type": "MANUAL", "idempotency_key": "exp-setup-1",
        "batch_number": "EXP-001", "expiry_date": "2020-01-01",
    }, headers={"Authorization": f"Bearer {token}"})
    resp = client.post("/api/cycle-counts/expire-batches", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["expired_count"] >= 1


def test_expire_batches_no_expired_returns_zero(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "exp-none@example.com")
    resp = client.post("/api/cycle-counts/expire-batches", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["expired_count"] == 0


# ─── Outbox Events ───────────────────────────────────────────────────────────

def test_outbox_event_publish(db_session: Session) -> None:
    from app.events.outbox import publish_event
    event = publish_event(db_session, None, "test.event", {"key": "value"})
    db_session.commit()
    assert event.id is not None
    assert event.event_type == "test.event"
    assert event.status.value == "PENDING"


def test_outbox_event_mark_processed(db_session: Session) -> None:
    from app.events.outbox import publish_event
    from app.repositories.operations import OutboxRepository
    event = publish_event(db_session, None, "test.processed", {"data": 1})
    db_session.commit()
    repo = OutboxRepository(db_session)
    pending = repo.list_pending()
    assert any(e.id == event.id for e in pending)
    repo.mark_processed(event)
    db_session.commit()
    assert event.status.value == "PROCESSED"
    assert event.processed_at is not None


# ─── Stock State Expansion ───────────────────────────────────────────────────

def test_warehouse_stock_has_expanded_fields(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "stock-exp@example.com")
    client.post("/api/inventory/stock-in", json={
        "product_id": pid, "warehouse_id": wid, "location_id": lid,
        "quantity": "10", "reference_type": "MANUAL", "idempotency_key": "stock-exp-1",
    }, headers={"Authorization": f"Bearer {token}"})
    resp = client.get("/api/inventory/stock", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    stocks = resp.json()
    assert len(stocks) >= 1
    s = stocks[0]
    assert "quantity_in_transit" in s
    assert "quantity_qc_hold" in s
    assert "quantity_damaged" in s
    assert "quantity_expired" in s
    assert "quantity_quarantine" in s


# ─── Putaway completed cannot be cancelled ───────────────────────────────────

def test_putaway_completed_cannot_be_cancelled(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "pt-no-cancel@example.com")
    create = client.post("/api/putaway-tasks", json={
        "product_id": pid, "warehouse_id": wid,
        "from_location_id": lid, "quantity": "10",
    }, headers={"Authorization": f"Bearer {token}"})
    task_id = create.json()["id"]
    client.post(f"/api/putaway-tasks/{task_id}/complete", headers={"Authorization": f"Bearer {token}"})
    resp = client.post(f"/api/putaway-tasks/{task_id}/cancel", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 409


# ─── Reorder rule not found ──────────────────────────────────────────────────

def test_reorder_rule_not_found(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "rr-404@example.com")
    resp = client.get("/api/reorder-rules/99999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


# ─── Cycle count get session ─────────────────────────────────────────────────

def test_cycle_count_get_session(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "cc-get@example.com")
    session = client.post("/api/cycle-counts", json={"warehouse_id": wid}, headers={"Authorization": f"Bearer {token}"})
    sid = session.json()["id"]
    resp = client.get(f"/api/cycle-counts/{sid}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == sid


# ─── Putaway filter by status ────────────────────────────────────────────────

def test_putaway_filter_by_status(client: TestClient, db_session: Session) -> None:
    token, tid, pid, wid, lid, uid = _setup(db_session, client, "pt-filter@example.com")
    client.post("/api/putaway-tasks", json={
        "product_id": pid, "warehouse_id": wid,
        "from_location_id": lid, "quantity": "10",
    }, headers={"Authorization": f"Bearer {token}"})
    resp = client.get("/api/putaway-tasks?status=PENDING", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    for task in resp.json():
        assert task["status"] == "PENDING"
