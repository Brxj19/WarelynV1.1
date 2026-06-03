import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, LargeBinary, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NumberSequenceKey(str, enum.Enum):
    INVOICE = "INVOICE"
    BILL = "BILL"
    GRN = "GRN"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    SALES_ORDER = "SALES_ORDER"


class DocumentTemplateChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    PDF = "PDF"


class DocumentTemplatePurpose(str, enum.Enum):
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    INVOICE_EMAIL = "INVOICE_EMAIL"
    BILL_EMAIL = "BILL_EMAIL"
    INVOICE_PDF = "INVOICE_PDF"
    BILL_PDF = "BILL_PDF"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    PASSWORD_RESET = "PASSWORD_RESET"
    USER_DISABLED = "USER_DISABLED"
    USER_ENABLED = "USER_ENABLED"
    ROLE_CHANGED = "ROLE_CHANGED"


class DocumentTemplateKey(str, enum.Enum):
    EMAIL_VERIFICATION = "EMAIL_VERIFICATION"
    EMAIL_VERIFICATION_MODERN = "EMAIL_VERIFICATION_MODERN"
    EMAIL_VERIFICATION_MINIMAL = "EMAIL_VERIFICATION_MINIMAL"
    INVOICE_SEND = "INVOICE_SEND"
    INVOICE_SEND_MODERN = "INVOICE_SEND_MODERN"
    INVOICE_SEND_MINIMAL = "INVOICE_SEND_MINIMAL"
    INVOICE_SEND_FORMAL = "INVOICE_SEND_FORMAL"
    BILL_SEND = "BILL_SEND"
    BILL_SEND_MODERN = "BILL_SEND_MODERN"
    BILL_SEND_MINIMAL = "BILL_SEND_MINIMAL"
    BILL_SEND_FORMAL = "BILL_SEND_FORMAL"
    PDF_INVOICE = "PDF_INVOICE"
    PDF_INVOICE_MODERN = "PDF_INVOICE_MODERN"
    PDF_INVOICE_MINIMAL = "PDF_INVOICE_MINIMAL"
    PDF_INVOICE_BOLD = "PDF_INVOICE_BOLD"
    PDF_INVOICE_WARM = "PDF_INVOICE_WARM"
    PDF_BILL = "PDF_BILL"
    PDF_BILL_MODERN = "PDF_BILL_MODERN"
    PDF_BILL_MINIMAL = "PDF_BILL_MINIMAL"
    PDF_BILL_BOLD = "PDF_BILL_BOLD"
    PDF_BILL_WARM = "PDF_BILL_WARM"
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    PASSWORD_RESET = "PASSWORD_RESET"
    USER_DISABLED = "USER_DISABLED"
    USER_ENABLED = "USER_ENABLED"
    ROLE_CHANGED = "ROLE_CHANGED"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    VOID = "VOID"


class BillStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    VOID = "VOID"


class NumberSequence(Base):
    __tablename__ = "number_sequences"
    __table_args__ = (UniqueConstraint("tenant_id", "sequence_key", name="uq_number_sequences_tenant_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_key: Mapped[NumberSequenceKey] = mapped_column(
        Enum(NumberSequenceKey, name="number_sequence_key", native_enum=False),
        nullable=False,
        index=True,
    )
    prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    next_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    padding: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class DocumentTemplate(Base):
    __tablename__ = "document_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "template_code", name="uq_document_templates_tenant_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[DocumentTemplateChannel] = mapped_column(
        Enum(DocumentTemplateChannel, name="document_template_channel", native_enum=False),
        nullable=False,
        index=True,
    )
    template_key: Mapped[DocumentTemplateKey | None] = mapped_column(
        Enum(DocumentTemplateKey, name="document_template_key", native_enum=False),
        nullable=True,
        index=True,
    )
    purpose: Mapped[DocumentTemplatePurpose] = mapped_column(
        Enum(DocumentTemplatePurpose, name="document_template_purpose", native_enum=False),
        nullable=False,
        index=True,
    )
    template_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    cloned_from_template_id: Mapped[int | None] = mapped_column(ForeignKey("document_templates.id"), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_template: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    body_template_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("tenant_id", "invoice_number", name="uq_invoices_tenant_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_id: Mapped[int | None] = mapped_column(ForeignKey("sales_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    fulfillment_id: Mapped[int | None] = mapped_column(ForeignKey("sales_fulfillments.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus, name="invoice_status", native_enum=False), default=InvoiceStatus.DRAFT, nullable=False, index=True)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    billing_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    items: Mapped[list["InvoiceItem"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    sales_order_item_id: Mapped[int | None] = mapped_column(ForeignKey("sales_order_items.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="items")


class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = (UniqueConstraint("tenant_id", "bill_number", name="uq_bills_tenant_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_order_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True, index=True)
    receipt_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_receipts.id", ondelete="SET NULL"), nullable=True, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=False, index=True)
    bill_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    status: Mapped[BillStatus] = mapped_column(Enum(BillStatus, name="bill_status", native_enum=False), default=BillStatus.DRAFT, nullable=False, index=True)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    billing_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pdf_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    items: Mapped[list["BillItem"]] = relationship(back_populates="bill", cascade="all, delete-orphan")


class BillItem(Base):
    __tablename__ = "bill_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_order_item_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_order_items.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    bill: Mapped[Bill] = relationship(back_populates="items")
