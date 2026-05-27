from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.schemas.fulfillment import PackageCreate, PackagePackRequest, PackageRead, PackageUpdate, PickTaskCreate, PickTaskPickRequest, PickTaskRead, PickTaskUpdate
from app.services.auth import UserContext
from app.services.fulfillment import FulfillmentService

router = APIRouter(tags=["fulfillment"])
read_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.SALES_STAFF, UserRole.VIEWER)
writer_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.SALES_STAFF)


@router.get("/pick-tasks", response_model=list[PickTaskRead])
def list_pick_tasks(context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[PickTaskRead]:
    return FulfillmentService(db).list_pick_tasks(context.tenant_id)


@router.post("/sales-orders/{order_id}/pick-tasks", response_model=PickTaskRead, status_code=status.HTTP_201_CREATED)
def create_pick_task(order_id: int, request: PickTaskCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PickTaskRead:
    return FulfillmentService(db).create_pick_task(context.tenant_id, context.user.id, order_id, request.model_dump())


@router.get("/sales-orders/{order_id}/pick-tasks", response_model=list[PickTaskRead])
def list_pick_tasks_for_order(order_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[PickTaskRead]:
    return FulfillmentService(db).list_pick_tasks_for_order(context.tenant_id, order_id)


@router.get("/pick-tasks/{pick_task_id}", response_model=PickTaskRead)
def get_pick_task(pick_task_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> PickTaskRead:
    return FulfillmentService(db).get_pick_task(context.tenant_id, pick_task_id)


@router.patch("/pick-tasks/{pick_task_id}", response_model=PickTaskRead)
def update_pick_task(pick_task_id: int, request: PickTaskUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PickTaskRead:
    return FulfillmentService(db).update_pick_task(context.tenant_id, pick_task_id, request.model_dump(exclude_unset=True))


@router.post("/pick-tasks/{pick_task_id}/start", response_model=PickTaskRead)
def start_pick_task(pick_task_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PickTaskRead:
    return FulfillmentService(db).start_pick_task(context.tenant_id, pick_task_id)


@router.post("/pick-tasks/{pick_task_id}/pick", response_model=PickTaskRead)
def pick_pick_task(pick_task_id: int, request: PickTaskPickRequest, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PickTaskRead:
    return FulfillmentService(db).pick_pick_task(context.tenant_id, pick_task_id, request.model_dump())


@router.post("/pick-tasks/{pick_task_id}/cancel", response_model=PickTaskRead)
def cancel_pick_task(pick_task_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PickTaskRead:
    return FulfillmentService(db).cancel_pick_task(context.tenant_id, pick_task_id)


@router.post("/sales-orders/{order_id}/packages", response_model=PackageRead, status_code=status.HTTP_201_CREATED)
def create_package(order_id: int, request: PackageCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PackageRead:
    return FulfillmentService(db).create_package(context.tenant_id, order_id, request.model_dump())


@router.get("/sales-orders/{order_id}/packages", response_model=list[PackageRead])
def list_packages_for_order(order_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[PackageRead]:
    return FulfillmentService(db).list_packages_for_order(context.tenant_id, order_id)


@router.get("/packages/{package_id}", response_model=PackageRead)
def get_package(package_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> PackageRead:
    return FulfillmentService(db).get_package(context.tenant_id, package_id)


@router.patch("/packages/{package_id}", response_model=PackageRead)
def update_package(package_id: int, request: PackageUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PackageRead:
    return FulfillmentService(db).update_package(context.tenant_id, package_id, request.model_dump(exclude_unset=True))


@router.post("/packages/{package_id}/pack", response_model=PackageRead)
def pack_package(package_id: int, request: PackagePackRequest, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PackageRead:
    return FulfillmentService(db).pack_package(context.tenant_id, context.user.id, package_id, request.model_dump())


@router.post("/packages/{package_id}/cancel", response_model=PackageRead)
def cancel_package(package_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> PackageRead:
    return FulfillmentService(db).cancel_package(context.tenant_id, package_id)
