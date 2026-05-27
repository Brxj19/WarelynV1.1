import csv
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from io import StringIO
from typing import Any

from sqlalchemy.orm import Session

from app.domain.inventory.reconciliation import InventoryReconciliation
from app.models.fulfillment import PickTaskStatus
from app.models.inventory import InventoryBatchStatus, InventorySerialStatus, MovementType, ReferenceType
from app.models.master_data import Product, RecordStatus, Warehouse, WarehouseLocation
from app.models.purchasing import PurchaseOrderStatus, PurchaseReceiptStatus
from app.models.returns import BlockedReturnStockStatus, SalesReturnStatus
from app.models.sales import SalesOrderStatus
from app.repositories.inventory import InventoryRepository
from app.repositories.reports import ReportsRepository

ZERO = Decimal("0")
BLOCKED_BATCH_STATUSES = {InventoryBatchStatus.QC_HOLD, InventoryBatchStatus.DAMAGED, InventoryBatchStatus.EXPIRED, InventoryBatchStatus.QUARANTINE, InventoryBatchStatus.SCRAPPED}
BLOCKED_SERIAL_STATUSES = {InventorySerialStatus.QC_HOLD, InventorySerialStatus.DAMAGED, InventorySerialStatus.SCRAPPED, InventorySerialStatus.RETURNED}


class ReportsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ReportsRepository(db)

    def inventory_summary(self, tenant_id: int) -> dict[str, Any]:
        products = self.repository.products(tenant_id)
        active_products = [product for product in products if product.status == RecordStatus.ACTIVE]
        stock = self.repository.stock(tenant_id)
        batches = self.repository.batches(tenant_id)
        blocked = self.blocked_stock(tenant_id)
        reconciliation = self.reconciliation(tenant_id)
        today = date.today()
        soon = today + timedelta(days=30)
        product_by_id = self._products(tenant_id)
        total_value = sum((product_by_id.get(row.product_id).cost_price or ZERO) * row.quantity_on_hand for row in stock if product_by_id.get(row.product_id) is not None)
        low_stock = self.low_stock(tenant_id)
        return {
            "total_products": len(products),
            "active_products": len(active_products),
            "total_skus_with_stock": len({row.product_id for row in stock if row.quantity_on_hand > ZERO}),
            "total_on_hand_quantity": sum((row.quantity_on_hand for row in stock), ZERO),
            "total_available_quantity": sum((row.quantity_available for row in stock), ZERO),
            "total_reserved_quantity": sum((row.quantity_reserved for row in stock), ZERO),
            "total_stock_value_cost": total_value,
            "low_stock_count": len([row for row in low_stock if row["status"] == "LOW_STOCK"]),
            "out_of_stock_count": len([row for row in low_stock if row["status"] == "OUT_OF_STOCK"]),
            "expiring_soon_batch_count": len([batch for batch in batches if batch.expiry_date and today <= batch.expiry_date <= soon]),
            "expired_batch_count": len([batch for batch in batches if batch.expiry_date and batch.expiry_date < today]),
            "damaged_blocked_qc_count": len(blocked),
            "reconciliation_mismatch_count": reconciliation["mismatch_count"],
        }

    def warehouse_stock(self, tenant_id: int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        products = self._products(tenant_id)
        warehouses = self._warehouses(tenant_id)
        rows = []
        for stock in self.repository.stock(tenant_id):
            product = products.get(stock.product_id)
            warehouse = warehouses.get(stock.warehouse_id)
            if not product or not warehouse or not self._matches_product_filters(product, filters):
                continue
            if filters.get("warehouse_id") and stock.warehouse_id != filters["warehouse_id"]:
                continue
            rows.append(self._stock_row(stock, product, warehouse))
        return rows

    def location_stock(self, tenant_id: int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        products = self._products(tenant_id)
        warehouses = self._warehouses(tenant_id)
        locations = self._locations(tenant_id)
        rows = []
        for stock in self.repository.stock(tenant_id):
            product = products.get(stock.product_id)
            warehouse = warehouses.get(stock.warehouse_id)
            location = locations.get(stock.location_id)
            if not product or not warehouse or not location or not self._matches_product_filters(product, filters):
                continue
            if filters.get("warehouse_id") and stock.warehouse_id != filters["warehouse_id"]:
                continue
            if filters.get("location_id") and stock.location_id != filters["location_id"]:
                continue
            rows.append({**self._stock_row(stock, product, warehouse), "location_id": location.id, "location_code": location.code, "location_name": location.name, "location_type": location.location_type.value})
        return rows

    def stock_movements(self, tenant_id: int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        products = self._products(tenant_id)
        warehouses = self._warehouses(tenant_id)
        locations = self._locations(tenant_id)
        movement_type = filters.get("movement_type")
        reference_type = filters.get("reference_type")
        rows = []
        for entry in self.repository.ledger(tenant_id, filters.get("date_from"), filters.get("date_to")):
            product = products.get(entry.product_id)
            warehouse = warehouses.get(entry.warehouse_id)
            location = locations.get(entry.location_id)
            if not product or not warehouse or not location:
                continue
            if not self._matches_product_filters(product, filters):
                continue
            if filters.get("warehouse_id") and entry.warehouse_id != filters["warehouse_id"]:
                continue
            if filters.get("location_id") and entry.location_id != filters["location_id"]:
                continue
            if movement_type and entry.movement_type != MovementType(movement_type):
                continue
            if reference_type and entry.reference_type != ReferenceType(reference_type):
                continue
            rows.append(
                {
                    "ledger_id": entry.id,
                    "movement_type": entry.movement_type,
                    "reference_type": entry.reference_type,
                    "reference_id": entry.reference_id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "sku": product.sku,
                    "warehouse_id": warehouse.id,
                    "warehouse_name": warehouse.name,
                    "location_id": location.id,
                    "location_name": location.name,
                    "batch_id": entry.batch_id,
                    "serial_id": entry.serial_id,
                    "quantity_delta": entry.quantity_delta,
                    "reserved_delta": entry.reserved_delta,
                    "available_delta": entry.available_delta,
                    "created_by": entry.created_by,
                    "created_at": entry.created_at,
                    "note": entry.note,
                }
            )
        return self._page(rows, filters)

    def low_stock(self, tenant_id: int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        rows = []
        for row in self.warehouse_stock(tenant_id, filters):
            reorder_level = row["reorder_level"]
            if reorder_level is None:
                continue
            if row["available"] <= ZERO:
                status = "OUT_OF_STOCK"
            elif row["available"] <= Decimal(str(reorder_level)):
                status = "LOW_STOCK"
            else:
                continue
            rows.append({**row, "suggested_reorder_quantity": self._suggested_quantity(Decimal(str(reorder_level)), row["available"]), "status": status})
        return rows

    def reorder_suggestions(self, tenant_id: int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        suggestions = []
        for row in self.low_stock(tenant_id, filters):
            suggestions.append(
                {
                    "product_id": row["product_id"],
                    "product_name": row["product_name"],
                    "sku": row["sku"],
                    "default_vendor_id": None,
                    "default_vendor_name": None,
                    "warehouse_id": row["warehouse_id"],
                    "warehouse_name": row["warehouse_name"],
                    "available": row["available"],
                    "reorder_level": row["reorder_level"],
                    "suggested_quantity": row["suggested_reorder_quantity"],
                    "reason": row["status"],
                }
            )
        return suggestions

    def product_valuation(self, tenant_id: int, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        rows = self.warehouse_stock(tenant_id, filters)
        return {"total_stock_value": sum((row["stock_value"] for row in rows), ZERO), "total_units": sum((row["on_hand"] for row in rows), ZERO), "rows": rows}

    def batch_expiry(self, tenant_id: int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        products = self._products(tenant_id)
        warehouses = self._warehouses(tenant_id)
        locations = self._locations(tenant_id)
        today = date.today()
        soon = today + timedelta(days=int(filters.get("expiry_within_days") or 30))
        rows = []
        for batch in self.repository.batches(tenant_id):
            product = products.get(batch.product_id)
            warehouse = warehouses.get(batch.warehouse_id)
            location = locations.get(batch.location_id)
            if not product or not warehouse or not location or not self._matches_product_filters(product, filters):
                continue
            if filters.get("warehouse_id") and batch.warehouse_id != filters["warehouse_id"]:
                continue
            if filters.get("location_id") and batch.location_id != filters["location_id"]:
                continue
            if filters.get("status") and batch.status.value != filters["status"]:
                continue
            if filters.get("expiry_before") and (not batch.expiry_date or batch.expiry_date > filters["expiry_before"]):
                continue
            days_to_expiry = (batch.expiry_date - today).days if batch.expiry_date else None
            if batch.expiry_date and batch.expiry_date < today:
                expiry_status = "EXPIRED"
            elif batch.expiry_date and batch.expiry_date <= soon:
                expiry_status = "EXPIRING_SOON"
            else:
                expiry_status = "OK"
            rows.append({"batch_id": batch.id, "batch_number": batch.batch_number, "product_id": product.id, "product_name": product.name, "sku": product.sku, "warehouse_id": warehouse.id, "warehouse_name": warehouse.name, "location_id": location.id, "location_name": location.name, "expiry_date": batch.expiry_date, "quantity_on_hand": batch.quantity_on_hand, "quantity_available": batch.quantity_available, "quantity_reserved": batch.quantity_reserved, "status": batch.status, "days_to_expiry": days_to_expiry, "expiry_status": expiry_status})
        return rows

    def serial_status(self, tenant_id: int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        products = self._products(tenant_id)
        warehouses = self._warehouses(tenant_id)
        locations = self._locations(tenant_id)
        rows = []
        for serial in self.repository.serials(tenant_id):
            product = products.get(serial.product_id)
            warehouse = warehouses.get(serial.warehouse_id)
            location = locations.get(serial.location_id)
            if not product or not warehouse or not location or not self._matches_product_filters(product, filters):
                continue
            if filters.get("warehouse_id") and serial.warehouse_id != filters["warehouse_id"]:
                continue
            if filters.get("location_id") and serial.location_id != filters["location_id"]:
                continue
            if filters.get("status") and serial.status.value != filters["status"]:
                continue
            rows.append({"serial_id": serial.id, "serial_number": serial.serial_number, "product_id": product.id, "product_name": product.name, "sku": product.sku, "warehouse_id": warehouse.id, "warehouse_name": warehouse.name, "location_id": location.id, "location_name": location.name, "batch_id": serial.batch_id, "status": serial.status, "warranty_until": serial.warranty_until, "expires_on": serial.expires_on, "created_at": serial.created_at})
        return rows

    def blocked_stock(self, tenant_id: int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        products = self._products(tenant_id)
        warehouses = self._warehouses(tenant_id)
        locations = self._locations(tenant_id)
        rows = []
        for blocked in self.repository.blocked_return_stock(tenant_id):
            rows.append(self._blocked_row("RETURN_BLOCKED", blocked.product_id, blocked.warehouse_id, blocked.location_id, blocked.batch_id, blocked.serial_id, blocked.quantity, blocked.status.value, blocked.reason, blocked.created_at, products, warehouses, locations))
        for batch in self.repository.batches(tenant_id):
            if batch.status in BLOCKED_BATCH_STATUSES:
                rows.append(self._blocked_row("BATCH_STATUS", batch.product_id, batch.warehouse_id, batch.location_id, batch.id, None, batch.quantity_on_hand, batch.status.value, None, batch.created_at, products, warehouses, locations))
        for serial in self.repository.serials(tenant_id):
            if serial.status in BLOCKED_SERIAL_STATUSES:
                rows.append(self._blocked_row("SERIAL_STATUS", serial.product_id, serial.warehouse_id, serial.location_id, serial.batch_id, serial.id, Decimal("1"), serial.status.value, None, serial.created_at, products, warehouses, locations))
        rows = [row for row in rows if row and self._matches_blocked_filters(row, filters)]
        return rows

    def reconciliation(self, tenant_id: int) -> dict[str, Any]:
        raw = InventoryReconciliation(InventoryRepository(self.db)).dry_run(tenant_id)
        products = self._products(tenant_id)
        warehouses = self._warehouses(tenant_id)
        locations = self._locations(tenant_id)
        mismatches = []
        for item in raw["mismatches"]:
            product = products.get(item["product_id"])
            warehouse = warehouses.get(item["warehouse_id"])
            location = locations.get(item["location_id"])
            mismatches.append({**item, "product_name": product.name if product else None, "sku": product.sku if product else None, "warehouse_name": warehouse.name if warehouse else None, "location_name": location.name if location else None})
        return {"tenant_id": tenant_id, "mismatch_count": raw["mismatch_count"], "mismatches": mismatches}

    def operational_dashboard(self, tenant_id: int, compare_previous: bool = False) -> dict[str, Any]:
        summary = self.inventory_summary(tenant_id)
        purchase_orders = self.repository.purchase_orders(tenant_id)
        purchase_receipts = self.repository.purchase_receipts(tenant_id)
        sales_orders = self.repository.sales_orders(tenant_id)
        pick_tasks = self.repository.pick_tasks(tenant_id)
        returns = self.repository.sales_returns(tenant_id)
        expiring = self.batch_expiry(tenant_id, {"expiry_within_days": 30})
        low_stock_all = self.low_stock(tenant_id)
        low_stock = low_stock_all[:5]
        result: dict[str, Any] = {
            "kpis": summary,
            "pending_purchase_orders": len([po for po in purchase_orders if po.status in {PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.SUBMITTED, PurchaseOrderStatus.PARTIALLY_RECEIVED}]),
            "pending_purchase_receipts": len([receipt for receipt in purchase_receipts if receipt.status == PurchaseReceiptStatus.DRAFT]),
            "open_sales_orders": len([order for order in sales_orders if order.status in {SalesOrderStatus.DRAFT, SalesOrderStatus.CONFIRMED, SalesOrderStatus.PARTIALLY_FULFILLED}]),
            "active_pick_tasks": len([task for task in pick_tasks if task.status in {PickTaskStatus.PENDING, PickTaskStatus.IN_PROGRESS}]),
            "pending_returns_qc": len([row for row in returns if row.status in {SalesReturnStatus.SUBMITTED, SalesReturnStatus.INSPECTION_PENDING}]),
            "blocked_stock_count": summary["damaged_blocked_qc_count"],
            "expiring_soon_count": summary["expiring_soon_batch_count"],
            "reconciliation_mismatch_count": summary["reconciliation_mismatch_count"],
            "recent_stock_movements": self.stock_movements(tenant_id, {"page": 1, "page_size": 5}),
            "low_stock_items": low_stock,
            "expiring_batches": [row for row in expiring if row["expiry_status"] in {"EXPIRED", "EXPIRING_SOON"}][:5],
            "pending_actions": [
                {"label": "Low stock items", "count": len(low_stock), "tone": "warning"},
                {"label": "Returns awaiting QC", "count": len([row for row in returns if row.status in {SalesReturnStatus.SUBMITTED, SalesReturnStatus.INSPECTION_PENDING}]), "tone": "primary"},
                {"label": "Reconciliation mismatches", "count": summary["reconciliation_mismatch_count"], "tone": "danger" if summary["reconciliation_mismatch_count"] else "success"},
            ],
        }

        # Real previous period comparison (no fake/random data)
        if compare_previous:
            today = date.today()
            current_end = today
            current_start = today - timedelta(days=7)
            previous_end = current_start - timedelta(days=1)
            previous_start = previous_end - timedelta(days=6)
            previous_ledger = self.repository.ledger(tenant_id, previous_start, previous_end)
            if previous_ledger:
                # Count movements in previous period to derive comparable KPIs
                current_ledger = self.repository.ledger(tenant_id, current_start, current_end)
                current_inbound = sum(1 for e in current_ledger if e.movement_type in {MovementType.STOCK_IN, MovementType.ADJUSTMENT_IN, MovementType.RETURN_RESTOCK, MovementType.TRANSFER_IN})
                current_outbound = sum(1 for e in current_ledger if e.movement_type in {MovementType.STOCK_OUT, MovementType.ADJUSTMENT_OUT, MovementType.SALES_DEDUCT, MovementType.TRANSFER_OUT})
                previous_inbound = sum(1 for e in previous_ledger if e.movement_type in {MovementType.STOCK_IN, MovementType.ADJUSTMENT_IN, MovementType.RETURN_RESTOCK, MovementType.TRANSFER_IN})
                previous_outbound = sum(1 for e in previous_ledger if e.movement_type in {MovementType.STOCK_OUT, MovementType.ADJUSTMENT_OUT, MovementType.SALES_DEDUCT, MovementType.TRANSFER_OUT})
                # Build previous_kpis using current summary as base with movement-based deltas
                previous_kpis = dict(summary)
                movement_diff = (current_inbound - current_outbound) - (previous_inbound - previous_outbound)
                prev_on_hand = max(ZERO, summary["total_on_hand_quantity"] - Decimal(str(movement_diff)))
                previous_kpis["total_on_hand_quantity"] = prev_on_hand
                previous_kpis["total_available_quantity"] = max(ZERO, summary["total_available_quantity"] - Decimal(str(movement_diff)))
                result["previous_kpis"] = previous_kpis
            else:
                result["previous_kpis"] = None

        # Charts
        result["charts"] = self._build_charts(tenant_id, purchase_orders, sales_orders, low_stock_all)

        # Insights
        result["insights"] = self._build_insights(tenant_id, summary, expiring)

        return result

    def _build_charts(self, tenant_id: int, purchase_orders: list[Any], sales_orders: list[Any], low_stock_items: list[dict[str, Any]]) -> dict[str, Any]:
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        ledger_entries = self.repository.ledger(tenant_id, thirty_days_ago, today)

        # Stock movements by day
        inbound_types = {MovementType.STOCK_IN, MovementType.ADJUSTMENT_IN, MovementType.RETURN_RESTOCK, MovementType.TRANSFER_IN}
        outbound_types = {MovementType.STOCK_OUT, MovementType.ADJUSTMENT_OUT, MovementType.SALES_DEDUCT, MovementType.TRANSFER_OUT}
        day_map: dict[str, dict[str, int]] = {}
        for i in range(30):
            d = (thirty_days_ago + timedelta(days=i + 1)).isoformat()
            day_map[d] = {"inbound": 0, "outbound": 0}
        for entry in ledger_entries:
            entry_date = entry.created_at.date().isoformat() if entry.created_at else None
            if entry_date and entry_date in day_map:
                if entry.movement_type in inbound_types:
                    day_map[entry_date]["inbound"] += 1
                elif entry.movement_type in outbound_types:
                    day_map[entry_date]["outbound"] += 1
        stock_movements_by_day = [{"date": d, "inbound": v["inbound"], "outbound": v["outbound"]} for d, v in sorted(day_map.items())]

        # Order status summary
        po_status_counts: dict[str, int] = {}
        for po in purchase_orders:
            status_val = po.status.value if hasattr(po.status, "value") else str(po.status)
            po_status_counts[status_val] = po_status_counts.get(status_val, 0) + 1
        so_status_counts: dict[str, int] = {}
        for so in sales_orders:
            status_val = so.status.value if hasattr(so.status, "value") else str(so.status)
            so_status_counts[status_val] = so_status_counts.get(status_val, 0) + 1
        order_status_summary = {"purchase_orders": po_status_counts, "sales_orders": so_status_counts}

        # Low stock by category
        products = self._products(tenant_id)
        categories = {cat.id: cat.name for cat in self.repository.categories(tenant_id)}
        category_counts: dict[str, int] = {}
        for item in low_stock_items:
            product = products.get(item["product_id"])
            cat_name = categories.get(product.category_id, "Uncategorized") if product and product.category_id else "Uncategorized"
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        low_stock_by_category = [{"category": cat, "count": cnt} for cat, cnt in sorted(category_counts.items())]

        return {
            "stock_movements_by_day": stock_movements_by_day,
            "order_status_summary": order_status_summary,
            "low_stock_by_category": low_stock_by_category,
        }

    def _build_insights(self, tenant_id: int, summary: dict[str, Any], expiring_batches: list[dict[str, Any]]) -> list[dict[str, Any]]:
        insights: list[dict[str, Any]] = []
        low_stock_count = summary.get("low_stock_count", 0)
        if low_stock_count > 5:
            insights.append({
                "severity": "warning",
                "title": "High number of low-stock products",
                "message": f"{low_stock_count} products are below their reorder level. Review purchasing priorities.",
                "action_url": "/reports/low-stock",
            })
        mismatch_count = summary.get("reconciliation_mismatch_count", 0)
        if mismatch_count > 0:
            insights.append({
                "severity": "danger",
                "title": "Reconciliation mismatches detected",
                "message": f"{mismatch_count} stock position{'s differ' if mismatch_count > 1 else ' differs'} from ledger history. Investigate immediately.",
                "action_url": "/reports/reconciliation",
            })
        # Expiring within 7 days
        today = date.today()
        soon_7 = today + timedelta(days=7)
        expiring_7_days = [b for b in expiring_batches if b.get("expiry_date") and b["expiry_date"] <= soon_7 and b["expiry_date"] >= today]
        if expiring_7_days:
            insights.append({
                "severity": "warning",
                "title": "Batches expiring within 7 days",
                "message": f"{len(expiring_7_days)} batch{'es' if len(expiring_7_days) > 1 else ''} will expire in the next 7 days.",
                "action_url": "/reports/batch-expiry",
            })
        return insights

    def export_csv(self, tenant_id: int, report_key: str, filters: dict[str, Any] | None = None) -> str:
        rows = self.export_rows(tenant_id, report_key, filters)
        output = StringIO()
        if not rows:
            output.write("message\r\nNo data\r\n")
            return output.getvalue()
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: self._csv_value(value) for key, value in row.items()})
        return output.getvalue()

    def export_rows(self, tenant_id: int, report_key: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        if report_key == "inventory-summary":
            return [self.inventory_summary(tenant_id)]
        if report_key == "warehouse-stock":
            return self.warehouse_stock(tenant_id, filters)
        if report_key == "location-stock":
            return self.location_stock(tenant_id, filters)
        if report_key == "stock-movements":
            return self.stock_movements(tenant_id, filters)
        if report_key == "low-stock":
            return self.low_stock(tenant_id, filters)
        if report_key == "reorder-suggestions":
            return self.reorder_suggestions(tenant_id, filters)
        if report_key == "product-valuation":
            report = self.product_valuation(tenant_id, filters)
            return report["rows"]
        if report_key == "batch-expiry":
            return self.batch_expiry(tenant_id, filters)
        if report_key == "serial-status":
            return self.serial_status(tenant_id, filters)
        if report_key == "blocked-stock":
            return self.blocked_stock(tenant_id, filters)
        if report_key == "reconciliation":
            report = self.reconciliation(tenant_id)
            return report["mismatches"]
        raise ValueError(report_key)

    def _products(self, tenant_id: int) -> dict[int, Product]:
        return {row.id: row for row in self.repository.products(tenant_id)}

    def _warehouses(self, tenant_id: int) -> dict[int, Warehouse]:
        return {row.id: row for row in self.repository.warehouses(tenant_id)}

    def _locations(self, tenant_id: int) -> dict[int, WarehouseLocation]:
        return {row.id: row for row in self.repository.locations(tenant_id)}

    def _stock_row(self, stock: Any, product: Product, warehouse: Warehouse) -> dict[str, Any]:
        cost = product.cost_price or ZERO
        reorder_level = product.reorder_level
        if stock.quantity_available <= ZERO:
            status = "OUT_OF_STOCK"
        elif reorder_level is not None and stock.quantity_available <= Decimal(str(reorder_level)):
            status = "LOW_STOCK"
        else:
            status = "HEALTHY"
        return {"warehouse_id": warehouse.id, "warehouse_name": warehouse.name, "product_id": product.id, "product_name": product.name, "sku": product.sku, "on_hand": stock.quantity_on_hand, "reserved": stock.quantity_reserved, "available": stock.quantity_available, "cost_price": cost, "stock_value": cost * stock.quantity_on_hand, "reorder_level": reorder_level, "stock_status": status}

    def _matches_product_filters(self, product: Product, filters: dict[str, Any]) -> bool:
        if filters.get("product_id") and product.id != filters["product_id"]:
            return False
        if filters.get("category_id") and product.category_id != filters["category_id"]:
            return False
        if filters.get("brand_id") and product.brand_id != filters["brand_id"]:
            return False
        if filters.get("search"):
            term = str(filters["search"]).lower()
            return term in product.name.lower() or term in product.sku.lower() or (product.barcode and term in product.barcode.lower())
        return True

    def _suggested_quantity(self, reorder_level: Decimal, available: Decimal) -> Decimal:
        return max((reorder_level * Decimal("2")) - available, reorder_level)

    def _page(self, rows: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
        page = int(filters.get("page") or 1)
        page_size = min(int(filters.get("page_size") or 100), 500)
        start = (page - 1) * page_size
        return rows[start : start + page_size]

    def _blocked_row(self, source_type: str, product_id: int, warehouse_id: int, location_id: int, batch_id: int | None, serial_id: int | None, quantity: Decimal, status: str, reason: str | None, created_at: datetime, products: dict[int, Product], warehouses: dict[int, Warehouse], locations: dict[int, WarehouseLocation]) -> dict[str, Any] | None:
        product = products.get(product_id)
        warehouse = warehouses.get(warehouse_id)
        location = locations.get(location_id)
        if not product or not warehouse or not location:
            return None
        return {"source_type": source_type, "product_id": product.id, "product_name": product.name, "sku": product.sku, "warehouse_id": warehouse.id, "warehouse_name": warehouse.name, "location_id": location.id, "location_name": location.name, "batch_id": batch_id, "serial_id": serial_id, "quantity": quantity, "status": status, "reason": reason, "created_at": created_at}

    def _matches_blocked_filters(self, row: dict[str, Any], filters: dict[str, Any]) -> bool:
        if filters.get("product_id") and row["product_id"] != filters["product_id"]:
            return False
        if filters.get("warehouse_id") and row["warehouse_id"] != filters["warehouse_id"]:
            return False
        if filters.get("location_id") and row["location_id"] != filters["location_id"]:
            return False
        if filters.get("status") and row["status"] != filters["status"]:
            return False
        return True

    def _csv_value(self, value: Any) -> Any:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if hasattr(value, "value"):
            return value.value
        return value
