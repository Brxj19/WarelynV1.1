import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.domain.inventory.reconciliation import InventoryReconciliation
from app.models.inventory import InventoryBatchStatus, InventorySerial, InventorySerialStatus, MovementType, ReferenceType, ReservationStatus, StockLedgerEntry, StockReservation, WarehouseStock
from app.models.returns import BlockedReturnStockStatus
from app.repositories.inventory import InventoryRepository

ZERO = Decimal("0")


class InventoryEngine:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = InventoryRepository(db)

    def stock_in(self, tenant_id: int, actor_id: int, payload: dict[str, Any], auto_commit: bool = True) -> dict:
        return self._run_idempotent("stock_in", tenant_id, actor_id, payload, lambda: self._stock_in(tenant_id, actor_id, payload), auto_commit=auto_commit)

    def stock_out(self, tenant_id: int, actor_id: int, payload: dict[str, Any]) -> dict:
        return self._run_idempotent("stock_out", tenant_id, actor_id, payload, lambda: self._stock_out(tenant_id, actor_id, payload))

    def adjust_stock(self, tenant_id: int, actor_id: int, payload: dict[str, Any]) -> dict:
        return self._run_idempotent("adjust_stock", tenant_id, actor_id, payload, lambda: self._adjust_stock(tenant_id, actor_id, payload))

    def reserve_stock(self, tenant_id: int, actor_id: int, payload: dict[str, Any], auto_commit: bool = True) -> dict:
        return self._run_idempotent("reserve_stock", tenant_id, actor_id, payload, lambda: self._reserve_stock(tenant_id, actor_id, payload), auto_commit=auto_commit)

    def release_reservation(self, tenant_id: int, actor_id: int, reservation_id: int, payload: dict[str, Any], auto_commit: bool = True) -> dict:
        body = {**payload, "reservation_id": reservation_id}
        return self._run_idempotent("release_reservation", tenant_id, actor_id, body, lambda: self._release_reservation(tenant_id, actor_id, reservation_id, payload), auto_commit=auto_commit)

    def deduct_reserved_stock(self, tenant_id: int, actor_id: int, reservation_id: int, payload: dict[str, Any], auto_commit: bool = True) -> dict:
        body = {**payload, "reservation_id": reservation_id}
        return self._run_idempotent("deduct_reserved_stock", tenant_id, actor_id, body, lambda: self._deduct_reserved_stock(tenant_id, actor_id, reservation_id, payload), auto_commit=auto_commit)

    def transfer_stock(self, tenant_id: int, actor_id: int, payload: dict[str, Any]) -> dict:
        return self._run_idempotent("transfer_stock", tenant_id, actor_id, payload, lambda: self._transfer_stock(tenant_id, actor_id, payload))

    def return_restock(self, tenant_id: int, actor_id: int, payload: dict[str, Any], auto_commit: bool = True) -> dict:
        return self._run_idempotent("return_restock", tenant_id, actor_id, payload, lambda: self._return_restock(tenant_id, actor_id, payload), auto_commit=auto_commit)

    def record_return_blocked(self, tenant_id: int, actor_id: int, payload: dict[str, Any], auto_commit: bool = True) -> dict:
        return self._run_idempotent("record_return_blocked", tenant_id, actor_id, payload, lambda: self._record_return_non_sellable(tenant_id, actor_id, payload, BlockedReturnStockStatus.QC_HOLD, InventorySerialStatus.QC_HOLD), auto_commit=auto_commit)

    def record_return_damaged(self, tenant_id: int, actor_id: int, payload: dict[str, Any], auto_commit: bool = True) -> dict:
        return self._run_idempotent("record_return_damaged", tenant_id, actor_id, payload, lambda: self._record_return_non_sellable(tenant_id, actor_id, payload, BlockedReturnStockStatus.DAMAGED, InventorySerialStatus.DAMAGED), auto_commit=auto_commit)

    def record_return_scrap(self, tenant_id: int, actor_id: int, payload: dict[str, Any], auto_commit: bool = True) -> dict:
        return self._run_idempotent("record_return_scrap", tenant_id, actor_id, payload, lambda: self._record_return_non_sellable(tenant_id, actor_id, payload, BlockedReturnStockStatus.SCRAPPED, InventorySerialStatus.SCRAPPED), auto_commit=auto_commit)

    def reconcile_stock_dry_run(self, tenant_id: int) -> dict:
        return InventoryReconciliation(self.repository).dry_run(tenant_id)

    def _stock_in(self, tenant_id: int, actor_id: int, payload: dict[str, Any]) -> dict:
        quantity = self._positive_quantity(payload["quantity"])
        self._validate_dimension(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        product = self.repository.get_product(tenant_id, payload["product_id"])
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        stock = self.repository.get_or_create_stock(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        stock.quantity_on_hand += quantity
        stock.quantity_available += quantity
        self._assert_invariants(stock)
        entries = self._apply_inbound_tracking(stock, product, quantity, actor_id, payload)
        if not entries:
            entries = [self._ledger(stock, MovementType.STOCK_IN, quantity, ZERO, quantity, actor_id, payload)]
        return self._response(stock, entries, None, payload["idempotency_key"])

    def _stock_out(self, tenant_id: int, actor_id: int, payload: dict[str, Any]) -> dict:
        quantity = self._positive_quantity(payload["quantity"])
        self._validate_dimension(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        stock = self.repository.lock_stock(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        if stock is None:
            raise AppError("STOCK_NOT_FOUND", "Stock was not found for this tenant.", 404)
        self._require_available(stock, quantity)
        stock.quantity_on_hand -= quantity
        stock.quantity_available -= quantity
        self._assert_invariants(stock)
        entry = self._ledger(stock, MovementType.STOCK_OUT, -quantity, ZERO, -quantity, actor_id, payload)
        return self._response(stock, [entry], None, payload["idempotency_key"])

    def _adjust_stock(self, tenant_id: int, actor_id: int, payload: dict[str, Any]) -> dict:
        delta = Decimal(str(payload["delta"]))
        if delta == ZERO:
            raise AppError("INVALID_STOCK_QUANTITY", "Adjustment delta cannot be zero.", 400)
        self._validate_dimension(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        stock = self.repository.get_or_create_stock(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        if delta < ZERO:
            self._require_available(stock, abs(delta))
            movement = MovementType.ADJUSTMENT_OUT
        else:
            movement = MovementType.ADJUSTMENT_IN
        stock.quantity_on_hand += delta
        stock.quantity_available += delta
        self._assert_invariants(stock)
        entry = self._ledger(stock, movement, delta, ZERO, delta, actor_id, payload)
        return self._response(stock, [entry], None, payload["idempotency_key"])

    def _reserve_stock(self, tenant_id: int, actor_id: int, payload: dict[str, Any]) -> dict:
        quantity = self._positive_quantity(payload["quantity"])
        self._validate_dimension(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        stock = self.repository.lock_stock(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        if stock is None:
            raise AppError("STOCK_NOT_FOUND", "Stock was not found for this tenant.", 404)
        self._require_available(stock, quantity)
        reservation = self.repository.create_reservation(
            {
                "tenant_id": tenant_id,
                "product_id": payload["product_id"],
                "warehouse_id": payload["warehouse_id"],
                "location_id": payload["location_id"],
                "quantity": quantity,
                "status": ReservationStatus.ACTIVE,
                "reference_type": payload.get("reference_type", ReferenceType.SALES_ORDER),
                "reference_id": payload.get("reference_id"),
                "created_by": actor_id,
            }
        )
        stock.quantity_reserved += quantity
        stock.quantity_available -= quantity
        self._assert_invariants(stock)
        entry = self._ledger(stock, MovementType.SALES_RESERVE, ZERO, quantity, -quantity, actor_id, payload)
        return self._response(stock, [entry], reservation, payload["idempotency_key"])

    def _release_reservation(self, tenant_id: int, actor_id: int, reservation_id: int, payload: dict[str, Any]) -> dict:
        reservation = self.repository.lock_reservation(tenant_id, reservation_id)
        if reservation is None:
            raise AppError("RESERVATION_NOT_FOUND", "Reservation was not found for this tenant.", 404)
        if reservation.status != ReservationStatus.ACTIVE:
            raise AppError("INVALID_RESERVATION_STATE", "Only active reservations can be released.", 409)
        stock = self.repository.lock_stock(tenant_id, reservation.product_id, reservation.warehouse_id, reservation.location_id)
        if stock is None:
            raise AppError("STOCK_NOT_FOUND", "Stock was not found for this tenant.", 404)
        reservation.status = ReservationStatus.RELEASED
        reservation.released_at = datetime.now(UTC)
        stock.quantity_reserved -= reservation.quantity
        stock.quantity_available += reservation.quantity
        self._assert_invariants(stock)
        ledger_payload = {**payload, "reference_type": reservation.reference_type, "reference_id": reservation.reference_id, "idempotency_key": payload["idempotency_key"]}
        entry = self._ledger(stock, MovementType.SALES_RELEASE, ZERO, -reservation.quantity, reservation.quantity, actor_id, ledger_payload)
        return self._response(stock, [entry], reservation, payload["idempotency_key"])

    def _deduct_reserved_stock(self, tenant_id: int, actor_id: int, reservation_id: int, payload: dict[str, Any]) -> dict:
        reservation = self.repository.lock_reservation(tenant_id, reservation_id)
        if reservation is None:
            raise AppError("RESERVATION_NOT_FOUND", "Reservation was not found for this tenant.", 404)
        if reservation.status != ReservationStatus.ACTIVE:
            raise AppError("INVALID_RESERVATION_STATE", "Only active reservations can be deducted.", 409)
        stock = self.repository.lock_stock(tenant_id, reservation.product_id, reservation.warehouse_id, reservation.location_id)
        if stock is None:
            raise AppError("STOCK_NOT_FOUND", "Stock was not found for this tenant.", 404)
        product = self.repository.get_product(tenant_id, reservation.product_id)
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        if product.track_serial:
            serial_id = payload.get("serial_id")
            if serial_id is None:
                raise AppError("SERIAL_SELECTION_REQUIRED", "Serial-tracked deduction requires a picked serial allocation.", 400)
            if reservation.quantity != Decimal("1"):
                raise AppError("SERIAL_RESERVATION_QUANTITY_INVALID", "Serial reservations must be deducted one unit at a time.", 409)
            serial = self.repository.get_serial(tenant_id, int(serial_id))
            if serial is None:
                raise AppError("SERIAL_NOT_FOUND", "Serial was not found for this tenant.", 404)
            if serial.product_id != reservation.product_id or serial.warehouse_id != reservation.warehouse_id or serial.location_id != reservation.location_id:
                raise AppError("SERIAL_RESERVATION_MISMATCH", "Picked serial must match the reservation dimensions.", 400)
            if serial.status != InventorySerialStatus.IN_STOCK:
                raise AppError("SERIAL_NOT_AVAILABLE", "Picked serial must be in stock before deduction.", 409)
            serial.status = InventorySerialStatus.SOLD
        reservation.status = ReservationStatus.DEDUCTED
        reservation.deducted_at = datetime.now(UTC)
        stock.quantity_on_hand -= reservation.quantity
        stock.quantity_reserved -= reservation.quantity
        self._assert_invariants(stock)
        ledger_payload = {**payload, "reference_type": reservation.reference_type, "reference_id": reservation.reference_id, "idempotency_key": payload["idempotency_key"]}
        entry = self._ledger(stock, MovementType.SALES_DEDUCT, -reservation.quantity, -reservation.quantity, ZERO, actor_id, ledger_payload)
        return self._response(stock, [entry], reservation, payload["idempotency_key"])

    def _transfer_stock(self, tenant_id: int, actor_id: int, payload: dict[str, Any]) -> dict:
        quantity = self._positive_quantity(payload["quantity"])
        source = (payload["product_id"], payload["source_warehouse_id"], payload["source_location_id"])
        destination = (payload["product_id"], payload["destination_warehouse_id"], payload["destination_location_id"])
        if source == destination:
            raise AppError("INVALID_STOCK_STATE", "Source and destination stock dimensions must differ.", 400)
        self._validate_dimension(tenant_id, *source)
        self._validate_dimension(tenant_id, *destination)
        locked = {}
        for dimension in sorted([source, destination]):
            locked[dimension] = self.repository.get_or_create_stock(tenant_id, *dimension)
        source_stock = locked[source]
        destination_stock = locked[destination]
        self._require_available(source_stock, quantity)
        source_stock.quantity_on_hand -= quantity
        source_stock.quantity_available -= quantity
        destination_stock.quantity_on_hand += quantity
        destination_stock.quantity_available += quantity
        self._assert_invariants(source_stock)
        self._assert_invariants(destination_stock)
        source_payload = {**payload, "warehouse_id": source_stock.warehouse_id, "location_id": source_stock.location_id}
        dest_payload = {**payload, "warehouse_id": destination_stock.warehouse_id, "location_id": destination_stock.location_id}
        out_entry = self._ledger(source_stock, MovementType.TRANSFER_OUT, -quantity, ZERO, -quantity, actor_id, source_payload)
        in_entry = self._ledger(destination_stock, MovementType.TRANSFER_IN, quantity, ZERO, quantity, actor_id, dest_payload)
        return self._response([source_stock, destination_stock], [out_entry, in_entry], None, payload["idempotency_key"])

    def _return_restock(self, tenant_id: int, actor_id: int, payload: dict[str, Any]) -> dict:
        quantity = self._positive_quantity(payload["quantity"])
        self._validate_dimension(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        product = self.repository.get_product(tenant_id, payload["product_id"])
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        stock = self.repository.get_or_create_stock(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        serial = None
        if product.track_serial:
            serial_id = payload.get("serial_id")
            if serial_id is None:
                raise AppError("SERIAL_SELECTION_REQUIRED", "Serial-tracked returns require a sold serial reference.", 400)
            if quantity != Decimal("1"):
                raise AppError("SERIAL_RETURN_QUANTITY_INVALID", "Serial-tracked returns must be processed one unit at a time.", 400)
            serial = self.repository.lock_serial(tenant_id, int(serial_id))
            if serial is None:
                raise AppError("SERIAL_NOT_FOUND", "Serial was not found for this tenant.", 404)
            if serial.product_id != product.id:
                raise AppError("SERIAL_PRODUCT_MISMATCH", "Returned serial must match the returned product.", 400)
            if serial.status != InventorySerialStatus.SOLD:
                raise AppError("SERIAL_NOT_SOLD", "Only sold serials can be returned to stock.", 409)
            serial.warehouse_id = stock.warehouse_id
            serial.location_id = stock.location_id
            serial.batch_id = payload.get("batch_id")
            serial.status = InventorySerialStatus.IN_STOCK
        elif payload.get("serial_id") is not None:
            raise AppError("SERIAL_TRACKING_NOT_ENABLED", "Serial IDs cannot be returned for a non-serial-tracked product.", 400)
        batch_id = payload.get("batch_id")
        if batch_id is not None:
            batch = self.repository.lock_batch_by_id(tenant_id, int(batch_id))
            if batch is None:
                raise AppError("BATCH_NOT_FOUND", "Inventory batch was not found for this tenant.", 404)
            if batch.product_id != stock.product_id:
                raise AppError("BATCH_PRODUCT_MISMATCH", "Returned batch must match the returned product.", 400)
            batch.quantity_on_hand += quantity
            batch.quantity_available += quantity
        stock.quantity_on_hand += quantity
        stock.quantity_available += quantity
        self._assert_invariants(stock)
        entry = self._ledger(stock, MovementType.RETURN_RESTOCK, quantity, ZERO, quantity, actor_id, {**payload, "reference_type": ReferenceType.SALES_RETURN, "serial_id": serial.id if serial else payload.get("serial_id")})
        return self._response(stock, [entry], None, payload["idempotency_key"])

    def _record_return_non_sellable(self, tenant_id: int, actor_id: int, payload: dict[str, Any], blocked_status: BlockedReturnStockStatus, serial_status: InventorySerialStatus) -> dict:
        quantity = self._positive_quantity(payload["quantity"])
        self._validate_dimension(tenant_id, payload["product_id"], payload["warehouse_id"], payload["location_id"])
        product = self.repository.get_product(tenant_id, payload["product_id"])
        if product is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        serial = None
        if product.track_serial:
            serial_id = payload.get("serial_id")
            if serial_id is None:
                raise AppError("SERIAL_SELECTION_REQUIRED", "Serial-tracked returns require a sold serial reference.", 400)
            if quantity != Decimal("1"):
                raise AppError("SERIAL_RETURN_QUANTITY_INVALID", "Serial-tracked returns must be processed one unit at a time.", 400)
            serial = self.repository.lock_serial(tenant_id, int(serial_id))
            if serial is None:
                raise AppError("SERIAL_NOT_FOUND", "Serial was not found for this tenant.", 404)
            if serial.product_id != product.id:
                raise AppError("SERIAL_PRODUCT_MISMATCH", "Returned serial must match the returned product.", 400)
            if serial.status != InventorySerialStatus.SOLD:
                raise AppError("SERIAL_NOT_SOLD", "Only sold serials can be accepted into return QC.", 409)
            serial.warehouse_id = payload["warehouse_id"]
            serial.location_id = payload["location_id"]
            serial.batch_id = payload.get("batch_id")
            serial.status = serial_status
        elif payload.get("serial_id") is not None:
            raise AppError("SERIAL_TRACKING_NOT_ENABLED", "Serial IDs cannot be returned for a non-serial-tracked product.", 400)
        blocked = self.repository.create_blocked_return_stock(
            {
                "tenant_id": tenant_id,
                "sales_return_id": payload["sales_return_id"],
                "sales_return_item_id": payload["sales_return_item_id"],
                "product_id": payload["product_id"],
                "warehouse_id": payload["warehouse_id"],
                "location_id": payload["location_id"],
                "batch_id": payload.get("batch_id"),
                "serial_id": serial.id if serial else payload.get("serial_id"),
                "quantity": quantity,
                "status": blocked_status,
                "reason": payload.get("reason"),
                "notes": payload.get("note"),
            }
        )
        self.db.flush()
        return {"blocked_return_stock_id": blocked.id, "status": blocked.status.value, "quantity": str(blocked.quantity), "idempotency_key": payload["idempotency_key"]}

    def _validate_dimension(self, tenant_id: int, product_id: int, warehouse_id: int, location_id: int) -> None:
        if self.repository.get_product(tenant_id, product_id) is None:
            raise AppError("PRODUCT_NOT_FOUND", "Product was not found for this tenant.", 404)
        if self.repository.get_warehouse(tenant_id, warehouse_id) is None:
            raise AppError("WAREHOUSE_NOT_FOUND", "Warehouse was not found for this tenant.", 404)
        if self.repository.get_location(tenant_id, warehouse_id, location_id) is None:
            raise AppError("LOCATION_NOT_FOUND", "Location was not found for this tenant warehouse.", 404)

    def _run_idempotent(self, operation: str, tenant_id: int, actor_id: int, payload: dict[str, Any], handler: Any, auto_commit: bool = True) -> dict:
        key = payload.get("idempotency_key")
        if not key:
            raise AppError("IDEMPOTENCY_KEY_REQUIRED", "Idempotency key is required.", 400)
        request_hash = self._request_hash(payload)
        existing = self.repository.get_idempotency(tenant_id, key, operation)
        if existing:
            if existing.request_hash != request_hash:
                raise AppError("IDEMPOTENCY_CONFLICT", "Idempotency key was already used with a different request.", 409)
            return existing.response_json
        try:
            response = handler()
            self.repository.store_idempotency(tenant_id, key, operation, request_hash, response, actor_id)
            if auto_commit:
                self.db.commit()
            return response
        except AppError:
            if auto_commit:
                self.db.rollback()
            raise
        except IntegrityError as exc:
            if auto_commit:
                self.db.rollback()
            raise AppError("IDEMPOTENCY_CONFLICT", "Idempotency key was already used.", 409) from exc

    def _ledger(self, stock: WarehouseStock, movement_type: MovementType, quantity_delta: Decimal, reserved_delta: Decimal, available_delta: Decimal, actor_id: int, payload: dict[str, Any]) -> StockLedgerEntry:
        return self.repository.add_ledger_entry(
            {
                "tenant_id": stock.tenant_id,
                "product_id": stock.product_id,
                "warehouse_id": stock.warehouse_id,
                "location_id": stock.location_id,
                "batch_id": payload.get("batch_id"),
                "serial_id": payload.get("serial_id"),
                "movement_type": movement_type,
                "quantity_delta": quantity_delta,
                "reserved_delta": reserved_delta,
                "available_delta": available_delta,
                "reference_type": payload.get("reference_type", ReferenceType.MANUAL),
                "reference_id": payload.get("reference_id"),
                "idempotency_key": payload["idempotency_key"],
                "note": payload.get("note"),
                "created_by": actor_id,
            }
        )

    def _apply_inbound_tracking(self, stock: WarehouseStock, product: Any, quantity: Decimal, actor_id: int, payload: dict[str, Any]) -> list[StockLedgerEntry]:
        serial_numbers = self._normalized_serial_numbers(payload.get("serial_numbers"))
        has_tracking_payload = any(payload.get(field) is not None for field in ["batch_number", "supplier_batch_number", "manufacture_date", "expiry_date", "warranty_until"]) or bool(serial_numbers)
        if not product.track_batch and not product.track_expiry and not product.track_serial:
            if has_tracking_payload:
                raise AppError("TRACKING_NOT_ENABLED", "Tracking fields cannot be received for an untracked product.", 400)
            return []

        if product.track_serial:
            if not serial_numbers:
                raise AppError("SERIAL_NUMBERS_REQUIRED", "Serial-tracked products require serial numbers on stock in.", 400)
            if quantity != Decimal(len(serial_numbers)):
                raise AppError("SERIAL_QUANTITY_MISMATCH", "Serial-tracked stock in quantity must match serial number count.", 400)
        elif serial_numbers:
            raise AppError("SERIAL_TRACKING_NOT_ENABLED", "Serial numbers cannot be received for a non-serial-tracked product.", 400)

        batch = None
        if product.track_batch or product.track_expiry or payload.get("batch_number"):
            batch_number = str(payload.get("batch_number") or "").strip()
            if not batch_number:
                raise AppError("BATCH_NUMBER_REQUIRED", "Batch or expiry tracked products require a batch number on stock in.", 400)
            if product.track_expiry and not payload.get("expiry_date"):
                raise AppError("EXPIRY_DATE_REQUIRED", "Expiry-tracked products require an expiry date on stock in.", 400)
            batch = self.repository.lock_batch(stock.tenant_id, stock.product_id, stock.warehouse_id, stock.location_id, batch_number)
            if batch is None:
                batch = self.repository.create_batch(
                    {
                        "tenant_id": stock.tenant_id,
                        "product_id": stock.product_id,
                        "warehouse_id": stock.warehouse_id,
                        "location_id": stock.location_id,
                        "batch_number": batch_number,
                        "supplier_batch_number": payload.get("supplier_batch_number"),
                        "manufacture_date": payload.get("manufacture_date"),
                        "expiry_date": payload.get("expiry_date"),
                        "warranty_until": payload.get("warranty_until"),
                        "quantity_on_hand": ZERO,
                        "quantity_available": ZERO,
                        "quantity_reserved": ZERO,
                        "status": InventoryBatchStatus.ACTIVE,
                    }
                )
            batch.quantity_on_hand += quantity
            batch.quantity_available += quantity

        if product.track_serial:
            entries = []
            for serial_number in serial_numbers:
                if self.repository.get_serial_by_number(stock.tenant_id, stock.product_id, serial_number) is not None:
                    raise AppError("SERIAL_NUMBER_EXISTS", "Serial number already exists for this product.", 409)
                serial = self.repository.create_serial(
                    {
                        "tenant_id": stock.tenant_id,
                        "product_id": stock.product_id,
                        "warehouse_id": stock.warehouse_id,
                        "location_id": stock.location_id,
                        "batch_id": batch.id if batch else None,
                        "serial_number": serial_number,
                        "status": InventorySerialStatus.IN_STOCK,
                        "warranty_until": payload.get("warranty_until"),
                        "expires_on": payload.get("expiry_date"),
                    }
                )
                entries.append(self._ledger(stock, MovementType.STOCK_IN, Decimal("1"), ZERO, Decimal("1"), actor_id, {**payload, "batch_id": batch.id if batch else None, "serial_id": serial.id}))
            return entries

        if batch is not None:
            return [self._ledger(stock, MovementType.STOCK_IN, quantity, ZERO, quantity, actor_id, {**payload, "batch_id": batch.id})]
        return []

    def _normalized_serial_numbers(self, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise AppError("INVALID_SERIAL_NUMBERS", "Serial numbers must be a list.", 400)
        serial_numbers = [str(item).strip() for item in value if str(item).strip()]
        if len(serial_numbers) != len(value) or len(set(serial_numbers)) != len(serial_numbers):
            raise AppError("INVALID_SERIAL_NUMBERS", "Serial numbers must be non-empty and unique.", 400)
        return serial_numbers

    def _response(self, stock: WarehouseStock | list[WarehouseStock], entries: list[StockLedgerEntry], reservation: StockReservation | None, idempotency_key: str) -> dict:
        self.db.flush()
        return {
            "stock": [self._stock_json(item) for item in stock] if isinstance(stock, list) else self._stock_json(stock),
            "ledger_entries": [self._ledger_json(entry) for entry in entries],
            "reservation": self._reservation_json(reservation) if reservation else None,
            "idempotency_key": idempotency_key,
        }

    def _stock_json(self, stock: WarehouseStock) -> dict:
        return {
            "id": stock.id,
            "tenant_id": stock.tenant_id,
            "product_id": stock.product_id,
            "warehouse_id": stock.warehouse_id,
            "location_id": stock.location_id,
            "quantity_on_hand": str(stock.quantity_on_hand),
            "quantity_reserved": str(stock.quantity_reserved),
            "quantity_available": str(stock.quantity_available),
            "updated_at": datetime.now(UTC).isoformat(),
        }

    def _ledger_json(self, entry: StockLedgerEntry) -> dict:
        return {
            "id": entry.id,
            "tenant_id": entry.tenant_id,
            "product_id": entry.product_id,
            "warehouse_id": entry.warehouse_id,
            "location_id": entry.location_id,
            "batch_id": entry.batch_id,
            "serial_id": entry.serial_id,
            "movement_type": entry.movement_type.value,
            "quantity_delta": str(entry.quantity_delta),
            "reserved_delta": str(entry.reserved_delta),
            "available_delta": str(entry.available_delta),
            "reference_type": entry.reference_type.value,
            "reference_id": entry.reference_id,
            "idempotency_key": entry.idempotency_key,
            "note": entry.note,
            "created_by": entry.created_by,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def _reservation_json(self, reservation: StockReservation) -> dict:
        return {
            "id": reservation.id,
            "tenant_id": reservation.tenant_id,
            "product_id": reservation.product_id,
            "warehouse_id": reservation.warehouse_id,
            "location_id": reservation.location_id,
            "quantity": str(reservation.quantity),
            "status": reservation.status.value,
            "reference_type": reservation.reference_type.value,
            "reference_id": reservation.reference_id,
            "created_by": reservation.created_by,
            "released_at": reservation.released_at.isoformat() if reservation.released_at else None,
            "deducted_at": reservation.deducted_at.isoformat() if reservation.deducted_at else None,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

    def _request_hash(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def _positive_quantity(self, value: Any) -> Decimal:
        quantity = Decimal(str(value))
        if quantity <= ZERO:
            raise AppError("INVALID_STOCK_QUANTITY", "Quantity must be greater than zero.", 400)
        return quantity

    def _require_available(self, stock: WarehouseStock, quantity: Decimal) -> None:
        if stock.quantity_available < quantity:
            raise AppError("INSUFFICIENT_STOCK", "Available stock is insufficient for this operation.", 409)

    def _assert_invariants(self, stock: WarehouseStock) -> None:
        if stock.quantity_on_hand < ZERO or stock.quantity_reserved < ZERO or stock.quantity_available < ZERO:
            raise AppError("INVALID_STOCK_STATE", "Stock quantities cannot be negative.", 409)
        if stock.quantity_reserved > stock.quantity_on_hand:
            raise AppError("INVALID_STOCK_STATE", "Reserved quantity cannot exceed on-hand quantity.", 409)
        if stock.quantity_available != stock.quantity_on_hand - stock.quantity_reserved:
            raise AppError("INVALID_STOCK_STATE", "Available quantity must equal on-hand minus reserved quantity.", 409)
