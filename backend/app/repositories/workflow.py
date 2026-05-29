from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.workflow import WorkflowEvent, WorkflowTask


class WorkflowRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task(self, tenant_id: int, data: dict) -> WorkflowTask:
        task = WorkflowTask(tenant_id=tenant_id, **data)
        self.db.add(task)
        self.db.flush()
        return task

    def get_all_tasks(self, tenant_id: int, status: str | None = None) -> list[WorkflowTask]:
        stmt = select(WorkflowTask).where(WorkflowTask.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(WorkflowTask.status == status)
        return list(self.db.scalars(stmt.order_by(WorkflowTask.created_at.desc())))

    def get_tasks_for_role(self, tenant_id: int, role: str, status: str | None = None) -> list[WorkflowTask]:
        stmt = select(WorkflowTask).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.assigned_role == role,
        )
        if status:
            stmt = stmt.where(WorkflowTask.status == status)
        return list(self.db.scalars(stmt.order_by(WorkflowTask.created_at.desc())))

    def get_tasks_for_user(self, tenant_id: int, user_id: int, status: str | None = None) -> list[WorkflowTask]:
        stmt = select(WorkflowTask).where(
            WorkflowTask.tenant_id == tenant_id,
            WorkflowTask.assigned_to_user_id == user_id,
        )
        if status:
            stmt = stmt.where(WorkflowTask.status == status)
        return list(self.db.scalars(stmt.order_by(WorkflowTask.created_at.desc())))

    def get_task(self, tenant_id: int, task_id: int) -> WorkflowTask | None:
        return self.db.scalar(
            select(WorkflowTask).where(
                WorkflowTask.tenant_id == tenant_id,
                WorkflowTask.id == task_id,
            )
        )

    def start_task(self, tenant_id: int, task_id: int, user_id: int) -> WorkflowTask | None:
        task = self.get_task(tenant_id, task_id)
        if not task or task.status != "OPEN":
            return task
        task.status = "IN_PROGRESS"
        task.assigned_to_user_id = user_id
        self.db.flush()
        return task

    def complete_task(self, tenant_id: int, task_id: int, user_id: int) -> WorkflowTask | None:
        task = self.get_task(tenant_id, task_id)
        if not task:
            return None
        task.status = "COMPLETED"
        task.completed_by = user_id
        task.completed_at = datetime.now(timezone.utc)
        self.db.flush()
        return task

    def cancel_tasks_for_entity(self, tenant_id: int, entity_type: str, entity_id: int) -> None:
        tasks = list(self.db.scalars(
            select(WorkflowTask).where(
                WorkflowTask.tenant_id == tenant_id,
                WorkflowTask.entity_type == entity_type,
                WorkflowTask.entity_id == entity_id,
                WorkflowTask.status.in_(["OPEN", "IN_PROGRESS"]),
            )
        ))
        for task in tasks:
            task.status = "CANCELLED"
        self.db.flush()

    def complete_tasks_for_entity_step(
        self, tenant_id: int, entity_type: str, entity_id: int, step_key: str, user_id: int
    ) -> None:
        tasks = list(
            self.db.scalars(
                select(WorkflowTask).where(
                    WorkflowTask.tenant_id == tenant_id,
                    WorkflowTask.entity_type == entity_type,
                    WorkflowTask.entity_id == entity_id,
                    WorkflowTask.step_key == step_key,
                    WorkflowTask.status.in_(["OPEN", "IN_PROGRESS"]),
                )
            )
        )
        now = datetime.now(timezone.utc)
        for task in tasks:
            task.status = "COMPLETED"
            task.completed_by = user_id
            task.completed_at = now
        self.db.flush()

    def has_open_task(self, tenant_id: int, entity_type: str, entity_id: int, step_key: str) -> bool:
        return self.db.scalar(
            select(WorkflowTask.id).where(
                WorkflowTask.tenant_id == tenant_id,
                WorkflowTask.entity_type == entity_type,
                WorkflowTask.entity_id == entity_id,
                WorkflowTask.step_key == step_key,
                WorkflowTask.status.in_(["OPEN", "IN_PROGRESS"]),
            ).limit(1)
        ) is not None

    def log_event(self, tenant_id: int, event_type: str, entity_type: str, entity_id: int, actor_user_id: int | None, payload: dict | None) -> WorkflowEvent:
        event = WorkflowEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            payload_json=payload,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def list_events(self, tenant_id: int, entity_type: str | None = None, entity_id: int | None = None, limit: int = 100) -> list[WorkflowEvent]:
        stmt = select(WorkflowEvent).where(WorkflowEvent.tenant_id == tenant_id)
        if entity_type:
            stmt = stmt.where(WorkflowEvent.entity_type == entity_type)
        if entity_id:
            stmt = stmt.where(WorkflowEvent.entity_id == entity_id)
        return list(self.db.scalars(stmt.order_by(WorkflowEvent.created_at.desc()).limit(limit)))
