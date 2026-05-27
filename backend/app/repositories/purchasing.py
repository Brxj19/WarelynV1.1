from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.master_data import Product, Vendor, Warehouse, WarehouseLocation
from app.models.purchasing import PurchaseOrder, PurchaseOrderItem, PurchaseReceipt, PurchaseReceiptItem


class PurchasingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_purchase_orders(self, tenant_id: int) -> list[PurchaseOrder]:
        return list(
            self.db.scalars(
                select(PurchaseOrder)
                .where(PurchaseOrder.tenant_id == tenant_id)
                .options(selectinload(PurchaseOrder.items))
                .order_by(PurchaseOrder.created_at.desc(), PurchaseOrder.id.desc())
            )
        )

    def get_purchase_order(self, tenant_id: int, po_id: int) -> PurchaseOrder | None:
        return self.db.scalar(
            select(PurchaseOrder)
            .where(PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == tenant_id)
            .options(selectinload(PurchaseOrder.items))
        )

    def lock_purchase_order(self, tenant_id: int, po_id: int) -> PurchaseOrder | None:
        return self.db.scalar(select(PurchaseOrder).where(PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == tenant_id).with_for_update())

    def create_purchase_order(self, values: dict) -> PurchaseOrder:
        record = PurchaseOrder(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def create_purchase_order_item(self, values: dict) -> PurchaseOrderItem:
        record = PurchaseOrderItem(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def delete_purchase_order_items(self, tenant_id: int, po_id: int) -> None:
        self.db.execute(delete(PurchaseOrderItem).where(PurchaseOrderItem.tenant_id == tenant_id, PurchaseOrderItem.purchase_order_id == po_id))

    def get_purchase_order_item(self, tenant_id: int, item_id: int) -> PurchaseOrderItem | None:
        return self.db.scalar(select(PurchaseOrderItem).where(PurchaseOrderItem.id == item_id, PurchaseOrderItem.tenant_id == tenant_id))

    def lock_purchase_order_item(self, tenant_id: int, item_id: int) -> PurchaseOrderItem | None:
        return self.db.scalar(select(PurchaseOrderItem).where(PurchaseOrderItem.id == item_id, PurchaseOrderItem.tenant_id == tenant_id).with_for_update())

    def list_receipts_for_order(self, tenant_id: int, po_id: int) -> list[PurchaseReceipt]:
        return list(
            self.db.scalars(
                select(PurchaseReceipt)
                .where(PurchaseReceipt.tenant_id == tenant_id, PurchaseReceipt.purchase_order_id == po_id)
                .options(selectinload(PurchaseReceipt.items))
                .order_by(PurchaseReceipt.created_at.desc(), PurchaseReceipt.id.desc())
            )
        )

    def get_receipt(self, tenant_id: int, receipt_id: int) -> PurchaseReceipt | None:
        return self.db.scalar(
            select(PurchaseReceipt)
            .where(PurchaseReceipt.id == receipt_id, PurchaseReceipt.tenant_id == tenant_id)
            .options(selectinload(PurchaseReceipt.items))
        )

    def lock_receipt(self, tenant_id: int, receipt_id: int) -> PurchaseReceipt | None:
        return self.db.scalar(select(PurchaseReceipt).where(PurchaseReceipt.id == receipt_id, PurchaseReceipt.tenant_id == tenant_id).with_for_update())

    def create_receipt(self, values: dict) -> PurchaseReceipt:
        record = PurchaseReceipt(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def create_receipt_item(self, values: dict) -> PurchaseReceiptItem:
        record = PurchaseReceiptItem(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def delete_receipt_items(self, tenant_id: int, receipt_id: int) -> None:
        self.db.execute(delete(PurchaseReceiptItem).where(PurchaseReceiptItem.tenant_id == tenant_id, PurchaseReceiptItem.purchase_receipt_id == receipt_id))

    def get_vendor(self, tenant_id: int, vendor_id: int) -> Vendor | None:
        return self.db.scalar(select(Vendor).where(Vendor.id == vendor_id, Vendor.tenant_id == tenant_id))

    def get_product(self, tenant_id: int, product_id: int) -> Product | None:
        return self.db.scalar(select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id))

    def get_warehouse(self, tenant_id: int, warehouse_id: int) -> Warehouse | None:
        return self.db.scalar(select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.tenant_id == tenant_id))

    def get_location(self, tenant_id: int, warehouse_id: int, location_id: int) -> WarehouseLocation | None:
        return self.db.scalar(select(WarehouseLocation).where(WarehouseLocation.id == location_id, WarehouseLocation.warehouse_id == warehouse_id, WarehouseLocation.tenant_id == tenant_id))
