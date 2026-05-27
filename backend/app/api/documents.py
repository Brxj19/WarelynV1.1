from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.schemas.documents import (
    BillCreate,
    BillRead,
    DocumentEmailRequest,
    DocumentStatusResponse,
    DocumentTemplateCreate,
    DocumentTemplateDetailResponse,
    DocumentTemplateDuplicate,
    DocumentTemplateListResponse,
    DocumentTemplatePreviewRequest,
    DocumentTemplatePreviewResponse,
    DocumentTemplateRead,
    DocumentTemplateUpdate,
    InvoiceCreate,
    InvoiceRead,
)
from app.services.auth import UserContext
from app.services.documents import DocumentsService, DocumentTemplateService

router = APIRouter(tags=["documents"])
read_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PURCHASE_STAFF, UserRole.SALES_STAFF, UserRole.VIEWER)
write_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.PURCHASE_STAFF, UserRole.SALES_STAFF)
admin_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER)


@router.get("/invoices", response_model=list[InvoiceRead])
def list_invoices(context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[InvoiceRead]:
    return DocumentsService(db).list_invoices(context.tenant_id)


@router.post("/invoices", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice(request: InvoiceCreate, context: UserContext = Depends(require_roles(*write_roles)), db: Session = Depends(get_db)) -> InvoiceRead:
    return DocumentsService(db).create_invoice(context.tenant_id, context.user.id, request.model_dump(exclude_none=True))


@router.get("/invoices/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> InvoiceRead:
    return DocumentsService(db).get_invoice(context.tenant_id, invoice_id)


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceRead)
def send_invoice(invoice_id: int, request: DocumentEmailRequest, context: UserContext = Depends(require_roles(*write_roles)), db: Session = Depends(get_db)) -> InvoiceRead:
    return DocumentsService(db).send_invoice(context.tenant_id, invoice_id, context.user.id, request.email)


@router.post("/invoices/{invoice_id}/mark-paid", response_model=InvoiceRead)
def mark_invoice_paid(invoice_id: int, context: UserContext = Depends(require_roles(*write_roles)), db: Session = Depends(get_db)) -> InvoiceRead:
    return DocumentsService(db).mark_invoice_paid(context.tenant_id, invoice_id, context.user.id)


@router.post("/invoices/{invoice_id}/void", response_model=InvoiceRead)
def void_invoice(invoice_id: int, context: UserContext = Depends(require_roles(*write_roles)), db: Session = Depends(get_db)) -> InvoiceRead:
    return DocumentsService(db).void_invoice(context.tenant_id, invoice_id, context.user.id)


@router.get("/invoices/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> Response:
    invoice = DocumentsService(db).get_invoice(context.tenant_id, invoice_id)
    result = DocumentsService(db).render_invoice_pdf(context.tenant_id, invoice_id, context.user.id)
    return Response(
        content=result.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"',
            "X-Warelyn-Template-Id": str(result.template_id),
            "X-Warelyn-Template-Key": result.template_key,
            "X-Warelyn-Template-Purpose": result.template_purpose,
        },
    )


@router.get("/bills", response_model=list[BillRead])
def list_bills(context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[BillRead]:
    return DocumentsService(db).list_bills(context.tenant_id)


@router.post("/bills", response_model=BillRead, status_code=status.HTTP_201_CREATED)
def create_bill(request: BillCreate, context: UserContext = Depends(require_roles(*write_roles)), db: Session = Depends(get_db)) -> BillRead:
    return DocumentsService(db).create_bill(context.tenant_id, context.user.id, request.model_dump(exclude_none=True))


@router.get("/bills/{bill_id}", response_model=BillRead)
def get_bill(bill_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> BillRead:
    return DocumentsService(db).get_bill(context.tenant_id, bill_id)


@router.post("/bills/{bill_id}/send", response_model=BillRead)
def send_bill(bill_id: int, request: DocumentEmailRequest, context: UserContext = Depends(require_roles(*write_roles)), db: Session = Depends(get_db)) -> BillRead:
    return DocumentsService(db).send_bill(context.tenant_id, bill_id, context.user.id, request.email)


@router.post("/bills/{bill_id}/mark-paid", response_model=BillRead)
def mark_bill_paid(bill_id: int, context: UserContext = Depends(require_roles(*write_roles)), db: Session = Depends(get_db)) -> BillRead:
    return DocumentsService(db).mark_bill_paid(context.tenant_id, bill_id, context.user.id)


@router.post("/bills/{bill_id}/void", response_model=BillRead)
def void_bill(bill_id: int, context: UserContext = Depends(require_roles(*write_roles)), db: Session = Depends(get_db)) -> BillRead:
    return DocumentsService(db).void_bill(context.tenant_id, bill_id, context.user.id)


@router.get("/bills/{bill_id}/pdf")
def download_bill_pdf(bill_id: int, context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> Response:
    bill = DocumentsService(db).get_bill(context.tenant_id, bill_id)
    result = DocumentsService(db).render_bill_pdf(context.tenant_id, bill_id, context.user.id)
    return Response(
        content=result.pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{bill.bill_number}.pdf"',
            "X-Warelyn-Template-Id": str(result.template_id),
            "X-Warelyn-Template-Key": result.template_key,
            "X-Warelyn-Template-Purpose": result.template_purpose,
        },
    )


@router.get("/document-templates", response_model=list[DocumentTemplateRead])
def list_document_templates(
    channel: str | None = None,
    purpose: str | None = None,
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> list[DocumentTemplateRead]:
    return DocumentTemplateService(db).list_templates(context.tenant_id, channel, purpose)


@router.get("/document-templates/{template_id}", response_model=DocumentTemplateDetailResponse)
def get_document_template(
    template_id: int,
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> DocumentTemplateDetailResponse:
    return DocumentTemplateService(db).get_template(context.tenant_id, template_id)


@router.post("/document-templates", response_model=DocumentTemplateDetailResponse, status_code=status.HTTP_201_CREATED)
def create_document_template(
    request: DocumentTemplateCreate,
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> DocumentTemplateDetailResponse:
    return DocumentTemplateService(db).create_custom_template(
        context.tenant_id, context.user.id, request.model_dump(exclude_unset=True)
    )


@router.patch("/document-templates/{template_id}", response_model=DocumentTemplateDetailResponse)
def update_document_template(
    template_id: int,
    request: DocumentTemplateUpdate,
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> DocumentTemplateDetailResponse:
    return DocumentTemplateService(db).update_template(context.tenant_id, template_id, request.model_dump(exclude_unset=True))


@router.delete("/document-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_template(
    template_id: int,
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> None:
    DocumentTemplateService(db).delete_template(context.tenant_id, template_id)


@router.post("/document-templates/{template_id}/duplicate", response_model=DocumentTemplateDetailResponse, status_code=status.HTTP_201_CREATED)
def duplicate_document_template(
    template_id: int,
    request: DocumentTemplateDuplicate,
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> DocumentTemplateDetailResponse:
    return DocumentTemplateService(db).duplicate_template(
        context.tenant_id, context.user.id, template_id, request.name, request.description
    )


@router.post("/document-templates/{template_id}/preview", response_model=DocumentTemplatePreviewResponse)
def preview_document_template(
    template_id: int,
    request: DocumentTemplatePreviewRequest,
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> DocumentTemplatePreviewResponse:
    return DocumentTemplateService(db).preview_template(context.tenant_id, template_id, request.model_dump(exclude_none=True))


@router.post("/document-templates/{template_id}/preview-pdf")
def preview_template_pdf(
    template_id: int,
    request: DocumentTemplatePreviewRequest,
    context: UserContext = Depends(require_roles(*admin_roles)),
    db: Session = Depends(get_db),
) -> Response:
    pdf_bytes = DocumentsService(db).preview_template_pdf(
        context.tenant_id, template_id, request.variables or {}
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=preview.pdf"},
    )


@router.get("/pdf-template-resolution/{document_type}")
def resolve_pdf_template(
    document_type: str,
    context: UserContext = Depends(require_roles(*read_roles)),
    db: Session = Depends(get_db),
) -> dict:
    """Resolve which PDF template would be used for a given document type.

    Resolution order: user preference -> tenant default -> system default.
    """
    return DocumentsService(db).resolve_pdf_template_for_document(
        context.tenant_id, document_type, context.user.id
    )
