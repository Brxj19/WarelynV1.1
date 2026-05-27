"""Tests for user-defined templates with strict purpose validation."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.documents import DocumentTemplate, DocumentTemplatePurpose
from app.models.settings import UserPreferences


def _setup(db_session: Session, client: TestClient, email: str = "custom-tpl@example.com"):
    """Create a tenant + admin user and return (token, tenant_id, user_id)."""
    tenant = Tenant(company_name="CustomTplCo", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="TplUser", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    data = login.json()
    return data["access_token"], tenant.id, data["user"]["id"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── Create Custom Template ─────────────────────────────────────────────────


def test_create_custom_template_with_valid_purpose_channel(client: TestClient, db_session: Session) -> None:
    token, tenant_id, user_id = _setup(db_session, client, "create-valid@example.com")
    resp = client.post(
        "/api/document-templates",
        json={
            "name": "My Invoice PDF",
            "purpose": "INVOICE_PDF",
            "body_template": "<html><body>Custom Invoice</body></html>",
            "description": "A custom invoice template",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Invoice PDF"
    assert data["purpose"] == "INVOICE_PDF"
    assert data["channel"] == "PDF"
    assert data["is_system"] is False
    assert data["created_by"] == user_id
    assert data["template_code"].startswith("CUSTOM_INVOICE_PDF_")
    assert data["description"] == "A custom invoice template"


def test_create_custom_email_template(client: TestClient, db_session: Session) -> None:
    token, tenant_id, user_id = _setup(db_session, client, "create-email@example.com")
    resp = client.post(
        "/api/document-templates",
        json={
            "name": "My Invoice Email",
            "purpose": "INVOICE_EMAIL",
            "subject_template": "Invoice {{ invoice_number }}",
            "body_template": "<html><body>Hello {{ customer_name }}</body></html>",
            "body_template_text": "Hello {{ customer_name }}",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["channel"] == "EMAIL"
    assert data["purpose"] == "INVOICE_EMAIL"
    assert data["is_system"] is False


def test_create_custom_template_rejects_invalid_purpose(client: TestClient, db_session: Session) -> None:
    token, _, _ = _setup(db_session, client, "create-invalid@example.com")
    resp = client.post(
        "/api/document-templates",
        json={
            "name": "Bad Template",
            "purpose": "INVALID_PURPOSE",
            "body_template": "<html><body>Bad</body></html>",
        },
        headers=_headers(token),
    )
    assert resp.status_code == 400
    assert "INVALID_TEMPLATE_PURPOSE" in resp.json()["error"]["code"]


# ─── Duplicate Template ──────────────────────────────────────────────────────


def test_duplicate_system_template(client: TestClient, db_session: Session) -> None:
    token, tenant_id, user_id = _setup(db_session, client, "dup-system@example.com")
    # List templates to get a system template
    listed = client.get("/api/document-templates?channel=PDF", headers=_headers(token))
    assert listed.status_code == 200
    system_tpl = listed.json()[0]
    assert system_tpl["is_system"] is True

    resp = client.post(
        f"/api/document-templates/{system_tpl['id']}/duplicate",
        json={"name": "My Copy of System Template", "description": "Duplicated for customization"},
        headers=_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My Copy of System Template"
    assert data["is_system"] is False
    assert data["created_by"] == user_id
    assert data["cloned_from_template_id"] == system_tpl["id"]
    assert data["purpose"] == system_tpl["purpose"]
    assert data["channel"] == system_tpl["channel"]
    assert data["template_code"].startswith("CUSTOM_")


# ─── Delete Template ─────────────────────────────────────────────────────────


def test_delete_custom_template(client: TestClient, db_session: Session) -> None:
    token, tenant_id, user_id = _setup(db_session, client, "del-custom@example.com")
    # Create a custom template first
    created = client.post(
        "/api/document-templates",
        json={"name": "To Delete", "purpose": "BILL_PDF", "body_template": "<html>Delete me</html>"},
        headers=_headers(token),
    )
    assert created.status_code == 201
    template_id = created.json()["id"]

    resp = client.delete(f"/api/document-templates/{template_id}", headers=_headers(token))
    assert resp.status_code == 204

    # Verify it's gone
    get_resp = client.get(f"/api/document-templates/{template_id}", headers=_headers(token))
    assert get_resp.status_code == 404


def test_cannot_delete_system_template(client: TestClient, db_session: Session) -> None:
    token, _, _ = _setup(db_session, client, "del-system@example.com")
    listed = client.get("/api/document-templates?channel=PDF", headers=_headers(token))
    system_tpl = [t for t in listed.json() if t["is_system"]][0]

    resp = client.delete(f"/api/document-templates/{system_tpl['id']}", headers=_headers(token))
    assert resp.status_code == 400
    assert "CANNOT_DELETE_SYSTEM_TEMPLATE" in resp.json()["error"]["code"]


def test_cannot_delete_template_in_use_by_preference(client: TestClient, db_session: Session) -> None:
    token, tenant_id, user_id = _setup(db_session, client, "del-inuse@example.com")
    # Create a custom template
    created = client.post(
        "/api/document-templates",
        json={"name": "In Use Template", "purpose": "INVOICE_PDF", "body_template": "<html>In use</html>"},
        headers=_headers(token),
    )
    assert created.status_code == 201
    template_id = created.json()["id"]

    # Set it as a preference
    prefs = db_session.query(UserPreferences).filter_by(user_id=user_id).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user_id)
        db_session.add(prefs)
    prefs.preferred_invoice_template_id = template_id
    db_session.commit()

    # Try to delete
    resp = client.delete(f"/api/document-templates/{template_id}", headers=_headers(token))
    assert resp.status_code == 400
    assert "TEMPLATE_IN_USE" in resp.json()["error"]["code"]


# ─── List Templates Filtered by Purpose ──────────────────────────────────────


def test_list_templates_filtered_by_purpose(client: TestClient, db_session: Session) -> None:
    token, _, _ = _setup(db_session, client, "list-purpose@example.com")
    resp = client.get("/api/document-templates?purpose=INVOICE_PDF", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5  # 5 system invoice PDF templates
    for t in data:
        assert t["purpose"] == "INVOICE_PDF"
        assert t["channel"] == "PDF"


def test_list_templates_filtered_by_email_verification_purpose(client: TestClient, db_session: Session) -> None:
    token, _, _ = _setup(db_session, client, "list-verif@example.com")
    resp = client.get("/api/document-templates?purpose=EMAIL_VERIFICATION", headers=_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3  # 3 system verification templates
    for t in data:
        assert t["purpose"] == "EMAIL_VERIFICATION"
        assert t["channel"] == "EMAIL"


# ─── Preference Validation Rejects Wrong Purpose ─────────────────────────────


def test_preference_validation_rejects_wrong_purpose(client: TestClient, db_session: Session) -> None:
    token, tenant_id, user_id = _setup(db_session, client, "pref-reject@example.com")
    # Get a BILL_PDF template
    listed = client.get("/api/document-templates?purpose=BILL_PDF", headers=_headers(token))
    bill_tpl = listed.json()[0]

    # Try to set it as invoice PDF preference (wrong purpose)
    resp = client.patch(
        "/api/settings/preferences",
        json={"preferred_invoice_template_id": bill_tpl["id"]},
        headers=_headers(token),
    )
    assert resp.status_code == 400
    assert "TEMPLATE_PURPOSE_MISMATCH" in resp.json()["error"]["code"]


def test_preference_validation_accepts_correct_purpose(client: TestClient, db_session: Session) -> None:
    token, tenant_id, user_id = _setup(db_session, client, "pref-accept@example.com")
    # Get an INVOICE_PDF template
    listed = client.get("/api/document-templates?purpose=INVOICE_PDF", headers=_headers(token))
    invoice_tpl = listed.json()[0]

    # Set it as invoice PDF preference (correct purpose)
    resp = client.patch(
        "/api/settings/preferences",
        json={"preferred_invoice_template_id": invoice_tpl["id"]},
        headers=_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["preferred_invoice_template_id"] == invoice_tpl["id"]


# ─── Cross-Tenant Isolation ──────────────────────────────────────────────────


def test_cross_tenant_isolation(client: TestClient, db_session: Session) -> None:
    token_a, tenant_a, _ = _setup(db_session, client, "tenant-a-iso@example.com")
    token_b, tenant_b, _ = _setup(db_session, client, "tenant-b-iso@example.com")

    # Create a custom template in tenant A
    created = client.post(
        "/api/document-templates",
        json={"name": "Tenant A Only", "purpose": "INVOICE_PDF", "body_template": "<html>A only</html>"},
        headers=_headers(token_a),
    )
    assert created.status_code == 201
    template_id = created.json()["id"]

    # Tenant B cannot see it
    resp = client.get(f"/api/document-templates/{template_id}", headers=_headers(token_b))
    assert resp.status_code == 404

    # Tenant B cannot delete it
    resp = client.delete(f"/api/document-templates/{template_id}", headers=_headers(token_b))
    assert resp.status_code == 404


# ─── Invoice PDF Uses Correct Template ───────────────────────────────────────


def test_invoice_pdf_uses_correct_purpose_template(client: TestClient, db_session: Session) -> None:
    """Invoice PDF rendering uses a template with purpose=INVOICE_PDF."""
    from app.services.documents import DocumentsService

    token, tenant_id, user_id = _setup(db_session, client, "inv-purpose@example.com")

    # Seed templates
    svc = DocumentsService(db_session)
    svc.templates._ensure_defaults(tenant_id)

    # Verify all invoice PDF templates have correct purpose
    templates = db_session.query(DocumentTemplate).filter_by(
        tenant_id=tenant_id, purpose=DocumentTemplatePurpose.INVOICE_PDF
    ).all()
    assert len(templates) == 5
    for t in templates:
        assert t.channel.value == "PDF"
        assert t.purpose == DocumentTemplatePurpose.INVOICE_PDF


def test_bill_pdf_uses_correct_purpose_template(client: TestClient, db_session: Session) -> None:
    """Bill PDF rendering uses a template with purpose=BILL_PDF."""
    from app.services.documents import DocumentsService

    token, tenant_id, user_id = _setup(db_session, client, "bill-purpose@example.com")

    # Seed templates
    svc = DocumentsService(db_session)
    svc.templates._ensure_defaults(tenant_id)

    # Verify all bill PDF templates have correct purpose
    templates = db_session.query(DocumentTemplate).filter_by(
        tenant_id=tenant_id, purpose=DocumentTemplatePurpose.BILL_PDF
    ).all()
    assert len(templates) == 5
    for t in templates:
        assert t.channel.value == "PDF"
        assert t.purpose == DocumentTemplatePurpose.BILL_PDF


# ─── Purpose/Channel Mismatch on Create ─────────────────────────────────────


def test_purpose_determines_channel_automatically(client: TestClient, db_session: Session) -> None:
    """Creating a template with purpose=INVOICE_PDF automatically sets channel=PDF."""
    token, _, _ = _setup(db_session, client, "auto-channel@example.com")
    resp = client.post(
        "/api/document-templates",
        json={"name": "Auto Channel", "purpose": "BILL_EMAIL", "body_template": "<html>Email</html>"},
        headers=_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["channel"] == "EMAIL"
    assert resp.json()["purpose"] == "BILL_EMAIL"


# ─── System Templates Are Seeded With Correct Purpose ────────────────────────


def test_system_templates_seeded_with_correct_purpose(client: TestClient, db_session: Session) -> None:
    token, tenant_id, _ = _setup(db_session, client, "seed-purpose@example.com")
    # Trigger seeding by listing
    client.get("/api/document-templates", headers=_headers(token))

    # Check all templates have purpose set
    all_templates = db_session.query(DocumentTemplate).filter_by(tenant_id=tenant_id).all()
    assert len(all_templates) == 26  # 26 system templates

    for t in all_templates:
        assert t.is_system is True
        assert t.purpose is not None
        assert t.template_code is not None
        assert t.template_code == t.template_key.value


def test_system_templates_have_template_code_matching_key(client: TestClient, db_session: Session) -> None:
    token, tenant_id, _ = _setup(db_session, client, "code-key@example.com")
    client.get("/api/document-templates", headers=_headers(token))

    templates = db_session.query(DocumentTemplate).filter_by(tenant_id=tenant_id, is_system=True).all()
    for t in templates:
        assert t.template_code == t.template_key.value
