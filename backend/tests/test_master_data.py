from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.inventory import WarehouseStock
from app.models.master_data import Product, WarehouseLocation


def register_and_login(client: TestClient, email: str = "admin@example.com") -> dict[str, object]:
    response = client.post(
        "/api/auth/register",
        json={"company_name": "Acme", "name": "Admin", "email": email, "password": "StrongPass123!"},
    )
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


def test_catalog_crud_is_tenant_scoped(client: TestClient) -> None:
    login_a = register_and_login(client, "admin-a@example.com")
    login_b = register_and_login(client, "admin-b@example.com")

    create = client.post("/api/catalog/categories", json={"name": "Electronics"}, headers=auth_headers(login_a["access_token"]))
    assert create.status_code == 201

    list_a = client.get("/api/catalog/categories", headers=auth_headers(login_a["access_token"]))
    list_b = client.get("/api/catalog/categories", headers=auth_headers(login_b["access_token"]))

    assert [category["name"] for category in list_a.json()] == ["Electronics"]
    assert list_b.json() == []


def test_duplicate_product_sku_blocked_per_tenant(client: TestClient) -> None:
    login = register_and_login(client)
    headers = auth_headers(login["access_token"])

    first = client.post("/api/catalog/products", json={"name": "Widget", "sku": "W-1"}, headers=headers)
    second = client.post("/api/catalog/products", json={"name": "Widget 2", "sku": "W-1"}, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_RECORD"


def test_viewer_can_read_but_not_write_catalog(client: TestClient, db_session: Session) -> None:
    admin = register_and_login(client)
    client.post("/api/catalog/products", json={"name": "Widget", "sku": "W-1"}, headers=auth_headers(admin["access_token"]))
    viewer_token = create_role_user(client, db_session, UserRole.VIEWER, "viewer@example.com")

    read = client.get("/api/catalog/products", headers=auth_headers(viewer_token))
    write = client.post("/api/catalog/products", json={"name": "Other", "sku": "O-1"}, headers=auth_headers(viewer_token))

    assert read.status_code == 200
    assert len(read.json()) == 1
    assert write.status_code == 403


def test_role_specific_catalog_read_access(client: TestClient, db_session: Session) -> None:
    register_and_login(client)
    sales_token = create_role_user(client, db_session, UserRole.SALES_STAFF, "sales@example.com")
    purchase_token = create_role_user(client, db_session, UserRole.PURCHASE_STAFF, "purchase@example.com")

    assert client.get("/api/catalog/customers", headers=auth_headers(sales_token)).status_code == 200
    assert client.get("/api/catalog/vendors", headers=auth_headers(sales_token)).status_code == 403
    assert client.get("/api/catalog/vendors", headers=auth_headers(purchase_token)).status_code == 200
    assert client.get("/api/catalog/customers", headers=auth_headers(purchase_token)).status_code == 403


def test_warehouse_and_locations_crud(client: TestClient) -> None:
    login = register_and_login(client)
    headers = auth_headers(login["access_token"])

    warehouse = client.post("/api/warehouses", json={"name": "Main", "code": "MAIN"}, headers=headers)
    assert warehouse.status_code == 201
    warehouse_id = warehouse.json()["id"]

    location = client.post(f"/api/warehouses/{warehouse_id}/locations", json={"name": "Aisle 1", "code": "A1"}, headers=headers)
    locations = client.get(f"/api/warehouses/{warehouse_id}/locations", headers=headers)

    assert location.status_code == 201
    assert locations.status_code == 200
    assert locations.json()[0]["code"] == "A1"


def test_product_and_warehouse_setup_does_not_create_stock_rows(client: TestClient, db_session: Session) -> None:
    login = register_and_login(client)
    headers = auth_headers(login["access_token"])

    product = client.post("/api/catalog/products", json={"name": "Widget", "sku": "W-1"}, headers=headers)
    warehouse = client.post("/api/warehouses", json={"name": "Main", "code": "MAIN"}, headers=headers)
    location = client.post(f"/api/warehouses/{warehouse.json()['id']}/locations", json={"name": "Aisle 1", "code": "A1"}, headers=headers)

    assert product.status_code == 201
    assert warehouse.status_code == 201
    assert location.status_code == 201
    assert db_session.query(Product).count() == 1
    assert db_session.query(WarehouseLocation).count() == 1
    assert db_session.query(WarehouseStock).count() == 0
