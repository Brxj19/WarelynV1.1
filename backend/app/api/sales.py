from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.schemas.sales import (
    SalesFulfillmentCommitRequest,
    SalesFulfillmentCreate,
    SalesFulfillmentRead,
    SalesFulfillmentUpdate,
    SalesOrderConfirmRequest,
    SalesOrderCreate,
    SalesOrderRead,
    SalesOrderUpdate,
    SalesWorkflowSummary,
)
from app.services.auth import UserContext
from app.services.sales import SalesService

router = APIRouter(tags=["sales"])
read_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.SALES_STAFF, UserRole.VIEWER)
writer_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.SALES_STAFF)


@router.get("/sales-orders", response_model=list[SalesOrderRead])
def list_sales_orders(context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[SalesOrderRead]:
    return SalesService(db).list_sales_orders(context.tenant_id)


@router.post("/sales-orders", response_model=SalesOrderRead, status_code=status.HTTP_201_CREATED)
def create_sales_order(request: SalesOrderCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesOrderRead:
    return SalesService(db).create_sales_order(context.tenant_id, context.user.id, request.model_dump())


@router.get("/sales-orders/{order_id}", response_model=SalesOrderRead)
def get_sales_order(order_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> SalesOrderRead:
    return SalesService(db).get_sales_order(context.tenant_id, order_id)


@router.patch("/sales-orders/{order_id}", response_model=SalesOrderRead)
def update_sales_order(order_id: int, request: SalesOrderUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesOrderRead:
    return SalesService(db).update_sales_order(context.tenant_id, order_id, request.model_dump(exclude_unset=True))


@router.post("/sales-orders/{order_id}/confirm", response_model=SalesWorkflowSummary)
def confirm_sales_order(order_id: int, request: SalesOrderConfirmRequest, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesWorkflowSummary:
    return SalesService(db).confirm_sales_order(context.tenant_id, context.user.id, order_id, request.model_dump())


@router.post("/sales-orders/{order_id}/cancel", response_model=SalesOrderRead)
def cancel_sales_order(order_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesOrderRead:
    return SalesService(db).cancel_sales_order(context.tenant_id, context.user.id, order_id)


@router.post("/sales-orders/{order_id}/close", response_model=SalesOrderRead)
def close_sales_order(order_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesOrderRead:
    return SalesService(db).close_sales_order(context.tenant_id, context.user.id, order_id)


@router.post("/sales-orders/{order_id}/fulfillments", response_model=SalesFulfillmentRead, status_code=status.HTTP_201_CREATED)
def create_sales_fulfillment(order_id: int, request: SalesFulfillmentCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesFulfillmentRead:
    return SalesService(db).create_fulfillment(context.tenant_id, context.user.id, order_id, request.model_dump())


@router.get("/sales-orders/{order_id}/fulfillments", response_model=list[SalesFulfillmentRead])
def list_sales_fulfillments(order_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[SalesFulfillmentRead]:
    return SalesService(db).list_fulfillments_for_order(context.tenant_id, order_id)


@router.get("/sales-fulfillments", response_model=list[SalesFulfillmentRead])
def list_all_fulfillments(context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[SalesFulfillmentRead]:
    return SalesService(db).list_all_fulfillments(context.tenant_id)


@router.get("/sales-fulfillments/{fulfillment_id}", response_model=SalesFulfillmentRead)
def get_sales_fulfillment(fulfillment_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> SalesFulfillmentRead:
    return SalesService(db).get_fulfillment(context.tenant_id, fulfillment_id)


@router.patch("/sales-fulfillments/{fulfillment_id}", response_model=SalesFulfillmentRead)
def update_sales_fulfillment(fulfillment_id: int, request: SalesFulfillmentUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesFulfillmentRead:
    return SalesService(db).update_fulfillment(context.tenant_id, fulfillment_id, request.model_dump(exclude_unset=True))


@router.post("/sales-fulfillments/{fulfillment_id}/commit", response_model=SalesWorkflowSummary)
def commit_sales_fulfillment(fulfillment_id: int, request: SalesFulfillmentCommitRequest, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesWorkflowSummary:
    return SalesService(db).commit_fulfillment(context.tenant_id, context.user.id, fulfillment_id, request.model_dump())


@router.post("/sales-fulfillments/{fulfillment_id}/cancel", response_model=SalesFulfillmentRead)
def cancel_sales_fulfillment(fulfillment_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> SalesFulfillmentRead:
    return SalesService(db).cancel_fulfillment(context.tenant_id, fulfillment_id)
