from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.schemas.returns import ReturnInspectionRequest, ReturnProcessRequest, ReturnWorkflowSummary, SalesReturnCreate, SalesReturnRead, SalesReturnUpdate
from app.services.auth import UserContext
from app.services.returns import ReturnsService

router = APIRouter(tags=["sales-returns"])
read_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.SALES_STAFF, UserRole.VIEWER)
writer_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.SALES_STAFF)
qc_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER)


@router.get("/sales-returns", response_model=list[SalesReturnRead])
def list_sales_returns(context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[SalesReturnRead]:
    return ReturnsService(db).list_returns(context.tenant_id)


@router.post("/sales-returns", response_model=SalesReturnRead, status_code=status.HTTP_201_CREATED)
def create_sales_return(request: SalesReturnCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesReturnRead:
    return ReturnsService(db).create_return(context.tenant_id, context.user.id, request.model_dump())


@router.get("/sales-returns/{return_id}", response_model=SalesReturnRead)
def get_sales_return(return_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> SalesReturnRead:
    return ReturnsService(db).get_return(context.tenant_id, return_id)


@router.patch("/sales-returns/{return_id}", response_model=SalesReturnRead)
def update_sales_return(return_id: int, request: SalesReturnUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesReturnRead:
    return ReturnsService(db).update_return(context.tenant_id, return_id, request.model_dump(exclude_unset=True))


@router.post("/sales-returns/{return_id}/submit", response_model=SalesReturnRead)
def submit_sales_return(return_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesReturnRead:
    return ReturnsService(db).submit_return(context.tenant_id, context.user.id, return_id)


@router.post("/sales-returns/{return_id}/cancel", response_model=SalesReturnRead)
def cancel_sales_return(return_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesReturnRead:
    return ReturnsService(db).cancel_return(context.tenant_id, return_id)


@router.post("/sales-returns/{return_id}/inspect", response_model=SalesReturnRead)
def inspect_sales_return(return_id: int, request: ReturnInspectionRequest, context: UserContext = Depends(require_roles(*qc_roles)), db: Session = Depends(get_db)) -> SalesReturnRead:
    return ReturnsService(db).inspect_return(context.tenant_id, context.user.id, return_id, request.model_dump())


@router.post("/sales-returns/{return_id}/process", response_model=ReturnWorkflowSummary)
def process_sales_return(return_id: int, request: ReturnProcessRequest, context: UserContext = Depends(require_roles(*qc_roles)), db: Session = Depends(get_db)) -> ReturnWorkflowSummary:
    return ReturnsService(db).process_return(context.tenant_id, context.user.id, return_id, request.model_dump())
