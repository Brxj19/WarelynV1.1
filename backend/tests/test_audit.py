from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.audit import AuditLog
from app.models.auth import Tenant, User, UserRole, UserStatus


def create_super_admin(db_session: Session, client: TestClient, email: str = "super@x.com") -> str:
    sa = User(
        name="Super",
        email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        tenant_id=None,
    )
    db_session.add(sa)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"]


def create_tenant_with_user(db_session: Session, client: TestClient, email: str = "tadmin@x.com") -> tuple[str, int]:
    tenant = Tenant(company_name="AuditTenant", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id,
        name="TAdmin",
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


def test_super_admin_can_list_audit_logs(db_session: Session, client: TestClient) -> None:
    sa_token = create_super_admin(db_session, client)
    response = client.get("/api/audit-logs", headers={"Authorization": f"Bearer {sa_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tenant_admin_can_list_own_tenant_audit_logs(db_session: Session, client: TestClient) -> None:
    token, tid = create_tenant_with_user(db_session, client)
    log = AuditLog(tenant_id=tid, action="TEST_ACTION", entity_type="test")
    db_session.add(log)
    db_session.commit()
    response = client.get("/api/audit-logs/tenant", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["action"] == "TEST_ACTION"


def test_settings_update_creates_audit_log(db_session: Session, client: TestClient) -> None:
    token, tid = create_tenant_with_user(db_session, client)
    client.patch("/api/settings/tenant", json={"company_display_name": "AuditTestCo"}, headers={"Authorization": f"Bearer {token}"})
    logs = db_session.query(AuditLog).filter(AuditLog.tenant_id == tid).all()
    assert any("company_display_name" in (log.metadata_json or "") for log in logs)


def test_inventory_stock_in_mutation_creates_audit_log(db_session: Session, client: TestClient) -> None:
    token, tid = create_tenant_with_user(db_session, client)
    headers = {"Authorization": f"Bearer {token}"}
    product = client.post("/api/catalog/products", json={"name": "AudWidget", "sku": "AUD-001"}, headers=headers)
    warehouse = client.post("/api/warehouses", json={"name": "AudWH", "code": "AWH"}, headers=headers)
    assert product.status_code == 201
    assert warehouse.status_code == 201
    loc = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "A1", "code": "A1"}, headers=headers)
    assert loc.status_code == 201
    dim = {"product_id": product.json()["id"], "warehouse_id": warehouse.json()["id"], "location_id": loc.json()["id"]}
    client.post("/api/inventory/stock-in", json={**dim, "quantity": "10", "idempotency_key": "aud-stock"}, headers=headers)
    logs = db_session.query(AuditLog).filter(AuditLog.action == "STOCK_IN").all()
    assert len(logs) >= 1
    assert logs[0].metadata_json is not None


def test_audit_log_contains_correct_metadata(db_session: Session, client: TestClient) -> None:
    token, tid = create_tenant_with_user(db_session, client)
    headers = {"Authorization": f"Bearer {token}"}
    product = client.post("/api/catalog/products", json={"name": "MetaWidget", "sku": "META-001"}, headers=headers).json()
    warehouse = client.post("/api/warehouses", json={"name": "MetaWH", "code": "MWH"}, headers=headers).json()
    loc = client.post(f"/api/warehouses/{warehouse['id']}/locations", json={"name": "A1", "code": "A1"}, headers=headers).json()
    dim = {"product_id": product["id"], "warehouse_id": warehouse["id"], "location_id": loc["id"]}
    client.post("/api/inventory/stock-in", json={**dim, "quantity": "5", "idempotency_key": "meta-stock"}, headers=headers)
    log = db_session.query(AuditLog).filter(AuditLog.action == "STOCK_IN").order_by(AuditLog.created_at.desc()).first()
    assert log is not None
    assert log.tenant_id == tid
    import json
    meta = json.loads(log.metadata_json) if log.metadata_json else {}
    assert str(product["id"]) == str(meta.get("product_id"))
    assert meta.get("quantity") == "5"


def test_audit_logs_do_not_change_stock(db_session: Session, client: TestClient) -> None:
    from app.models.inventory import WarehouseStock
    stock_before = db_session.query(WarehouseStock).count()
    token, tid = create_tenant_with_user(db_session, client)
    headers = {"Authorization": f"Bearer {token}"}
    product = client.post("/api/catalog/products", json={"name": "SafeWidget", "sku": "SAFE-001"}, headers=headers).json()
    warehouse = client.post("/api/warehouses", json={"name": "SafeWH", "code": "SWH"}, headers=headers).json()
    loc = client.post(f"/api/warehouses/{warehouse['id']}/locations", json={"name": "A1", "code": "A1"}, headers=headers).json()
    dim = {"product_id": product["id"], "warehouse_id": warehouse["id"], "location_id": loc["id"]}
    client.post("/api/inventory/stock-in", json={**dim, "quantity": "5", "idempotency_key": "safe-stock"}, headers=headers)
    stock_after = db_session.query(WarehouseStock).count()
    assert stock_after == stock_before + 1
    assert db_session.query(AuditLog).filter(AuditLog.action == "STOCK_IN").count() >= 1
