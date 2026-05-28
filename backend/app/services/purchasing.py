from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.inventory import ReferenceType
from app.models.purchasing import PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus, PurchaseReceipt, PurchaseReceiptStatus
from app.repositories.purchasing import PurchasingRepository
from app.schemas.workflow import WorkflowTaskCreate
from app.services.inventory import InventoryService
from app.services.workflow import WorkflowService

RECEIVABLE_STATUSES = {PurchaseOrderStatus.SUBMITTED, PurchaseOrderStatus.PARTIALLY_RECEIVED}


class PurchasingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = PurchasingRepository(db)

    def list_purchase_orders(self, tenant_id: int) -> list[PurchaseOrder]:
        return self.repository.list_purchase_orders(tenant_id)

    def get_purchase_order(self, tenant_id: int, po_id: int) -> PurchaseOrder:
        po = self.repository.get_purchase_order(tenant_id, po_id)
        if po is None:
            raise AppError("PURCHASE_ORDER_NOT_FOUND", "Purchase order was not found for this tenant.", 404)
        return po

    def create_purchase_order(self, tenant_id: int, actor_id: int, values: dict[str, Any]) -> PurchaseOrder:
        self._require_vendor(tenant_id, values["vendor_id"])
        items = values.pop("items", [])
        po = self.repository.create_purchase_order({**values, "tenant_id": tenant_id, "created_by": actor_id, "status": PurchaseOrderStatus.DRAFT})
        self._replace_order_items(tenant_id, po.id, items)
        return self._commit_and_get_po(tenant_id, po.id)

    def update_purchase_order(self, tenant_id: int, po_id: int, values: dict[str, Any]) -> PurchaseOrder:
        po = self.get_purchase_order(tenant_id, po_id)
        if po.status != PurchaseOrderStatus.DRAFT:
            raise AppError("INVALID_PURCHASE_ORDER_STATE", "Only draft purchase orders can be edited.", 409)
        if values.get("vendor_id"):
            self._require_vendor(tenant_id, values["vendor_id"])
        items = values.pop("items", None)
        for key, value in values.items():
            setattr(po, key, value)
        if items is not None:
            self.repository.delete_purchase_order_items(tenant_id, po.id)
            self._replace_order_items(tenant_id, po.id, items)
        return self._commit_and_get_po(tenant_id, po.id)

    def submit_purchase_order(self, tenant_id: int, po_id: int) -> PurchaseOrder:
        po = self.get_purchase_order(tenant_id, po_id)
        if po.status != PurchaseOrderStatus.DRAFT:
            raise AppError("INVALID_PURCHASE_ORDER_STATE", "Only draft purchase orders can be submitted.", 409)
        if not po.items:
            raise AppError("PURCHASE_ORDER_ITEMS_REQUIRED", "Purchase order must include at least one item before submit.", 400)
        po.status = PurchaseOrderStatus.SUBMITTED
        po.submitted_at = datetime.now(UTC)
        result = self._commit_and_get_po(tenant_id, po.id)
        try:
            workflow = WorkflowService(self.db)
            workflow.log_event(tenant_id, "PURCHASE_ORDER_SUBMITTED", "purchase_order", po.id, None, {"po_number": po.po_number})
            total_value = sum((item.unit_cost or Decimal("0")) * item.ordered_quantity for item in result.items)
            if total_value > Decimal("10000"):
                workflow.create_task(tenant_id, WorkflowTaskCreate(
                    workflow_type="PURCHASING",
                    entity_type="purchase_order",
                    entity_id=po.id,
                    step_key="APPROVE_PO",
                    title=f"Approve high-value PO {po.po_number}",
                    description=f"Purchase order total {total_value} exceeds approval threshold.",
                    assigned_role="TENANT_ADMIN",
                    priority="HIGH",
                    action_url=f"/purchases/{po.id}",
                ))
            self.db.commit()
        except Exception:
            pass
        return result

    def cancel_purchase_order(self, tenant_id: int, po_id: int) -> PurchaseOrder:
        po = self.get_purchase_order(tenant_id, po_id)
        if po.status not in {PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.SUBMITTED}:
            raise AppError("INVALID_PURCHASE_ORDER_STATE", "Only draft or submitted purchase orders can be cancelled.", 409)
        po.status = PurchaseOrderStatus.CANCELLED
        po.cancelled_at = datetime.now(UTC)
        return self._commit_and_get_po(tenant_id, po.id)

    def close_purchase_order(self, tenant_id: int, po_id: int) -> PurchaseOrder:
        po = self.get_purchase_order(tenant_id, po_id)
        if po.status not in {PurchaseOrderStatus.SUBMITTED, PurchaseOrderStatus.PARTIALLY_RECEIVED}:
            raise AppError("INVALID_PURCHASE_ORDER_STATE", "Only submitted or partially received purchase orders can be closed.", 409)
        po.status = PurchaseOrderStatus.CLOSED
        po.closed_at = datetime.now(UTC)
        return self._commit_and_get_po(tenant_id, po.id)

    def list_receipts_for_order(self, tenant_id: int, po_id: int) -> list[PurchaseReceipt]:
        self.get_purchase_order(tenant_id, po_id)
        return self.repository.list_receipts_for_order(tenant_id, po_id)

    def get_receipt(self, tenant_id: int, receipt_id: int) -> PurchaseReceipt:
        receipt = self.repository.get_receipt(tenant_id, receipt_id)
        if receipt is None:
            raise AppError("PURCHASE_RECEIPT_NOT_FOUND", "Purchase receipt was not found for this tenant.", 404)
        return receipt

    def create_receipt(self, tenant_id: int, actor_id: int, po_id: int, values: dict[str, Any]) -> PurchaseReceipt:
        po = self.get_purchase_order(tenant_id, po_id)
        self._require_receivable(po)
        items = values.pop("items", [])
        receipt = self.repository.create_receipt({**values, "tenant_id": tenant_id, "purchase_order_id": po_id, "received_by": actor_id, "status": PurchaseReceiptStatus.DRAFT})
        self._replace_receipt_items(tenant_id, po, receipt.id, items)
        return self._commit_and_get_receipt(tenant_id, receipt.id)

    def update_receipt(self, tenant_id: int, receipt_id: int, values: dict[str, Any]) -> PurchaseReceipt:
        receipt = self.get_receipt(tenant_id, receipt_id)
        if receipt.status != PurchaseReceiptStatus.DRAFT:
            raise AppError("INVALID_PURCHASE_RECEIPT_STATE", "Only draft purchase receipts can be edited.", 409)
        po = self.get_purchase_order(tenant_id, receipt.purchase_order_id)
        self._require_receivable(po)
        items = values.pop("items", None)
        for key, value in values.items():
            setattr(receipt, key, value)
        if items is not None:
            self.repository.delete_receipt_items(tenant_id, receipt.id)
            self._replace_receipt_items(tenant_id, po, receipt.id, items)
        return self._commit_and_get_receipt(tenant_id, receipt.id)

    def cancel_receipt(self, tenant_id: int, receipt_id: int) -> PurchaseReceipt:
        receipt = self.get_receipt(tenant_id, receipt_id)
        if receipt.status != PurchaseReceiptStatus.DRAFT:
            raise AppError("INVALID_PURCHASE_RECEIPT_STATE", "Only draft purchase receipts can be cancelled.", 409)
        receipt.status = PurchaseReceiptStatus.CANCELLED
        receipt.cancelled_at = datetime.now(UTC)
        return self._commit_and_get_receipt(tenant_id, receipt.id)

    def commit_receipt(self, tenant_id: int, actor_id: int, receipt_id: int, values: dict[str, Any]) -> dict[str, Any]:
        receipt = self.repository.lock_receipt(tenant_id, receipt_id)
        if receipt is None:
            raise AppError("PURCHASE_RECEIPT_NOT_FOUND", "Purchase receipt was not found for this tenant.", 404)
        if receipt.status == PurchaseReceiptStatus.COMMITTED:
            return {"purchase_order": self.get_purchase_order(tenant_id, receipt.purchase_order_id), "receipt": self.get_receipt(tenant_id, receipt.id), "stock_results": []}
        if receipt.status != PurchaseReceiptStatus.DRAFT:
            raise AppError("INVALID_PURCHASE_RECEIPT_STATE", "Only draft purchase receipts can be committed.", 409)
        po = self.repository.lock_purchase_order(tenant_id, receipt.purchase_order_id)
        if po is None:
            raise AppError("PURCHASE_ORDER_NOT_FOUND", "Purchase order was not found for this tenant.", 404)
        self._require_receivable(po)
        receipt = self.get_receipt(tenant_id, receipt_id)
        if not receipt.items:
            raise AppError("PURCHASE_RECEIPT_ITEMS_REQUIRED", "Purchase receipt must include at least one item before commit.", 400)
        stock_results = []
        try:
            for item in receipt.items:
                po_item = self.repository.lock_purchase_order_item(tenant_id, item.purchase_order_item_id)
                if po_item is None or po_item.purchase_order_id != po.id:
                    raise AppError("PURCHASE_ORDER_ITEM_NOT_FOUND", "Purchase order item was not found for this purchase order.", 404)
                remaining = po_item.ordered_quantity - po_item.received_quantity
                if item.received_quantity > remaining:
                    raise AppError("OVER_RECEIVING_NOT_ALLOWED", "Received quantity cannot exceed remaining ordered quantity.", 409)
                result = InventoryService(self.db).stock_in(
                    tenant_id,
                    actor_id,
                    {
                        "product_id": item.product_id,
                        "warehouse_id": item.warehouse_id,
                        "location_id": item.location_id,
                        "quantity": item.received_quantity,
                        "batch_number": item.batch_number,
                        "supplier_batch_number": item.supplier_batch_number,
                        "manufacture_date": item.manufacture_date,
                        "expiry_date": item.expiry_date,
                        "warranty_until": item.warranty_until,
                        "serial_numbers": item.serial_numbers,
                        "reference_type": ReferenceType.PURCHASE_RECEIPT,
                        "reference_id": receipt.receipt_number,
                        "note": values.get("note") or receipt.notes,
                        "idempotency_key": f"{values['idempotency_key']}:receipt:{receipt.id}:item:{item.id}",
                    },
                    auto_commit=False,
                )
                stock_results.append(result)
                po_item.received_quantity += item.received_quantity
            receipt.status = PurchaseReceiptStatus.COMMITTED
            now = datetime.now(UTC)
            receipt.committed_at = now
            receipt.received_at = receipt.received_at or now
            self._update_purchase_order_receive_status(po)
            self.db.commit()
        except AppError:
            self.db.rollback()
            raise
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("PURCHASE_RECEIPT_COMMIT_FAILED", "Purchase receipt commit failed because of duplicate or invalid data.", 409) from exc
        try:
            workflow = WorkflowService(self.db)
            workflow.log_event(tenant_id, "RECEIPT_COMMITTED", "purchase_receipt", receipt.id, actor_id, {"po_number": po.po_number, "receipt_number": receipt.receipt_number})
            workflow.create_task(tenant_id, WorkflowTaskCreate(
                workflow_type="PURCHASING",
                entity_type="purchase_receipt",
                entity_id=receipt.id,
                step_key="PUTAWAY_STOCK",
                title=f"Putaway received stock for PO {po.po_number}",
                description="Receipt committed. Move stock to designated storage locations.",
                assigned_role="INVENTORY_MANAGER",
                priority="NORMAL",
                action_url=f"/putaway-tasks",
            ), created_by=actor_id)
            self.db.commit()
        except Exception:
            pass
        return {"purchase_order": self.get_purchase_order(tenant_id, po.id), "receipt": self.get_receipt(tenant_id, receipt.id), "stock_results": stock_results}

    def _replace_order_items(self, tenant_id: int, po_id: int, items: list[dict[str, Any]]) -> None:
        for item in items:
            self._require_product(tenant_id, item["product_id"])
            self.repository.create_purchase_order_item({**item, "tenant_id": tenant_id, "purchase_order_id": po_id, "received_quantity": Decimal("0")})

    def _replace_receipt_items(self, tenant_id: int, po: PurchaseOrder, receipt_id: int, items: list[dict[str, Any]]) -> None:
        pending_by_item: dict[int, Decimal] = {}
        for item in items:
            po_item = self.repository.get_purchase_order_item(tenant_id, item["purchase_order_item_id"])
            if po_item is None or po_item.purchase_order_id != po.id:
                raise AppError("PURCHASE_ORDER_ITEM_NOT_FOUND", "Purchase order item was not found for this purchase order.", 404)
            if po_item.product_id != item["product_id"]:
                raise AppError("PURCHASE_RECEIPT_PRODUCT_MISMATCH", "Receipt item product must match the purchase order item.", 400)
            product = self._require_product(tenant_id, item["product_id"])
            self._require_warehouse(tenant_id, item["warehouse_id"])
            self._require_location(tenant_id, item["warehouse_id"], item["location_id"])
            self._validate_tracking_fields(product, item)
            pending_by_item[po_item.id] = pending_by_item.get(po_item.id, Decimal("0")) + Decimal(str(item["received_quantity"]))
            remaining = po_item.ordered_quantity - po_item.received_quantity
            if pending_by_item[po_item.id] > remaining:
                raise AppError("OVER_RECEIVING_NOT_ALLOWED", "Received quantity cannot exceed remaining ordered quantity.", 409)
            values = {**item, "unit_cost": item.get("unit_cost") if item.get("unit_cost") is not None else po_item.unit_cost, "tenant_id": tenant_id, "purchase_receipt_id": receipt_id}
            self.repository.create_receipt_item(values)

    def _update_purchase_order_receive_status(self, po: PurchaseOrder) -> None:
        items = [self.repository.lock_purchase_order_item(po.tenant_id, item.id) for item in self.get_purchase_order(po.tenant_id, po.id).items]
        if all(item and item.received_quantity >= item.ordered_quantity for item in items):
            po.status = PurchaseOrderStatus.RECEIVED
            po.received_at = datetime.now(UTC)
        else:
            po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED

    def _require_receivable(self, po: PurchaseOrder) -> None:
        if po.status not in RECEIVABLE_STATUSES:
            raise AppError("INVALID_PURCHASE_ORDER_STATE", "Only submitted or partially received purchase orders can be received.", 409)

    def _require_vendor(self, tenant_id: int, vendor_id: int) -> None:
        if self.repository.get_vendor(tenant_id, vendor_id) is None:
            raise AppError("VENDOR_NOT_FOUND", "Vendor was not found for this tenant.", 404)

    def _require_product(self, tenant_id: int, product_id: int):
        product = self.repository.get_product(tenant_id, product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        return product

    def _validate_tracking_fields(self, product, item: dict[str, Any]) -> None:
        serial_numbers = item.get("serial_numbers") or []
        has_tracking_payload = any(item.get(field) is not None for field in ["batch_number", "supplier_batch_number", "manufacture_date", "expiry_date", "warranty_until"]) or bool(serial_numbers)
        if not product.track_batch and not product.track_expiry and not product.track_serial:
            if has_tracking_payload:
                raise AppError("TRACKING_NOT_ENABLED", "Tracking fields cannot be received for an untracked product.", 400)
            return
        if product.track_batch or product.track_expiry:
            if not str(item.get("batch_number") or "").strip():
                raise AppError("BATCH_NUMBER_REQUIRED", "Batch or expiry tracked receipt items require a batch number.", 400)
        if product.track_expiry and not item.get("expiry_date"):
            raise AppError("EXPIRY_DATE_REQUIRED", "Expiry-tracked receipt items require an expiry date.", 400)
        if product.track_serial:
            normalized = [str(value).strip() for value in serial_numbers]
            if not normalized or len(normalized) != len(serial_numbers) or len(set(normalized)) != len(normalized):
                raise AppError("INVALID_SERIAL_NUMBERS", "Serial numbers must be non-empty and unique.", 400)
            if Decimal(len(normalized)) != Decimal(str(item["received_quantity"])):
                raise AppError("SERIAL_QUANTITY_MISMATCH", "Serial number count must match received quantity.", 400)
            item["serial_numbers"] = normalized
        elif serial_numbers:
            raise AppError("SERIAL_TRACKING_NOT_ENABLED", "Serial numbers cannot be received for a non-serial-tracked product.", 400)

    def _require_warehouse(self, tenant_id: int, warehouse_id: int) -> None:
        if self.repository.get_warehouse(tenant_id, warehouse_id) is None:
            raise AppError("WAREHOUSE_NOT_FOUND", "Warehouse was not found for this tenant.", 404)

    def _require_location(self, tenant_id: int, warehouse_id: int, location_id: int) -> None:
        if self.repository.get_location(tenant_id, warehouse_id, location_id) is None:
            raise AppError("LOCATION_NOT_FOUND", "Location was not found for this tenant warehouse.", 404)

    def _commit_and_get_po(self, tenant_id: int, po_id: int) -> PurchaseOrder:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_PURCHASE_ORDER", "A purchase order with these unique values already exists for this tenant.", 409) from exc
        return self.get_purchase_order(tenant_id, po_id)

    def _commit_and_get_receipt(self, tenant_id: int, receipt_id: int) -> PurchaseReceipt:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AppError("DUPLICATE_PURCHASE_RECEIPT", "A purchase receipt with these unique values already exists for this tenant.", 409) from exc
        return self.get_receipt(tenant_id, receipt_id)
