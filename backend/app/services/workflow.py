from sqlalchemy.orm import Session

from app.models.workflow import WorkflowTask
from app.repositories.workflow import WorkflowRepository
from app.schemas.workflow import WorkflowTaskCreate


class WorkflowService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = WorkflowRepository(db)

    def create_task(self, tenant_id: int, data: WorkflowTaskCreate, created_by: int | None = None) -> WorkflowTask | None:
        if self.repository.has_open_task(tenant_id, data.entity_type, data.entity_id, data.step_key):
            return None
        values = data.model_dump(exclude_none=True)
        values["created_by"] = created_by
        return self.repository.create_task(tenant_id, values)

    def complete_task(self, tenant_id: int, task_id: int, user_id: int) -> WorkflowTask | None:
        task = self.repository.complete_task(tenant_id, task_id, user_id)
        if task:
            self.repository.log_event(
                tenant_id=tenant_id,
                event_type="task.completed",
                entity_type=task.entity_type,
                entity_id=task.entity_id,
                actor_user_id=user_id,
                payload={"task_id": task.id, "step_key": task.step_key},
            )
        return task

    def cancel_entity_tasks(self, tenant_id: int, entity_type: str, entity_id: int) -> None:
        self.repository.cancel_tasks_for_entity(tenant_id, entity_type, entity_id)

    def get_my_tasks(self, tenant_id: int, user_id: int, user_role: str, status_filter: str | None = None) -> list[WorkflowTask]:
        role_tasks = self.repository.get_tasks_for_role(tenant_id, user_role, status_filter)
        user_tasks = self.repository.get_tasks_for_user(tenant_id, user_id, status_filter)
        seen_ids: set[int] = set()
        merged: list[WorkflowTask] = []
        for task in role_tasks + user_tasks:
            if task.id not in seen_ids:
                seen_ids.add(task.id)
                merged.append(task)
        merged.sort(key=lambda t: t.created_at, reverse=True)
        return merged

    def get_task(self, tenant_id: int, task_id: int) -> WorkflowTask | None:
        return self.repository.get_task(tenant_id, task_id)

    def log_event(self, tenant_id: int, event_type: str, entity_type: str, entity_id: int, actor_user_id: int | None = None, payload: dict | None = None) -> None:
        self.repository.log_event(tenant_id, event_type, entity_type, entity_id, actor_user_id, payload)

    def list_events(self, tenant_id: int, entity_type: str | None = None, entity_id: int | None = None) -> list:
        return self.repository.list_events(tenant_id, entity_type, entity_id)
