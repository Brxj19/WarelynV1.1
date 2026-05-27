"""Phase 23 — Email toolbar, preferred template wiring, PDF fallback tests."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.services.pdf_service import _extract_all_tables, _extract_block_text, _fallback_pdf, render_html_to_pdf


def _setup(db_session: Session, client: TestClient, email: str = "p23@example.com"):
    tenant = Tenant(company_name="Phase23Co", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P23User", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id, user.id


def test_pdf_fallback_extracts_table_rows():
    html = """<table><tr><td>Product A</td><td>10</td><td>$50.00</td></tr>
    <tr><td>Product B</td><td>5</td><td>$100.00</td></tr></table>"""
    sections = _extract_all_tables(html)
    lines = [line for section in sections for line in section]
    assert len(lines) == 2
    assert "Product A" in lines[0]
    assert "Product B" in lines[1]


def test_pdf_fallback_extracts_paragraphs():
    html = "<p>Invoice INV-00001</p><p>Total: $1,180.00</p>"
    lines = _extract_block_text(html)
    assert len(lines) == 2
    assert "INV-00001" in lines[0]
    assert "$1,180.00" in lines[1]


def test_pdf_fallback_produces_valid_pdf():
    html = "<h1>Test Invoice</h1><p>Amount: $500</p>"
    pdf_bytes = _fallback_pdf(html)
    assert pdf_bytes[:5] == b"%PDF-"
    assert b"%%EOF" in pdf_bytes


def test_render_html_to_pdf_returns_bytes():
    html = "<html><body><h1>Hello</h1></body></html>"
    result = render_html_to_pdf(html)
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result[:5] == b"%PDF-"


def test_pdf_fallback_a4_mediabox():
    html = "<p>Test</p>"
    pdf_bytes = _fallback_pdf(html)
    assert b"595 842" in pdf_bytes


def test_preferred_template_used_in_pdf_render(client: TestClient, db_session: Session):
    token, tenant_id, user_id = _setup(db_session, client, "pref-pdf@example.com")
    tpl_resp = client.get("/api/document-templates?channel=PDF", headers={"Authorization": f"Bearer {token}"})
    assert tpl_resp.status_code == 200
    templates = tpl_resp.json()
    assert len(templates) > 0
    # Pick an INVOICE_PDF template for the invoice preference
    invoice_tpl = next(t for t in templates if t.get("purpose") == "INVOICE_PDF")
    client.patch(
        "/api/settings/preferences",
        json={"preferred_invoice_template_id": invoice_tpl["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    prefs_resp = client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    assert prefs_resp.json()["preferred_invoice_template_id"] == invoice_tpl["id"]


def test_preferred_email_template_stored(client: TestClient, db_session: Session):
    token, tenant_id, user_id = _setup(db_session, client, "pref-email@example.com")
    tpl_resp = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    assert tpl_resp.status_code == 200
    templates = tpl_resp.json()
    assert len(templates) > 0
    # Pick an INVOICE_EMAIL template for the invoice email preference
    invoice_email_tpl = next(t for t in templates if t.get("purpose") == "INVOICE_EMAIL")
    resp = client.patch(
        "/api/settings/preferences",
        json={"preferred_invoice_email_template_id": invoice_email_tpl["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["preferred_invoice_email_template_id"] == invoice_email_tpl["id"]


def test_template_preview_renders_with_sample_data(client: TestClient, db_session: Session):
    token, tenant_id, _ = _setup(db_session, client, "preview-render@example.com")
    tpl_resp = client.get("/api/document-templates?channel=PDF", headers={"Authorization": f"Bearer {token}"})
    templates = tpl_resp.json()
    assert len(templates) > 0
    invoice_tpl = next((t for t in templates if "INVOICE" in (t.get("template_key") or "")), templates[0])
    preview_resp = client.post(
        f"/api/document-templates/{invoice_tpl['id']}/preview",
        json={"variables": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert preview_resp.status_code == 200
    body = preview_resp.json()["body"]
    assert "Sample Company" in body or "INV-00001" in body or "BILL-00001" in body
