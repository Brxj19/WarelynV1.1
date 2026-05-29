from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.inventory import IdempotencyKey, IdempotencyStatus, InventoryBatch, InventorySerial, StockLedgerEntry, StockReservation, WarehouseStock
from app.models.master_data import Product, Warehouse, WarehouseLocation
from app.models.returns import BlockedReturnStock


class InventoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_product(self, tenant_id: int, product_id: int) -> Product | None:
        return self.db.scalar(select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id))

    def get_warehouse(self, tenant_id: int, warehouse_id: int) -> Warehouse | None:
        return self.db.scalar(select(Warehouse).where(Warehouse.id == warehouse_id, Warehouse.tenant_id == tenant_id))

    def get_location(self, tenant_id: int, warehouse_id: int, location_id: int) -> WarehouseLocation | None:
        return self.db.scalar(select(WarehouseLocation).where(WarehouseLocation.id == location_id, WarehouseLocation.warehouse_id == warehouse_id, WarehouseLocation.tenant_id == tenant_id))

    def list_stock(self, tenant_id: int) -> list[WarehouseStock]:
        return list(self.db.scalars(select(WarehouseStock).where(WarehouseStock.tenant_id == tenant_id)))

    def list_ledger(self, tenant_id: int) -> list[StockLedgerEntry]:
        return list(self.db.scalars(select(StockLedgerEntry).where(StockLedgerEntry.tenant_id == tenant_id).order_by(StockLedgerEntry.created_at.desc(), StockLedgerEntry.id.desc())))

    def list_reservations(self, tenant_id: int) -> list[StockReservation]:
        return list(self.db.scalars(select(StockReservation).where(StockReservation.tenant_id == tenant_id).order_by(StockReservation.created_at.desc(), StockReservation.id.desc())))

    def list_batches(self, tenant_id: int) -> list[InventoryBatch]:
        return list(self.db.scalars(select(InventoryBatch).where(InventoryBatch.tenant_id == tenant_id).order_by(InventoryBatch.created_at.desc(), InventoryBatch.id.desc())))

    def get_batch(self, tenant_id: int, batch_id: int) -> InventoryBatch | None:
        return self.db.scalar(select(InventoryBatch).where(InventoryBatch.id == batch_id, InventoryBatch.tenant_id == tenant_id))

    def list_serials(self, tenant_id: int) -> list[InventorySerial]:
        return list(self.db.scalars(select(InventorySerial).where(InventorySerial.tenant_id == tenant_id).order_by(InventorySerial.created_at.desc(), InventorySerial.id.desc())))

    def get_serial(self, tenant_id: int, serial_id: int) -> InventorySerial | None:
        return self.db.scalar(select(InventorySerial).where(InventorySerial.id == serial_id, InventorySerial.tenant_id == tenant_id))

    def stock_query(self, tenant_id: int, product_id: int, warehouse_id: int, location_id: int) -> Select[tuple[WarehouseStock]]:
        return select(WarehouseStock).where(
            WarehouseStock.tenant_id == tenant_id,
            WarehouseStock.product_id == product_id,
            WarehouseStock.warehouse_id == warehouse_id,
            WarehouseStock.location_id == location_id,
        )

    def get_stock(self, tenant_id: int, product_id: int, warehouse_id: int, location_id: int) -> WarehouseStock | None:
        return self.db.scalar(self.stock_query(tenant_id, product_id, warehouse_id, location_id))

    def lock_stock(self, tenant_id: int, product_id: int, warehouse_id: int, location_id: int) -> WarehouseStock | None:
        return self.db.scalar(self.stock_query(tenant_id, product_id, warehouse_id, location_id).with_for_update())

    def create_stock(self, tenant_id: int, product_id: int, warehouse_id: int, location_id: int) -> WarehouseStock:
        stock = WarehouseStock(
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            location_id=location_id,
            quantity_on_hand=Decimal("0"),
            quantity_reserved=Decimal("0"),
            quantity_available=Decimal("0"),
        )
        self.db.add(stock)
        self.db.flush()
        return stock

    def get_or_create_stock(self, tenant_id: int, product_id: int, warehouse_id: int, location_id: int) -> WarehouseStock:
        stock = self.lock_stock(tenant_id, product_id, warehouse_id, location_id)
        if stock is not None:
            return stock
        return self.create_stock(tenant_id, product_id, warehouse_id, location_id)

    def batch_query(self, tenant_id: int, product_id: int, warehouse_id: int, location_id: int, batch_number: str) -> Select[tuple[InventoryBatch]]:
        return select(InventoryBatch).where(
            InventoryBatch.tenant_id == tenant_id,
            InventoryBatch.product_id == product_id,
            InventoryBatch.warehouse_id == warehouse_id,
            InventoryBatch.location_id == location_id,
            InventoryBatch.batch_number == batch_number,
        )

    def lock_batch(self, tenant_id: int, product_id: int, warehouse_id: int, location_id: int, batch_number: str) -> InventoryBatch | None:
        return self.db.scalar(self.batch_query(tenant_id, product_id, warehouse_id, location_id, batch_number).with_for_update())

    def create_batch(self, values: dict[str, Any]) -> InventoryBatch:
        batch = InventoryBatch(**values)
        self.db.add(batch)
        self.db.flush()
        return batch

    def get_serial_by_number(self, tenant_id: int, product_id: int, serial_number: str) -> InventorySerial | None:
        return self.db.scalar(select(InventorySerial).where(InventorySerial.tenant_id == tenant_id, InventorySerial.product_id == product_id, InventorySerial.serial_number == serial_number))

    def create_serial(self, values: dict[str, Any]) -> InventorySerial:
        serial = InventorySerial(**values)
        self.db.add(serial)
        self.db.flush()
        return serial

    def lock_serial(self, tenant_id: int, serial_id: int) -> InventorySerial | None:
        return self.db.scalar(select(InventorySerial).where(InventorySerial.id == serial_id, InventorySerial.tenant_id == tenant_id).with_for_update())

    def lock_batch_by_id(self, tenant_id: int, batch_id: int) -> InventoryBatch | None:
        return self.db.scalar(select(InventoryBatch).where(InventoryBatch.id == batch_id, InventoryBatch.tenant_id == tenant_id).with_for_update())

    def create_blocked_return_stock(self, values: dict[str, Any]) -> BlockedReturnStock:
        record = BlockedReturnStock(**values)
        self.db.add(record)
        self.db.flush()
        return record

    def add_ledger_entry(self, values: dict[str, Any]) -> StockLedgerEntry:
        entry = StockLedgerEntry(**values)
        self.db.add(entry)
        self.db.flush()
        return entry

    def create_reservation(self, values: dict[str, Any]) -> StockReservation:
        reservation = StockReservation(**values)
        self.db.add(reservation)
        self.db.flush()
        return reservation

    def lock_reservation(self, tenant_id: int, reservation_id: int) -> StockReservation | None:
        return self.db.scalar(select(StockReservation).where(StockReservation.id == reservation_id, StockReservation.tenant_id == tenant_id).with_for_update())

    def get_idempotency(self, tenant_id: int, key: str, operation: str) -> IdempotencyKey | None:
        return self.db.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id == tenant_id, IdempotencyKey.key == key, IdempotencyKey.operation == operation).with_for_update())

    def store_idempotency(self, tenant_id: int, key: str, operation: str, request_hash: str, response_json: dict[str, Any], created_by: int) -> IdempotencyKey:
        record = IdempotencyKey(
            tenant_id=tenant_id,
            key=key,
            operation=operation,
            request_hash=request_hash,
            response_json=response_json,
            status=IdempotencyStatus.COMPLETED,
            created_by=created_by,
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        self.db.add(record)
        self.db.flush()
        return record

    def ledger_totals(self, tenant_id: int) -> list[tuple[int, int, int, Decimal, Decimal, Decimal]]:
        return list(
            self.db.execute(
                select(
                    StockLedgerEntry.product_id,
                    StockLedgerEntry.warehouse_id,
                    StockLedgerEntry.location_id,
                    func.coalesce(func.sum(StockLedgerEntry.quantity_delta), 0),
                    func.coalesce(func.sum(StockLedgerEntry.reserved_delta), 0),
                    func.coalesce(func.sum(StockLedgerEntry.available_delta), 0),
                )
                .where(StockLedgerEntry.tenant_id == tenant_id)
                .group_by(StockLedgerEntry.product_id, StockLedgerEntry.warehouse_id, StockLedgerEntry.location_id)
            )
        )
