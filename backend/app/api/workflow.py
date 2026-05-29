from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.schemas.workflow import WorkflowEventRead, WorkflowTaskComplete, WorkflowTaskRead
from app.services.auth import UserContext
from app.services.workflow import WorkflowService

router = APIRouter(prefix="/workflow", tags=["workflow"])

task_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.SALES_STAFF, UserRole.PURCHASE_STAFF)
admin_roles = (UserRole.TENANT_ADMIN,)


@router.get("/my-tasks/count", response_model=dict)
def get_my_task_count(
    status_filter: str | None = Query("OPEN", alias="status"),
    context: UserContext = Depends(require_roles(*task_roles)),
    db: Session = Depends(get_db),
) -> dict:
    tasks = WorkflowService(db).get_my_tasks(
        context.tenant_id, context.user.id, context.user.role.value, status_filter
    )
    return {"count": len(tasks)}


@router.get("/my-tasks", response_model=list[WorkflowTaskRead])
def get_my_tasks(
    status_filter: str | None = Query(None, alias="status"),
    context: UserContext = Depends(require_roles(*task_roles)),
    db: Session = Depends(get_db),
) -> list[WorkflowTaskRead]:
    service = WorkflowService(db)
    return service.get_my_tasks(context.tenant_id, context.user.id, context.user.role.value, status_filter)


@router.get("/tasks/{task_id}", response_model=WorkflowTaskRead)
def get_task(
    task_id: int,
    context: UserContext = Depends(require_roles(*task_roles)),
    db: Session = Depends(get_db),
) -> WorkflowTaskRead:
    service = WorkflowService(db)
    task = service.get_task(context.tenant_id, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/start", response_model=WorkflowTaskRead)
def start_task(
    task_id: int,
    context: UserContext = Depends(require_roles(*task_roles)),
    db: Session = Depends(get_db),
) -> WorkflowTaskRead:
    service = WorkflowService(db)
    task = service.get_task(context.tenant_id, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    is_admin = context.user.role == UserRole.TENANT_ADMIN
    is_role_match = task.assigned_role == context.user.role.value
    is_direct = task.assigned_to_user_id == context.user.id
    if not (is_admin or is_role_match or is_direct):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to start this task")
    if task.status != "OPEN":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Task is already {task.status}")
    started = service.start_task(context.tenant_id, task_id, context.user.id)
    return started


@router.post("/tasks/{task_id}/complete", response_model=WorkflowTaskRead)
def complete_task(
    task_id: int,
    body: WorkflowTaskComplete,
    context: UserContext = Depends(require_roles(*task_roles)),
    db: Session = Depends(get_db),
) -> WorkflowTaskRead:
    service = WorkflowService(db)
    task = service.get_task(context.tenant_id, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    is_admin = context.user.role == UserRole.TENANT_ADMIN
    is_role_match = task.assigned_role == context.user.role.value
    is_direct = task.assigned_to_user_id == context.user.id
    if not (is_admin or is_role_match or is_direct):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to complete this task")
    if task.status not in ("OPEN", "IN_PROGRESS"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Task is already {task.status}")
    completed = service.complete_task(context.tenant_id, task_id, context.user.id)
    return completed


@router.get("/events", response_model=list[WorkflowEventRead])
def list_events(
    entity_type: str | None = Query(None),
    entity_id: int | None = Query(None),
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> list[WorkflowEventRead]:
    service = WorkflowService(db)
    return service.list_events(context.tenant_id, entity_type, entity_id)
