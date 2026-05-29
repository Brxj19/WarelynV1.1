from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.inventory import InventoryBatch, InventorySerial, MovementType, ReferenceType, StockLedgerEntry
from app.models.master_data import Product, Warehouse, WarehouseLocation
from app.models.returns import BlockedReturnStock, ReturnQCInspection, SalesReturn, SalesReturnItem, SalesReturnStatus
from app.models.sales import SalesOrder, SalesOrderItem


class ReturnsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_returns(self, tenant_id: int) -> list[SalesReturn]:
        return list(self.db.scalars(select(SalesReturn).where(SalesReturn.tenant_id == tenant_id).options(selectinload(SalesReturn.items), selectinload(SalesReturn.blocked_stock)).order_by(SalesReturn.created_at.desc(), SalesReturn.id.desc())))

    def get_return(self, tenant_id: int, return_id: int) -> SalesReturn | None:
        return self.db.scalar(select(SalesReturn).where(SalesReturn.id == return_id, SalesReturn.tenant_id == tenant_id).options(selectinload(SalesReturn.items), selectinload(SalesReturn.inspections), selectinload(SalesReturn.blocked_stock)))

    def lock_return(self, tenant_id: int, return_id: int) -> SalesReturn | None:
        return self.db.scalar(select(SalesReturn).where(SalesReturn.id == return_id, SalesReturn.tenant_id == tenant_id).with_for_update())

    def create_return(self, values: dict) -> SalesReturn:
        record = SalesReturn(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def create_return_item(self, values: dict) -> SalesReturnItem:
        record = SalesReturnItem(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def get_return_item(self, tenant_id: int, item_id: int) -> SalesReturnItem | None:
        return self.db.scalar(select(SalesReturnItem).where(SalesReturnItem.id == item_id, SalesReturnItem.tenant_id == tenant_id))

    def get_sales_order(self, tenant_id: int, order_id: int) -> SalesOrder | None:
        return self.db.scalar(select(SalesOrder).where(SalesOrder.id == order_id, SalesOrder.tenant_id == tenant_id).options(selectinload(SalesOrder.items)))

    def get_sales_order_item(self, tenant_id: int, item_id: int) -> SalesOrderItem | None:
        return self.db.scalar(select(SalesOrderItem).where(SalesOrderItem.id == item_id, SalesOrderItem.tenant_id == tenant_id))

    def get_product(self, tenant_id: int, product_id: int) -> Product | None:
        return self.db.scalar(select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id))

    def get_warehouse(self, tenant_id: int, warehouse_id: int) -> Warehouse | None:
        return self.db.scalar(select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.tenant_id == tenant_id))

    def get_location(self, tenant_id: int, warehouse_id: int, location_id: int) -> WarehouseLocation | None:
        return self.db.scalar(select(WarehouseLocation).where(WarehouseLocation.id == location_id, WarehouseLocation.warehouse_id == warehouse_id, WarehouseLocation.tenant_id == tenant_id))

    def get_serial(self, tenant_id: int, serial_id: int) -> InventorySerial | None:
        return self.db.scalar(select(InventorySerial).where(InventorySerial.id == serial_id, InventorySerial.tenant_id == tenant_id))

    def get_batch(self, tenant_id: int, batch_id: int) -> InventoryBatch | None:
        return self.db.scalar(select(InventoryBatch).where(InventoryBatch.id == batch_id, InventoryBatch.tenant_id == tenant_id))

    def create_inspection(self, values: dict) -> ReturnQCInspection:
        record = ReturnQCInspection(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def get_latest_inspection(self, tenant_id: int, return_id: int) -> ReturnQCInspection | None:
        return self.db.scalar(
            select(ReturnQCInspection)
            .where(
                ReturnQCInspection.tenant_id == tenant_id,
                ReturnQCInspection.sales_return_id == return_id,
            )
            .order_by(ReturnQCInspection.created_at.desc())
            .limit(1)
        )

    def returned_quantity_for_order_item(self, tenant_id: int, sales_order_item_id: int, exclude_return_id: int | None = None) -> Decimal:
        query = select(func.coalesce(func.sum(SalesReturnItem.returned_quantity), 0)).join(SalesReturn, SalesReturn.id == SalesReturnItem.sales_return_id).where(
            SalesReturnItem.tenant_id == tenant_id,
            SalesReturnItem.sales_order_item_id == sales_order_item_id,
            SalesReturn.status != SalesReturnStatus.CANCELLED,
        )
        if exclude_return_id is not None:
            query = query.where(SalesReturn.id != exclude_return_id)
        return self.db.scalar(query) or Decimal("0")

    def serial_was_deducted_for_order(self, tenant_id: int, serial_id: int, order_number: str) -> bool:
        return self.db.scalar(
            select(StockLedgerEntry.id)
            .where(
                StockLedgerEntry.tenant_id == tenant_id,
                StockLedgerEntry.serial_id == serial_id,
                StockLedgerEntry.movement_type == MovementType.SALES_DEDUCT,
                StockLedgerEntry.reference_type == ReferenceType.SALES_ORDER,
                StockLedgerEntry.reference_id == order_number,
            )
            .limit(1)
        ) is not None

    def list_blocked_return_stock(self, tenant_id: int) -> list[BlockedReturnStock]:
        return list(self.db.scalars(select(BlockedReturnStock).where(BlockedReturnStock.tenant_id == tenant_id).order_by(BlockedReturnStock.created_at.desc(), BlockedReturnStock.id.desc())))
