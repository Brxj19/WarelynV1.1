from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.schemas.operations import (
    ExpireBatchesResponse,
    StockCountLineCreate,
    StockCountLineRead,
    StockCountLineUpdate,
    StockCountSessionCreate,
    StockCountSessionRead,
)
from app.services.auth import UserContext
from app.services.operations import CycleCountService, ExpireBatchesService

router = APIRouter(prefix="/cycle-counts", tags=["cycle-counts"])
roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER)


@router.get("", response_model=list[StockCountSessionRead])
def list_sessions(context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return CycleCountService(db).list_sessions(context.tenant_id)


@router.get("/{session_id}", response_model=StockCountSessionRead)
def get_session(session_id: int, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return CycleCountService(db).get_session(context.tenant_id, session_id)


@router.post("", response_model=StockCountSessionRead, status_code=201)
def create_session(body: StockCountSessionCreate, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return CycleCountService(db).create_session(context.tenant_id, context.user.id, body.model_dump())


@router.get("/{session_id}/lines", response_model=list[StockCountLineRead])
def list_lines(session_id: int, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return CycleCountService(db).list_lines(context.tenant_id, session_id)


@router.post("/{session_id}/lines", response_model=StockCountLineRead, status_code=201)
def add_line(session_id: int, body: StockCountLineCreate, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return CycleCountService(db).add_line(context.tenant_id, session_id, body.model_dump())


@router.patch("/{session_id}/lines/{line_id}", response_model=StockCountLineRead)
def update_line(session_id: int, line_id: int, body: StockCountLineUpdate, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return CycleCountService(db).update_line(context.tenant_id, session_id, line_id, body.model_dump(exclude_unset=True))


@router.post("/{session_id}/submit", response_model=StockCountSessionRead)
def submit_session(session_id: int, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return CycleCountService(db).submit(context.tenant_id, session_id)


@router.post("/{session_id}/reconcile", response_model=StockCountSessionRead)
def reconcile_session(session_id: int, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    session, _ = CycleCountService(db).reconcile(context.tenant_id, session_id, context.user.id)
    return session


@router.post("/{session_id}/cancel", response_model=StockCountSessionRead)
def cancel_session(session_id: int, context: UserContext = Depends(require_roles(*roles)), db: Session = Depends(get_db)):
    return CycleCountService(db).cancel_session(context.tenant_id, session_id)


@router.post("/expire-batches", response_model=ExpireBatchesResponse)
def trigger_expire_batches(context: UserContext = Depends(require_roles(UserRole.TENANT_ADMIN)), db: Session = Depends(get_db)):
    return ExpireBatchesService(db).run(context.tenant_id)
