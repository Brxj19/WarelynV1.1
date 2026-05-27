"""Phase 22 — preferences template fields tests."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.documents import DocumentTemplate, DocumentTemplatePurpose


def _setup(db_session: Session, client: TestClient, email: str = "p22@example.com"):
    tenant = Tenant(company_name="Phase22Co", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P22User", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id


def _seed_templates(client: TestClient, token: str):
    """Trigger template seeding by listing templates."""
    client.get("/api/document-templates", headers={"Authorization": f"Bearer {token}"})


def _get_template_id_by_purpose(db_session: Session, tenant_id: int, purpose: DocumentTemplatePurpose) -> int:
    """Get the first template ID matching a purpose for the tenant."""
    tpl = db_session.query(DocumentTemplate).filter_by(
        tenant_id=tenant_id, purpose=purpose
    ).first()
    assert tpl is not None
    return tpl.id


def test_user_preferences_preferred_invoice_template_id_stored(client: TestClient, db_session: Session) -> None:
    token, tenant_id = _setup(db_session, client, "inv-tpl-pref@example.com")
    # Seed templates and get preferences defaults
    _seed_templates(client, token)
    client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    # Get a valid INVOICE_PDF template
    tpl_id = _get_template_id_by_purpose(db_session, tenant_id, DocumentTemplatePurpose.INVOICE_PDF)
    # Update with a valid template id
    resp = client.patch(
        "/api/settings/preferences",
        json={"preferred_invoice_template_id": tpl_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["preferred_invoice_template_id"] == tpl_id


def test_user_preferences_preferred_bill_template_id_stored(client: TestClient, db_session: Session) -> None:
    token, tenant_id = _setup(db_session, client, "bill-tpl-pref@example.com")
    _seed_templates(client, token)
    client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    # Get a valid BILL_PDF template
    tpl_id = _get_template_id_by_purpose(db_session, tenant_id, DocumentTemplatePurpose.BILL_PDF)
    resp = client.patch(
        "/api/settings/preferences",
        json={"preferred_bill_template_id": tpl_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["preferred_bill_template_id"] == tpl_id


def test_user_preferences_nullable_template_fields_default_null(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "null-tpl@example.com")
    resp = client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["preferred_invoice_template_id"] is None
    assert data["preferred_bill_template_id"] is None
    assert data["preferred_invoice_email_template_id"] is None
    assert data["preferred_bill_email_template_id"] is None


def test_user_preferences_all_template_fields_present_in_response(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "all-fields@example.com")
    resp = client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    for field in [
        "preferred_invoice_template_id",
        "preferred_bill_template_id",
        "preferred_invoice_email_template_id",
        "preferred_bill_email_template_id",
    ]:
        assert field in data, f"Missing field: {field}"


def test_user_preferences_email_template_id_stored(client: TestClient, db_session: Session) -> None:
    token, tenant_id = _setup(db_session, client, "email-tpl-pref@example.com")
    _seed_templates(client, token)
    client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    # Get valid email templates
    inv_email_id = _get_template_id_by_purpose(db_session, tenant_id, DocumentTemplatePurpose.INVOICE_EMAIL)
    bill_email_id = _get_template_id_by_purpose(db_session, tenant_id, DocumentTemplatePurpose.BILL_EMAIL)
    resp = client.patch(
        "/api/settings/preferences",
        json={"preferred_invoice_email_template_id": inv_email_id, "preferred_bill_email_template_id": bill_email_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["preferred_invoice_email_template_id"] == inv_email_id
    assert resp.json()["preferred_bill_email_template_id"] == bill_email_id


def test_user_preferences_migration_schema_is_correct(db_session: Session) -> None:
    """Verify the 4 new columns exist on the user_preferences table."""
    from sqlalchemy import inspect
    inspector = inspect(db_session.bind)
    cols = {c["name"] for c in inspector.get_columns("user_preferences")}
    assert "preferred_invoice_template_id" in cols
    assert "preferred_bill_template_id" in cols
    assert "preferred_invoice_email_template_id" in cols
    assert "preferred_bill_email_template_id" in cols


def test_user_preferences_template_id_can_be_cleared(client: TestClient, db_session: Session) -> None:
    token, tenant_id = _setup(db_session, client, "clear-tpl@example.com")
    _seed_templates(client, token)
    client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    # Set a valid value first
    tpl_id = _get_template_id_by_purpose(db_session, tenant_id, DocumentTemplatePurpose.INVOICE_PDF)
    client.patch(
        "/api/settings/preferences",
        json={"preferred_invoice_template_id": tpl_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    # Clear it
    resp = client.patch(
        "/api/settings/preferences",
        json={"preferred_invoice_template_id": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["preferred_invoice_template_id"] is None


def test_user_preferences_theme_and_density_persist(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "theme-dens@example.com")
    client.get("/api/settings/preferences", headers={"Authorization": f"Bearer {token}"})
    resp = client.patch(
        "/api/settings/preferences",
        json={"theme_preference": "dark", "table_density": "compact"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["theme_preference"] == "dark"
    assert resp.json()["table_density"] == "compact"
