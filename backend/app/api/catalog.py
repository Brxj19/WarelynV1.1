import csv
from io import StringIO

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles, require_tenant_user
from app.models.auth import UserRole
from app.schemas.master_data import (
    BrandCreate,
    BrandRead,
    BrandUpdate,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    VendorCreate,
    VendorRead,
    VendorUpdate,
)
from app.services.auth import UserContext
from app.services.master_data import CatalogService

router = APIRouter(prefix="/catalog", tags=["catalog"])
writer_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER)
product_reader_roles = (*writer_roles, UserRole.VIEWER, UserRole.SALES_STAFF, UserRole.PURCHASE_STAFF)


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(context: UserContext = Depends(require_tenant_user), db: Session = Depends(get_db)) -> list[CategoryRead]:
    return CatalogService(db).list_categories(context.tenant_id)


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(request: CategoryCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> CategoryRead:
    return CatalogService(db).create_category(context.tenant_id, request.model_dump())


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, request: CategoryUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> CategoryRead:
    return CatalogService(db).update_category(context.tenant_id, category_id, request.model_dump(exclude_unset=True))


@router.get("/brands", response_model=list[BrandRead])
def list_brands(context: UserContext = Depends(require_tenant_user), db: Session = Depends(get_db)) -> list[BrandRead]:
    return CatalogService(db).list_brands(context.tenant_id)


@router.post("/brands", response_model=BrandRead, status_code=status.HTTP_201_CREATED)
def create_brand(request: BrandCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> BrandRead:
    return CatalogService(db).create_brand(context.tenant_id, request.model_dump())


@router.patch("/brands/{brand_id}", response_model=BrandRead)
def update_brand(brand_id: int, request: BrandUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> BrandRead:
    return CatalogService(db).update_brand(context.tenant_id, brand_id, request.model_dump(exclude_unset=True))


@router.get("/vendors", response_model=list[VendorRead])
def list_vendors(context: UserContext = Depends(require_roles(*writer_roles, UserRole.VIEWER, UserRole.PURCHASE_STAFF)), db: Session = Depends(get_db)) -> list[VendorRead]:
    return CatalogService(db).list_vendors(context.tenant_id)


@router.post("/vendors", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
def create_vendor(request: VendorCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> VendorRead:
    return CatalogService(db).create_vendor(context.tenant_id, request.model_dump())


@router.patch("/vendors/{vendor_id}", response_model=VendorRead)
def update_vendor(vendor_id: int, request: VendorUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> VendorRead:
    return CatalogService(db).update_vendor(context.tenant_id, vendor_id, request.model_dump(exclude_unset=True))


@router.get("/customers", response_model=list[CustomerRead])
def list_customers(context: UserContext = Depends(require_roles(*writer_roles, UserRole.VIEWER, UserRole.SALES_STAFF)), db: Session = Depends(get_db)) -> list[CustomerRead]:
    return CatalogService(db).list_customers(context.tenant_id)


@router.post("/customers", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(request: CustomerCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> CustomerRead:
    return CatalogService(db).create_customer(context.tenant_id, request.model_dump())


@router.patch("/customers/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, request: CustomerUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> CustomerRead:
    return CatalogService(db).update_customer(context.tenant_id, customer_id, request.model_dump(exclude_unset=True))


@router.get("/products", response_model=list[ProductRead])
def list_products(search: str | None = None, context: UserContext = Depends(require_roles(*product_reader_roles)), db: Session = Depends(get_db)) -> list[ProductRead]:
    return CatalogService(db).list_products(context.tenant_id, search)


@router.get("/products/export.csv")
def export_products(search: str | None = None, context: UserContext = Depends(require_roles(*product_reader_roles)), db: Session = Depends(get_db)) -> Response:
    products = CatalogService(db).list_products(context.tenant_id, search)
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "name",
            "sku",
            "barcode",
            "description",
            "unit",
            "category_id",
            "brand_id",
            "cost_price",
            "selling_price",
            "reorder_level",
            "track_batch",
            "track_expiry",
            "track_serial",
            "status",
        ],
    )
    writer.writeheader()
    for product in products:
        writer.writerow(
            {
                "name": product.name,
                "sku": product.sku,
                "barcode": product.barcode,
                "description": product.description,
                "unit": product.unit,
                "category_id": product.category_id,
                "brand_id": product.brand_id,
                "cost_price": product.cost_price,
                "selling_price": product.selling_price,
                "reorder_level": product.reorder_level,
                "track_batch": product.track_batch,
                "track_expiry": product.track_expiry,
                "track_serial": product.track_serial,
                "status": product.status.value if hasattr(product.status, "value") else product.status,
            }
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="products.csv"'},
    )


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(request: ProductCreate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> ProductRead:
    return CatalogService(db).create_product(context.tenant_id, request.model_dump())


@router.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, request: ProductUpdate, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> ProductRead:
    return CatalogService(db).update_product(context.tenant_id, product_id, request.model_dump(exclude_unset=True))
