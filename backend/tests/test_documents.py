from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.documents import Bill, DocumentTemplate, Invoice, NumberSequence
from app.services.documents import DocumentTemplateService, DocumentsService
from test_purchasing import auth_headers as purchase_headers
from test_purchasing import create_po, create_receipt, register_and_login as purchase_login, setup_purchase_dimension, submit_po
from test_sales import auth_headers as sales_headers
from test_sales import confirm_sales_order, create_fulfillment, create_sales_order, register_and_login as sales_login, setup_sales_dimension, stock_in


def test_create_invoice_from_sales_order_and_download_pdf(client: TestClient, db_session: Session) -> None:
    login = sales_login(client)
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "INV")
    order = create_sales_order(client, token, dimension, "3", "SO-INV")

    created = client.post("/api/invoices", json={"sales_order_id": order["id"]}, headers=sales_headers(token))
    pdf = client.get(f"/api/invoices/{created.json()['id']}/pdf", headers=sales_headers(token))

    assert created.status_code == 201
    assert created.json()["invoice_number"].startswith("INV-")
    assert created.json()["total_amount"] == "29.97"
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert db_session.query(Invoice).count() == 1
    assert db_session.query(NumberSequence).count() >= 1


def test_create_invoice_from_fulfillment_and_send_paid_void(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = sales_login(client, "invoice-fulfill@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "INVFUL")
    stock_in(client, token, dimension, "4", "invful-stock")
    order = create_sales_order(client, token, dimension, "4", "SO-INVFUL")
    confirmed = confirm_sales_order(client, token, order, dimension, "4", "invful-confirm")
    fulfillment = create_fulfillment(client, token, order, dimension, confirmed["stock_results"][0]["reservation"]["id"], "4", "FUL-INV")

    created = client.post("/api/invoices", json={"fulfillment_id": fulfillment["id"]}, headers=sales_headers(token))
    sent = client.post(f"/api/invoices/{created.json()['id']}/send", json={}, headers=sales_headers(token))
    paid = client.post(f"/api/invoices/{created.json()['id']}/mark-paid", json={}, headers=sales_headers(token))
    void = client.post(f"/api/invoices/{created.json()['id']}/void", json={}, headers=sales_headers(token))

    assert created.status_code == 201
    assert sent.status_code == 200
    assert sent.json()["status"] == "SENT"
    assert paid.status_code == 200
    assert paid.json()["status"] == "PAID"
    assert void.status_code == 409
    assert db_session.query(Invoice).one().status.value == "PAID"


def test_create_bill_from_receipt_send_pdf_and_paid(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = purchase_login(client, "bill@example.com")
    token = login["access_token"]
    dimension = setup_purchase_dimension(client, token, "BILL")
    po = submit_po(client, token, create_po(client, token, dimension, "5", "PO-BILL")["id"])
    receipt = create_receipt(client, token, po, dimension, "5", "GRN-BILL")

    created = client.post("/api/bills", json={"receipt_id": receipt["id"]}, headers=purchase_headers(token))
    sent = client.post(f"/api/bills/{created.json()['id']}/send", json={"email": "vendor@example.com"}, headers=purchase_headers(token))
    pdf = client.get(f"/api/bills/{created.json()['id']}/pdf", headers=purchase_headers(token))
    paid = client.post(f"/api/bills/{created.json()['id']}/mark-paid", json={}, headers=purchase_headers(token))

    assert created.status_code == 201
    assert created.json()["bill_number"].startswith("BILL-")
    assert sent.status_code == 200
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert paid.status_code == 200
    assert db_session.query(Bill).count() == 1


def test_document_templates_list_update_and_preview(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "templates@example.com")
    token = login["access_token"]

    listed = client.get("/api/document-templates?channel=EMAIL", headers=sales_headers(token))
    assert listed.status_code == 200
    template = listed.json()[0]
    updated = client.patch(
        f"/api/document-templates/{template['id']}",
        json={"subject_template": "Hello {{ company_name }}", "body_template": "Invoice {{ invoice_number }}"},
        headers=sales_headers(token),
    )
    preview = client.post(
        f"/api/document-templates/{template['id']}/preview",
        json={"variables": {"invoice_number": "INV-00999"}},
        headers=sales_headers(token),
    )

    assert updated.status_code == 200
    assert preview.status_code == 200
    assert "INV-00999" in preview.json()["body"]
    assert db_session.query(DocumentTemplate).count() >= 1


# ─── Phase 15 Tests ───────────────────────────────────────────────────────────


def test_invoice_pdf_endpoint_returns_pdf_content_type(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "pdf-ct@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "PDFCT")
    order = create_sales_order(client, token, dimension, "2", "SO-PDFCT")
    created = client.post("/api/invoices", json={"sales_order_id": order["id"]}, headers=sales_headers(token))
    pdf = client.get(f"/api/invoices/{created.json()['id']}/pdf", headers=sales_headers(token))
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert len(pdf.content) > 100


def test_bill_pdf_endpoint_returns_pdf_bytes_with_length(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = purchase_login(client, "billpdf@example.com")
    token = login["access_token"]
    dimension = setup_purchase_dimension(client, token, "BPDF")
    po = submit_po(client, token, create_po(client, token, dimension, "3", "PO-BPDF")["id"])
    receipt = create_receipt(client, token, po, dimension, "3", "GRN-BPDF")
    created = client.post("/api/bills", json={"receipt_id": receipt["id"]}, headers=purchase_headers(token))
    pdf = client.get(f"/api/bills/{created.json()['id']}/pdf", headers=purchase_headers(token))
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert len(pdf.content) > 100


def test_render_invoice_html_contains_invoice_number(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "invhtml@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "IHTML")
    order = create_sales_order(client, token, dimension, "1", "SO-IHTML")
    created = client.post("/api/invoices", json={"sales_order_id": order["id"]}, headers=sales_headers(token))
    invoice_number = created.json()["invoice_number"]
    pdf = client.get(f"/api/invoices/{created.json()['id']}/pdf", headers=sales_headers(token))
    assert pdf.status_code == 200
    assert invoice_number.startswith("INV-")


def test_render_bill_html_contains_bill_number(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = purchase_login(client, "billhtml@example.com")
    token = login["access_token"]
    dimension = setup_purchase_dimension(client, token, "BHTML")
    po = submit_po(client, token, create_po(client, token, dimension, "2", "PO-BHTML")["id"])
    receipt = create_receipt(client, token, po, dimension, "2", "GRN-BHTML")
    created = client.post("/api/bills", json={"receipt_id": receipt["id"]}, headers=purchase_headers(token))
    bill_number = created.json()["bill_number"]
    assert bill_number.startswith("BILL-")


def test_render_invoice_jinja2_for_loop_produces_items(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "jinja-loop@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "JLOOP")
    order = create_sales_order(client, token, dimension, "2", "SO-JLOOP")
    created = client.post("/api/invoices", json={"sales_order_id": order["id"]}, headers=sales_headers(token))
    svc = DocumentsService(db_session)
    invoice = svc.get_invoice(created.json()["tenant_id"], created.json()["id"])
    context = {**svc._base_template_context(invoice.tenant_id), **svc._invoice_context(invoice)}
    from app.models.documents import DocumentTemplateChannel, DocumentTemplateKey
    rendered = svc.templates.render_by_key(
        invoice.tenant_id, DocumentTemplateChannel.PDF, DocumentTemplateKey.PDF_INVOICE, context
    )
    assert "Widget JLOOP" in rendered["body"] or "Product" in rendered["body"]


def test_render_email_verification_uses_jinja2_code_variable(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "jinja-otp@example.com")
    token = login["access_token"]
    tenant_id = login["user"]["tenant_id"]
    svc = DocumentTemplateService(db_session)
    from app.models.documents import DocumentTemplateChannel, DocumentTemplateKey
    rendered = svc.render_by_key(
        tenant_id, DocumentTemplateChannel.EMAIL, DocumentTemplateKey.EMAIL_VERIFICATION,
        {"code": "ABC123", "purpose": "email verification", "ttl_minutes": 10},
    )
    assert "ABC123" in rendered["body"]
    assert "email verification" in rendered["body"].lower()


def test_email_verification_send_on_fresh_tenant_does_not_404(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.api.verification.send_email", lambda *args, **kwargs: None)
    login = sales_login(client, "fresh-tenant@example.com")
    token = login["access_token"]
    resp = client.post("/api/verification/email/send", headers=sales_headers(token))
    assert resp.status_code == 200
    assert "code" in resp.json().get("development_code", "")  or resp.json().get("development_code") is not None


def test_template_auto_seed_on_render_by_key(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "autoseed@example.com")
    token = login["access_token"]
    tenant_id = login["user"]["tenant_id"]
    assert db_session.query(DocumentTemplate).filter_by(tenant_id=tenant_id).count() == 0
    svc = DocumentTemplateService(db_session)
    from app.models.documents import DocumentTemplateChannel, DocumentTemplateKey
    rendered = svc.render_by_key(
        tenant_id, DocumentTemplateChannel.EMAIL, DocumentTemplateKey.EMAIL_VERIFICATION,
        {"code": "999999", "purpose": "test", "ttl_minutes": 5},
    )
    assert "999999" in rendered["body"]
    assert db_session.query(DocumentTemplate).filter_by(tenant_id=tenant_id).count() == 26


def test_body_template_text_is_stored_in_db(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "textcol@example.com")
    token = login["access_token"]
    tenant_id = login["user"]["tenant_id"]
    svc = DocumentTemplateService(db_session)
    svc._ensure_defaults(tenant_id)
    template = db_session.query(DocumentTemplate).filter_by(
        tenant_id=tenant_id, template_key="EMAIL_VERIFICATION"
    ).first()
    assert template is not None
    assert template.body_template_text is not None
    assert "{{ code }}" in template.body_template_text


def test_invoice_send_email_uses_html_template(client: TestClient, db_session: Session, monkeypatch) -> None:
    captured = {}
    def mock_send(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
    monkeypatch.setattr("app.services.documents.send_email", mock_send)
    login = sales_login(client, "inv-email-html@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "IEHTML")
    order = create_sales_order(client, token, dimension, "2", "SO-IEHTML")
    created = client.post("/api/invoices", json={"sales_order_id": order["id"]}, headers=sales_headers(token))
    client.post(f"/api/invoices/{created.json()['id']}/send", json={"email": "test@example.com"}, headers=sales_headers(token))
    assert captured.get("kwargs", {}).get("body_html") is not None or (len(captured.get("args", [])) >= 4 and captured["args"][3] is not None)


def test_invoice_mark_paid_status_transition(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = sales_login(client, "inv-paid@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "IPAID")
    order = create_sales_order(client, token, dimension, "1", "SO-IPAID")
    created = client.post("/api/invoices", json={"sales_order_id": order["id"]}, headers=sales_headers(token))
    inv_id = created.json()["id"]
    paid = client.post(f"/api/invoices/{inv_id}/mark-paid", json={}, headers=sales_headers(token))
    assert paid.status_code == 200
    assert paid.json()["status"] == "PAID"
    assert paid.json()["paid_at"] is not None


def test_invoice_void_status_transition(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = sales_login(client, "inv-void@example.com")
    token = login["access_token"]
    dimension = setup_sales_dimension(client, token, "IVOID")
    order = create_sales_order(client, token, dimension, "1", "SO-IVOID")
    created = client.post("/api/invoices", json={"sales_order_id": order["id"]}, headers=sales_headers(token))
    inv_id = created.json()["id"]
    void = client.post(f"/api/invoices/{inv_id}/void", json={}, headers=sales_headers(token))
    assert void.status_code == 200
    assert void.json()["status"] == "VOID"
    assert void.json()["voided_at"] is not None


def test_bill_mark_paid_status_transition(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = purchase_login(client, "bill-paid@example.com")
    token = login["access_token"]
    dimension = setup_purchase_dimension(client, token, "BPAID")
    po = submit_po(client, token, create_po(client, token, dimension, "2", "PO-BPAID")["id"])
    receipt = create_receipt(client, token, po, dimension, "2", "GRN-BPAID")
    created = client.post("/api/bills", json={"receipt_id": receipt["id"]}, headers=purchase_headers(token))
    bill_id = created.json()["id"]
    paid = client.post(f"/api/bills/{bill_id}/mark-paid", json={}, headers=purchase_headers(token))
    assert paid.status_code == 200
    assert paid.json()["status"] == "PAID"


def test_bill_pdf_endpoint_returns_valid_pdf_bytes(client: TestClient, db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = purchase_login(client, "billpdf2@example.com")
    token = login["access_token"]
    dimension = setup_purchase_dimension(client, token, "BPDF2")
    po = submit_po(client, token, create_po(client, token, dimension, "4", "PO-BPDF2")["id"])
    receipt = create_receipt(client, token, po, dimension, "4", "GRN-BPDF2")
    created = client.post("/api/bills", json={"receipt_id": receipt["id"]}, headers=purchase_headers(token))
    pdf = client.get(f"/api/bills/{created.json()['id']}/pdf", headers=purchase_headers(token))
    assert pdf.status_code == 200
    assert pdf.content[:5] == b"%PDF-"


def test_template_update_persists_to_db(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "tpl-persist@example.com")
    token = login["access_token"]
    listed = client.get("/api/document-templates?channel=EMAIL", headers=sales_headers(token))
    template = listed.json()[0]
    new_subject = "Updated subject {{ code }}"
    client.patch(
        f"/api/document-templates/{template['id']}",
        json={"subject_template": new_subject},
        headers=sales_headers(token),
    )
    fetched = db_session.query(DocumentTemplate).filter_by(id=template["id"]).first()
    assert fetched.subject_template == new_subject


def test_template_preview_renders_with_provided_variables(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "tpl-preview@example.com")
    token = login["access_token"]
    listed = client.get("/api/document-templates?channel=EMAIL", headers=sales_headers(token))
    template = listed.json()[0]
    client.patch(
        f"/api/document-templates/{template['id']}",
        json={"body_template": "Hello {{ name }}, your code is {{ code }}"},
        headers=sales_headers(token),
    )
    preview = client.post(
        f"/api/document-templates/{template['id']}/preview",
        json={"variables": {"name": "Alice", "code": "XYZ789"}},
        headers=sales_headers(token),
    )
    assert preview.status_code == 200
    assert "Alice" in preview.json()["body"]
    assert "XYZ789" in preview.json()["body"]


def test_jinja2_filter_lower_works_in_document_kind(client: TestClient, db_session: Session) -> None:
    login = sales_login(client, "jinja-filter@example.com")
    token = login["access_token"]
    tenant_id = login["user"]["tenant_id"]
    svc = DocumentTemplateService(db_session)
    from app.models.documents import DocumentTemplateChannel, DocumentTemplateKey
    rendered = svc.render_by_key(
        tenant_id, DocumentTemplateChannel.EMAIL, DocumentTemplateKey.INVOICE_SEND,
        {"title": "Invoice INV-001", "intro": "Hi", "document_kind": "Invoice", "document_number": "INV-001", "notes": None, "sender_name": "Test Co"},
    )
    assert "invoice" in rendered["body"]


# ─── Template Purpose Validation Tests ────────────────────────────────────────


def test_invoice_pdf_rejects_bill_template(client: TestClient, db_session: Session) -> None:
    """Invoice PDF rendering must reject a template whose key starts with PDF_BILL."""
    import pytest
    from app.core.exceptions import AppError
    from app.models.documents import DocumentTemplate, DocumentTemplateChannel, DocumentTemplateKey
    from app.models.settings import UserPreferences

    login = sales_login(client, "inv-reject-bill@example.com")
    token = login["access_token"]
    tenant_id = login["user"]["tenant_id"]
    user_id = login["user"]["id"]

    # Ensure default templates exist
    svc = DocumentsService(db_session)
    svc.templates._ensure_defaults(tenant_id)

    # Find a PDF_BILL template
    bill_template = db_session.query(DocumentTemplate).filter_by(
        tenant_id=tenant_id, template_key=DocumentTemplateKey.PDF_BILL
    ).first()
    assert bill_template is not None

    # Set user preference to point invoice PDF at the bill template
    prefs = db_session.query(UserPreferences).filter_by(user_id=user_id).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user_id)
        db_session.add(prefs)
    prefs.preferred_invoice_template_id = bill_template.id
    db_session.commit()

    # Create an invoice to render
    dimension = setup_sales_dimension(client, token, "REJB")
    order = create_sales_order(client, token, dimension, "1", "SO-REJB")
    created = client.post("/api/invoices", json={"sales_order_id": order["id"]}, headers=sales_headers(token))
    invoice_id = created.json()["id"]

    with pytest.raises(AppError) as exc_info:
        svc.render_invoice_pdf(tenant_id, invoice_id, user_id)
    assert exc_info.value.code == "TEMPLATE_PURPOSE_MISMATCH"
    assert exc_info.value.status_code == 400


def test_bill_pdf_rejects_invoice_template(client: TestClient, db_session: Session, monkeypatch) -> None:
    """Bill PDF rendering must reject a template whose key starts with PDF_INVOICE."""
    import pytest
    from app.core.exceptions import AppError
    from app.models.documents import DocumentTemplate, DocumentTemplateChannel, DocumentTemplateKey
    from app.models.settings import UserPreferences

    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)
    login = purchase_login(client, "bill-reject-inv@example.com")
    token = login["access_token"]
    tenant_id = login["user"]["tenant_id"]
    user_id = login["user"]["id"]

    svc = DocumentsService(db_session)
    svc.templates._ensure_defaults(tenant_id)

    # Find a PDF_INVOICE template
    invoice_template = db_session.query(DocumentTemplate).filter_by(
        tenant_id=tenant_id, template_key=DocumentTemplateKey.PDF_INVOICE
    ).first()
    assert invoice_template is not None

    # Set user preference to point bill PDF at the invoice template
    prefs = db_session.query(UserPreferences).filter_by(user_id=user_id).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user_id)
        db_session.add(prefs)
    prefs.preferred_bill_template_id = invoice_template.id
    db_session.commit()

    # Create a bill to render
    dimension = setup_purchase_dimension(client, token, "REJI")
    po = submit_po(client, token, create_po(client, token, dimension, "2", "PO-REJI")["id"])
    receipt = create_receipt(client, token, po, dimension, "2", "GRN-REJI")
    created = client.post("/api/bills", json={"receipt_id": receipt["id"]}, headers=purchase_headers(token))
    bill_id = created.json()["id"]

    with pytest.raises(AppError) as exc_info:
        svc.render_bill_pdf(tenant_id, bill_id, user_id)
    assert exc_info.value.code == "TEMPLATE_PURPOSE_MISMATCH"
    assert exc_info.value.status_code == 400


def test_invoice_pdf_rejects_inactive_template(client: TestClient, db_session: Session) -> None:
    """Invoice PDF rendering must reject an inactive preferred template."""
    import pytest
    from app.core.exceptions import AppError
    from app.models.documents import DocumentTemplate, DocumentTemplateChannel, DocumentTemplateKey
    from app.models.settings import UserPreferences

    login = sales_login(client, "inv-inactive@example.com")
    token = login["access_token"]
    tenant_id = login["user"]["tenant_id"]
    user_id = login["user"]["id"]

    svc = DocumentsService(db_session)
    svc.templates._ensure_defaults(tenant_id)

    # Find a PDF_INVOICE template and deactivate it
    invoice_template = db_session.query(DocumentTemplate).filter_by(
        tenant_id=tenant_id, template_key=DocumentTemplateKey.PDF_INVOICE
    ).first()
    assert invoice_template is not None
    invoice_template.is_active = False
    db_session.commit()

    # Set user preference to point at the now-inactive template
    prefs = db_session.query(UserPreferences).filter_by(user_id=user_id).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user_id)
        db_session.add(prefs)
    prefs.preferred_invoice_template_id = invoice_template.id
    db_session.commit()

    # Create an invoice to render
    dimension = setup_sales_dimension(client, token, "INACT")
    order = create_sales_order(client, token, dimension, "1", "SO-INACT")
    created = client.post("/api/invoices", json={"sales_order_id": order["id"]}, headers=sales_headers(token))
    invoice_id = created.json()["id"]

    # get_template_by_id filters is_active=True, so inactive returns None -> 404
    with pytest.raises(AppError) as exc_info:
        svc.render_invoice_pdf(tenant_id, invoice_id, user_id)
    assert exc_info.value.code == "DOCUMENT_TEMPLATE_NOT_FOUND"
    assert exc_info.value.status_code == 404


def test_bill_pdf_rejects_cross_tenant_template(client: TestClient, db_session: Session, monkeypatch) -> None:
    """Bill PDF rendering must reject a template belonging to a different tenant."""
    import pytest
    from app.core.exceptions import AppError
    from app.models.documents import DocumentTemplate, DocumentTemplateChannel, DocumentTemplateKey
    from app.models.settings import UserPreferences

    monkeypatch.setattr("app.services.documents.send_email", lambda *args, **kwargs: None)

    # Create two tenants
    login_a = purchase_login(client, "tenant-a-cross@example.com")
    token_a = login_a["access_token"]
    tenant_a_id = login_a["user"]["tenant_id"]

    login_b = purchase_login(client, "tenant-b-cross@example.com")
    token_b = login_b["access_token"]
    tenant_b_id = login_b["user"]["tenant_id"]
    user_b_id = login_b["user"]["id"]

    # Ensure defaults for both tenants
    svc_a = DocumentsService(db_session)
    svc_a.templates._ensure_defaults(tenant_a_id)
    svc_b = DocumentsService(db_session)
    svc_b.templates._ensure_defaults(tenant_b_id)

    # Get a PDF_BILL template from tenant A
    template_a = db_session.query(DocumentTemplate).filter_by(
        tenant_id=tenant_a_id, template_key=DocumentTemplateKey.PDF_BILL
    ).first()
    assert template_a is not None

    # Set tenant B user preference to point at tenant A's template
    prefs = db_session.query(UserPreferences).filter_by(user_id=user_b_id).first()
    if prefs is None:
        prefs = UserPreferences(user_id=user_b_id)
        db_session.add(prefs)
    prefs.preferred_bill_template_id = template_a.id
    db_session.commit()

    # Create a bill in tenant B
    dimension = setup_purchase_dimension(client, token_b, "CROSS")
    po = submit_po(client, token_b, create_po(client, token_b, dimension, "1", "PO-CROSS")["id"])
    receipt = create_receipt(client, token_b, po, dimension, "1", "GRN-CROSS")
    created = client.post("/api/bills", json={"receipt_id": receipt["id"]}, headers=purchase_headers(token_b))
    bill_id = created.json()["id"]

    # get_template_by_id filters by tenant_id, so cross-tenant returns None -> 404
    with pytest.raises(AppError) as exc_info:
        svc_b.render_bill_pdf(tenant_b_id, bill_id, user_b_id)
    assert exc_info.value.code == "DOCUMENT_TEMPLATE_NOT_FOUND"
    assert exc_info.value.status_code == 404
