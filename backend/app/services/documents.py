from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import jinja2
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.documents import (
    Bill,
    BillItem,
    BillStatus,
    DocumentTemplate,
    DocumentTemplateChannel,
    DocumentTemplateKey,
    DocumentTemplatePurpose,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    NumberSequenceKey,
)
from app.repositories.audit import AuditLogRepository
from app.repositories.documents import DocumentsRepository
from app.repositories.settings import UserPreferencesRepository
from app.services.default_templates import DEFAULT_TEMPLATES
from app.services.email_service import send_email
from app.services.pdf_service import render_html_to_pdf
from app.services.workflow import WorkflowService
from app.utils.currency import get_currency_info

from dataclasses import dataclass

ZERO = Decimal("0.00")

# Mapping from template_key to purpose for system templates
_KEY_TO_PURPOSE: dict[DocumentTemplateKey, DocumentTemplatePurpose] = {
    DocumentTemplateKey.EMAIL_VERIFICATION: DocumentTemplatePurpose.EMAIL_VERIFICATION,
    DocumentTemplateKey.EMAIL_VERIFICATION_MODERN: DocumentTemplatePurpose.EMAIL_VERIFICATION,
    DocumentTemplateKey.EMAIL_VERIFICATION_MINIMAL: DocumentTemplatePurpose.EMAIL_VERIFICATION,
    DocumentTemplateKey.INVOICE_SEND: DocumentTemplatePurpose.INVOICE_EMAIL,
    DocumentTemplateKey.INVOICE_SEND_MODERN: DocumentTemplatePurpose.INVOICE_EMAIL,
    DocumentTemplateKey.INVOICE_SEND_MINIMAL: DocumentTemplatePurpose.INVOICE_EMAIL,
    DocumentTemplateKey.INVOICE_SEND_FORMAL: DocumentTemplatePurpose.INVOICE_EMAIL,
    DocumentTemplateKey.BILL_SEND: DocumentTemplatePurpose.BILL_EMAIL,
    DocumentTemplateKey.BILL_SEND_MODERN: DocumentTemplatePurpose.BILL_EMAIL,
    DocumentTemplateKey.BILL_SEND_MINIMAL: DocumentTemplatePurpose.BILL_EMAIL,
    DocumentTemplateKey.BILL_SEND_FORMAL: DocumentTemplatePurpose.BILL_EMAIL,
    DocumentTemplateKey.PDF_INVOICE: DocumentTemplatePurpose.INVOICE_PDF,
    DocumentTemplateKey.PDF_INVOICE_MODERN: DocumentTemplatePurpose.INVOICE_PDF,
    DocumentTemplateKey.PDF_INVOICE_MINIMAL: DocumentTemplatePurpose.INVOICE_PDF,
    DocumentTemplateKey.PDF_INVOICE_BOLD: DocumentTemplatePurpose.INVOICE_PDF,
    DocumentTemplateKey.PDF_INVOICE_WARM: DocumentTemplatePurpose.INVOICE_PDF,
    DocumentTemplateKey.PDF_BILL: DocumentTemplatePurpose.BILL_PDF,
    DocumentTemplateKey.PDF_BILL_MODERN: DocumentTemplatePurpose.BILL_PDF,
    DocumentTemplateKey.PDF_BILL_MINIMAL: DocumentTemplatePurpose.BILL_PDF,
    DocumentTemplateKey.PDF_BILL_BOLD: DocumentTemplatePurpose.BILL_PDF,
    DocumentTemplateKey.PDF_BILL_WARM: DocumentTemplatePurpose.BILL_PDF,
    DocumentTemplateKey.ACCOUNT_CREATED: DocumentTemplatePurpose.ACCOUNT_CREATED,
    DocumentTemplateKey.PASSWORD_RESET: DocumentTemplatePurpose.PASSWORD_RESET,
    DocumentTemplateKey.USER_DISABLED: DocumentTemplatePurpose.USER_DISABLED,
    DocumentTemplateKey.USER_ENABLED: DocumentTemplatePurpose.USER_ENABLED,
    DocumentTemplateKey.ROLE_CHANGED: DocumentTemplatePurpose.ROLE_CHANGED,
}

# Strict channel validation for each purpose
_PURPOSE_CHANNEL_MAP: dict[DocumentTemplatePurpose, DocumentTemplateChannel] = {
    DocumentTemplatePurpose.EMAIL_VERIFICATION: DocumentTemplateChannel.EMAIL,
    DocumentTemplatePurpose.INVOICE_EMAIL: DocumentTemplateChannel.EMAIL,
    DocumentTemplatePurpose.BILL_EMAIL: DocumentTemplateChannel.EMAIL,
    DocumentTemplatePurpose.INVOICE_PDF: DocumentTemplateChannel.PDF,
    DocumentTemplatePurpose.BILL_PDF: DocumentTemplateChannel.PDF,
    DocumentTemplatePurpose.ACCOUNT_CREATED: DocumentTemplateChannel.EMAIL,
    DocumentTemplatePurpose.PASSWORD_RESET: DocumentTemplateChannel.EMAIL,
    DocumentTemplatePurpose.USER_DISABLED: DocumentTemplateChannel.EMAIL,
    DocumentTemplatePurpose.USER_ENABLED: DocumentTemplateChannel.EMAIL,
    DocumentTemplatePurpose.ROLE_CHANGED: DocumentTemplateChannel.EMAIL,
}

# Preference field -> expected purpose
_PREFERENCE_PURPOSE_MAP: dict[str, DocumentTemplatePurpose] = {
    "preferred_invoice_template_id": DocumentTemplatePurpose.INVOICE_PDF,
    "preferred_bill_template_id": DocumentTemplatePurpose.BILL_PDF,
    "preferred_invoice_email_template_id": DocumentTemplatePurpose.INVOICE_EMAIL,
    "preferred_bill_email_template_id": DocumentTemplatePurpose.BILL_EMAIL,
    "preferred_verification_template_id": DocumentTemplatePurpose.EMAIL_VERIFICATION,
}


