"""Phase 20 — Branded Email + PDF Templates tests."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.documents import DocumentTemplate, DocumentTemplateChannel, DocumentTemplateKey
from app.services.default_templates import DEFAULT_TEMPLATES
from app.services.documents import DocumentTemplateService


def _setup(db_session: Session, client: TestClient, email: str = "p20@example.com"):
    tenant = Tenant(company_name="Phase20Co", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P20User", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id


def test_default_templates_has_13_entries() -> None:
    assert len(DEFAULT_TEMPLATES) == 26


def test_all_pdf_templates_have_body() -> None:
    for (channel, key), payload in DEFAULT_TEMPLATES.items():
        if channel == DocumentTemplateChannel.PDF:
            assert payload["body_template"] is not None, f"{key} has no body_template"
            assert len(payload["body_template"]) > 100, f"{key} body_template too short"


def test_ensure_defaults_seeds_all_13(client: TestClient, db_session: Session) -> None:
    token, tenant_id = _setup(db_session, client, "seed13@example.com")
    resp = client.get("/api/document-templates", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    templates = resp.json()
    assert len(templates) == 26
    pdf_templates = [t for t in templates if t["channel"] == "PDF"]
    assert len(pdf_templates) == 10


def test_pdf_template_variants_exist(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "variants@example.com")
    resp = client.get("/api/document-templates?channel=PDF", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    names = {t["template_key"] for t in resp.json()}
    expected = {
        "PDF_INVOICE", "PDF_INVOICE_MODERN", "PDF_INVOICE_MINIMAL", "PDF_INVOICE_BOLD", "PDF_INVOICE_WARM",
        "PDF_BILL", "PDF_BILL_MODERN", "PDF_BILL_MINIMAL", "PDF_BILL_BOLD", "PDF_BILL_WARM",
    }
    assert expected.issubset(names)


def test_branded_email_template_renders_otp(client: TestClient, db_session: Session) -> None:
    token, tenant_id = _setup(db_session, client, "otp-render@example.com")
    resp = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    otp_tpl = next(t for t in resp.json() if t["template_key"] == "EMAIL_VERIFICATION")
    resp = client.post(
        f"/api/document-templates/{otp_tpl['id']}/preview",
        json={"variables": {"code": "123456", "purpose": "login", "ttl_minutes": "10"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()["body"]
    assert "123456" in body
    assert "linear-gradient" in body


def test_branded_email_template_renders_document(client: TestClient, db_session: Session) -> None:
    token, tenant_id = _setup(db_session, client, "doc-render@example.com")
    resp = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    inv_tpl = next(t for t in resp.json() if t["template_key"] == "INVOICE_SEND")
    resp = client.post(
        f"/api/document-templates/{inv_tpl['id']}/preview",
        json={"variables": {
            "title": "Invoice INV-00001",
            "sender_name": "TestCo",
            "intro": "Please find your invoice attached.",
            "document_kind": "Invoice",
            "document_number": "INV-00001",
            "notes": "Net 30",
        }},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()["body"]
    assert "INV-00001" in body
    assert "TestCo" in body
    assert "Net 30" in body


def test_custom_template_not_overwritten_on_reseed(client: TestClient, db_session: Session) -> None:
    token, tenant_id = _setup(db_session, client, "no-overwrite@example.com")
    # Seed defaults
    client.get("/api/document-templates", headers={"Authorization": f"Bearer {token}"})
    # Customize one
    resp = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    tpl = resp.json()[0]
    custom_body = "<p>Custom template body</p>"
    client.patch(
        f"/api/document-templates/{tpl['id']}",
        json={"body_template": custom_body},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Trigger ensure_defaults again via a new list call
    resp2 = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    found = next(t for t in resp2.json() if t["id"] == tpl["id"])
    assert found["body_template"] == custom_body


def test_modern_invoice_template_has_sidebar_layout() -> None:
    tpl = DEFAULT_TEMPLATES[(DocumentTemplateChannel.PDF, DocumentTemplateKey.PDF_INVOICE_MODERN)]
    body = tpl["body_template"]
    assert "sidebar" in body
    assert "Inventory Platform" in body
    assert "items" in body
