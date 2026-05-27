from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.documents import DocumentTemplate


def _setup(db_session: Session, client: TestClient, email: str = "p17b@example.com"):
    tenant = Tenant(company_name="P17BCo", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P17BUser", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id


def test_list_pdf_templates_returns_only_pdf_channel(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "list-pdf@example.com")
    resp = client.get("/api/document-templates?channel=PDF", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10
    for t in data:
        assert t["channel"] == "PDF"


def test_preview_pdf_template_returns_pdf_bytes(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "pdf-preview@example.com")
    listed = client.get("/api/document-templates?channel=PDF", headers={"Authorization": f"Bearer {token}"})
    template = listed.json()[0]
    resp = client.post(
        f"/api/document-templates/{template['id']}/preview-pdf",
        json={"variables": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert len(resp.content) > 100


def test_preview_pdf_template_uses_sample_data_for_missing_vars(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "pdf-sample@example.com")
    listed = client.get("/api/document-templates?channel=PDF", headers={"Authorization": f"Bearer {token}"})
    template = listed.json()[0]
    resp = client.post(
        f"/api/document-templates/{template['id']}/preview-pdf",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"


def test_preview_pdf_template_with_custom_html(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "pdf-custom@example.com")
    listed = client.get("/api/document-templates?channel=PDF", headers={"Authorization": f"Bearer {token}"})
    template = listed.json()[0]
    client.patch(
        f"/api/document-templates/{template['id']}",
        json={"body_template": "<html><body><h1>Custom {{ tenant.company_name }}</h1></body></html>"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.post(
        f"/api/document-templates/{template['id']}/preview-pdf",
        json={"variables": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.content[:5] == b"%PDF-"


def test_invoice_pdf_uses_stored_html_template(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "inv-stored@example.com")
    listed = client.get("/api/document-templates?channel=PDF", headers={"Authorization": f"Bearer {token}"})
    invoice_tpl = [t for t in listed.json() if t["template_key"] == "PDF_INVOICE"][0]
    assert "<html" in invoice_tpl["body_template"].lower()


def test_bill_pdf_uses_stored_html_template(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "bill-stored@example.com")
    listed = client.get("/api/document-templates?channel=PDF", headers={"Authorization": f"Bearer {token}"})
    bill_tpl = [t for t in listed.json() if t["template_key"] == "PDF_BILL"][0]
    assert "<html" in bill_tpl["body_template"].lower()