@dataclass
class PdfRenderResult:
    """Result of a PDF render operation, including template metadata."""
    pdf_bytes: bytes
    template_id: int
    template_key: str
    template_name: str
    template_purpose: str


class SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return ""


def _naive_utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _decimal(value: Any) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


class DocumentTemplateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = DocumentsRepository(db)

    def list_templates(self, tenant_id: int, channel: str | None = None, purpose: str | None = None) -> list:
        self._ensure_defaults(tenant_id)
        if purpose:
            resolved_purpose = DocumentTemplatePurpose(purpose)
            return self.repository.list_templates_by_purpose(tenant_id, resolved_purpose)
        resolved = DocumentTemplateChannel(channel) if channel else None
        return self.repository.list_templates(tenant_id, resolved)

    def get_template(self, tenant_id: int, template_id: int):
        self._ensure_defaults(tenant_id)
        template = self.repository.get_template(tenant_id, template_id)
        if template is None:
            raise AppError("DOCUMENT_TEMPLATE_NOT_FOUND", "Document template was not found for this tenant.", 404)
        return template

    def update_template(self, tenant_id: int, template_id: int, values: dict[str, Any]):
        template = self.repository.get_template(tenant_id, template_id)
        if template is None:
            raise AppError("DOCUMENT_TEMPLATE_NOT_FOUND", "Document template was not found for this tenant.", 404)
        for key, value in values.items():
            setattr(template, key, value)
        self.db.commit()
        self.db.refresh(template)
        return template

    def preview_template(self, tenant_id: int, template_id: int, values: dict[str, Any]) -> dict[str, str | None]:
        template = self.repository.get_template(tenant_id, template_id)
        if template is None:
            raise AppError("DOCUMENT_TEMPLATE_NOT_FOUND", "Document template was not found for this tenant.", 404)
        context = self._preview_context(tenant_id, values)
        return {
            "subject": self._render(template.subject_template, context) if template.subject_template else None,
            "body": self._render(template.body_template, context),
        }

    def render_by_key(
        self,
        tenant_id: int,
        channel: DocumentTemplateChannel,
        template_key: DocumentTemplateKey,
        context: dict[str, Any],
        preferred_template_id: int | None = None,
    ) -> dict[str, str | None]:
        self._ensure_defaults(tenant_id)
        expected_purpose = _KEY_TO_PURPOSE.get(template_key)
        template = None
        if preferred_template_id:
            template = self.repository.get_template_by_id(tenant_id, preferred_template_id)
            if template is None:
                raise AppError("DOCUMENT_TEMPLATE_NOT_FOUND", "The selected preferred template is no longer available.", 404)
            # Validate purpose using the purpose field
            if expected_purpose and template.purpose != expected_purpose:
                raise AppError(
                    "TEMPLATE_PURPOSE_MISMATCH",
                    "Selected template cannot be used for this document type.",
                    400,
                )
        if template is None:
            template = self.repository.get_template_by_key(tenant_id, channel, template_key)
        if template is None or not template.is_active:
            raise AppError("DOCUMENT_TEMPLATE_NOT_FOUND", "Active document template was not found for this tenant.", 404)
        return {
            "subject": self._render(template.subject_template, context) if template.subject_template else None,
            "body": self._render(template.body_template, context),
            "text": self._render(template.body_template_text, context) if template.body_template_text else None,
            "template_id": template.id,
            "template_key": template.template_key.value if template.template_key else template.template_code,
            "template_name": template.name,
            "template_purpose": template.purpose.value,
        }

    @staticmethod
    def _template_purpose_prefix(template_key: DocumentTemplateKey) -> str | None:
        """Derive the expected template_key prefix for purpose validation."""
        key_value = template_key.value
        if key_value.startswith("PDF_INVOICE"):
            return "PDF_INVOICE"
        if key_value.startswith("PDF_BILL"):
            return "PDF_BILL"
        if key_value.startswith("INVOICE_SEND"):
            return "INVOICE_SEND"
        if key_value.startswith("BILL_SEND"):
            return "BILL_SEND"
        if key_value.startswith("EMAIL_VERIFICATION"):
            return "EMAIL_VERIFICATION"
        return None

    def create_custom_template(self, tenant_id: int, user_id: int, data: dict[str, Any]) -> DocumentTemplate:
        """Create a custom template with strict purpose/channel validation."""
        self._ensure_defaults(tenant_id)
        try:
            purpose = DocumentTemplatePurpose(data["purpose"])
        except (ValueError, KeyError):
            raise AppError(
                "INVALID_TEMPLATE_PURPOSE",
                f"Invalid purpose. Must be one of: {', '.join(p.value for p in DocumentTemplatePurpose)}",
                400,
            )
        expected_channel = _PURPOSE_CHANNEL_MAP[purpose]
        template_code = f"CUSTOM_{purpose.value}_{uuid.uuid4().hex[:8]}"
        template = self.repository.create_template({
            "tenant_id": tenant_id,
            "channel": expected_channel,
            "template_key": None,
            "purpose": purpose,
            "template_code": template_code,
            "is_system": False,
            "created_by": user_id,
            "description": data.get("description"),
            "name": data["name"],
            "subject_template": data.get("subject_template"),
            "body_template": data["body_template"],
            "body_template_text": data.get("body_template_text"),
            "is_active": data.get("is_active", True),
        })
        self.db.commit()
        self.db.refresh(template)
        return template

    def duplicate_template(self, tenant_id: int, user_id: int, template_id: int, new_name: str | None = None, description: str | None = None) -> DocumentTemplate:
        """Duplicate an existing template (system or custom)."""
        source = self.repository.get_template(tenant_id, template_id)
        if source is None:
            raise AppError("DOCUMENT_TEMPLATE_NOT_FOUND", "Document template was not found for this tenant.", 404)
        name = new_name or f"{source.name} (Copy)"
        template_code = f"CUSTOM_{source.purpose.value}_{uuid.uuid4().hex[:8]}"
        result = self.repository.duplicate_template(tenant_id, template_id, name, template_code, user_id, description)
        if result is None:
            raise AppError("DOCUMENT_TEMPLATE_NOT_FOUND", "Document template was not found for this tenant.", 404)
        self.db.commit()
        self.db.refresh(result)
        return result

    def delete_template(self, tenant_id: int, template_id: int) -> None:
        """Delete a custom template. System templates cannot be deleted."""
        template = self.repository.get_template(tenant_id, template_id)
        if template is None:
            raise AppError("DOCUMENT_TEMPLATE_NOT_FOUND", "Document template was not found for this tenant.", 404)
        if template.is_system:
            raise AppError("CANNOT_DELETE_SYSTEM_TEMPLATE", "System templates cannot be deleted.", 400)
        if self.repository.is_template_in_use_by_preference(template_id):
            raise AppError("TEMPLATE_IN_USE", "Cannot delete a template that is currently set as a user preference.", 400)
        self.repository.delete_template(tenant_id, template_id)
        self.db.commit()

    def validate_template_preference(self, tenant_id: int, template_id: int, expected_purpose: DocumentTemplatePurpose) -> DocumentTemplate:
        """Validate that a template can be used for a given preference purpose."""
        self._ensure_defaults(tenant_id)
        template = self.repository.get_template(tenant_id, template_id)
        if template is None:
            raise AppError("DOCUMENT_TEMPLATE_NOT_FOUND", "Template not found or does not belong to this tenant.", 400)
        if not template.is_active:
            raise AppError("TEMPLATE_INACTIVE", "Cannot set an inactive template as a preference.", 400)
        if template.purpose != expected_purpose:
            raise AppError(
                "TEMPLATE_PURPOSE_MISMATCH",
                f"Template purpose '{template.purpose.value}' does not match expected purpose '{expected_purpose.value}'.",
                400,
            )
        return template

    def _preview_context(self, tenant_id: int, values: dict[str, Any]) -> dict[str, Any]:
        base = DocumentsService(self.db)._base_template_context(tenant_id)
        if values.get("invoice_id"):
            invoice = DocumentsService(self.db).get_invoice(tenant_id, int(values["invoice_id"]))
            return {**base, **DocumentsService(self.db)._invoice_context(invoice)}
        if values.get("bill_id"):
            bill = DocumentsService(self.db).get_bill(tenant_id, int(values["bill_id"]))
            return {**base, **DocumentsService(self.db)._bill_context(bill)}
        sample = DocumentsService(self.db)._sample_pdf_invoice_context()
        return {**sample, **base, **values.get("variables", {})}

    def _ensure_defaults(self, tenant_id: int) -> None:
        created = False
        for (channel, template_key), payload in DEFAULT_TEMPLATES.items():
            if self.repository.get_template_by_key(tenant_id, channel, template_key) is None:
                purpose = _KEY_TO_PURPOSE[template_key]
                self.repository.create_template(
                    {
                        "tenant_id": tenant_id,
                        "channel": channel,
                        "template_key": template_key,
                        "purpose": purpose,
                        "template_code": template_key.value,
                        "is_system": True,
                        "name": payload["name"],
                        "subject_template": payload["subject_template"],
                        "body_template": payload["body_template"],
                        "body_template_text": payload.get("body_template_text"),
                        "is_active": payload["is_active"],
                    }
                )
                created = True
        if created:
            self.db.commit()

    def _render(self, template: str | None, context: dict[str, Any]) -> str:
        if not template:
            return ""
        try:
            rendered = jinja2.Template(template).render(**context)
        except jinja2.TemplateError:
            rendered = template
        if rendered == template and "{" in rendered:
            flat = {}
            for k, v in context.items():
                if isinstance(v, dict):
                    for sk, sv in v.items():
                        flat[sk] = sv if sv is not None else ""
                else:
                    flat[k] = v if v is not None else ""
            try:
                rendered = rendered.format_map(SafeDict(flat))
            except (KeyError, ValueError, IndexError):
                pass
        return rendered


class DocumentsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = DocumentsRepository(db)
        self.audit_logs = AuditLogRepository(db)
        self.templates = DocumentTemplateService(db)

    def list_invoices(self, tenant_id: int) -> list[Invoice]:
        return self.repository.list_invoices(tenant_id)

    def get_invoice(self, tenant_id: int, invoice_id: int) -> Invoice:
        invoice = self.repository.get_invoice(tenant_id, invoice_id)
        if invoice is None:
            raise AppError("INVOICE_NOT_FOUND", "Invoice was not found for this tenant.", 404)
        return invoice

    def create_invoice(self, tenant_id: int, actor_user_id: int, values: dict[str, Any]) -> Invoice:
        sales_order_id = values.get("sales_order_id")
        fulfillment_id = values.get("fulfillment_id")
        if not sales_order_id and not fulfillment_id:
            raise AppError("INVOICE_SOURCE_REQUIRED", "Invoice must reference a sales order or fulfillment.", 400)
        if sales_order_id:
            order = self.repository.get_sales_order(tenant_id, int(sales_order_id))
            if order is None:
                raise AppError("SALES_ORDER_NOT_FOUND", "Sales order was not found for this tenant.", 404)
        else:
            order = None
        fulfillment = self.repository.get_fulfillment(tenant_id, int(fulfillment_id)) if fulfillment_id else None
        if fulfillment_id and fulfillment is None:
            raise AppError("SALES_FULFILLMENT_NOT_FOUND", "Sales fulfillment was not found for this tenant.", 404)
        if fulfillment and order is None:
            order = self.repository.get_sales_order(tenant_id, fulfillment.sales_order_id)
        assert order is not None
        customer = self.repository.get_customer(tenant_id, order.customer_id)
        if customer is None:
            raise AppError("CUSTOMER_NOT_FOUND", "Customer was not found for this tenant.", 404)
        sequence = self._next_number(tenant_id, NumberSequenceKey.INVOICE, "INV")
        issue_date = values.get("issue_date") or date.today()
        tax_amount = _decimal(values.get("tax_amount"))
        discount_amount = _decimal(values.get("discount_amount"))
        line_items = []
        if fulfillment:
            order_items = {item.id: item for item in order.items}
            for row in fulfillment.items:
                order_item = order_items.get(row.sales_order_item_id)
                if order_item is None:
                    continue
                product = self.repository.get_product(tenant_id, row.product_id)
                description = product.name if product else f"Product #{row.product_id}"
                quantity = Decimal(str(row.fulfilled_quantity))
                unit_price = _decimal(order_item.unit_price)
                line_items.append(
                    {
                        "tenant_id": tenant_id,
                        "sales_order_item_id": order_item.id,
                        "product_id": row.product_id,
                        "description": description,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": _decimal(quantity * unit_price),
                    }
                )
        else:
            for order_item in order.items:
                product = self.repository.get_product(tenant_id, order_item.product_id)
                description = product.name if product else f"Product #{order_item.product_id}"
                quantity = Decimal(str(order_item.ordered_quantity))
                unit_price = _decimal(order_item.unit_price)
                line_items.append(
                    {
                        "tenant_id": tenant_id,
                        "sales_order_item_id": order_item.id,
                        "product_id": order_item.product_id,
                        "description": description,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "line_total": _decimal(quantity * unit_price),
                    }
                )
        subtotal = sum((item["line_total"] for item in line_items), ZERO)
        invoice = self.repository.create_invoice(
            {
                "tenant_id": tenant_id,
                "sales_order_id": order.id,
                "fulfillment_id": fulfillment.id if fulfillment else None,
                "customer_id": order.customer_id,
                "invoice_number": sequence,
                "status": InvoiceStatus.DRAFT,
                "issue_date": issue_date,
                "due_date": values.get("due_date"),
                "currency": values.get("currency") or self._base_template_context(tenant_id)["currency"] or "USD",
                "billing_address": self._address_for_party(customer),
                "subtotal_amount": subtotal,
                "tax_amount": tax_amount,
                "discount_amount": discount_amount,
                "total_amount": subtotal + tax_amount - discount_amount,
                "notes": values.get("notes"),
                "created_by": actor_user_id,
            }
        )
        for item in line_items:
            self.db.add(InvoiceItem(invoice_id=invoice.id, **item))
        return self._commit_and_refresh_invoice(tenant_id, invoice.id, "INVOICE_CREATED", actor_user_id)

    def list_bills(self, tenant_id: int) -> list[Bill]:
        return self.repository.list_bills(tenant_id)

    def get_bill(self, tenant_id: int, bill_id: int) -> Bill:
        bill = self.repository.get_bill(tenant_id, bill_id)
        if bill is None:
            raise AppError("BILL_NOT_FOUND", "Bill was not found for this tenant.", 404)
        return bill

    def create_bill(self, tenant_id: int, actor_user_id: int, values: dict[str, Any]) -> Bill:
        purchase_order_id = values.get("purchase_order_id")
        receipt_id = values.get("receipt_id")
        if not purchase_order_id and not receipt_id:
            raise AppError("BILL_SOURCE_REQUIRED", "Bill must reference a purchase order or purchase receipt.", 400)
        if purchase_order_id:
            po = self.repository.get_purchase_order(tenant_id, int(purchase_order_id))
            if po is None:
                raise AppError("PURCHASE_ORDER_NOT_FOUND", "Purchase order was not found for this tenant.", 404)
        else:
            po = None
        receipt = self.repository.get_purchase_receipt(tenant_id, int(receipt_id)) if receipt_id else None
        if receipt_id and receipt is None:
            raise AppError("PURCHASE_RECEIPT_NOT_FOUND", "Purchase receipt was not found for this tenant.", 404)
        if receipt and po is None:
            po = self.repository.get_purchase_order(tenant_id, receipt.purchase_order_id)
        assert po is not None
        vendor = self.repository.get_vendor(tenant_id, po.vendor_id)
        if vendor is None:
            raise AppError("VENDOR_NOT_FOUND", "Vendor was not found for this tenant.", 404)
        sequence = self._next_number(tenant_id, NumberSequenceKey.BILL, "BILL")
        issue_date = values.get("issue_date") or date.today()
        tax_amount = _decimal(values.get("tax_amount"))
        discount_amount = _decimal(values.get("discount_amount"))
        line_items = []
        if receipt:
            po_items = {item.id: item for item in po.items}
            for row in receipt.items:
                po_item = po_items.get(row.purchase_order_item_id)
                if po_item is None:
                    continue
                product = self.repository.get_product(tenant_id, row.product_id)
                description = product.name if product else f"Product #{row.product_id}"
                quantity = Decimal(str(row.received_quantity))
                unit_cost = _decimal(row.unit_cost or po_item.unit_cost)
                line_items.append(
                    {
                        "tenant_id": tenant_id,
                        "purchase_order_item_id": po_item.id,
                        "product_id": row.product_id,
                        "description": description,
                        "quantity": quantity,
                        "unit_cost": unit_cost,
                        "line_total": _decimal(quantity * unit_cost),
                    }
                )
        else:
            for po_item in po.items:
                product = self.repository.get_product(tenant_id, po_item.product_id)
                description = product.name if product else f"Product #{po_item.product_id}"
                quantity = Decimal(str(po_item.ordered_quantity))
                unit_cost = _decimal(po_item.unit_cost)
                line_items.append(
                    {
                        "tenant_id": tenant_id,
                        "purchase_order_item_id": po_item.id,
                        "product_id": po_item.product_id,
                        "description": description,
                        "quantity": quantity,
                        "unit_cost": unit_cost,
                        "line_total": _decimal(quantity * unit_cost),
                    }
                )
        subtotal = sum((item["line_total"] for item in line_items), ZERO)
        bill = self.repository.create_bill(
            {
                "tenant_id": tenant_id,
                "purchase_order_id": po.id,
                "receipt_id": receipt.id if receipt else None,
                "vendor_id": po.vendor_id,
                "bill_number": sequence,
                "status": BillStatus.DRAFT,
                "issue_date": issue_date,
                "due_date": values.get("due_date"),
                "currency": values.get("currency") or self._base_template_context(tenant_id)["currency"] or "USD",
                "billing_address": self._address_for_party(vendor),
                "subtotal_amount": subtotal,
                "tax_amount": tax_amount,
                "discount_amount": discount_amount,
                "total_amount": subtotal + tax_amount - discount_amount,
                "notes": values.get("notes"),
                "created_by": actor_user_id,
            }
        )
        for item in line_items:
            self.db.add(BillItem(bill_id=bill.id, **item))
        result = self._commit_and_refresh_bill(tenant_id, bill.id, "BILL_CREATED", actor_user_id)
        try:
            workflow = WorkflowService(self.db)
            workflow.log_event(tenant_id, "BILL_RECORDED", "bill", bill.id, actor_user_id, {"bill_number": bill.bill_number, "purchase_order_id": po.id})
            workflow.cancel_entity_tasks(tenant_id, "purchase_order", po.id)
            self.db.commit()
        except Exception:
            pass
        return result

    def send_invoice(self, tenant_id: int, invoice_id: int, actor_user_id: int, email: str | None = None) -> Invoice:
        invoice = self.get_invoice(tenant_id, invoice_id)
        context = {**self._base_template_context(tenant_id), **self._invoice_context(invoice)}
        context["sender_name"] = context["tenant"]["company_name"]
        customer = self.repository.get_customer(tenant_id, invoice.customer_id)
        target_email = email or (customer.email if customer else None)
        if not target_email:
            raise AppError("INVOICE_EMAIL_REQUIRED", "Invoice email delivery requires a destination email address.", 400)
        preferred_id = self._get_user_preferred_template(actor_user_id, "preferred_invoice_email_template_id")
        rendered = self.templates.render_by_key(tenant_id, DocumentTemplateChannel.EMAIL, DocumentTemplateKey.INVOICE_SEND, context, preferred_id)
        pdf_result = self.render_invoice_pdf(tenant_id, invoice_id, actor_user_id)
        send_email(
            target_email,
            rendered["subject"] or f"Invoice {invoice.invoice_number}",
            body_text=rendered.get("text") or rendered["body"],
            body_html=rendered["body"] if "<html" in rendered["body"].lower() or "<body" in rendered["body"].lower() else None,
            attachment=pdf_result.pdf_bytes,
            attachment_filename=f"{invoice.invoice_number}.pdf",
        )
        invoice.status = InvoiceStatus.SENT
        invoice.sent_at = _naive_utcnow()
        result = self._commit_and_refresh_invoice(tenant_id, invoice.id, "INVOICE_SENT", actor_user_id)
        try:
            workflow = WorkflowService(self.db)
            workflow.log_event(tenant_id, "INVOICE_SENT", "invoice", invoice.id, actor_user_id, {"invoice_number": invoice.invoice_number, "sales_order_id": invoice.sales_order_id})
            if invoice.sales_order_id:
                workflow.cancel_entity_tasks(tenant_id, "sales_order", invoice.sales_order_id)
            self.db.commit()
        except Exception:
            pass
        return result

    def send_bill(self, tenant_id: int, bill_id: int, actor_user_id: int, email: str | None = None) -> Bill:
        bill = self.get_bill(tenant_id, bill_id)
        context = {**self._base_template_context(tenant_id), **self._bill_context(bill)}
        context["sender_name"] = context["tenant"]["company_name"]
        vendor = self.repository.get_vendor(tenant_id, bill.vendor_id)
        target_email = email or (vendor.email if vendor else None)
        if not target_email:
            raise AppError("BILL_EMAIL_REQUIRED", "Bill email delivery requires a destination email address.", 400)
        preferred_id = self._get_user_preferred_template(actor_user_id, "preferred_bill_email_template_id")
        rendered = self.templates.render_by_key(tenant_id, DocumentTemplateChannel.EMAIL, DocumentTemplateKey.BILL_SEND, context, preferred_id)
        pdf_result = self.render_bill_pdf(tenant_id, bill_id, actor_user_id)
        send_email(
            target_email,
            rendered["subject"] or f"Bill {bill.bill_number}",
            body_text=rendered.get("text") or rendered["body"],
            body_html=rendered["body"] if "<html" in rendered["body"].lower() or "<body" in rendered["body"].lower() else None,
            attachment=pdf_result.pdf_bytes,
            attachment_filename=f"{bill.bill_number}.pdf",
        )
        bill.status = BillStatus.SENT
        bill.sent_at = _naive_utcnow()
        return self._commit_and_refresh_bill(tenant_id, bill.id, "BILL_SENT", actor_user_id)

    def mark_invoice_paid(self, tenant_id: int, invoice_id: int, actor_user_id: int) -> Invoice:
        invoice = self.get_invoice(tenant_id, invoice_id)
        if invoice.status == InvoiceStatus.VOID:
            raise AppError("INVALID_INVOICE_STATE", "Void invoices cannot be marked as paid.", 409)
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = _naive_utcnow()
        return self._commit_and_refresh_invoice(tenant_id, invoice.id, "INVOICE_PAID", actor_user_id)

    def void_invoice(self, tenant_id: int, invoice_id: int, actor_user_id: int) -> Invoice:
        invoice = self.get_invoice(tenant_id, invoice_id)
        if invoice.status == InvoiceStatus.PAID:
            raise AppError("INVALID_INVOICE_STATE", "Paid invoices cannot be voided.", 409)
        invoice.status = InvoiceStatus.VOID
        invoice.voided_at = _naive_utcnow()
        return self._commit_and_refresh_invoice(tenant_id, invoice.id, "INVOICE_VOIDED", actor_user_id)

    def mark_bill_paid(self, tenant_id: int, bill_id: int, actor_user_id: int) -> Bill:
        bill = self.get_bill(tenant_id, bill_id)
        if bill.status == BillStatus.VOID:
            raise AppError("INVALID_BILL_STATE", "Void bills cannot be marked as paid.", 409)
        bill.status = BillStatus.PAID
        bill.paid_at = _naive_utcnow()
        return self._commit_and_refresh_bill(tenant_id, bill.id, "BILL_PAID", actor_user_id)

    def void_bill(self, tenant_id: int, bill_id: int, actor_user_id: int) -> Bill:
        bill = self.get_bill(tenant_id, bill_id)
        if bill.status == BillStatus.PAID:
            raise AppError("INVALID_BILL_STATE", "Paid bills cannot be voided.", 409)
        bill.status = BillStatus.VOID
        bill.voided_at = _naive_utcnow()
        return self._commit_and_refresh_bill(tenant_id, bill.id, "BILL_VOIDED", actor_user_id)

    def render_invoice_pdf(self, tenant_id: int, invoice_id: int, actor_user_id: int | None = None) -> PdfRenderResult:
        invoice = self.get_invoice(tenant_id, invoice_id)
        preferred_id = self._get_user_preferred_template(actor_user_id, "preferred_invoice_template_id") if actor_user_id else None
        context = {**self._base_template_context(tenant_id), **self._invoice_context(invoice)}
        context["sender_name"] = context["tenant"]["company_name"]
        rendered = self.templates.render_by_key(tenant_id, DocumentTemplateChannel.PDF, DocumentTemplateKey.PDF_INVOICE, context, preferred_id)
        pdf = render_html_to_pdf(rendered["body"])
        return PdfRenderResult(
            pdf_bytes=pdf,
            template_id=rendered["template_id"],
            template_key=rendered["template_key"],
            template_name=rendered["template_name"],
            template_purpose=rendered["template_purpose"],
        )

    def render_bill_pdf(self, tenant_id: int, bill_id: int, actor_user_id: int | None = None) -> PdfRenderResult:
        bill = self.get_bill(tenant_id, bill_id)
        preferred_id = self._get_user_preferred_template(actor_user_id, "preferred_bill_template_id") if actor_user_id else None
        context = {**self._base_template_context(tenant_id), **self._bill_context(bill)}
        context["sender_name"] = context["tenant"]["company_name"]
        rendered = self.templates.render_by_key(tenant_id, DocumentTemplateChannel.PDF, DocumentTemplateKey.PDF_BILL, context, preferred_id)
        pdf = render_html_to_pdf(rendered["body"])
        return PdfRenderResult(
            pdf_bytes=pdf,
            template_id=rendered["template_id"],
            template_key=rendered["template_key"],
            template_name=rendered["template_name"],
            template_purpose=rendered["template_purpose"],
        )

    def resolve_pdf_template_for_document(
        self,
        tenant_id: int,
        document_type: str,
        actor_user_id: int | None = None,
    ) -> dict[str, Any]:
        """Determine which PDF template will be used for a document type.

        Resolution order:
        1. User preference (preferred_invoice_template_id / preferred_bill_template_id)
        2. Tenant default (the base template key for the channel)
        3. System default (from DEFAULT_TEMPLATES)

        Returns template metadata: id, key, name, purpose, and resolution_source.
        """
        if document_type == "invoice":
            pref_field = "preferred_invoice_template_id"
            template_key = DocumentTemplateKey.PDF_INVOICE
            expected_purpose = DocumentTemplatePurpose.INVOICE_PDF
        elif document_type == "bill":
            pref_field = "preferred_bill_template_id"
            template_key = DocumentTemplateKey.PDF_BILL
            expected_purpose = DocumentTemplatePurpose.BILL_PDF
        else:
            raise AppError("INVALID_DOCUMENT_TYPE", f"Unknown document type: {document_type}", 400)

        self.templates._ensure_defaults(tenant_id)

        # 1. User preference
        preferred_id = self._get_user_preferred_template(actor_user_id, pref_field) if actor_user_id else None
        if preferred_id:
            template = self.repository.get_template_by_id(tenant_id, preferred_id)
            if template and template.is_active:
                # Validate purpose match
                if template.purpose == expected_purpose:
                    return {
                        "template_id": template.id,
                        "template_key": template.template_key.value if template.template_key else template.template_code,
                        "template_name": template.name,
                        "template_purpose": template.purpose.value,
                        "resolution_source": "user_preference",
                    }

        # 2. Tenant default (the base key)
        template = self.templates.repository.get_template_by_key(
            tenant_id, DocumentTemplateChannel.PDF, template_key
        )
        if template and template.is_active:
            return {
                "template_id": template.id,
                "template_key": template.template_key.value if template.template_key else template.template_code,
                "template_name": template.name,
                "template_purpose": template.purpose.value,
                "resolution_source": "tenant_default",
            }

        # 3. System default - should always exist after _ensure_defaults
        raise AppError(
            "DOCUMENT_TEMPLATE_NOT_FOUND",
            f"No active PDF template found for {document_type}.",
            404,
        )

    def _get_user_preferred_template(self, user_id: int | None, field: str) -> int | None:
        if not user_id:
            return None
        prefs_repo = UserPreferencesRepository(self.db)
        prefs = prefs_repo.get_by_user(user_id)
        if prefs is None:
            return None
        return getattr(prefs, field, None)

    def _next_number(self, tenant_id: int, sequence_key: NumberSequenceKey, default_prefix: str) -> str:
        sequence = self.repository.get_sequence(tenant_id, sequence_key)
        if sequence is None:
            sequence = self.repository.create_sequence(
                {
                    "tenant_id": tenant_id,
                    "sequence_key": sequence_key,
                    "prefix": default_prefix,
                    "next_number": 1,
                    "padding": 5,
                }
            )
            self.db.flush()
        current = sequence.next_number
        sequence.next_number += 1
        return f"{sequence.prefix}-{str(current).zfill(sequence.padding)}"

    def _base_template_context(self, tenant_id: int) -> dict[str, Any]:
        tenant = self.repository.get_tenant(tenant_id)
        settings = self.repository.get_tenant_settings(tenant_id)
        company_name = (settings.company_display_name if settings and settings.company_display_name else tenant.company_name if tenant else "Warelyn")
        currency = settings.currency if settings and settings.currency else "USD"
        currency_info = get_currency_info(currency)
        currency_symbol = currency_info["symbol"] if currency_info else "$"
        footer = settings.document_footer if settings and settings.document_footer else "Generated by Warelyn"
        return {
            "tenant": {
                "company_name": company_name,
                "contact_email": (settings.contact_email if settings else None) or (tenant.contact_email if tenant else ""),
                "phone": settings.phone if settings else None,
                "address": settings.address_line1 if settings and hasattr(settings, "address_line1") else None,
                "logo_url": settings.document_logo_url if settings and hasattr(settings, "document_logo_url") else None,
                "footer": footer,
                "currency": currency,
            },
            "company_name": company_name,
            "currency": currency,
            "currency_code": currency,
            "currency_symbol": currency_symbol,
            "document_footer": footer,
        }

    def _invoice_context(self, invoice: Invoice) -> dict[str, Any]:
        customer = self.repository.get_customer(invoice.tenant_id, invoice.customer_id)
        so = self.repository.get_sales_order(invoice.tenant_id, invoice.sales_order_id) if invoice.sales_order_id else None
        items = [
            {
                "product_name": item.description or f"Product #{item.product_id}",
                "warehouse_name": "",
                "quantity": str(item.quantity),
                "unit_price": str(item.unit_price),
                "tax_rate": (
                    str(round(float(item.line_total) and float(invoice.tax_amount) / max(float(invoice.subtotal_amount), 0.01) * 100, 1))
                    if invoice.subtotal_amount and float(invoice.subtotal_amount) > 0 and invoice.tax_amount and float(invoice.tax_amount) > 0
                    else "0"
                ),
                "total_price": str(item.line_total),
            }
            for item in (invoice.items or [])
        ]
        if hasattr(invoice, 'fulfillment_id') and invoice.fulfillment_id:
            fulfillment = self.repository.get_fulfillment(invoice.tenant_id, invoice.fulfillment_id)
            if fulfillment and fulfillment.items:
                for fi in fulfillment.items:
                    if hasattr(fi, 'location_id') and fi.location_id:
                        location = self.repository.get_location(invoice.tenant_id, fi.location_id)
                        if location:
                            warehouse = self.repository.get_warehouse(invoice.tenant_id, location.warehouse_id)
                            if warehouse:
                                for item in items:
                                    if item.get("warehouse_name") == "":
                                        item["warehouse_name"] = warehouse.name
                                        break
        return {
            "invoice": {
                "invoice_number": invoice.invoice_number,
                "invoice_date": str(invoice.issue_date),
                "due_date": str(invoice.due_date) if invoice.due_date else None,
                "subtotal": str(invoice.subtotal_amount),
                "tax_amount": str(invoice.tax_amount),
                "discount_amount": str(invoice.discount_amount),
                "total_amount": str(invoice.total_amount),
                "notes": invoice.notes if hasattr(invoice, "notes") else None,
            },
            "customer": {
                "name": customer.name if customer else f"Customer #{invoice.customer_id}",
                "email": customer.contact_email if customer and hasattr(customer, "contact_email") else (customer.email if customer and hasattr(customer, "email") else None),
                "phone": customer.phone if customer and hasattr(customer, "phone") else None,
                "billing_address": None,
            },
            "sales_order": {"so_number": so.so_number if hasattr(so, "so_number") else str(so.id)} if so else None,
            "items": items,
            "title": f"Invoice {invoice.invoice_number}",
            "intro": f"Please find attached invoice {invoice.invoice_number}.",
            "document_kind": "Invoice",
            "document_number": invoice.invoice_number,
            "sender_name": "",
            "invoice_number": invoice.invoice_number,
            "customer_name": customer.name if customer else f"Customer #{invoice.customer_id}",
            "status": invoice.status.value if hasattr(invoice.status, "value") else str(invoice.status),
            "issue_date": str(invoice.issue_date),
            "due_date": str(invoice.due_date) if invoice.due_date else "",
            "subtotal_amount": str(invoice.subtotal_amount),
            "tax_amount": str(invoice.tax_amount),
            "discount_amount": str(invoice.discount_amount),
            "total_amount": str(invoice.total_amount),
            "currency_code": invoice.currency,
            "currency_symbol": (get_currency_info(invoice.currency) or {}).get("symbol", "$"),
        }

    def _bill_context(self, bill: Bill) -> dict[str, Any]:
        vendor = self.repository.get_vendor(bill.tenant_id, bill.vendor_id)
        po = self.repository.get_purchase_order(bill.tenant_id, bill.purchase_order_id) if bill.purchase_order_id else None
        items = [
            {
                "product_name": item.description or f"Product #{item.product_id}",
                "warehouse_name": "",
                "quantity_ordered": str(item.quantity),
                "unit_price": str(item.unit_cost),
                "tax_rate": (
                    str(round(float(bill.tax_amount) / max(float(bill.subtotal_amount), 0.01) * 100, 1))
                    if bill.subtotal_amount and float(bill.subtotal_amount) > 0 and bill.tax_amount and float(bill.tax_amount) > 0
                    else "0"
                ),
                "total_price": str(item.line_total),
            }
            for item in (bill.items or [])
        ]
        return {
            "bill": {
                "bill_number": bill.bill_number,
                "bill_date": str(bill.issue_date),
                "due_date": str(bill.due_date) if bill.due_date else None,
                "subtotal": str(bill.subtotal_amount),
                "tax_amount": str(bill.tax_amount),
                "total_amount": str(bill.total_amount),
                "notes": bill.notes if hasattr(bill, "notes") else None,
            },
            "vendor": {
                "name": vendor.name if vendor else f"Vendor #{bill.vendor_id}",
                "email": vendor.contact_email if vendor and hasattr(vendor, "contact_email") else (vendor.email if vendor and hasattr(vendor, "email") else None),
                "phone": vendor.phone if vendor and hasattr(vendor, "phone") else None,
                "address": vendor.address if vendor and hasattr(vendor, "address") else None,
            },
            "purchase_order": {"po_number": po.po_number if hasattr(po, "po_number") else str(po.id)} if po else None,
            "items": items,
            "title": f"Bill {bill.bill_number}",
            "intro": f"Please find attached bill {bill.bill_number}.",
            "document_kind": "Bill",
            "document_number": bill.bill_number,
            "sender_name": "",
            "bill_number": bill.bill_number,
            "vendor_name": vendor.name if vendor else f"Vendor #{bill.vendor_id}",
            "status": bill.status.value if hasattr(bill.status, "value") else str(bill.status),
            "issue_date": str(bill.issue_date),
            "due_date": str(bill.due_date) if bill.due_date else "",
            "subtotal_amount": str(bill.subtotal_amount),
            "tax_amount": str(bill.tax_amount),
            "discount_amount": str(bill.discount_amount),
            "total_amount": str(bill.total_amount),
            "currency_code": bill.currency,
            "currency_symbol": (get_currency_info(bill.currency) or {}).get("symbol", "$"),
        }

    def _address_for_party(self, party: Any) -> str | None:
        parts = [getattr(party, field, None) for field in ["name", "email", "phone"]]
        values = [str(part).strip() for part in parts if part]
        return "\n".join(values) if values else None

    def preview_template_pdf(self, tenant_id: int, template_id: int, variables: dict) -> bytes:
        sample = self._sample_pdf_invoice_context()
        context = {**sample, **variables}
        rendered = self.templates.preview_template(tenant_id, template_id, context)
        return render_html_to_pdf(rendered["body"], allow_fallback=True)

    def _sample_pdf_invoice_context(self) -> dict:
        return {
            "tenant": {
                "company_name": "Sample Company Ltd",
                "contact_email": "info@sample.com",
                "phone": "+1 555-0100",
                "address": "123 Business Ave, Suite 200",
                "logo_url": None,
                "footer": "Thank you for your business.",
                "currency": "USD",
            },
            "customer": {"name": "John Doe", "email": "john@example.com", "phone": "+1 555-0200", "billing_address": "456 Customer St"},
            "invoice": {
                "invoice_number": "INV-00001",
                "invoice_date": "2026-05-25",
                "due_date": "2026-06-25",
                "subtotal": "1,000.00",
                "tax_amount": "180.00",
                "discount_amount": "0.00",
                "total_amount": "1,180.00",
                "notes": "Net 30 payment terms.",
            },
            "sales_order": {"so_number": "SO-00001"},
            "items": [
                {"product_name": "Product A", "warehouse_name": "Main WH", "quantity": "10", "unit_price": "50.00", "tax_rate": "18", "total_price": "500.00"},
                {"product_name": "Product B", "warehouse_name": "Main WH", "quantity": "5", "unit_price": "100.00", "tax_rate": "18", "total_price": "500.00"},
            ],
            "vendor": {"name": "Vendor Corp", "email": "vendor@example.com", "phone": "+1 555-0300", "address": "789 Vendor Blvd"},
            "bill": {
                "bill_number": "BILL-00001",
                "bill_date": "2026-05-25",
                "due_date": "2026-06-25",
                "subtotal": "1,000.00",
                "tax_amount": "180.00",
                "total_amount": "1,180.00",
                "notes": "Payment due on receipt.",
            },
            "purchase_order": {"po_number": "PO-00001"},
        }

    def _commit_and_refresh_invoice(self, tenant_id: int, invoice_id: int, action: str, actor_user_id: int) -> Invoice:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("INVOICE_WRITE_FAILED", "Invoice change failed because of duplicate or invalid data.", 409) from exc
        invoice = self.get_invoice(tenant_id, invoice_id)
        self.audit_logs.create(
            {
                "tenant_id": tenant_id,
                "actor_user_id": actor_user_id,
                "actor_role": "",
                "action": action,
                "entity_type": "invoice",
                "entity_id": str(invoice.id),
            }
        )
        self.db.commit()
        return self.get_invoice(tenant_id, invoice_id)

    def _commit_and_refresh_bill(self, tenant_id: int, bill_id: int, action: str, actor_user_id: int) -> Bill:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("BILL_WRITE_FAILED", "Bill change failed because of duplicate or invalid data.", 409) from exc
        bill = self.get_bill(tenant_id, bill_id)
        self.audit_logs.create(
            {
                "tenant_id": tenant_id,
                "actor_user_id": actor_user_id,
                "actor_role": "",
                "action": action,
                "entity_type": "bill",
                "entity_id": str(bill.id),
            }
        )
        self.db.commit()
        return self.get_bill(tenant_id, bill_id)
