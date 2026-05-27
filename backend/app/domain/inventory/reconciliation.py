from decimal import Decimal

from app.repositories.inventory import InventoryRepository


class InventoryReconciliation:
    def __init__(self, repository: InventoryRepository) -> None:
        self.repository = repository

    def dry_run(self, tenant_id: int) -> dict:
        mismatches = []
        seen_dimensions = set()
        for product_id, warehouse_id, location_id, on_hand, reserved, available in self.repository.ledger_totals(tenant_id):
            seen_dimensions.add((product_id, warehouse_id, location_id))
            stock = self.repository.get_stock(tenant_id, product_id, warehouse_id, location_id)
            actual_on_hand = stock.quantity_on_hand if stock else Decimal("0")
            actual_reserved = stock.quantity_reserved if stock else Decimal("0")
            actual_available = stock.quantity_available if stock else Decimal("0")
            if actual_on_hand != on_hand or actual_reserved != reserved or actual_available != available:
                mismatches.append(
                    {
                        "product_id": product_id,
                        "warehouse_id": warehouse_id,
                        "location_id": location_id,
                        "expected_on_hand": on_hand,
                        "actual_on_hand": actual_on_hand,
                        "expected_reserved": reserved,
                        "actual_reserved": actual_reserved,
                        "expected_available": available,
                        "actual_available": actual_available,
                    }
                )
        for stock in self.repository.list_stock(tenant_id):
            dimension = (stock.product_id, stock.warehouse_id, stock.location_id)
            if dimension not in seen_dimensions and (stock.quantity_on_hand or stock.quantity_reserved or stock.quantity_available):
                mismatches.append(
                    {
                        "product_id": stock.product_id,
                        "warehouse_id": stock.warehouse_id,
                        "location_id": stock.location_id,
                        "expected_on_hand": Decimal("0"),
                        "actual_on_hand": stock.quantity_on_hand,
                        "expected_reserved": Decimal("0"),
                        "actual_reserved": stock.quantity_reserved,
                        "expected_available": Decimal("0"),
                        "actual_available": stock.quantity_available,
                    }
                )
        return {"tenant_id": tenant_id, "mismatch_count": len(mismatches), "mismatches": mismatches}
