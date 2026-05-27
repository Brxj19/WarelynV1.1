from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.fulfillment import Package, PackageStatus, PickTask, PickTaskItemStatus, PickTaskStatus
from app.models.inventory import InventoryBatchStatus, InventorySerialStatus, ReservationStatus
from app.models.sales import SalesOrderStatus
from app.repositories.fulfillment import FulfillmentRepository

ZERO = Decimal("0")
ONE = Decimal("1")
PICKABLE_ORDER_STATUSES = {SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIALLY_FULFILLED}


class FulfillmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = FulfillmentRepository(db)

    def list_pick_tasks(self, tenant_id: int) -> list[PickTask]:
        return self.repository.list_pick_tasks(tenant_id)

    def create_pick_task(self, tenant_id: int, actor_id: int, order_id: int, values: dict[str, Any]) -> PickTask:
        order = self._require_order(tenant_id, order_id)
        if order.status not in PICKABLE_ORDER_STATUSES:
            raise AppError("INVALID_SALES_ORDER_STATE", "Only confirmed or partially fulfilled sales orders can be picked.", 409)
        reservations = self.repository.active_reservations_for_order(tenant_id, order.order_number)
        if not reservations:
            raise AppError("NO_ACTIVE_RESERVATIONS", "Pick tasks require active sales order reservations.", 409)
        item_by_product = {item.product_id: item for item in order.items}
        try:
            pick_task = self.repository.create_pick_task({"tenant_id": tenant_id, "sales_order_id": order.id, "pick_number": values["pick_number"], "status": PickTaskStatus.PENDING, "assigned_to": values.get("assigned_to"), "notes": values.get("notes"), "created_by": actor_id})
            for reservation in reservations:
                if self.repository.has_active_pick_for_reservation(tenant_id, reservation.id):
                    raise AppError("PICK_TASK_ALREADY_EXISTS", "An active pick task already exists for one or more reservations.", 409)
                order_item = item_by_product.get(reservation.product_id)
                if order_item is None:
                    raise AppError("SALES_ORDER_ITEM_NOT_FOUND", "Reservation product does not match this sales order.", 409)
                product = self._require_product(tenant_id, reservation.product_id)
                item_count = int(reservation.quantity) if product.track_serial else 1
                if product.track_serial and reservation.quantity != Decimal(item_count):
                    raise AppError("SERIAL_RESERVATION_QUANTITY_INVALID", "Serial reservations must be split into one-unit lines before picking.", 409)
                for _ in range(item_count):
                    required = ONE if product.track_serial else reservation.quantity
                    self.repository.create_pick_task_item({"tenant_id": tenant_id, "pick_task_id": pick_task.id, "sales_order_item_id": order_item.id, "reservation_id": reservation.id, "product_id": reservation.product_id, "warehouse_id": reservation.warehouse_id, "location_id": reservation.location_id, "required_quantity": required, "picked_quantity": ZERO, "status": PickTaskItemStatus.PENDING})
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_PICK_TASK", "A pick task with these unique values already exists for this tenant.", 409) from exc
        return self.get_pick_task(tenant_id, pick_task.id)

    def list_pick_tasks_for_order(self, tenant_id: int, order_id: int) -> list[PickTask]:
        self._require_order(tenant_id, order_id)
        return self.repository.list_pick_tasks_for_order(tenant_id, order_id)

    def get_pick_task(self, tenant_id: int, pick_task_id: int) -> PickTask:
        pick_task = self.repository.get_pick_task(tenant_id, pick_task_id)
        if pick_task is None:
            raise AppError("PICK_TASK_NOT_FOUND", "Pick task was not found for this tenant.", 404)
        return pick_task

    def update_pick_task(self, tenant_id: int, pick_task_id: int, values: dict[str, Any]) -> PickTask:
        pick_task = self.get_pick_task(tenant_id, pick_task_id)
        if pick_task.status in {PickTaskStatus.PICKED, PickTaskStatus.CANCELLED}:
            raise AppError("INVALID_PICK_TASK_STATE", "Picked or cancelled pick tasks cannot be edited.", 409)
        for key, value in values.items():
            setattr(pick_task, key, value)
        return self._commit_and_get_pick_task(tenant_id, pick_task.id)

    def start_pick_task(self, tenant_id: int, pick_task_id: int) -> PickTask:
        pick_task = self.repository.lock_pick_task(tenant_id, pick_task_id)
        if pick_task is None:
            raise AppError("PICK_TASK_NOT_FOUND", "Pick task was not found for this tenant.", 404)
        if pick_task.status == PickTaskStatus.PENDING:
            pick_task.status = PickTaskStatus.IN_PROGRESS
            pick_task.started_at = datetime.now(UTC)
        elif pick_task.status != PickTaskStatus.IN_PROGRESS:
            raise AppError("INVALID_PICK_TASK_STATE", "Only pending pick tasks can be started.", 409)
        return self._commit_and_get_pick_task(tenant_id, pick_task.id)

    def pick_pick_task(self, tenant_id: int, pick_task_id: int, values: dict[str, Any]) -> PickTask:
        pick_task = self.repository.lock_pick_task(tenant_id, pick_task_id)
        if pick_task is None:
            raise AppError("PICK_TASK_NOT_FOUND", "Pick task was not found for this tenant.", 404)
        if pick_task.status == PickTaskStatus.CANCELLED:
            raise AppError("INVALID_PICK_TASK_STATE", "Cancelled pick tasks cannot be picked.", 409)
        if pick_task.status == PickTaskStatus.PICKED:
            raise AppError("INVALID_PICK_TASK_STATE", "Picked tasks cannot be changed in Phase 7.", 409)
        seen_serials: set[int] = set()
        try:
            for request_item in values.get("items", []):
                item = self.repository.lock_pick_task_item(tenant_id, request_item["pick_task_item_id"])
                if item is None or item.pick_task_id != pick_task.id:
                    raise AppError("PICK_TASK_ITEM_NOT_FOUND", "Pick task item was not found for this pick task.", 404)
                if item.status == PickTaskItemStatus.CANCELLED:
                    raise AppError("INVALID_PICK_TASK_ITEM_STATE", "Cancelled pick task items cannot be picked.", 409)
                quantity = Decimal(str(request_item["picked_quantity"]))
                if quantity < ZERO or quantity > item.required_quantity:
                    raise AppError("PICK_QUANTITY_INVALID", "Picked quantity cannot exceed required quantity.", 400)
                reservation = self.repository.get_reservation(tenant_id, item.reservation_id)
                if reservation is None or reservation.status != ReservationStatus.ACTIVE:
                    raise AppError("INVALID_RESERVATION_STATE", "Picking requires an active reservation.", 409)
                if quantity > reservation.quantity:
                    raise AppError("PICK_QUANTITY_INVALID", "Picked quantity cannot exceed active reservation quantity.", 400)
                product = self._require_product(tenant_id, item.product_id)
                batch_id = request_item.get("batch_id")
                serial_id = request_item.get("serial_id")
                if product.track_serial:
                    if quantity != ONE or serial_id is None:
                        raise AppError("SERIAL_SELECTION_REQUIRED", "Serial-tracked products require one explicit serial per picked item.", 400)
                    if int(serial_id) in seen_serials:
                        raise AppError("DUPLICATE_SERIAL_ALLOCATION", "A serial can only be allocated once in a pick request.", 409)
                    seen_serials.add(int(serial_id))
                    serial = self.repository.get_serial(tenant_id, int(serial_id))
                    if serial is None:
                        raise AppError("SERIAL_NOT_FOUND", "Serial was not found for this tenant.", 404)
                    if serial.product_id != item.product_id:
                        raise AppError("SERIAL_PRODUCT_MISMATCH", "Selected serial must belong to the picked product.", 400)
                    if serial.warehouse_id != item.warehouse_id or serial.location_id != item.location_id:
                        raise AppError("SERIAL_LOCATION_MISMATCH", "Selected serial must belong to the reserved warehouse and location.", 400)
                    if serial.status != InventorySerialStatus.IN_STOCK:
                        raise AppError("SERIAL_NOT_AVAILABLE", "Selected serial must be in stock.", 409)
                    if self.repository.serial_allocated_elsewhere(tenant_id, serial.id, item.id):
                        raise AppError("DUPLICATE_SERIAL_ALLOCATION", "Selected serial is already allocated to another active pick task.", 409)
                    if serial.batch_id and batch_id is None:
                        batch_id = serial.batch_id
                    item.serial_id = serial.id
                elif serial_id is not None:
                    raise AppError("SERIAL_TRACKING_NOT_ENABLED", "Serial allocation is only valid for serial-tracked products.", 400)
                if batch_id is not None:
                    batch = self.repository.get_batch(tenant_id, int(batch_id))
                    if batch is None:
                        raise AppError("BATCH_NOT_FOUND", "Batch was not found for this tenant.", 404)
                    if batch.product_id != item.product_id or batch.warehouse_id != item.warehouse_id or batch.location_id != item.location_id:
                        raise AppError("BATCH_DIMENSION_MISMATCH", "Selected batch must belong to the picked product, warehouse, and location.", 400)
                    if batch.status != InventoryBatchStatus.ACTIVE:
                        raise AppError("BATCH_NOT_AVAILABLE", "Selected batch must be active.", 409)
                    item.batch_id = batch.id
                item.picked_quantity = quantity
                item.status = PickTaskItemStatus.PICKED if quantity == item.required_quantity else PickTaskItemStatus.PENDING
            refreshed = self.repository.get_pick_task(tenant_id, pick_task.id)
            if refreshed and refreshed.items and all(item.status == PickTaskItemStatus.PICKED for item in refreshed.items):
                pick_task.status = PickTaskStatus.PICKED
                pick_task.picked_at = datetime.now(UTC)
            else:
                pick_task.status = PickTaskStatus.IN_PROGRESS
                pick_task.started_at = pick_task.started_at or datetime.now(UTC)
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        return self.get_pick_task(tenant_id, pick_task.id)

    def cancel_pick_task(self, tenant_id: int, pick_task_id: int) -> PickTask:
        pick_task = self.repository.lock_pick_task(tenant_id, pick_task_id)
        if pick_task is None:
            raise AppError("PICK_TASK_NOT_FOUND", "Pick task was not found for this tenant.", 404)
        if pick_task.status == PickTaskStatus.CANCELLED:
            return self.get_pick_task(tenant_id, pick_task.id)
        if pick_task.status == PickTaskStatus.PICKED:
            raise AppError("INVALID_PICK_TASK_STATE", "Picked pick tasks cannot be cancelled in Phase 7.", 409)
        pick_task.status = PickTaskStatus.CANCELLED
        pick_task.cancelled_at = datetime.now(UTC)
        for item in self.get_pick_task(tenant_id, pick_task.id).items:
            item.status = PickTaskItemStatus.CANCELLED
        return self._commit_and_get_pick_task(tenant_id, pick_task.id)

    def create_package(self, tenant_id: int, order_id: int, values: dict[str, Any]) -> Package:
        order = self._require_order(tenant_id, order_id)
        item_ids = values.get("pick_task_item_ids") or []
        if not item_ids:
            raise AppError("PACKAGE_ITEMS_REQUIRED", "Package creation requires picked task items.", 400)
        try:
            package = self.repository.create_package({"tenant_id": tenant_id, "sales_order_id": order.id, "package_number": values["package_number"], "status": PackageStatus.DRAFT, "notes": values.get("notes")})
            for item_id in item_ids:
                item = self.repository.get_pick_task_item(tenant_id, int(item_id))
                if item is None or item.status != PickTaskItemStatus.PICKED:
                    raise AppError("PICKED_ITEM_REQUIRED", "Only picked task items can be packed.", 409)
                if item.sales_order_item_id not in {order_item.id for order_item in order.items}:
                    raise AppError("PICK_TASK_ITEM_ORDER_MISMATCH", "Pick task item does not belong to this sales order.", 400)
                packed_quantity = Decimal(str(self.repository.picked_quantity_for_item(tenant_id, item.id)))
                if packed_quantity + item.picked_quantity > item.picked_quantity:
                    raise AppError("PACKAGE_QUANTITY_EXCEEDED", "Picked item is already packed.", 409)
                self.repository.create_package_item({"tenant_id": tenant_id, "package_id": package.id, "pick_task_item_id": item.id, "sales_order_item_id": item.sales_order_item_id, "product_id": item.product_id, "batch_id": item.batch_id, "serial_id": item.serial_id, "quantity": item.picked_quantity})
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_PACKAGE", "A package with these unique values already exists for this tenant.", 409) from exc
        return self.get_package(tenant_id, package.id)

    def list_packages_for_order(self, tenant_id: int, order_id: int) -> list[Package]:
        self._require_order(tenant_id, order_id)
        return self.repository.list_packages_for_order(tenant_id, order_id)

    def get_package(self, tenant_id: int, package_id: int) -> Package:
        package = self.repository.get_package(tenant_id, package_id)
        if package is None:
            raise AppError("PACKAGE_NOT_FOUND", "Package was not found for this tenant.", 404)
        return package

    def update_package(self, tenant_id: int, package_id: int, values: dict[str, Any]) -> Package:
        package = self.get_package(tenant_id, package_id)
        if package.status != PackageStatus.DRAFT:
            raise AppError("INVALID_PACKAGE_STATE", "Only draft packages can be edited.", 409)
        for key, value in values.items():
            setattr(package, key, value)
        return self._commit_and_get_package(tenant_id, package.id)

    def pack_package(self, tenant_id: int, actor_id: int, package_id: int, values: dict[str, Any]) -> Package:
        package = self.repository.lock_package(tenant_id, package_id)
        if package is None:
            raise AppError("PACKAGE_NOT_FOUND", "Package was not found for this tenant.", 404)
        if package.status != PackageStatus.DRAFT:
            raise AppError("INVALID_PACKAGE_STATE", "Only draft packages can be packed.", 409)
        if not self.get_package(tenant_id, package.id).items:
            raise AppError("PACKAGE_ITEMS_REQUIRED", "Package must include items before packing.", 400)
        package.status = PackageStatus.PACKED
        package.packed_by = actor_id
        package.packed_at = datetime.now(UTC)
        if values.get("notes") is not None:
            package.notes = values["notes"]
        return self._commit_and_get_package(tenant_id, package.id)

    def cancel_package(self, tenant_id: int, package_id: int) -> Package:
        package = self.repository.lock_package(tenant_id, package_id)
        if package is None:
            raise AppError("PACKAGE_NOT_FOUND", "Package was not found for this tenant.", 404)
        if package.status == PackageStatus.PACKED:
            raise AppError("INVALID_PACKAGE_STATE", "Packed packages cannot be cancelled in Phase 7.", 409)
        package.status = PackageStatus.CANCELLED
        package.cancelled_at = datetime.now(UTC)
        return self._commit_and_get_package(tenant_id, package.id)

    def _require_order(self, tenant_id: int, order_id: int):
        order = self.repository.get_sales_order(tenant_id, order_id)
        if order is None:
            raise AppError("SALES_ORDER_NOT_FOUND", "Sales order was not found for this tenant.", 404)
        return order

    def _require_product(self, tenant_id: int, product_id: int):
        product = self.repository.get_product(tenant_id, product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        return product

    def _commit_and_get_pick_task(self, tenant_id: int, pick_task_id: int) -> PickTask:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_PICK_TASK", "A pick task with these unique values already exists for this tenant.", 409) from exc
        return self.get_pick_task(tenant_id, pick_task_id)

    def _commit_and_get_package(self, tenant_id: int, package_id: int) -> Package:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_PACKAGE", "A package with these unique values already exists for this tenant.", 409) from exc
        return self.get_package(tenant_id, package_id)
