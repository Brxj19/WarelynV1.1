from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, TenantStatus, User, UserRole, UserStatus
from app.utils.currency import validate_currency_code


class TestValidateCurrencyCode:
    def test_valid_usd(self):
        assert validate_currency_code("USD") is True

    def test_valid_lowercase(self):
        assert validate_currency_code("usd") is True

    def test_invalid_xyz(self):
        assert validate_currency_code("XYZ") is False

    def test_empty_string(self):
        assert validate_currency_code("") is False


def _create_tenant_and_admin(db: Session) -> tuple[Tenant, User]:
    tenant = Tenant(company_name="Currency Corp", contact_email="cur@test.com", status=TenantStatus.ACTIVE)
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        name="Admin",
        email="admin@currency.com",
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    return tenant, user


def _login(client: TestClient, email: str) -> str:
    resp = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestCurrencySettingsAPI:
    def test_patch_settings_invalid_currency_returns_422(self, client: TestClient, db_session: Session):
        resp = client.post("/api/auth/register", json={"company_name": "CurTest", "name": "Admin", "email": "admin@currency.com", "password": "StrongPass123!"})
        assert resp.status_code == 201
        token = _login(client, "admin@currency.com")
        resp = client.patch("/api/settings/tenant", json={"currency": "XYZ"}, headers=_headers(token))
        assert resp.status_code == 422

    def test_patch_settings_valid_currency_succeeds(self, client: TestClient, db_session: Session):
        resp = client.post("/api/auth/register", json={"company_name": "CurTest2", "name": "Admin", "email": "admin@currency.com", "password": "StrongPass123!"})
        assert resp.status_code == 201
        token = _login(client, "admin@currency.com")
        resp = client.patch("/api/settings/tenant", json={"currency": "EUR"}, headers=_headers(token))
        assert resp.status_code == 200
        assert resp.json()["currency"] == "EUR"


class TestInvoiceCurrencySnapshot:
    def test_invoice_snapshots_tenant_currency(self, client: TestClient, db_session: Session):
        resp = client.post("/api/auth/register", json={"company_name": "CurSnap", "name": "Admin", "email": "snap@currency.com", "password": "StrongPass123!"})
        assert resp.status_code == 201
        token = _login(client, "snap@currency.com")
        h = _headers(token)

        # Set tenant currency to GBP
        client.patch("/api/settings/tenant", json={"currency": "GBP"}, headers=h)

        customer = client.post("/api/catalog/customers", json={"name": "Cust", "email": "cust@snap.com"}, headers=h)
        product = client.post("/api/catalog/products", json={"name": "Prod", "sku": "CUR-1"}, headers=h)
        assert customer.status_code == 201
        assert product.status_code == 201

        # Create a sales order
        order = client.post("/api/sales-orders", json={
            "customer_id": customer.json()["id"],
            "order_number": "SO-CUR-1",
            "order_date": "2026-05-28",
            "items": [{"product_id": product.json()["id"], "ordered_quantity": "2", "unit_price": "5.00"}],
        }, headers=h)
        assert order.status_code == 201
        so = order.json()

        # Create invoice (no explicit currency — should snapshot tenant's GBP)
        inv_resp = client.post("/api/invoices", json={"sales_order_id": so["id"]}, headers=h)
        assert inv_resp.status_code == 201
        inv = inv_resp.json()
        assert inv["currency"] == "GBP"

        # Change tenant currency to JPY
        client.patch("/api/settings/tenant", json={"currency": "JPY"}, headers=h)

        # Invoice should still be GBP
        inv_detail = client.get(f"/api/invoices/{inv['id']}", headers=h)
        assert inv_detail.status_code == 200
        assert inv_detail.json()["currency"] == "GBP"
