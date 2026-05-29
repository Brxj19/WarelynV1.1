from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.schemas.master_data import WarehouseCreate, WarehouseLocationCreate, WarehouseLocationRead, WarehouseLocationUpdate, WarehouseRead, WarehouseUpdate
from app.services.auth import UserContext
from app.services.master_data import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["warehouses"])
writer_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER)
reader_roles = (*writer_roles, UserRole.VIEWER, UserRole.PURCHASE_STAFF, UserRole.SALES_STAFF)


@router.get("", response_model=list[WarehouseRead])
def list_warehouses(context: UserContext = Depends(require_roles(*reader_roles)), db: Session = Depends(get_db)) -> list[WarehouseRead]:
    return WarehouseService(db).list_warehouses(context.tenant_id)


@router.post("", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
def create_warehouse(request: WarehouseCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> WarehouseRead:
    return WarehouseService(db).create_warehouse(context.tenant_id, request.model_dump())


@router.patch("/{warehouse_id}", response_model=WarehouseRead)
def update_warehouse(warehouse_id: int, request: WarehouseUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> WarehouseRead:
    return WarehouseService(db).update_warehouse(context.tenant_id, warehouse_id, request.model_dump(exclude_unset=True))


@router.get("/{warehouse_id}/locations", response_model=list[WarehouseLocationRead])
def list_locations(warehouse_id: int, context: UserContext = Depends(require_roles(*reader_roles)), db: Session = Depends(get_db)) -> list[WarehouseLocationRead]:
    return WarehouseService(db).list_locations(context.tenant_id, warehouse_id)


@router.post("/{warehouse_id}/locations", response_model=WarehouseLocationRead, status_code=status.HTTP_201_CREATED)
def create_location(warehouse_id: int, request: WarehouseLocationCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> WarehouseLocationRead:
    return WarehouseService(db).create_location(context.tenant_id, warehouse_id, request.model_dump())


@router.patch("/{warehouse_id}/locations/{location_id}", response_model=WarehouseLocationRead)
def update_location(warehouse_id: int, location_id: int, request: WarehouseLocationUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> WarehouseLocationRead:
    return WarehouseService(db).update_location(context.tenant_id, warehouse_id, location_id, request.model_dump(exclude_unset=True))
