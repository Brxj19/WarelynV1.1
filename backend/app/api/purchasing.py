from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.schemas.purchasing import (
    PurchaseOrderCreate,
    PurchaseOrderRead,
    PurchaseOrderUpdate,
    PurchaseReceiptCommitRequest,
    PurchaseReceiptCreate,
    PurchaseReceiptRead,
    PurchaseReceiptUpdate,
    PurchaseWorkflowSummary,
)
from app.services.auth import UserContext
from app.services.purchasing import PurchasingService

router = APIRouter(tags=["purchasing"])
read_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PURCHASE_STAFF, UserRole.VIEWER)
writer_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PURCHASE_STAFF)


@router.get("/purchase-orders", response_model=list[PurchaseOrderRead])
def list_purchase_orders(context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[PurchaseOrderRead]:
    return PurchasingService(db).list_purchase_orders(context.tenant_id)


@router.post("/purchase-orders", response_model=PurchaseOrderRead, status_code=status.HTTP_201_CREATED)
def create_purchase_order(request: PurchaseOrderCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PurchaseOrderRead:
    return PurchasingService(db).create_purchase_order(context.tenant_id, context.user.id, request.model_dump())


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderRead)
def get_purchase_order(po_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> PurchaseOrderRead:
    return PurchasingService(db).get_purchase_order(context.tenant_id, po_id)


@router.patch("/purchase-orders/{po_id}", response_model=PurchaseOrderRead)
def update_purchase_order(po_id: int, request: PurchaseOrderUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PurchaseOrderRead:
    return PurchasingService(db).update_purchase_order(context.tenant_id, po_id, request.model_dump(exclude_unset=True))


@router.post("/purchase-orders/{po_id}/submit", response_model=PurchaseOrderRead)
def submit_purchase_order(po_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PurchaseOrderRead:
    return PurchasingService(db).submit_purchase_order(context.tenant_id, po_id)


@router.post("/purchase-orders/{po_id}/cancel", response_model=PurchaseOrderRead)
def cancel_purchase_order(po_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PurchaseOrderRead:
    return PurchasingService(db).cancel_purchase_order(context.tenant_id, po_id)


@router.post("/purchase-orders/{po_id}/close", response_model=PurchaseOrderRead)
def close_purchase_order(po_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PurchaseOrderRead:
    return PurchasingService(db).close_purchase_order(context.tenant_id, po_id)


@router.post("/purchase-orders/{po_id}/receipts", response_model=PurchaseReceiptRead, status_code=status.HTTP_201_CREATED)
def create_purchase_receipt(po_id: int, request: PurchaseReceiptCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PurchaseReceiptRead:
    return PurchasingService(db).create_receipt(context.tenant_id, context.user.id, po_id, request.model_dump())


@router.get("/purchase-orders/{po_id}/receipts", response_model=list[PurchaseReceiptRead])
def list_purchase_receipts(po_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[PurchaseReceiptRead]:
    return PurchasingService(db).list_receipts_for_order(context.tenant_id, po_id)


@router.get("/purchase-receipts/{receipt_id}", response_model=PurchaseReceiptRead)
def get_purchase_receipt(receipt_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> PurchaseReceiptRead:
    return PurchasingService(db).get_receipt(context.tenant_id, receipt_id)


@router.patch("/purchase-receipts/{receipt_id}", response_model=PurchaseReceiptRead)
def update_purchase_receipt(receipt_id: int, request: PurchaseReceiptUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PurchaseReceiptRead:
    return PurchasingService(db).update_receipt(context.tenant_id, receipt_id, request.model_dump(exclude_unset=True))


@router.post("/purchase-receipts/{receipt_id}/commit", response_model=PurchaseWorkflowSummary)
def commit_purchase_receipt(receipt_id: int, request: PurchaseReceiptCommitRequest, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PurchaseWorkflowSummary:
    return PurchasingService(db).commit_receipt(context.tenant_id, context.user.id, receipt_id, request.model_dump())


@router.post("/purchase-receipts/{receipt_id}/cancel", response_model=PurchaseReceiptRead)
def cancel_purchase_receipt(receipt_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PurchaseReceiptRead:
    return PurchasingService(db).cancel_receipt(context.tenant_id, receipt_id)
