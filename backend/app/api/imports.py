from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.models.imports import ProductImportMode
from app.schemas.imports import ImportJobRead, ImportJobRowRead, ProductImportCancelRequest, ProductImportCommitResponse, ProductImportUploadResponse, ProductImportValidationResponse
from app.services.auth import UserContext
from app.services.imports import ProductImportService

router = APIRouter(prefix="/imports/products", tags=["product-imports"])
writer_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER)
reader_roles = (*writer_roles, UserRole.VIEWER)


@router.get("/template.xlsx")
def download_import_template_xlsx(
    context: UserContext = Depends(require_roles(*writer_roles)),
) -> Response:
    content = ProductImportService.build_template_xlsx()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="products-import-template.xlsx"'},
    )


@router.post("/upload", response_model=ProductImportUploadResponse)
async def upload_product_import(
    file: UploadFile = File(...),
    mode: ProductImportMode = Form(ProductImportMode.create_only),
    create_missing_references: bool = Form(False),
    column_mapping_json: str | None = Form(default=None),
    context: UserContext = Depends(require_roles(*writer_roles)),
    db: Session = Depends(get_db),
) -> ProductImportUploadResponse:
    job = ProductImportService(db).upload(
        context.tenant_id,
        context.user.id,
        file.filename or "products.csv",
        await file.read(),
        mode,
        create_missing_references,
        column_mapping_json=column_mapping_json,
    )
    return {"job": job}


@router.get("/{job_id}", response_model=ImportJobRead)
def get_product_import(job_id: int, context: UserContext = Depends(require_roles(*reader_roles)), db: Session = Depends(get_db)) -> ImportJobRead:
    return ProductImportService(db).get_job(context.tenant_id, job_id)


@router.get("/{job_id}/rows", response_model=list[ImportJobRowRead])
def list_product_import_rows(job_id: int, context: UserContext = Depends(require_roles(*reader_roles)), db: Session = Depends(get_db)) -> list[ImportJobRowRead]:
    return ProductImportService(db).list_rows(context.tenant_id, job_id)


@router.post("/{job_id}/validate", response_model=ProductImportValidationResponse)
def validate_product_import(job_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> ProductImportValidationResponse:
    job, rows = ProductImportService(db).validate(context.tenant_id, job_id)
    return {"job": job, "rows": rows}


@router.post("/{job_id}/commit", response_model=ProductImportCommitResponse)
def commit_product_import(job_id: int, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> ProductImportCommitResponse:
    job, rows = ProductImportService(db).commit(context.tenant_id, job_id)
    return {"job": job, "rows": rows}


@router.post("/{job_id}/cancel", response_model=ImportJobRead)
def cancel_product_import(job_id: int, _: ProductImportCancelRequest | None = None, context: UserContext = Depends(require_roles(*writer_roles)), db: Session = Depends(get_db)) -> ImportJobRead:
    return ProductImportService(db).cancel(context.tenant_id, job_id)
