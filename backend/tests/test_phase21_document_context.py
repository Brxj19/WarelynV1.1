"""Phase 21 — PDF context fixes and XLSX download tests."""
from datetime import date
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.services.imports import ProductImportService


def _setup(db_session: Session, client: TestClient, email: str = "p21@example.com"):
    tenant = Tenant(company_name="Phase21Co", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P21User", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id


def test_invoice_item_tax_rate_computed_from_tax_amount(client: TestClient, db_session: Session) -> None:
    """Invoice context should compute tax_rate from tax_amount/subtotal."""
    from app.models.documents import Invoice, InvoiceItem, InvoiceStatus
    from app.services.documents import DocumentsService

    token, tenant_id = _setup(db_session, client, "tax-rate@example.com")

    from app.models.master_data import Customer, Product
    customer = Customer(tenant_id=tenant_id, name="TaxCust", email="c@c.com")
    db_session.add(customer)
    db_session.flush()
    product = Product(tenant_id=tenant_id, name="TaxProd", sku="TAX-001", unit="pcs")
    db_session.add(product)
    db_session.flush()

    invoice = Invoice(
        tenant_id=tenant_id, customer_id=customer.id, invoice_number="INV-TAX-001",
        status=InvoiceStatus.DRAFT, issue_date=date(2026, 5, 25),
        subtotal_amount=Decimal("1000.00"), tax_amount=Decimal("180.00"),
        discount_amount=Decimal("0.00"), total_amount=Decimal("1180.00"),
        created_by=1,
    )
    db_session.add(invoice)
    db_session.flush()
    item = InvoiceItem(
        tenant_id=tenant_id, invoice_id=invoice.id, product_id=product.id,
        description="TaxProd", quantity=Decimal("10"), unit_price=Decimal("100.00"),
        line_total=Decimal("1000.00"),
    )
    db_session.add(item)
    db_session.commit()

    svc = DocumentsService(db_session)
    ctx = svc._invoice_context(invoice)
    assert ctx["items"][0]["tax_rate"] == "18.0"


def test_invoice_item_tax_rate_zero_when_no_tax(client: TestClient, db_session: Session) -> None:
    """Items with zero tax_amount should render tax_rate as 0."""
    from app.models.documents import Invoice, InvoiceItem, InvoiceStatus
    from app.services.documents import DocumentsService

    token, tenant_id = _setup(db_session, client, "no-tax@example.com")

    from app.models.master_data import Customer, Product
    customer = Customer(tenant_id=tenant_id, name="NoTaxCust", email="nt@c.com")
    db_session.add(customer)
    db_session.flush()
    product = Product(tenant_id=tenant_id, name="NoTaxProd", sku="NOTAX-001", unit="pcs")
    db_session.add(product)
    db_session.flush()

    invoice = Invoice(
        tenant_id=tenant_id, customer_id=customer.id, invoice_number="INV-NOTAX-001",
        status=InvoiceStatus.DRAFT, issue_date=date(2026, 5, 25),
        subtotal_amount=Decimal("500.00"), tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"), total_amount=Decimal("500.00"),
        created_by=1,
    )
    db_session.add(invoice)
    db_session.flush()
    item = InvoiceItem(
        tenant_id=tenant_id, invoice_id=invoice.id, product_id=product.id,
        description="NoTaxProd", quantity=Decimal("5"), unit_price=Decimal("100.00"),
        line_total=Decimal("500.00"),
    )
    db_session.add(item)
    db_session.commit()

    svc = DocumentsService(db_session)
    ctx = svc._invoice_context(invoice)
    assert ctx["items"][0]["tax_rate"] == "0"


def test_xlsx_template_download_returns_200_with_valid_file(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "xlsx-200@example.com")
    r = client.get("/api/imports/products/template.xlsx", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_xlsx_template_has_all_required_header_columns(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "xlsx-headers@example.com")
    r = client.get("/api/imports/products/template.xlsx", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    zf = ZipFile(BytesIO(r.content))
    names = zf.namelist()
    assert "[Content_Types].xml" in names
    assert any("sheet" in n for n in names)
    sheet_content = ""
    for name in names:
        if "sheet" in name:
            sheet_content = zf.read(name).decode("utf-8", errors="ignore")
    for required in ["name", "sku", "unit"]:
        assert required in sheet_content or required.upper() in sheet_content


def test_xlsx_template_has_sample_row(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "xlsx-sample@example.com")
    r = client.get("/api/imports/products/template.xlsx", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    zf = ZipFile(BytesIO(r.content))
    all_content = ""
    for name in zf.namelist():
        all_content += zf.read(name).decode("utf-8", errors="ignore")
    assert "Sample Product" in all_content or "SKU-001" in all_content


def test_xlsx_template_content_disposition(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "xlsx-disp@example.com")
    r = client.get("/api/imports/products/template.xlsx", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert "products-import-template.xlsx" in r.headers.get("content-disposition", "")


def test_build_template_xlsx_static_method_returns_bytes() -> None:
    result = ProductImportService.build_template_xlsx()
    assert isinstance(result, bytes)
    assert len(result) > 100


def test_document_repository_get_location_returns_none_for_nonexistent(db_session: Session) -> None:
    from app.repositories.documents import DocumentsRepository
    from app.models.auth import Tenant
    tenant = Tenant(company_name="LocTestCo", contact_email="loc@test.com")
    db_session.add(tenant)
    db_session.commit()
    repo = DocumentsRepository(db_session)
    result = repo.get_location(tenant.id, 999999)
    assert result is None


def test_document_repository_get_warehouse_returns_none_for_nonexistent(db_session: Session) -> None:
    from app.repositories.documents import DocumentsRepository
    from app.models.auth import Tenant
    tenant = Tenant(company_name="WhTestCo", contact_email="wh@test.com")
    db_session.add(tenant)
    db_session.commit()
    repo = DocumentsRepository(db_session)
    result = repo.get_warehouse(tenant.id, 999999)
    assert result is None
