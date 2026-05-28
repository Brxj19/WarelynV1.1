from sqlalchemy.orm import Session

from app.models.operations import ReorderRule
from app.repositories.inventory import InventoryRepository
from app.repositories.operations import ReorderRuleRepository
from app.schemas.workflow import WorkflowTaskCreate
from app.services.workflow import WorkflowService


def run_low_stock_check(db: Session, tenant_id: int) -> dict:
    reorder_repo = ReorderRuleRepository(db)
    inventory_repo = InventoryRepository(db)
    workflow = WorkflowService(db)

    rules = reorder_repo.list(tenant_id)
    tasks_created = 0

    for rule in rules:
        if not rule.is_active:
            continue
        stock = inventory_repo.get_stock(tenant_id, rule.product_id, rule.warehouse_id, None)
        current_qty = stock.quantity_available if stock else 0
        if current_qty >= rule.min_quantity:
            continue
        try:
            if workflow.repository.has_open_task(tenant_id, "product", rule.product_id, "REORDER_STOCK"):
                continue
            workflow.create_task(tenant_id, WorkflowTaskCreate(
                workflow_type="INVENTORY",
                entity_type="product",
                entity_id=rule.product_id,
                step_key="REORDER_STOCK",
                title=f"Low stock: product #{rule.product_id} below reorder point",
                description=f"Current available: {current_qty}, minimum: {rule.min_quantity}. Create a purchase order.",
                assigned_role="PURCHASE_STAFF",
                priority="HIGH",
                action_url=f"/catalog/products/{rule.product_id}",
            ))
            tasks_created += 1
        except Exception:
            pass

    if tasks_created:
        try:
            db.commit()
        except Exception:
            pass

    return {"rules_checked": len(rules), "tasks_created": tasks_created}
