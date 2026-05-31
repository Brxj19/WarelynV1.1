from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.inventory import ReservationStatus, StockReservation
from app.models.master_data import Customer, Product, Warehouse, WarehouseLocation
from app.models.sales import SalesFulfillment, SalesFulfillmentItem, SalesFulfillmentStatus, SalesOrder, SalesOrderItem


class SalesRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_sales_orders(self, tenant_id: int) -> list[SalesOrder]:
        return list(self.db.scalars(select(SalesOrder).where(SalesOrder.tenant_id == tenant_id).options(selectinload(SalesOrder.items)).order_by(SalesOrder.created_at.desc(), SalesOrder.id.desc())))

    def get_sales_order(self, tenant_id: int, order_id: int) -> SalesOrder | None:
        return self.db.scalar(select(SalesOrder).where(SalesOrder.id == order_id, SalesOrder.tenant_id == tenant_id).options(selectinload(SalesOrder.items)))

    def lock_sales_order(self, tenant_id: int, order_id: int) -> SalesOrder | None:
        return self.db.scalar(select(SalesOrder).where(SalesOrder.id == order_id, SalesOrder.tenant_id == tenant_id).with_for_update())

    def create_sales_order(self, values: dict) -> SalesOrder:
        record = SalesOrder(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def create_sales_order_item(self, values: dict) -> SalesOrderItem:
        record = SalesOrderItem(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def delete_sales_order_items(self, tenant_id: int, order_id: int) -> None:
        self.db.execute(delete(SalesOrderItem).where(SalesOrderItem.tenant_id == tenant_id, SalesOrderItem.sales_order_id == order_id))

    def get_sales_order_item(self, tenant_id: int, item_id: int) -> SalesOrderItem | None:
        return self.db.scalar(select(SalesOrderItem).where(SalesOrderItem.id == item_id, SalesOrderItem.tenant_id == tenant_id))

    def lock_sales_order_item(self, tenant_id: int, item_id: int) -> SalesOrderItem | None:
        return self.db.scalar(select(SalesOrderItem).where(SalesOrderItem.id == item_id, SalesOrderItem.tenant_id == tenant_id).with_for_update())

    def list_fulfillments_for_order(self, tenant_id: int, order_id: int) -> list[SalesFulfillment]:
        return list(self.db.scalars(select(SalesFulfillment).where(SalesFulfillment.tenant_id == tenant_id, SalesFulfillment.sales_order_id == order_id).options(selectinload(SalesFulfillment.items)).order_by(SalesFulfillment.created_at.desc(), SalesFulfillment.id.desc())))

    def get_open_draft_fulfillment_for_order(self, tenant_id: int, order_id: int) -> SalesFulfillment | None:
        return self.db.scalar(
            select(SalesFulfillment)
            .where(
                SalesFulfillment.tenant_id == tenant_id,
                SalesFulfillment.sales_order_id == order_id,
                SalesFulfillment.status == SalesFulfillmentStatus.DRAFT,
            )
            .options(selectinload(SalesFulfillment.items))
            .order_by(SalesFulfillment.created_at.desc(), SalesFulfillment.id.desc())
            .limit(1)
        )

    def list_all_fulfillments(self, tenant_id: int) -> list[SalesFulfillment]:
        return list(self.db.scalars(select(SalesFulfillment).where(SalesFulfillment.tenant_id == tenant_id).options(selectinload(SalesFulfillment.items)).order_by(SalesFulfillment.created_at.desc(), SalesFulfillment.id.desc())))

    def get_fulfillment(self, tenant_id: int, fulfillment_id: int) -> SalesFulfillment | None:
        return self.db.scalar(select(SalesFulfillment).where(SalesFulfillment.id == fulfillment_id, SalesFulfillment.tenant_id == tenant_id).options(selectinload(SalesFulfillment.items)))

    def lock_fulfillment(self, tenant_id: int, fulfillment_id: int) -> SalesFulfillment | None:
        return self.db.scalar(select(SalesFulfillment).where(SalesFulfillment.id == fulfillment_id, SalesFulfillment.tenant_id == tenant_id).with_for_update())

    def create_fulfillment(self, values: dict) -> SalesFulfillment:
        record = SalesFulfillment(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def create_fulfillment_item(self, values: dict) -> SalesFulfillmentItem:
        record = SalesFulfillmentItem(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def get_fulfillment_item_by_reservation(
        self,
        tenant_id: int,
        fulfillment_id: int,
        reservation_id: int,
    ) -> SalesFulfillmentItem | None:
        return self.db.scalar(
            select(SalesFulfillmentItem).where(
                SalesFulfillmentItem.tenant_id == tenant_id,
                SalesFulfillmentItem.fulfillment_id == fulfillment_id,
                SalesFulfillmentItem.reservation_id == reservation_id,
            )
        )

    def delete_fulfillment_items(self, tenant_id: int, fulfillment_id: int) -> None:
        self.db.execute(delete(SalesFulfillmentItem).where(SalesFulfillmentItem.tenant_id == tenant_id, SalesFulfillmentItem.fulfillment_id == fulfillment_id))

    def get_customer(self, tenant_id: int, customer_id: int) -> Customer | None:
        return self.db.scalar(select(Customer).where(Customer.id == customer_id, Customer.tenant_id == tenant_id))

    def get_product(self, tenant_id: int, product_id: int) -> Product | None:
        return self.db.scalar(select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id))

    def get_warehouse(self, tenant_id: int, warehouse_id: int) -> Warehouse | None:
        return self.db.scalar(select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.tenant_id == tenant_id))

    def get_location(self, tenant_id: int, warehouse_id: int, location_id: int) -> WarehouseLocation | None:
        return self.db.scalar(select(WarehouseLocation).where(WarehouseLocation.id == location_id, WarehouseLocation.warehouse_id == warehouse_id, WarehouseLocation.tenant_id == tenant_id))

    def get_reservation(self, tenant_id: int, reservation_id: int) -> StockReservation | None:
        return self.db.scalar(select(StockReservation).where(StockReservation.id == reservation_id, StockReservation.tenant_id == tenant_id))

    def active_reservations_for_order(self, tenant_id: int, order_number: str) -> list[StockReservation]:
        return list(self.db.scalars(select(StockReservation).where(StockReservation.tenant_id == tenant_id, StockReservation.reference_id == order_number, StockReservation.status == ReservationStatus.ACTIVE).order_by(StockReservation.id)))
