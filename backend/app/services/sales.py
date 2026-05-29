from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.inventory import ReferenceType, ReservationStatus
from app.models.sales import SalesFulfillment, SalesFulfillmentStatus, SalesOrder, SalesOrderItem, SalesOrderStatus
from app.repositories.fulfillment import FulfillmentRepository
from app.repositories.sales import SalesRepository
from app.schemas.workflow import WorkflowTaskCreate
from app.services.inventory import InventoryService
from app.services.workflow import WorkflowService

FULFILLABLE_STATUSES = {SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIALLY_FULFILLED}
ZERO = Decimal("0")


class SalesService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SalesRepository(db)
        self.fulfillment_repository = FulfillmentRepository(db)

    def list_sales_orders(self, tenant_id: int) -> list[SalesOrder]:
        return self.repository.list_sales_orders(tenant_id)

    def get_sales_order(self, tenant_id: int, order_id: int) -> SalesOrder:
        order = self.repository.get_sales_order(tenant_id, order_id)
        if order is None:
            raise AppError("SALES_ORDER_NOT_FOUND", "Sales order was not found for this tenant.", 404)
        return order

    def create_sales_order(self, tenant_id: int, actor_id: int, values: dict[str, Any]) -> SalesOrder:
        self._require_customer(tenant_id, values["customer_id"])
        items = values.pop("items", [])
        order = self.repository.create_sales_order({**values, "tenant_id": tenant_id, "created_by": actor_id, "status": SalesOrderStatus.DRAFT})
        self._replace_order_items(tenant_id, order.id, items)
        return self._commit_and_get_order(tenant_id, order.id)

    def update_sales_order(self, tenant_id: int, order_id: int, values: dict[str, Any]) -> SalesOrder:
        order = self.get_sales_order(tenant_id, order_id)
        if order.status != SalesOrderStatus.DRAFT:
            raise AppError("INVALID_SALES_ORDER_STATE", "Only draft sales orders can be edited.", 409)
        if values.get("customer_id"):
            self._require_customer(tenant_id, values["customer_id"])
        items = values.pop("items", None)
        for key, value in values.items():
            setattr(order, key, value)
        if items is not None:
            self.repository.delete_sales_order_items(tenant_id, order.id)
            self._replace_order_items(tenant_id, order.id, items)
        return self._commit_and_get_order(tenant_id, order.id)

    def confirm_sales_order(self, tenant_id: int, actor_id: int, order_id: int, values: dict[str, Any]) -> dict[str, Any]:
        order = self.repository.lock_sales_order(tenant_id, order_id)
        if order is None:
            raise AppError("SALES_ORDER_NOT_FOUND", "Sales order was not found for this tenant.", 404)
        if order.status == SalesOrderStatus.CONFIRMED:
            return {"sales_order": self.get_sales_order(tenant_id, order.id), "fulfillment": None, "stock_results": []}
        if order.status != SalesOrderStatus.DRAFT:
            raise AppError("INVALID_SALES_ORDER_STATE", "Only draft sales orders can be confirmed.", 409)
        order = self.get_sales_order(tenant_id, order_id)
        if not order.items:
            raise AppError("SALES_ORDER_ITEMS_REQUIRED", "Sales order must include at least one item before confirmation.", 400)
        allocations = values.get("allocations") or []
        if not allocations:
            raise AppError("SALES_ALLOCATIONS_REQUIRED", "Sales confirmation requires explicit warehouse/location allocation lines.", 400)
        self._validate_confirm_allocations(tenant_id, order, allocations)
        stock_results = []
        try:
            for index, allocation in enumerate(allocations):
                item = self.repository.lock_sales_order_item(tenant_id, allocation["sales_order_item_id"])
                if item is None or item.sales_order_id != order.id:
                    raise AppError("SALES_ORDER_ITEM_NOT_FOUND", "Sales order item was not found for this sales order.", 404)
                result = InventoryService(self.db).reserve_stock(
                    tenant_id,
                    actor_id,
                    {
                        "product_id": item.product_id,
                        "warehouse_id": allocation["warehouse_id"],
                        "location_id": allocation["location_id"],
                        "quantity": allocation["quantity"],
                        "reference_type": ReferenceType.SALES_ORDER,
                        "reference_id": order.order_number,
                        "note": values.get("note") or order.notes,
                        "idempotency_key": f"{values['idempotency_key']}:sales-order:{order.id}:reserve:{index}",
                    },
                    auto_commit=False,
                )
                stock_results.append(result)
                item.reserved_quantity += Decimal(str(allocation["quantity"]))
            order.status = SalesOrderStatus.CONFIRMED
            order.confirmed_at = datetime.now(UTC)
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("SALES_ORDER_CONFIRM_FAILED", "Sales order confirmation failed because of duplicate or invalid data.", 409) from exc
        try:
            workflow = WorkflowService(self.db)
            workflow.log_event(tenant_id, "SALES_ORDER_CONFIRMED", "sales_order", order.id, actor_id, {"order_number": order.order_number})
            workflow.create_task(tenant_id, WorkflowTaskCreate(
                workflow_type="SALES",
                entity_type="sales_order",
                entity_id=order.id,
                step_key="PICK_ORDER",
                title=f"Pick items for order {order.order_number}",
                description="Sales order confirmed. Pick and reserve required stock.",
                assigned_role="INVENTORY_MANAGER",
                priority="NORMAL",
                action_url=f"/sales/{order.id}",
            ), created_by=actor_id)
            self.db.commit()
        except Exception:
            pass
        try:
            self._auto_create_pick_task(tenant_id, actor_id, order)
        except Exception:
            pass
        return {"sales_order": self.get_sales_order(tenant_id, order.id), "fulfillment": None, "stock_results": stock_results}

    def cancel_sales_order(self, tenant_id: int, actor_id: int, order_id: int, values: dict[str, Any] | None = None) -> SalesOrder:
        values = values or {}
        order = self.repository.lock_sales_order(tenant_id, order_id)
        if order is None:
            raise AppError("SALES_ORDER_NOT_FOUND", "Sales order was not found for this tenant.", 404)
        if order.status == SalesOrderStatus.DRAFT:
            order.status = SalesOrderStatus.CANCELLED
            order.cancelled_at = datetime.now(UTC)
            result = self._commit_and_get_order(tenant_id, order.id)
            try:
                WorkflowService(self.db).cancel_entity_tasks(tenant_id, "sales_order", order.id)
                self.db.commit()
            except Exception:
                pass
            return result
        if order.status not in {SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIALLY_FULFILLED}:
            raise AppError("INVALID_SALES_ORDER_STATE", "Only draft, confirmed, or partially fulfilled sales orders can be cancelled.", 409)
        result = self._release_and_mark_order(tenant_id, actor_id, order, SalesOrderStatus.CANCELLED, "cancelled_at", values)
        try:
            WorkflowService(self.db).cancel_entity_tasks(tenant_id, "sales_order", order.id)
            self.db.commit()
        except Exception:
            pass
        return result

    def close_sales_order(self, tenant_id: int, actor_id: int, order_id: int, values: dict[str, Any] | None = None) -> SalesOrder:
        values = values or {}
        order = self.repository.lock_sales_order(tenant_id, order_id)
        if order is None:
            raise AppError("SALES_ORDER_NOT_FOUND", "Sales order was not found for this tenant.", 404)
        if order.status not in {SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIALLY_FULFILLED}:
            raise AppError("INVALID_SALES_ORDER_STATE", "Only confirmed or partially fulfilled sales orders can be closed.", 409)
        return self._release_and_mark_order(tenant_id, actor_id, order, SalesOrderStatus.CLOSED, "closed_at", values)

    def list_fulfillments_for_order(self, tenant_id: int, order_id: int) -> list[SalesFulfillment]:
        self.get_sales_order(tenant_id, order_id)
        return self.repository.list_fulfillments_for_order(tenant_id, order_id)

    def get_fulfillment(self, tenant_id: int, fulfillment_id: int) -> SalesFulfillment:
        fulfillment = self.repository.get_fulfillment(tenant_id, fulfillment_id)
        if fulfillment is None:
            raise AppError("SALES_FULFILLMENT_NOT_FOUND", "Sales fulfillment was not found for this tenant.", 404)
        return fulfillment

    def create_fulfillment(self, tenant_id: int, actor_id: int, order_id: int, values: dict[str, Any]) -> SalesFulfillment:
        order = self.get_sales_order(tenant_id, order_id)
        self._require_fulfillable(order)
        items = values.pop("items", [])
        fulfillment = self.repository.create_fulfillment({**values, "tenant_id": tenant_id, "sales_order_id": order_id, "fulfilled_by": actor_id, "status": SalesFulfillmentStatus.DRAFT})
        self._replace_fulfillment_items(tenant_id, order, fulfillment.id, items)
        return self._commit_and_get_fulfillment(tenant_id, fulfillment.id)

    def update_fulfillment(self, tenant_id: int, fulfillment_id: int, values: dict[str, Any]) -> SalesFulfillment:
        fulfillment = self.get_fulfillment(tenant_id, fulfillment_id)
        if fulfillment.status != SalesFulfillmentStatus.DRAFT:
            raise AppError("INVALID_SALES_FULFILLMENT_STATE", "Only draft fulfillments can be edited.", 409)
        order = self.get_sales_order(tenant_id, fulfillment.sales_order_id)
        self._require_fulfillable(order)
        items = values.pop("items", None)
        for key, value in values.items():
            setattr(fulfillment, key, value)
        if items is not None:
            self.repository.delete_fulfillment_items(tenant_id, fulfillment.id)
            self._replace_fulfillment_items(tenant_id, order, fulfillment.id, items)
        return self._commit_and_get_fulfillment(tenant_id, fulfillment.id)

    def cancel_fulfillment(self, tenant_id: int, fulfillment_id: int) -> SalesFulfillment:
        fulfillment = self.get_fulfillment(tenant_id, fulfillment_id)
        if fulfillment.status != SalesFulfillmentStatus.DRAFT:
            raise AppError("INVALID_SALES_FULFILLMENT_STATE", "Only draft fulfillments can be cancelled.", 409)
        fulfillment.status = SalesFulfillmentStatus.CANCELLED
        fulfillment.cancelled_at = datetime.now(UTC)
        return self._commit_and_get_fulfillment(tenant_id, fulfillment.id)

    def commit_fulfillment(self, tenant_id: int, actor_id: int, fulfillment_id: int, values: dict[str, Any]) -> dict[str, Any]:
        fulfillment = self.repository.lock_fulfillment(tenant_id, fulfillment_id)
        if fulfillment is None:
            raise AppError("SALES_FULFILLMENT_NOT_FOUND", "Sales fulfillment was not found for this tenant.", 404)
        if fulfillment.status == SalesFulfillmentStatus.COMMITTED:
            return {"sales_order": self.get_sales_order(tenant_id, fulfillment.sales_order_id), "fulfillment": self.get_fulfillment(tenant_id, fulfillment.id), "stock_results": []}
        if fulfillment.status != SalesFulfillmentStatus.DRAFT:
            raise AppError("INVALID_SALES_FULFILLMENT_STATE", "Only draft fulfillments can be committed.", 409)
        order = self.repository.lock_sales_order(tenant_id, fulfillment.sales_order_id)
        if order is None:
            raise AppError("SALES_ORDER_NOT_FOUND", "Sales order was not found for this tenant.", 404)
        self._require_fulfillable(order)
        fulfillment = self.get_fulfillment(tenant_id, fulfillment_id)
        if not fulfillment.items:
            raise AppError("SALES_FULFILLMENT_ITEMS_REQUIRED", "Sales fulfillment must include at least one item before commit.", 400)
        stock_results = []
        try:
            for item in fulfillment.items:
                order_item = self.repository.lock_sales_order_item(tenant_id, item.sales_order_item_id)
                if order_item is None or order_item.sales_order_id != order.id:
                    raise AppError("SALES_ORDER_ITEM_NOT_FOUND", "Sales order item was not found for this sales order.", 404)
                picked_item = self.fulfillment_repository.get_picked_item_for_reservation(tenant_id, item.reservation_id)
                tracking_payload = {}
                if picked_item is not None:
                    tracking_payload = {"batch_id": picked_item.batch_id, "serial_id": picked_item.serial_id}
                result = InventoryService(self.db).deduct_reserved_stock(
                    tenant_id,
                    actor_id,
                    item.reservation_id,
                    {
                        "note": values.get("note") or fulfillment.notes,
                        "idempotency_key": f"{values['idempotency_key']}:sales-fulfillment:{fulfillment.id}:item:{item.id}",
                        **tracking_payload,
                    },
                    auto_commit=False,
                )
                stock_results.append(result)
                order_item.fulfilled_quantity += item.fulfilled_quantity
            fulfillment.status = SalesFulfillmentStatus.COMMITTED
            now = datetime.now(UTC)
            fulfillment.committed_at = now
            fulfillment.fulfilled_at = fulfillment.fulfilled_at or now
            self._update_sales_order_fulfillment_status(order)
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("SALES_FULFILLMENT_COMMIT_FAILED", "Sales fulfillment commit failed because of duplicate or invalid data.", 409) from exc
        try:
            workflow = WorkflowService(self.db)
            workflow.log_event(tenant_id, "SALES_FULFILLMENT_COMMITTED", "sales_fulfillment", fulfillment.id, actor_id, {"sales_order_id": order.id})
            workflow.create_task(tenant_id, WorkflowTaskCreate(
                workflow_type="SALES",
                entity_type="sales_order",
                entity_id=order.id,
                step_key="CREATE_INVOICE",
                title=f"Create and send invoice for fulfilled order {order.order_number}",
                description="Fulfillment committed. Create invoice and send to customer.",
                assigned_role="SALES_STAFF",
                priority="NORMAL",
                action_url=f"/invoices",
            ), created_by=actor_id)
            self.db.commit()
        except Exception:
            pass
        try:
            self._auto_create_invoice(tenant_id, actor_id, order)
        except Exception:
            pass
        return {"sales_order": self.get_sales_order(tenant_id, order.id), "fulfillment": self.get_fulfillment(tenant_id, fulfillment.id), "stock_results": stock_results}

    def _auto_create_pick_task(self, tenant_id: int, actor_id: int, order: SalesOrder) -> None:
        from app.services.fulfillment import FulfillmentService
        import uuid
        pick_number = f"PICK-{uuid.uuid4().hex[:8].upper()}"
        FulfillmentService(self.db).create_pick_task(tenant_id, actor_id, order.id, {"pick_number": pick_number})

    def _auto_create_invoice(self, tenant_id: int, actor_id: int, order: SalesOrder) -> None:
        from app.services.documents import DocumentsService
        from app.repositories.documents import DocumentsRepository
        repo = DocumentsRepository(self.db)
        existing = repo.get_invoice_for_sales_order(tenant_id, order.id)
        if existing is not None:
            return
        DocumentsService(self.db).create_invoice(tenant_id, actor_id, {"sales_order_id": order.id})

    def _replace_order_items(self, tenant_id: int, order_id: int, items: list[dict[str, Any]]) -> None:
        seen_products = set()
        for item in items:
            if item["product_id"] in seen_products:
                raise AppError("DUPLICATE_SALES_ORDER_PRODUCT", "Phase 6 supports one line per product per sales order.", 400)
            seen_products.add(item["product_id"])
            self._require_product(tenant_id, item["product_id"])
            self.repository.create_sales_order_item({**item, "tenant_id": tenant_id, "sales_order_id": order_id, "reserved_quantity": ZERO, "fulfilled_quantity": ZERO})

    def _validate_confirm_allocations(self, tenant_id: int, order: SalesOrder, allocations: list[dict[str, Any]]) -> None:
        totals: dict[int, Decimal] = {}
        item_ids = {item.id for item in order.items}
        for allocation in allocations:
            if allocation["sales_order_item_id"] not in item_ids:
                raise AppError("SALES_ALLOCATION_ITEM_MISMATCH", "Allocation line must reference this sales order's items.", 400)
            item = next(order_item for order_item in order.items if order_item.id == allocation["sales_order_item_id"])
            product = self._require_product(tenant_id, item.product_id)
            if product.track_serial and Decimal(str(allocation["quantity"])) != Decimal("1"):
                raise AppError("SERIAL_ALLOCATION_MUST_BE_UNIT", "Serial-tracked sales allocations must be split into one-unit reservation lines.", 400)
            self._require_warehouse(tenant_id, allocation["warehouse_id"])
            self._require_location(tenant_id, allocation["warehouse_id"], allocation["location_id"])
            totals[item.id] = totals.get(item.id, ZERO) + Decimal(str(allocation["quantity"]))
        for item in order.items:
            if totals.get(item.id, ZERO) != item.ordered_quantity:
                raise AppError("SALES_ALLOCATION_QUANTITY_MISMATCH", "Allocated quantity must equal ordered quantity for each item in Phase 6.", 400)

    def _replace_fulfillment_items(self, tenant_id: int, order: SalesOrder, fulfillment_id: int, items: list[dict[str, Any]]) -> None:
        pending_by_item: dict[int, Decimal] = {}
        for item in items:
            order_item = self.repository.get_sales_order_item(tenant_id, item["sales_order_item_id"])
            if order_item is None or order_item.sales_order_id != order.id:
                raise AppError("SALES_ORDER_ITEM_NOT_FOUND", "Sales order item was not found for this sales order.", 404)
            if order_item.product_id != item["product_id"]:
                raise AppError("SALES_FULFILLMENT_PRODUCT_MISMATCH", "Fulfillment item product must match the sales order item.", 400)
            reservation = self.repository.get_reservation(tenant_id, item["reservation_id"])
            if reservation is None:
                raise AppError("RESERVATION_NOT_FOUND", "Reservation was not found for this tenant.", 404)
            if reservation.status != ReservationStatus.ACTIVE or reservation.reference_type != ReferenceType.SALES_ORDER or reservation.reference_id != order.order_number:
                raise AppError("INVALID_RESERVATION_STATE", "Fulfillment requires an active reservation for this sales order.", 409)
            if reservation.product_id != item["product_id"] or reservation.warehouse_id != item["warehouse_id"] or reservation.location_id != item["location_id"]:
                raise AppError("SALES_FULFILLMENT_RESERVATION_MISMATCH", "Fulfillment item must match the selected reservation dimensions.", 400)
            if Decimal(str(item["fulfilled_quantity"])) != reservation.quantity:
                raise AppError("SALES_FULFILLMENT_RESERVATION_QUANTITY", "Phase 6 fulfillment quantity must match the selected reservation quantity.", 400)
            product = self._require_product(tenant_id, item["product_id"])
            if product.track_serial and self.fulfillment_repository.get_picked_item_for_reservation(tenant_id, reservation.id) is None:
                raise AppError("SERIAL_PICK_REQUIRED", "Serial-tracked fulfillment requires explicit serial picking first.", 409)
            self._require_warehouse(tenant_id, item["warehouse_id"])
            self._require_location(tenant_id, item["warehouse_id"], item["location_id"])
            pending_by_item[order_item.id] = pending_by_item.get(order_item.id, ZERO) + Decimal(str(item["fulfilled_quantity"]))
            remaining = order_item.reserved_quantity - order_item.fulfilled_quantity
            if pending_by_item[order_item.id] > remaining:
                raise AppError("OVER_FULFILLMENT_NOT_ALLOWED", "Fulfilled quantity cannot exceed remaining reserved quantity.", 409)
            self.repository.create_fulfillment_item({**item, "tenant_id": tenant_id, "fulfillment_id": fulfillment_id})

    def _release_and_mark_order(self, tenant_id: int, actor_id: int, order: SalesOrder, status: SalesOrderStatus, timestamp_field: str, values: dict[str, Any]) -> SalesOrder:
        try:
            for reservation in self.repository.active_reservations_for_order(tenant_id, order.order_number):
                InventoryService(self.db).release_reservation(
                    tenant_id,
                    actor_id,
                    reservation.id,
                    {
                        "note": values.get("note") or order.notes,
                        "idempotency_key": f"{values.get('idempotency_key', f'order-{order.id}-{status.value.lower()}')}:sales-order:{order.id}:release:{reservation.id}",
                    },
                    auto_commit=False,
                )
                order_item = next((item for item in self.get_sales_order(tenant_id, order.id).items if item.product_id == reservation.product_id), None)
                if order_item:
                    order_item.reserved_quantity -= reservation.quantity
            order.status = status
            setattr(order, timestamp_field, datetime.now(UTC))
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        return self.get_sales_order(tenant_id, order.id)

    def _update_sales_order_fulfillment_status(self, order: SalesOrder) -> None:
        items = [self.repository.lock_sales_order_item(order.tenant_id, item.id) for item in self.get_sales_order(order.tenant_id, order.id).items]
        if all(item and item.fulfilled_quantity >= item.ordered_quantity for item in items):
            order.status = SalesOrderStatus.FULFILLED
            order.fulfilled_at = datetime.now(UTC)
        else:
            order.status = SalesOrderStatus.PARTIALLY_FULFILLED

    def _require_fulfillable(self, order: SalesOrder) -> None:
        if order.status not in FULFILLABLE_STATUSES:
            raise AppError("INVALID_SALES_ORDER_STATE", "Only confirmed or partially fulfilled sales orders can be fulfilled.", 409)

    def _require_customer(self, tenant_id: int, customer_id: int) -> None:
        if self.repository.get_customer(tenant_id, customer_id) is None:
            raise AppError("CUSTOMER_NOT_FOUND", "Customer was not found for this tenant.", 404)

    def _require_product(self, tenant_id: int, product_id: int):
        product = self.repository.get_product(tenant_id, product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        return product

    def _require_warehouse(self, tenant_id: int, warehouse_id: int) -> None:
        if self.repository.get_warehouse(tenant_id, warehouse_id) is None:
            raise AppError("WAREHOUSE_NOT_FOUND", "Warehouse was not found for this tenant.", 404)

    def _require_location(self, tenant_id: int, warehouse_id: int, location_id: int) -> None:
        if self.repository.get_location(tenant_id, warehouse_id, location_id) is None:
            raise AppError("LOCATION_NOT_FOUND", "Location was not found for this tenant warehouse.", 404)

    def _commit_and_get_order(self, tenant_id: int, order_id: int) -> SalesOrder:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_SALES_ORDER", "A sales order with these unique values already exists for this tenant.", 409) from exc
        return self.get_sales_order(tenant_id, order_id)

    def _commit_and_get_fulfillment(self, tenant_id: int, fulfillment_id: int) -> SalesFulfillment:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_SALES_FULFILLMENT", "A sales fulfillment with these unique values already exists for this tenant.", 409) from exc
        return self.get_fulfillment(tenant_id, fulfillment_id)
