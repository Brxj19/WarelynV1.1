from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.domain.inventory.engine import InventoryEngine
from app.models.inventory import InventoryBatch, InventoryBatchStatus, MovementType, ReferenceType, WarehouseStock
from app.models.operations import PutawayTask, PutawayTaskStatus, StockCountSession, StockCountSessionStatus
from app.repositories.inventory import InventoryRepository
from app.repositories.operations import CycleCountRepository, OutboxRepository, PutawayTaskRepository, ReorderRuleRepository
from app.schemas.workflow import WorkflowTaskCreate
from app.services.workflow import WorkflowService


class ReorderRuleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ReorderRuleRepository(db)

    def list(self, tenant_id: int):
        return self.repository.list(tenant_id)

    def get(self, tenant_id: int, rule_id: int):
        rule = self.repository.get(tenant_id, rule_id)
        if rule is None:
            raise AppError("REORDER_RULE_NOT_FOUND", "Reorder rule not found.", 404)
        return rule

    def create(self, tenant_id: int, data: dict):
        rule = self.repository.create({**data, "tenant_id": tenant_id})
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update(self, tenant_id: int, rule_id: int, data: dict):
        rule = self.get(tenant_id, rule_id)
        rule = self.repository.update(rule, data)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete(self, tenant_id: int, rule_id: int) -> None:
        rule = self.get(tenant_id, rule_id)
        self.repository.delete(rule)
        self.db.commit()


class PutawayTaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = PutawayTaskRepository(db)

    def list(self, tenant_id: int, status: PutawayTaskStatus | None = None):
        return self.repository.list(tenant_id, status)

    def get(self, tenant_id: int, task_id: int):
        task = self.repository.get(tenant_id, task_id)
        if task is None:
            raise AppError("PUTAWAY_TASK_NOT_FOUND", "Putaway task not found.", 404)
        return task

    def create(self, tenant_id: int, data: dict):
        task = self.repository.create({**data, "tenant_id": tenant_id})
        self.db.commit()
        self.db.refresh(task)
        return task

    def start(self, tenant_id: int, task_id: int):
        task = self.get(tenant_id, task_id)
        if task.status != PutawayTaskStatus.PENDING:
            raise AppError("INVALID_PUTAWAY_STATE", "Only pending tasks can be started.", 409)
        task.status = PutawayTaskStatus.IN_PROGRESS
        task.started_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(task)
        return task

    def complete(self, tenant_id: int, task_id: int, to_location_id: int | None = None):
        task = self.get(tenant_id, task_id)
        if task.status not in (PutawayTaskStatus.PENDING, PutawayTaskStatus.IN_PROGRESS):
            raise AppError("INVALID_PUTAWAY_STATE", "Only pending or in-progress tasks can be completed.", 409)
        if to_location_id is not None:
            task.to_location_id = to_location_id
        task.status = PutawayTaskStatus.COMPLETED
        task.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(task)
        try:
            workflow = WorkflowService(self.db)
            workflow.log_event(tenant_id, "PUTAWAY_COMPLETED", "putaway_task", task.id, None, {"receipt_id": task.receipt_id})
            if task.receipt_id:
                workflow.cancel_entity_tasks(tenant_id, "purchase_receipt", task.receipt_id)
                from app.repositories.purchasing import PurchasingRepository
                receipt = PurchasingRepository(self.db).get_receipt(tenant_id, task.receipt_id)
                if receipt and receipt.purchase_order_id:
                    workflow.create_task(tenant_id, WorkflowTaskCreate(
                        workflow_type="PURCHASING",
                        entity_type="purchase_order",
                        entity_id=receipt.purchase_order_id,
                        step_key="RECORD_BILL",
                        title=f"Record bill for received PO",
                        description="Putaway complete. Record vendor bill for this purchase order.",
                        assigned_role="PURCHASE_STAFF",
                        priority="NORMAL",
                        action_url=f"/bills/new?purchase_order_id={receipt.purchase_order_id}",
                    ))
            self.db.commit()
        except Exception:
            pass
        return task

    def cancel(self, tenant_id: int, task_id: int):
        task = self.get(tenant_id, task_id)
        if task.status == PutawayTaskStatus.COMPLETED:
            raise AppError("INVALID_PUTAWAY_STATE", "Completed tasks cannot be cancelled.", 409)
        task.status = PutawayTaskStatus.CANCELLED
        self.db.commit()
        self.db.refresh(task)
        return task


