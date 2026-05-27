from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.auth import Tenant, User, UserRole, UserStatus
from app.models.documents import DocumentTemplate


def _setup(db_session: Session, client: TestClient, email: str = "p17a@example.com"):
    tenant = Tenant(company_name="P17ACo", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="P17AUser", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.TENANT_ADMIN, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    assert login.status_code == 200
    return login.json()["access_token"], tenant.id


def _viewer_token(db_session: Session, client: TestClient, email: str = "viewer-17a@example.com"):
    tenant = Tenant(company_name="ViewerCo17A", contact_email=email)
    db_session.add(tenant)
    db_session.flush()
    user = User(
        tenant_id=tenant.id, name="Viewer", email=email,
        password_hash=get_password_hash("StrongPass123!"),
        role=UserRole.VIEWER, status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123!"})
    return login.json()["access_token"]


def test_list_email_templates_returns_only_email_channel(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "list-email@example.com")
    resp = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3
    for t in data:
        assert t["channel"] == "EMAIL"


def test_get_template_returns_correct_template(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "get-tpl@example.com")
    listed = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    template = listed.json()[0]
    resp = client.get(f"/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    found = [t for t in resp.json() if t["id"] == template["id"]]
    assert len(found) == 1
    assert found[0]["name"] == template["name"]


def test_update_template_subject_persists(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "upd-subj@example.com")
    listed = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    template = listed.json()[0]
    new_subject = "New subject {{ code }}"
    resp = client.patch(
        f"/api/document-templates/{template['id']}",
        json={"subject_template": new_subject},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["subject_template"] == new_subject


def test_update_template_body_persists(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "upd-body@example.com")
    listed = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    template = listed.json()[0]
    new_body = "<p>Hello {{ name }}</p>"
    resp = client.patch(
        f"/api/document-templates/{template['id']}",
        json={"body_template": new_body},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["body_template"] == new_body


def test_preview_template_renders_variables(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "preview-vars@example.com")
    listed = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    template = listed.json()[0]
    client.patch(
        f"/api/document-templates/{template['id']}",
        json={"body_template": "Code: {{ code }}, Purpose: {{ purpose }}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.post(
        f"/api/document-templates/{template['id']}/preview",
        json={"variables": {"code": "XYZ", "purpose": "test"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert "XYZ" in resp.json()["body"]
    assert "test" in resp.json()["body"]


def test_preview_template_with_missing_variable_does_not_crash(client: TestClient, db_session: Session) -> None:
    token, _ = _setup(db_session, client, "preview-miss@example.com")
    listed = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    template = listed.json()[0]
    client.patch(
        f"/api/document-templates/{template['id']}",
        json={"body_template": "Hello {{ missing_var }}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.post(
        f"/api/document-templates/{template['id']}/preview",
        json={"variables": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_template_required_admin_role(client: TestClient, db_session: Session) -> None:
    token = _viewer_token(db_session, client, "viewer-role-17a@example.com")
    resp = client.get("/api/document-templates?channel=EMAIL", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_list_templates_auto_seeds_defaults(client: TestClient, db_session: Session) -> None:
    token, tenant_id = _setup(db_session, client, "autoseed-17a@example.com")
    assert db_session.query(DocumentTemplate).filter_by(tenant_id=tenant_id).count() == 0
    resp = client.get("/api/document-templates", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) == 26
    assert db_session.query(DocumentTemplate).filter_by(tenant_id=tenant_id).count() == 26
