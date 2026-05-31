from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.models.operations import PutawayTaskStatus
from app.schemas.operations import PutawayTaskCreate, PutawayTaskRead, PutawayTaskUpdate
from app.services.auth import UserContext
from app.services.operations import PutawayTaskService

router = APIRouter(prefix="/putaway-tasks", tags=["putaway-tasks"])
roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER)
read_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PURCHASE_STAFF)


@router.get("", response_model=list[PutawayTaskRead])
def list_putaway_tasks(
    status: PutawayTaskStatus | None = Query(default=None),
    context: UserContext = Depends(require_roles(*read_roles)),
    db: Session = Depends(get_db),
):
    return PutawayTaskService(db).list(context.tenant_id, status)


@router.get("/{task_id}", response_model=PutawayTaskRead)
def get_putaway_task(task_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)):
    return PutawayTaskService(db).get(context.tenant_id, task_id)


@router.post("", response_model=PutawayTaskRead, status_code=201)
def create_putaway_task(body: PutawayTaskCreate, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return PutawayTaskService(db).create(context.tenant_id, body.model_dump())


@router.post("/{task_id}/start", response_model=PutawayTaskRead)
def start_putaway_task(task_id: int, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return PutawayTaskService(db).start(context.tenant_id, task_id)


@router.post("/{task_id}/complete", response_model=PutawayTaskRead)
def complete_putaway_task(task_id: int, body: PutawayTaskUpdate | None = None, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    to_loc = body.to_location_id if body else None
    return PutawayTaskService(db).complete(context.tenant_id, context.user.id, task_id, to_loc)


@router.post("/{task_id}/cancel", response_model=PutawayTaskRead)
def cancel_putaway_task(task_id: int, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return PutawayTaskService(db).cancel(context.tenant_id, task_id)