class CycleCountService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CycleCountRepository(db)
        self.inventory_repo = InventoryRepository(db)
        self.engine = InventoryEngine(db)

    def list_sessions(self, tenant_id: int):
        return self.repository.list_sessions(tenant_id)

    def get_session(self, tenant_id: int, session_id: int):
        session = self.repository.get_session(tenant_id, session_id)
        if session is None:
            raise AppError("CYCLE_COUNT_SESSION_NOT_FOUND", "Cycle count session not found.", 404)
        return session

    def create_session(self, tenant_id: int, user_id: int, data: dict):
        import uuid
        session_number = f"CC-{uuid.uuid4().hex[:8].upper()}"
        session = self.repository.create_session({
            "tenant_id": tenant_id,
            "warehouse_id": data["warehouse_id"],
            "session_number": session_number,
            "notes": data.get("notes"),
            "created_by": user_id,
        })
        self.db.commit()
        self.db.refresh(session)
        return session

    def add_line(self, tenant_id: int, session_id: int, data: dict):
        session = self.get_session(tenant_id, session_id)
        if session.status not in (StockCountSessionStatus.DRAFT, StockCountSessionStatus.IN_PROGRESS):
            raise AppError("INVALID_SESSION_STATE", "Lines can only be added to draft or in-progress sessions.", 409)
        stock = self.inventory_repo.get_stock(tenant_id, data["product_id"], session.warehouse_id, data["location_id"])
        system_qty = stock.quantity_on_hand if stock else Decimal("0")
        line = self.repository.create_line({
            "tenant_id": tenant_id,
            "session_id": session_id,
            "product_id": data["product_id"],
            "location_id": data["location_id"],
            "system_quantity": system_qty,
        })
        self.db.commit()
        self.db.refresh(line)
        return line

    def update_line(self, tenant_id: int, session_id: int, line_id: int, data: dict):
        session = self.get_session(tenant_id, session_id)
        if session.status not in (StockCountSessionStatus.DRAFT, StockCountSessionStatus.IN_PROGRESS):
            raise AppError("INVALID_SESSION_STATE", "Lines can only be updated in draft or in-progress sessions.", 409)
        lines = self.repository.list_lines(tenant_id, session_id)
        line = next((l for l in lines if l.id == line_id), None)
        if line is None:
            raise AppError("COUNT_LINE_NOT_FOUND", "Count line not found.", 404)
        counted = Decimal(str(data["counted_quantity"]))
        line.counted_quantity = counted
        line.variance = counted - line.system_quantity
        if data.get("notes") is not None:
            line.notes = data["notes"]
        self.db.flush()
        self.db.commit()
        self.db.refresh(line)
        return line

    def list_lines(self, tenant_id: int, session_id: int):
        self.get_session(tenant_id, session_id)
        return self.repository.list_lines(tenant_id, session_id)

    def submit(self, tenant_id: int, session_id: int):
        session = self.get_session(tenant_id, session_id)
        if session.status not in (StockCountSessionStatus.DRAFT, StockCountSessionStatus.IN_PROGRESS):
            raise AppError("INVALID_SESSION_STATE", "Only draft or in-progress sessions can be submitted.", 409)
        session.status = StockCountSessionStatus.SUBMITTED
        session.submitted_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(session)
        return session

    def reconcile(self, tenant_id: int, session_id: int, actor_id: int):
        session = self.get_session(tenant_id, session_id)
        if session.status != StockCountSessionStatus.SUBMITTED:
            raise AppError("INVALID_SESSION_STATE", "Only submitted sessions can be reconciled.", 409)
        lines = self.repository.list_lines(tenant_id, session_id)
        adjustments = []
        for line in lines:
            if line.variance is None or line.variance == Decimal("0"):
                continue
            import uuid
            self.engine.adjust_stock(tenant_id, actor_id, {
                "product_id": line.product_id,
                "warehouse_id": session.warehouse_id,
                "location_id": line.location_id,
                "delta": line.variance,
                "reference_type": ReferenceType.RECONCILIATION,
                "reference_id": session.session_number,
                "note": f"Cycle count adjustment: session {session.session_number}",
                "idempotency_key": f"cc-{session_id}-{line.id}-{uuid.uuid4().hex[:8]}",
            })
            adjustments.append(line.id)
        session.status = StockCountSessionStatus.RECONCILED
        session.reconciled_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(session)
        return session, adjustments


class ExpireBatchesService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.inventory_repo = InventoryRepository(db)

    def run(self, tenant_id: int) -> dict:
        from sqlalchemy import select
        from app.models.inventory import InventoryBatch
        from datetime import date

        today = date.today()
        batches = list(self.db.scalars(
            select(InventoryBatch).where(
                InventoryBatch.tenant_id == tenant_id,
                InventoryBatch.status == InventoryBatchStatus.ACTIVE,
                InventoryBatch.expiry_date <= today,
            )
        ))
        expired_ids = []
        for batch in batches:
            batch.status = InventoryBatchStatus.EXPIRED
            stock = self.inventory_repo.get_stock(tenant_id, batch.product_id, batch.warehouse_id, batch.location_id)
            if stock is not None:
                qty = batch.quantity_on_hand
                stock.quantity_available -= qty
                stock.quantity_expired += qty
            expired_ids.append(batch.id)
        self.db.commit()
        return {"expired_count": len(expired_ids), "batch_ids": expired_ids}
