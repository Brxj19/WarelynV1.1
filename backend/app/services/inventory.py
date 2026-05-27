import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.domain.inventory.engine import InventoryEngine
from app.models.inventory import InventoryBatch, InventorySerial, StockLedgerEntry, WarehouseStock
from app.repositories.audit import AuditLogRepository
from app.repositories.inventory import InventoryRepository


class InventoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = InventoryRepository(db)
        self.engine = InventoryEngine(db)
        self.audit_logs = AuditLogRepository(db)

    def _audit_mutation(self, tenant_id: int, actor_id: int, actor_role: str, action: str, values: dict[str, Any], result: dict) -> None:
        meta = {
            "product_id": values.get("product_id"),
            "warehouse_id": values.get("warehouse_id"),
            "location_id": values.get("location_id"),
            "quantity": str(values.get("quantity", "")),
            "reference_type": values.get("reference_type"),
            "reference_id": values.get("reference_id"),
            "idempotency_key": values.get("idempotency_key"),
        }
        if result and "ledger_entries" in result:
            entries = result["ledger_entries"]
            if isinstance(entries, list) and len(entries) > 0:
                meta["movement_type"] = entries[0].get("movement_type") if isinstance(entries[0], dict) else None
                meta["ledger_entry_ids"] = [e.get("id") if isinstance(e, dict) else None for e in entries]
        self.audit_logs.create(
            {
                "tenant_id": tenant_id,
                "actor_user_id": actor_id,
                "actor_role": actor_role,
                "action": action,
                "entity_type": "stock",
                "metadata_json": meta,
            }
        )

    def list_stock(self, tenant_id: int) -> list[WarehouseStock]:
        return self.repository.list_stock(tenant_id)

    def list_ledger(self, tenant_id: int) -> list[StockLedgerEntry]:
        return self.repository.list_ledger(tenant_id)

    def list_batches(self, tenant_id: int) -> list[InventoryBatch]:
        return self.repository.list_batches(tenant_id)

    def get_batch(self, tenant_id: int, batch_id: int) -> InventoryBatch:
        batch = self.repository.get_batch(tenant_id, batch_id)
        if batch is None:
            raise AppError("BATCH_NOT_FOUND", "Inventory batch was not found for this tenant.", 404)
        return batch

    def list_serials(self, tenant_id: int) -> list[InventorySerial]:
        return self.repository.list_serials(tenant_id)

    def get_serial(self, tenant_id: int, serial_id: int) -> InventorySerial:
        serial = self.repository.get_serial(tenant_id, serial_id)
        if serial is None:
            raise AppError("SERIAL_NOT_FOUND", "Inventory serial was not found for this tenant.", 404)
        return serial

    def stock_in(self, tenant_id: int, actor_id: int, values: dict[str, Any], auto_commit: bool = True, actor_role: str = "") -> dict:
        result = self.engine.stock_in(tenant_id, actor_id, values, auto_commit=auto_commit)
        self._audit_mutation(tenant_id, actor_id, actor_role, "STOCK_IN", values, result)
        return result

    def stock_out(self, tenant_id: int, actor_id: int, values: dict[str, Any], actor_role: str = "") -> dict:
        result = self.engine.stock_out(tenant_id, actor_id, values)
        self._audit_mutation(tenant_id, actor_id, actor_role, "STOCK_OUT", values, result)
        return result

    def adjust_stock(self, tenant_id: int, actor_id: int, values: dict[str, Any], actor_role: str = "") -> dict:
        result = self.engine.adjust_stock(tenant_id, actor_id, values)
        self._audit_mutation(tenant_id, actor_id, actor_role, "STOCK_ADJUST", values, result)
        return result

    def reserve_stock(self, tenant_id: int, actor_id: int, values: dict[str, Any], auto_commit: bool = True, actor_role: str = "") -> dict:
        result = self.engine.reserve_stock(tenant_id, actor_id, values, auto_commit=auto_commit)
        self._audit_mutation(tenant_id, actor_id, actor_role, "STOCK_RESERVE", values, result)
        return result

    def release_reservation(self, tenant_id: int, actor_id: int, reservation_id: int, values: dict[str, Any], auto_commit: bool = True, actor_role: str = "") -> dict:
        result = self.engine.release_reservation(tenant_id, actor_id, reservation_id, values, auto_commit=auto_commit)
        self._audit_mutation(tenant_id, actor_id, actor_role, "STOCK_RELEASE", {**values, "reservation_id": reservation_id}, result)
        return result

    def deduct_reserved_stock(self, tenant_id: int, actor_id: int, reservation_id: int, values: dict[str, Any], auto_commit: bool = True, actor_role: str = "") -> dict:
        result = self.engine.deduct_reserved_stock(tenant_id, actor_id, reservation_id, values, auto_commit=auto_commit)
        self._audit_mutation(tenant_id, actor_id, actor_role, "STOCK_DEDUCT", {**values, "reservation_id": reservation_id}, result)
        return result

    def transfer_stock(self, tenant_id: int, actor_id: int, values: dict[str, Any], actor_role: str = "") -> dict:
        result = self.engine.transfer_stock(tenant_id, actor_id, values)
        self._audit_mutation(tenant_id, actor_id, actor_role, "STOCK_TRANSFER", values, result)
        return result

    def return_restock(self, tenant_id: int, actor_id: int, values: dict[str, Any], auto_commit: bool = True, actor_role: str = "") -> dict:
        result = self.engine.return_restock(tenant_id, actor_id, values, auto_commit=auto_commit)
        self._audit_mutation(tenant_id, actor_id, actor_role, "RETURN_RESTOCK", values, result)
        return result

    def record_return_blocked(self, tenant_id: int, actor_id: int, values: dict[str, Any], auto_commit: bool = True, actor_role: str = "") -> dict:
        result = self.engine.record_return_blocked(tenant_id, actor_id, values, auto_commit=auto_commit)
        self._audit_mutation(tenant_id, actor_id, actor_role, "RETURN_BLOCKED", values, result)
        return result

    def record_return_damaged(self, tenant_id: int, actor_id: int, values: dict[str, Any], auto_commit: bool = True, actor_role: str = "") -> dict:
        result = self.engine.record_return_damaged(tenant_id, actor_id, values, auto_commit=auto_commit)
        self._audit_mutation(tenant_id, actor_id, actor_role, "RETURN_DAMAGED", values, result)
        return result

    def record_return_scrap(self, tenant_id: int, actor_id: int, values: dict[str, Any], auto_commit: bool = True, actor_role: str = "") -> dict:
        result = self.engine.record_return_scrap(tenant_id, actor_id, values, auto_commit=auto_commit)
        self._audit_mutation(tenant_id, actor_id, actor_role, "RETURN_SCRAP", values, result)
        return result

    def reconcile_stock_dry_run(self, tenant_id: int) -> dict:
        return self.engine.reconcile_stock_dry_run(tenant_id)
