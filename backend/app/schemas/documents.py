from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InvoiceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    product_id: int
    sales_order_item_id: int | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    created_at: datetime


class BillItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    product_id: int
    purchase_order_item_id: int | None = None
    description: str
    quantity: Decimal
    unit_cost: Decimal
    line_total: Decimal
    created_at: datetime


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    sales_order_id: int | None = None
    fulfillment_id: int | None = None
    customer_id: int
    invoice_number: str
    status: str
    issue_date: date
    due_date: date | None = None
    currency: str
    billing_address: str | None = None
    subtotal_amount: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    notes: str | None = None
    sent_at: datetime | None = None
    paid_at: datetime | None = None
    voided_at: datetime | None = None
    pdf_generated_at: datetime | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    items: list[InvoiceItemRead] = []


class BillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    purchase_order_id: int | None = None
    receipt_id: int | None = None
    vendor_id: int
    bill_number: str
    status: str
    issue_date: date
    due_date: date | None = None
    currency: str
    billing_address: str | None = None
    subtotal_amount: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    notes: str | None = None
    sent_at: datetime | None = None
    paid_at: datetime | None = None
    voided_at: datetime | None = None
    pdf_generated_at: datetime | None = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    items: list[BillItemRead] = []


class InvoiceCreate(BaseModel):
    sales_order_id: int | None = None
    fulfillment_id: int | None = None
    issue_date: date | None = None
    due_date: date | None = None
    currency: str | None = None
    notes: str | None = None
    tax_amount: Decimal | None = None
    discount_amount: Decimal | None = None


class BillCreate(BaseModel):
    purchase_order_id: int | None = None
    receipt_id: int | None = None
    issue_date: date | None = None
    due_date: date | None = None
    currency: str | None = None
    notes: str | None = None
    tax_amount: Decimal | None = None
    discount_amount: Decimal | None = None


class DocumentEmailRequest(BaseModel):
    email: str | None = None


class DocumentStatusResponse(BaseModel):
    success: bool = True
    message: str


class DocumentTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    channel: str
    template_key: str | None = None
    purpose: str
    template_code: str
    is_system: bool
    created_by: int | None = None
    cloned_from_template_id: int | None = None
    description: str | None = None
    name: str
    subject_template: str | None = None
    body_template: str
    body_template_text: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DocumentTemplateListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    channel: str
    template_key: str | None = None
    purpose: str
    template_code: str
    is_system: bool
    created_by: int | None = None
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DocumentTemplateDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    channel: str
    template_key: str | None = None
    purpose: str
    template_code: str
    is_system: bool
    created_by: int | None = None
    cloned_from_template_id: int | None = None
    description: str | None = None
    name: str
    subject_template: str | None = None
    body_template: str
    body_template_text: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DocumentTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    purpose: str = Field(..., description="One of: EMAIL_VERIFICATION, INVOICE_EMAIL, BILL_EMAIL, INVOICE_PDF, BILL_PDF")
    description: str | None = Field(None, max_length=500)
    subject_template: str | None = None
    body_template: str = Field(..., min_length=1)
    body_template_text: str | None = None
    is_active: bool = True


class DocumentTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    subject_template: str | None = None
    body_template: str | None = None
    body_template_text: str | None = None
    is_active: bool | None = None


class DocumentTemplateDuplicate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class DocumentTemplatePreviewRequest(BaseModel):
    invoice_id: int | None = None
    bill_id: int | None = None
    sales_order_id: int | None = None
    purchase_order_id: int | None = None
    variables: dict[str, str] = Field(default_factory=dict)


class DocumentTemplatePreviewResponse(BaseModel):
    subject: str | None = None
    body: str
