from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fulfillment import Package, PickTask
from app.models.inventory import InventoryBatch, InventorySerial, StockLedgerEntry, WarehouseStock
from app.models.master_data import Brand, Category, Product, RecordStatus, Warehouse, WarehouseLocation
from app.models.purchasing import PurchaseOrder, PurchaseReceipt
from app.models.returns import BlockedReturnStock, SalesReturn
from app.models.sales import SalesFulfillment, SalesOrder


class ReportsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def products(self, tenant_id: int) -> list[Product]:
        return list(self.db.scalars(select(Product).where(Product.tenant_id == tenant_id)))

    def active_products(self, tenant_id: int) -> list[Product]:
        return list(self.db.scalars(select(Product).where(Product.tenant_id == tenant_id, Product.status == RecordStatus.ACTIVE)))

    def warehouses(self, tenant_id: int) -> list[Warehouse]:
        return list(self.db.scalars(select(Warehouse).where(Warehouse.tenant_id == tenant_id)))

    def locations(self, tenant_id: int) -> list[WarehouseLocation]:
        return list(self.db.scalars(select(WarehouseLocation).where(WarehouseLocation.tenant_id == tenant_id)))

    def categories(self, tenant_id: int) -> list[Category]:
        return list(self.db.scalars(select(Category).where(Category.tenant_id == tenant_id)))

    def brands(self, tenant_id: int) -> list[Brand]:
        return list(self.db.scalars(select(Brand).where(Brand.tenant_id == tenant_id)))

    def stock(self, tenant_id: int) -> list[WarehouseStock]:
        return list(self.db.scalars(select(WarehouseStock).where(WarehouseStock.tenant_id == tenant_id)))

    def ledger(self, tenant_id: int, date_from: date | None = None, date_to: date | None = None) -> list[StockLedgerEntry]:
        query = select(StockLedgerEntry).where(StockLedgerEntry.tenant_id == tenant_id)
        if date_from:
            query = query.where(StockLedgerEntry.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            query = query.where(StockLedgerEntry.created_at <= datetime.combine(date_to, datetime.max.time()))
        return list(self.db.scalars(query.order_by(StockLedgerEntry.created_at.desc(), StockLedgerEntry.id.desc())))

    def batches(self, tenant_id: int) -> list[InventoryBatch]:
        return list(self.db.scalars(select(InventoryBatch).where(InventoryBatch.tenant_id == tenant_id).order_by(InventoryBatch.expiry_date, InventoryBatch.id)))

    def serials(self, tenant_id: int) -> list[InventorySerial]:
        return list(self.db.scalars(select(InventorySerial).where(InventorySerial.tenant_id == tenant_id).order_by(InventorySerial.created_at.desc(), InventorySerial.id.desc())))

    def blocked_return_stock(self, tenant_id: int) -> list[BlockedReturnStock]:
        return list(self.db.scalars(select(BlockedReturnStock).where(BlockedReturnStock.tenant_id == tenant_id).order_by(BlockedReturnStock.created_at.desc(), BlockedReturnStock.id.desc())))

    def purchase_orders(self, tenant_id: int) -> list[PurchaseOrder]:
        return list(self.db.scalars(select(PurchaseOrder).where(PurchaseOrder.tenant_id == tenant_id)))

    def purchase_receipts(self, tenant_id: int) -> list[PurchaseReceipt]:
        return list(self.db.scalars(select(PurchaseReceipt).where(PurchaseReceipt.tenant_id == tenant_id)))

    def sales_orders(self, tenant_id: int) -> list[SalesOrder]:
        return list(self.db.scalars(select(SalesOrder).where(SalesOrder.tenant_id == tenant_id)))

    def sales_fulfillments(self, tenant_id: int) -> list[SalesFulfillment]:
        return list(self.db.scalars(select(SalesFulfillment).where(SalesFulfillment.tenant_id == tenant_id)))

    def pick_tasks(self, tenant_id: int) -> list[PickTask]:
        return list(self.db.scalars(select(PickTask).where(PickTask.tenant_id == tenant_id).order_by(PickTask.created_at.desc(), PickTask.id.desc())))

    def packages(self, tenant_id: int) -> list[Package]:
        return list(self.db.scalars(select(Package).where(Package.tenant_id == tenant_id)))

    def sales_returns(self, tenant_id: int) -> list[SalesReturn]:
        return list(self.db.scalars(select(SalesReturn).where(SalesReturn.tenant_id == tenant_id)))
