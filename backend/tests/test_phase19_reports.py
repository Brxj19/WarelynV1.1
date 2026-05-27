"""Phase 19 — reports null guard regression tests."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus


def _setup(db_session: Session, client: TestClient, email: str = "p19@example.com"):
    tenant = Tenant(company_name="P19Co", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P19User", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"]


def test_inventory_summary_endpoint_returns_expected_keys(client: TestClient, db_session: Session) -> None:
    token = _setup(db_session, client, "p19-inv-sum@example.com")
    r = client.get("/api/reports/inventory-summary", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "total_products" in data
    assert "active_products" in data
    assert "total_on_hand_quantity" in data


def test_warehouse_stock_endpoint_returns_list(client: TestClient, db_session: Session) -> None:
    token = _setup(db_session, client, "p19-wh-stock@example.com")
    r = client.get("/api/reports/warehouse-stock", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_low_stock_endpoint_returns_list(client: TestClient, db_session: Session) -> None:
    token = _setup(db_session, client, "p19-low-stock@example.com")
    r = client.get("/api/reports/low-stock", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_reconciliation_endpoint_returns_object_with_mismatches(client: TestClient, db_session: Session) -> None:
    token = _setup(db_session, client, "p19-recon@example.com")
    r = client.get("/api/reports/reconciliation", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "mismatches" in data
    assert "mismatch_count" in data
