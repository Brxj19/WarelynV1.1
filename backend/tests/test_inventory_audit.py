import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.audit import AuditLog
from app.models.auth import Tenant, User, UserRole, UserStatus


def create_tenant_admin(db_session: Session, client: TestClient, email: str = "admin@x.com") -> tuple[str, int]:
    tenant = Tenant(company_name="InvAuditCo", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id,
        name="Admin",
        email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id


def setup_dimension(client, token):
    headers = {"Authorization": f"Bearer {token}"}
    product = client.post("/api/catalog/products", json={"name": "AuditWidget", "sku": f"AUD-{token[:6]}"}, headers=headers)
    warehouse = client.post("/api/warehouses", json={"name": "AuditWH", "code": f"AWH{token[:6]}"}, headers=headers)
    assert product.status_code == 201
    assert warehouse.status_code == 201
    location = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Aisle 1", "code": "A1"}, headers=headers)
    assert location.status_code == 201
    return {"product_id": product.json()["id"], "warehouse_id": warehouse.json()["id"], "location_id": location.json()["id"]}


def test_stock_in_mutation_creates_audit_log(db_session: Session, client: TestClient) -> None:
    token, tid = create_tenant_admin(db_session, client)
    headers = {"Authorization": f"Bearer {token}"}
    dim = setup_dimension(client, token)
    client.post("/api/inventory/stock-in", json={**dim, "quantity": "10", "idempotency_key": "audit-si-1"}, headers=headers)
    logs = db_session.query(AuditLog).filter(AuditLog.action == "STOCK_IN").all()
    assert len(logs) >= 1
    assert logs[0].tenant_id == tid


def test_adjust_stock_mutation_creates_audit_log(db_session: Session, client: TestClient) -> None:
    token, tid = create_tenant_admin(db_session, client)
    headers = {"Authorization": f"Bearer {token}"}
    dim = setup_dimension(client, token)
    client.post("/api/inventory/stock-in", json={**dim, "quantity": "10", "idempotency_key": "audit-adj-si"}, headers=headers)
    client.post("/api/inventory/adjust", json={**dim, "delta": "5", "note": "adjust", "idempotency_key": "audit-adj-1"}, headers=headers)
    logs = db_session.query(AuditLog).filter(AuditLog.action == "STOCK_ADJUST").all()
    assert len(logs) >= 1
    assert logs[0].tenant_id == tid


def test_audit_log_metadata_captures_movement_details(db_session: Session, client: TestClient) -> None:
    token, tid = create_tenant_admin(db_session, client)
    headers = {"Authorization": f"Bearer {token}"}
    dim = setup_dimension(client, token)
    client.post("/api/inventory/stock-in", json={**dim, "quantity": "7", "idempotency_key": "audit-meta-1"}, headers=headers)
    log = db_session.query(AuditLog).filter(AuditLog.action == "STOCK_IN").order_by(AuditLog.created_at.desc()).first()
    assert log is not None
    meta = json.loads(log.metadata_json) if log.metadata_json else {}
    assert str(dim["product_id"]) == str(meta.get("product_id"))
    assert str(dim["warehouse_id"]) == str(meta.get("warehouse_id"))
    assert str(dim["location_id"]) == str(meta.get("location_id"))
    assert meta.get("quantity") == "7"
    assert meta.get("movement_type") == "STOCK_IN"
