from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.auth import Tenant
from app.models.documents import Bill, DocumentTemplate, DocumentTemplateChannel, DocumentTemplateKey, DocumentTemplatePurpose, Invoice, NumberSequence, NumberSequenceKey
from app.models.master_data import Customer, Product, Vendor
from app.models.purchasing import PurchaseOrder, PurchaseReceipt
from app.models.sales import SalesFulfillment, SalesOrder
from app.models.settings import TenantSettings, UserPreferences


class DocumentsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_invoice(self, tenant_id: int, invoice_id: int) -> Invoice | None:
        return self.db.scalar(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(Invoice.tenant_id == tenant_id, Invoice.id == invoice_id)
        )

    def list_invoices(self, tenant_id: int) -> list[Invoice]:
        return list(
            self.db.scalars(
                select(Invoice)
                .options(selectinload(Invoice.items))
                .where(Invoice.tenant_id == tenant_id)
                .order_by(Invoice.created_at.desc(), Invoice.id.desc())
            )
        )

    def create_invoice(self, values: dict) -> Invoice:
        invoice = Invoice(**values)
        self.db.add(invoice)
        self.db.flush()
        return invoice

    def get_bill(self, tenant_id: int, bill_id: int) -> Bill | None:
        return self.db.scalar(
            select(Bill)
            .options(selectinload(Bill.items))
            .where(Bill.tenant_id == tenant_id, Bill.id == bill_id)
        )

    def get_bill_for_purchase_order(self, tenant_id: int, purchase_order_id: int) -> Bill | None:
        from app.models.documents import BillStatus
        return self.db.scalar(
            select(Bill).where(
                Bill.tenant_id == tenant_id,
                Bill.purchase_order_id == purchase_order_id,
                Bill.status != BillStatus.VOID,
            )
        )

    def get_invoice_for_sales_order(self, tenant_id: int, sales_order_id: int) -> Invoice | None:
        from app.models.documents import InvoiceStatus
        return self.db.scalar(
            select(Invoice).where(
                Invoice.tenant_id == tenant_id,
                Invoice.sales_order_id == sales_order_id,
                Invoice.status != InvoiceStatus.VOID,
            )
        )

    def list_bills(self, tenant_id: int) -> list[Bill]:
        return list(
            self.db.scalars(
                select(Bill)
                .options(selectinload(Bill.items))
                .where(Bill.tenant_id == tenant_id)
                .order_by(Bill.created_at.desc(), Bill.id.desc())
            )
        )

    def create_bill(self, values: dict) -> Bill:
        bill = Bill(**values)
        self.db.add(bill)
        self.db.flush()
        return bill

    def get_sales_order(self, tenant_id: int, order_id: int) -> SalesOrder | None:
        return self.db.scalar(
            select(SalesOrder)
            .options(selectinload(SalesOrder.items))
            .where(SalesOrder.tenant_id == tenant_id, SalesOrder.id == order_id)
        )

    def get_fulfillment(self, tenant_id: int, fulfillment_id: int) -> SalesFulfillment | None:
        return self.db.scalar(
            select(SalesFulfillment)
            .options(selectinload(SalesFulfillment.items))
            .where(SalesFulfillment.tenant_id == tenant_id, SalesFulfillment.id == fulfillment_id)
        )

    def get_purchase_order(self, tenant_id: int, po_id: int) -> PurchaseOrder | None:
        return self.db.scalar(
            select(PurchaseOrder)
            .options(selectinload(PurchaseOrder.items))
            .where(PurchaseOrder.tenant_id == tenant_id, PurchaseOrder.id == po_id)
        )

    def get_purchase_receipt(self, tenant_id: int, receipt_id: int) -> PurchaseReceipt | None:
        return self.db.scalar(
            select(PurchaseReceipt)
            .options(selectinload(PurchaseReceipt.items))
            .where(PurchaseReceipt.tenant_id == tenant_id, PurchaseReceipt.id == receipt_id)
        )

    def get_customer(self, tenant_id: int, customer_id: int) -> Customer | None:
        return self.db.scalar(select(Customer).where(Customer.tenant_id == tenant_id, Customer.id == customer_id))

    def get_vendor(self, tenant_id: int, vendor_id: int) -> Vendor | None:
        return self.db.scalar(select(Vendor).where(Vendor.tenant_id == tenant_id, Vendor.id == vendor_id))

    def get_product(self, tenant_id: int, product_id: int) -> Product | None:
        return self.db.scalar(select(Product).where(Product.tenant_id == tenant_id, Product.id == product_id))

    def get_tenant(self, tenant_id: int) -> Tenant | None:
        return self.db.scalar(select(Tenant).where(Tenant.id == tenant_id))

    def get_tenant_settings(self, tenant_id: int) -> TenantSettings | None:
        return self.db.scalar(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))

    def get_sequence(self, tenant_id: int, sequence_key: NumberSequenceKey) -> NumberSequence | None:
        return self.db.scalar(
            select(NumberSequence).where(NumberSequence.tenant_id == tenant_id, NumberSequence.sequence_key == sequence_key)
        )

    def get_or_create_sequence(self, tenant_id: int, sequence_key: NumberSequenceKey, prefix: str, padding: int) -> NumberSequence:
        seq = self.get_sequence(tenant_id, sequence_key)
        if seq is None:
            seq = self.create_sequence({"tenant_id": tenant_id, "sequence_key": sequence_key, "prefix": prefix, "next_number": 1, "padding": padding})
        return seq

    def create_sequence(self, values: dict) -> NumberSequence:
        sequence = NumberSequence(**values)
        self.db.add(sequence)
        self.db.flush()
        return sequence

    def list_templates(self, tenant_id: int, channel: DocumentTemplateChannel | None = None) -> list[DocumentTemplate]:
        stmt = select(DocumentTemplate).where(DocumentTemplate.tenant_id == tenant_id)
        if channel is not None:
            stmt = stmt.where(DocumentTemplate.channel == channel)
        stmt = stmt.order_by(DocumentTemplate.channel.asc(), DocumentTemplate.template_key.asc())
        return list(self.db.scalars(stmt))

    def get_template(self, tenant_id: int, template_id: int) -> DocumentTemplate | None:
        return self.db.scalar(
            select(DocumentTemplate).where(DocumentTemplate.tenant_id == tenant_id, DocumentTemplate.id == template_id)
        )

    def get_template_by_key(
        self,
        tenant_id: int,
        channel: DocumentTemplateChannel,
        template_key: DocumentTemplateKey,
    ) -> DocumentTemplate | None:
        return self.db.scalar(
            select(DocumentTemplate).where(
                DocumentTemplate.tenant_id == tenant_id,
                DocumentTemplate.channel == channel,
                DocumentTemplate.template_key == template_key,
            )
        )

    def create_template(self, values: dict) -> DocumentTemplate:
        template = DocumentTemplate(**values)
        self.db.add(template)
        self.db.flush()
        return template

    def get_location(self, tenant_id: int, location_id: int):
        from app.models.master_data import WarehouseLocation
        return self.db.scalar(
            select(WarehouseLocation).where(
                WarehouseLocation.id == location_id,
                WarehouseLocation.tenant_id == tenant_id,
            )
        )

    def get_warehouse(self, tenant_id: int, warehouse_id: int):
        from app.models.master_data import Warehouse
        return self.db.scalar(
            select(Warehouse).where(
                Warehouse.id == warehouse_id,
                Warehouse.tenant_id == tenant_id,
            )
        )

    def get_template_by_id(self, tenant_id: int, template_id: int) -> DocumentTemplate | None:
        return self.db.scalar(
            select(DocumentTemplate).where(
                DocumentTemplate.tenant_id == tenant_id,
                DocumentTemplate.id == template_id,
                DocumentTemplate.is_active == True,
            )
        )

    def list_templates_by_purpose(self, tenant_id: int, purpose: DocumentTemplatePurpose) -> list[DocumentTemplate]:
        stmt = select(DocumentTemplate).where(
            DocumentTemplate.tenant_id == tenant_id,
            DocumentTemplate.purpose == purpose,
        ).order_by(DocumentTemplate.is_system.desc(), DocumentTemplate.name.asc())
        return list(self.db.scalars(stmt))

    def duplicate_template(self, tenant_id: int, template_id: int, new_name: str, new_code: str, user_id: int, description: str | None = None) -> DocumentTemplate | None:
        source = self.db.scalar(
            select(DocumentTemplate).where(
                DocumentTemplate.tenant_id == tenant_id,
                DocumentTemplate.id == template_id,
            )
        )
        if source is None:
            return None
        new_template = DocumentTemplate(
            tenant_id=tenant_id,
            channel=source.channel,
            template_key=None,
            purpose=source.purpose,
            template_code=new_code,
            is_system=False,
            created_by=user_id,
            cloned_from_template_id=source.id,
            description=description or source.description,
            name=new_name,
            subject_template=source.subject_template,
            body_template=source.body_template,
            body_template_text=source.body_template_text,
            is_active=True,
        )
        self.db.add(new_template)
        self.db.flush()
        return new_template

    def delete_template(self, tenant_id: int, template_id: int) -> bool:
        template = self.db.scalar(
            select(DocumentTemplate).where(
                DocumentTemplate.tenant_id == tenant_id,
                DocumentTemplate.id == template_id,
            )
        )
        if template is None:
            return False
        self.db.delete(template)
        self.db.flush()
        return True

    def get_templates_for_preference(self, tenant_id: int, purpose: DocumentTemplatePurpose) -> list[DocumentTemplate]:
        stmt = select(DocumentTemplate).where(
            DocumentTemplate.tenant_id == tenant_id,
            DocumentTemplate.purpose == purpose,
            DocumentTemplate.is_active == True,
        ).order_by(DocumentTemplate.is_system.desc(), DocumentTemplate.name.asc())
        return list(self.db.scalars(stmt))

    def is_template_in_use_by_preference(self, template_id: int) -> bool:
        """Check if any user preference references this template."""
        stmt = select(UserPreferences).where(
            (UserPreferences.preferred_invoice_template_id == template_id)
            | (UserPreferences.preferred_bill_template_id == template_id)
            | (UserPreferences.preferred_invoice_email_template_id == template_id)
            | (UserPreferences.preferred_bill_email_template_id == template_id)
            | (UserPreferences.preferred_verification_template_id == template_id)
        )
        return self.db.scalar(stmt) is not None
