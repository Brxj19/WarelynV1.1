from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.inventory import InventorySerialStatus, ReferenceType
from app.models.returns import SalesReturn, SalesReturnItem, SalesReturnItemStatus, SalesReturnStatus
from app.models.sales import SalesOrderStatus
from app.repositories.returns import ReturnsRepository
from app.schemas.workflow import WorkflowTaskCreate
from app.services.inventory import InventoryService
from app.services.workflow import WorkflowService

ZERO = Decimal("0")


class ReturnsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ReturnsRepository(db)

    def list_returns(self, tenant_id: int) -> list[SalesReturn]:
        return self.repository.list_returns(tenant_id)

    def get_return(self, tenant_id: int, return_id: int) -> SalesReturn:
        sales_return = self.repository.get_return(tenant_id, return_id)
        if sales_return is None:
            raise AppError("SALES_RETURN_NOT_FOUND", "Sales return was not found for this tenant.", 404)
        return sales_return

    def create_return(self, tenant_id: int, actor_id: int, values: dict[str, Any]) -> SalesReturn:
        order = self.repository.get_sales_order(tenant_id, values["sales_order_id"])
        if order is None:
            raise AppError("SALES_ORDER_NOT_FOUND", "Sales order was not found for this tenant.", 404)
        if order.status not in {SalesOrderStatus.PARTIALLY_FULFILLED, SalesOrderStatus.FULFILLED, SalesOrderStatus.CLOSED}:
            raise AppError("INVALID_SALES_ORDER_STATE", "Returns can only be created for fulfilled sales orders.", 409)
        items = values.pop("items", [])
        if not items:
            raise AppError("SALES_RETURN_ITEMS_REQUIRED", "Sales return must include at least one item.", 400)
        try:
            sales_return = self.repository.create_return({**values, "tenant_id": tenant_id, "created_by": actor_id, "status": SalesReturnStatus.DRAFT})
            self._create_items(tenant_id, order, sales_return.id, items)
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("SALES_RETURN_CREATE_FAILED", "Sales return could not be created because of duplicate or invalid data.", 409) from exc
        return self.get_return(tenant_id, sales_return.id)

    def update_return(self, tenant_id: int, return_id: int, values: dict[str, Any]) -> SalesReturn:
        sales_return = self.repository.lock_return(tenant_id, return_id)
        if sales_return is None:
            raise AppError("SALES_RETURN_NOT_FOUND", "Sales return was not found for this tenant.", 404)
        if sales_return.status != SalesReturnStatus.DRAFT:
            raise AppError("INVALID_SALES_RETURN_STATE", "Only draft returns can be edited.", 409)
        for key, value in values.items():
            setattr(sales_return, key, value)
        self.db.commit()
        return self.get_return(tenant_id, return_id)

    def submit_return(self, tenant_id: int, actor_id: int, return_id: int) -> SalesReturn:
        sales_return = self.repository.lock_return(tenant_id, return_id)
        if sales_return is None:
            raise AppError("SALES_RETURN_NOT_FOUND", "Sales return was not found for this tenant.", 404)
        if sales_return.status == SalesReturnStatus.SUBMITTED:
            return self.get_return(tenant_id, return_id)
        if sales_return.status != SalesReturnStatus.DRAFT:
            raise AppError("INVALID_SALES_RETURN_STATE", "Only draft returns can be submitted.", 409)
        if not self.get_return(tenant_id, return_id).items:
            raise AppError("SALES_RETURN_ITEMS_REQUIRED", "Sales return must include at least one item before submission.", 400)
        sales_return.status = SalesReturnStatus.SUBMITTED
        sales_return.submitted_at = datetime.now(UTC)
        self.db.commit()
        try:
            workflow = WorkflowService(self.db)
            workflow.log_event(tenant_id, "RETURN_SUBMITTED", "sales_return", return_id, actor_id, {"return_number": sales_return.return_number})
            workflow.create_task(tenant_id, WorkflowTaskCreate(
                workflow_type="RETURNS",
                entity_type="sales_return",
                entity_id=return_id,
                step_key="RETURN_QC",
                title=f"Inspect returned items for return #{return_id}",
                description="Return submitted. Inspect items and record QC results.",
                assigned_role="INVENTORY_MANAGER",
                priority="NORMAL",
                action_url=f"/returns/{return_id}",
            ), created_by=actor_id)
            self.db.commit()
        except Exception:
            pass
        return self.get_return(tenant_id, return_id)

    def cancel_return(self, tenant_id: int, return_id: int) -> SalesReturn:
        sales_return = self.repository.lock_return(tenant_id, return_id)
        if sales_return is None:
            raise AppError("SALES_RETURN_NOT_FOUND", "Sales return was not found for this tenant.", 404)
        if sales_return.status not in {SalesReturnStatus.DRAFT, SalesReturnStatus.SUBMITTED, SalesReturnStatus.INSPECTION_PENDING}:
            raise AppError("INVALID_SALES_RETURN_STATE", "Only unprocessed returns can be cancelled.", 409)
        sales_return.status = SalesReturnStatus.CANCELLED
        sales_return.cancelled_at = datetime.now(UTC)
        self.db.commit()
        return self.get_return(tenant_id, return_id)

    def inspect_return(self, tenant_id: int, actor_id: int, return_id: int, values: dict[str, Any]) -> SalesReturn:
        sales_return = self.repository.lock_return(tenant_id, return_id)
        if sales_return is None:
            raise AppError("SALES_RETURN_NOT_FOUND", "Sales return was not found for this tenant.", 404)
        if sales_return.status not in {SalesReturnStatus.SUBMITTED, SalesReturnStatus.INSPECTION_PENDING}:
            raise AppError("INVALID_SALES_RETURN_STATE", "Only submitted returns can be inspected.", 409)
        if not values.get("items"):
            raise AppError("RETURN_INSPECTION_ITEMS_REQUIRED", "Inspection must include at least one item.", 400)
        for inspection in values["items"]:
            item = self.repository.get_return_item(tenant_id, inspection["sales_return_item_id"])
            if item is None or item.sales_return_id != return_id:
                raise AppError("SALES_RETURN_ITEM_NOT_FOUND", "Return item was not found for this return.", 404)
            self._validate_inspection(item, inspection)
            item.qc_status = inspection["qc_status"]
            item.accepted_quantity = Decimal(str(inspection["accepted_quantity"]))
            item.rejected_quantity = Decimal(str(inspection["rejected_quantity"]))
            item.reason = inspection.get("reason") or item.reason
            item.notes = inspection.get("notes") or item.notes
        now = datetime.now(UTC)
        sales_return.status = SalesReturnStatus.INSPECTION_PENDING
        sales_return.inspected_at = now
        existing = self.repository.get_latest_inspection(tenant_id, return_id)
        if existing is None:
            self.repository.create_inspection({"tenant_id": tenant_id, "sales_return_id": return_id, "inspected_by": actor_id, "inspected_at": now, "notes": values.get("notes")})
        self.db.commit()
        return self.get_return(tenant_id, return_id)

    def process_return(self, tenant_id: int, actor_id: int, return_id: int, values: dict[str, Any]) -> dict[str, Any]:
        sales_return = self.repository.lock_return(tenant_id, return_id)
        if sales_return is None:
            raise AppError("SALES_RETURN_NOT_FOUND", "Sales return was not found for this tenant.", 404)
        if sales_return.status == SalesReturnStatus.PROCESSED:
            return {"sales_return": self.get_return(tenant_id, return_id), "stock_results": []}
        if sales_return.status != SalesReturnStatus.INSPECTION_PENDING:
            raise AppError("INVALID_SALES_RETURN_STATE", "Only inspected returns can be processed.", 409)
        items = self.get_return(tenant_id, return_id).items
        if any(item.qc_status == SalesReturnItemStatus.PENDING for item in items):
            raise AppError("RETURN_QC_INCOMPLETE", "All return items must be inspected before processing.", 409)
        stock_results = []
        try:
            for index, item in enumerate(items):
                result = self._process_item(tenant_id, actor_id, sales_return, item, values, index)
                if result is not None:
                    stock_results.append(result)
            sales_return.status = SalesReturnStatus.PROCESSED
            sales_return.processed_at = datetime.now(UTC)
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("SALES_RETURN_PROCESS_FAILED", "Sales return processing failed because of duplicate or invalid data.", 409) from exc
        try:
            WorkflowService(self.db).complete_entity_step(
                tenant_id, "sales_return", return_id, "RETURN_QC", actor_id
            )
        except Exception:
            pass
        return {"sales_return": self.get_return(tenant_id, return_id), "stock_results": stock_results}

    def _create_items(self, tenant_id: int, order: Any, return_id: int, items: list[dict[str, Any]]) -> None:
        for item_values in items:
            order_item = self.repository.get_sales_order_item(tenant_id, item_values["sales_order_item_id"])
            if order_item is None or order_item.sales_order_id != order.id:
                raise AppError("SALES_ORDER_ITEM_NOT_FOUND", "Sales order item was not found for this sales order.", 404)
            product = self.repository.get_product(tenant_id, order_item.product_id)
            if product is None:
                raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
            self._validate_return_item(tenant_id, order, order_item, product, return_id, item_values)
            self.repository.create_return_item(
                {
                    "tenant_id": tenant_id,
                    "sales_return_id": return_id,
                    "sales_order_item_id": order_item.id,
                    "product_id": order_item.product_id,
                    "warehouse_id": item_values["warehouse_id"],
                    "location_id": item_values["location_id"],
                    "batch_id": item_values.get("batch_id"),
                    "serial_id": item_values.get("serial_id"),
                    "returned_quantity": Decimal(str(item_values["returned_quantity"])),
                    "accepted_quantity": ZERO,
                    "rejected_quantity": ZERO,
                    "qc_status": SalesReturnItemStatus.PENDING,
                    "reason": item_values.get("reason"),
                    "notes": item_values.get("notes"),
                }
            )

    def _validate_return_item(self, tenant_id: int, order: Any, order_item: Any, product: Any, return_id: int, values: dict[str, Any]) -> None:
        quantity = Decimal(str(values["returned_quantity"]))
        if quantity <= ZERO:
            raise AppError("INVALID_RETURN_QUANTITY", "Returned quantity must be greater than zero.", 400)
        if self.repository.get_warehouse(tenant_id, values["warehouse_id"]) is None:
            raise AppError("WAREHOUSE_NOT_FOUND", "Warehouse was not found for this tenant.", 404)
        if self.repository.get_location(tenant_id, values["warehouse_id"], values["location_id"]) is None:
            raise AppError("LOCATION_NOT_FOUND", "Location was not found for this tenant warehouse.", 404)
        already_returned = self.repository.returned_quantity_for_order_item(tenant_id, order_item.id, exclude_return_id=return_id)
        if already_returned + quantity > order_item.fulfilled_quantity:
            raise AppError("RETURN_QUANTITY_EXCEEDS_FULFILLED", "Returned quantity cannot exceed fulfilled sales quantity.", 409)
        if values.get("batch_id") is not None:
            batch = self.repository.get_batch(tenant_id, int(values["batch_id"]))
            if batch is None or batch.product_id != order_item.product_id:
                raise AppError("BATCH_PRODUCT_MISMATCH", "Returned batch must match the returned product.", 400)
        if product.track_serial:
            if quantity != Decimal("1") or values.get("serial_id") is None:
                raise AppError("SERIAL_RETURN_REQUIRED", "Serial-tracked returns require quantity 1 and a sold serial.", 400)
            serial = self.repository.get_serial(tenant_id, int(values["serial_id"]))
            if serial is None or serial.product_id != order_item.product_id:
                raise AppError("SERIAL_PRODUCT_MISMATCH", "Returned serial must match the returned product.", 400)
            if serial.status != InventorySerialStatus.SOLD:
                raise AppError("SERIAL_NOT_SOLD", "Only sold serials can be returned.", 409)
            if not self.repository.serial_was_deducted_for_order(tenant_id, serial.id, order.order_number):
                raise AppError("SERIAL_NOT_FULFILLED_FOR_ORDER", "Returned serial was not fulfilled for this sales order.", 409)
        elif values.get("serial_id") is not None:
            raise AppError("SERIAL_TRACKING_NOT_ENABLED", "Serial IDs cannot be returned for a non-serial-tracked product.", 400)

    def _validate_inspection(self, item: SalesReturnItem, values: dict[str, Any]) -> None:
        accepted = Decimal(str(values["accepted_quantity"]))
        rejected = Decimal(str(values["rejected_quantity"]))
        if accepted + rejected != item.returned_quantity:
            raise AppError("RETURN_QC_QUANTITY_MISMATCH", "Accepted plus rejected quantity must equal returned quantity.", 400)
        status = values["qc_status"]
        if status == SalesReturnItemStatus.REJECTED and accepted != ZERO:
            raise AppError("INVALID_RETURN_QC", "Rejected items cannot have accepted quantity.", 400)
        if status != SalesReturnItemStatus.REJECTED and accepted <= ZERO:
            raise AppError("INVALID_RETURN_QC", "Accepted return outcomes require accepted quantity.", 400)

    def _process_item(self, tenant_id: int, actor_id: int, sales_return: SalesReturn, item: SalesReturnItem, values: dict[str, Any], index: int) -> dict[str, Any] | None:
        if item.qc_status == SalesReturnItemStatus.REJECTED:
            return None
        payload = {
            "sales_return_id": sales_return.id,
            "sales_return_item_id": item.id,
            "product_id": item.product_id,
            "warehouse_id": item.warehouse_id,
            "location_id": item.location_id,
            "batch_id": item.batch_id,
            "serial_id": item.serial_id,
            "quantity": item.accepted_quantity,
            "reference_type": ReferenceType.SALES_RETURN,
            "reference_id": sales_return.return_number,
            "reason": item.reason,
            "note": values.get("note") or item.notes or sales_return.notes,
            "idempotency_key": f"{values['idempotency_key']}:sales-return:{sales_return.id}:item:{item.id}:{index}",
        }
        inventory = InventoryService(self.db)
        if item.qc_status == SalesReturnItemStatus.ACCEPTED_RESTOCK:
            return inventory.return_restock(tenant_id, actor_id, payload, auto_commit=False)
        if item.qc_status == SalesReturnItemStatus.ACCEPTED_BLOCKED:
            return inventory.record_return_blocked(tenant_id, actor_id, payload, auto_commit=False)
        if item.qc_status == SalesReturnItemStatus.DAMAGED:
            return inventory.record_return_damaged(tenant_id, actor_id, payload, auto_commit=False)
        if item.qc_status == SalesReturnItemStatus.SCRAPPED:
            return inventory.record_return_scrap(tenant_id, actor_id, payload, auto_commit=False)
        raise AppError("INVALID_RETURN_QC", "Unsupported return QC outcome.", 400)
