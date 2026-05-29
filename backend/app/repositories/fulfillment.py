from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.fulfillment import Package, PackageItem, PackageStatus, PickTask, PickTaskItem, PickTaskStatus
from app.models.inventory import InventoryBatch, InventorySerial, ReferenceType, ReservationStatus, StockReservation
from app.models.master_data import Product
from app.models.sales import SalesOrder, SalesOrderItem


class FulfillmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_sales_order(self, tenant_id: int, order_id: int) -> SalesOrder | None:
        return self.db.scalar(select(SalesOrder).where(SalesOrder.id == order_id, SalesOrder.tenant_id == tenant_id).options(selectinload(SalesOrder.items)))

    def get_sales_order_item(self, tenant_id: int, item_id: int) -> SalesOrderItem | None:
        return self.db.scalar(select(SalesOrderItem).where(SalesOrderItem.id == item_id, SalesOrderItem.tenant_id == tenant_id))

    def get_product(self, tenant_id: int, product_id: int) -> Product | None:
        return self.db.scalar(select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id))

    def active_reservations_for_order(self, tenant_id: int, order_number: str) -> list[StockReservation]:
        return list(self.db.scalars(select(StockReservation).where(StockReservation.tenant_id == tenant_id, StockReservation.reference_type == ReferenceType.SALES_ORDER, StockReservation.reference_id == order_number, StockReservation.status == ReservationStatus.ACTIVE).order_by(StockReservation.id)))

    def get_reservation(self, tenant_id: int, reservation_id: int) -> StockReservation | None:
        return self.db.scalar(select(StockReservation).where(StockReservation.id == reservation_id, StockReservation.tenant_id == tenant_id))

    def list_pick_tasks(self, tenant_id: int) -> list[PickTask]:
        return list(self.db.scalars(select(PickTask).where(PickTask.tenant_id == tenant_id).options(selectinload(PickTask.items)).order_by(PickTask.created_at.desc(), PickTask.id.desc())))

    def list_pick_tasks_for_order(self, tenant_id: int, order_id: int) -> list[PickTask]:
        return list(self.db.scalars(select(PickTask).where(PickTask.tenant_id == tenant_id, PickTask.sales_order_id == order_id).options(selectinload(PickTask.items)).order_by(PickTask.created_at.desc(), PickTask.id.desc())))

    def get_pick_task(self, tenant_id: int, pick_task_id: int) -> PickTask | None:
        return self.db.scalar(select(PickTask).where(PickTask.id == pick_task_id, PickTask.tenant_id == tenant_id).options(selectinload(PickTask.items)))

    def lock_pick_task(self, tenant_id: int, pick_task_id: int) -> PickTask | None:
        return self.db.scalar(select(PickTask).where(PickTask.id == pick_task_id, PickTask.tenant_id == tenant_id).with_for_update())

    def get_pick_task_item(self, tenant_id: int, item_id: int) -> PickTaskItem | None:
        return self.db.scalar(select(PickTaskItem).where(PickTaskItem.id == item_id, PickTaskItem.tenant_id == tenant_id))

    def lock_pick_task_item(self, tenant_id: int, item_id: int) -> PickTaskItem | None:
        return self.db.scalar(select(PickTaskItem).where(PickTaskItem.id == item_id, PickTaskItem.tenant_id == tenant_id).with_for_update())

    def create_pick_task(self, values: dict) -> PickTask:
        record = PickTask(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def create_pick_task_item(self, values: dict) -> PickTaskItem:
        record = PickTaskItem(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def has_active_pick_for_reservation(self, tenant_id: int, reservation_id: int) -> bool:
        return self.db.scalar(select(PickTaskItem.id).join(PickTask, PickTask.id == PickTaskItem.pick_task_id).where(PickTaskItem.tenant_id == tenant_id, PickTaskItem.reservation_id == reservation_id, PickTask.status != PickTaskStatus.CANCELLED).limit(1)) is not None

    def get_serial(self, tenant_id: int, serial_id: int) -> InventorySerial | None:
        return self.db.scalar(select(InventorySerial).where(InventorySerial.id == serial_id, InventorySerial.tenant_id == tenant_id))

    def get_batch(self, tenant_id: int, batch_id: int) -> InventoryBatch | None:
        return self.db.scalar(select(InventoryBatch).where(InventoryBatch.id == batch_id, InventoryBatch.tenant_id == tenant_id))

    def serial_allocated_elsewhere(self, tenant_id: int, serial_id: int, exclude_item_id: int | None = None) -> bool:
        query = select(PickTaskItem.id).join(PickTask, PickTask.id == PickTaskItem.pick_task_id).where(PickTaskItem.tenant_id == tenant_id, PickTaskItem.serial_id == serial_id, PickTask.status != PickTaskStatus.CANCELLED)
        if exclude_item_id is not None:
            query = query.where(PickTaskItem.id != exclude_item_id)
        return self.db.scalar(query.limit(1)) is not None

    def picked_quantity_for_item(self, tenant_id: int, pick_task_item_id: int) -> float:
        return self.db.scalar(select(func.coalesce(func.sum(PackageItem.quantity), 0)).join(Package, Package.id == PackageItem.package_id).where(PackageItem.tenant_id == tenant_id, PackageItem.pick_task_item_id == pick_task_item_id, Package.status != PackageStatus.CANCELLED)) or 0

    def list_all_packages(self, tenant_id: int) -> list[Package]:
        return list(self.db.scalars(select(Package).where(Package.tenant_id == tenant_id).options(selectinload(Package.items)).order_by(Package.created_at.desc(), Package.id.desc())))

    def list_packages_for_order(self, tenant_id: int, order_id: int) -> list[Package]:
        return list(self.db.scalars(select(Package).where(Package.tenant_id == tenant_id, Package.sales_order_id == order_id).options(selectinload(Package.items)).order_by(Package.created_at.desc(), Package.id.desc())))

    def get_package(self, tenant_id: int, package_id: int) -> Package | None:
        return self.db.scalar(select(Package).where(Package.id == package_id, Package.tenant_id == tenant_id).options(selectinload(Package.items)))

    def lock_package(self, tenant_id: int, package_id: int) -> Package | None:
        return self.db.scalar(select(Package).where(Package.id == package_id, Package.tenant_id == tenant_id).with_for_update())

    def create_package(self, values: dict) -> Package:
        record = Package(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def create_package_item(self, values: dict) -> PackageItem:
        record = PackageItem(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def get_picked_item_for_reservation(self, tenant_id: int, reservation_id: int) -> PickTaskItem | None:
        return self.db.scalar(select(PickTaskItem).join(PickTask, PickTask.id == PickTaskItem.pick_task_id).where(PickTaskItem.tenant_id == tenant_id, PickTaskItem.reservation_id == reservation_id, PickTaskItem.picked_quantity == PickTaskItem.required_quantity, PickTask.status == PickTaskStatus.PICKED).order_by(PickTaskItem.id).limit(1))
