from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.models.documents import Bill, Invoice
from app.models.master_data import Customer, Product, Vendor
from app.services.auth import UserContext

router = APIRouter(tags=["search"])
search_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.VIEWER)


@router.get("/search")
def global_search(
    q: str = Query(..., min_length=1, max_length=200),
    types: str | None = Query(default=None),
    context: UserContext = Depends(require_roles(*search_roles)),
    db: Session = Depends(get_db),
) -> dict:
    tenant_id = context.tenant_id
    term = f"%{q.strip()}%"
    limit = 10

    # Determine which entity types to search
    allowed_types = {"product", "customer", "vendor", "invoice", "bill"}
    if types:
        requested = {t.strip().lower() for t in types.split(",")}
        search_types = requested & allowed_types
    else:
        search_types = allowed_types

    results: dict = {}

    if "product" in search_types:
        rows = (
            db.query(Product)
            .filter(
                Product.tenant_id == tenant_id,
                or_(Product.name.ilike(term), Product.sku.ilike(term)),
            )
            .limit(limit)
            .all()
        )
        results["products"] = [
            {"id": r.id, "name": r.name, "sku": r.sku, "status": r.status.value}
            for r in rows
        ]

    if "customer" in search_types:
        rows = (
            db.query(Customer)
            .filter(
                Customer.tenant_id == tenant_id,
                or_(Customer.name.ilike(term), Customer.email.ilike(term)),
            )
            .limit(limit)
            .all()
        )
        results["customers"] = [
            {"id": r.id, "name": r.name, "email": r.email}
            for r in rows
        ]

    if "vendor" in search_types:
        rows = (
            db.query(Vendor)
            .filter(
                Vendor.tenant_id == tenant_id,
                or_(Vendor.name.ilike(term), Vendor.email.ilike(term)),
            )
            .limit(limit)
            .all()
        )
        results["vendors"] = [
            {"id": r.id, "name": r.name, "email": r.email}
            for r in rows
        ]

    if "invoice" in search_types:
        rows = (
            db.query(Invoice)
            .filter(
                Invoice.tenant_id == tenant_id,
                Invoice.invoice_number.ilike(term),
            )
            .limit(limit)
            .all()
        )
        results["invoices"] = [
            {"id": r.id, "invoice_number": r.invoice_number, "status": r.status.value, "total_amount": float(r.total_amount)}
            for r in rows
        ]

    if "bill" in search_types:
        rows = (
            db.query(Bill)
            .filter(
                Bill.tenant_id == tenant_id,
                Bill.bill_number.ilike(term),
            )
            .limit(limit)
            .all()
        )
        results["bills"] = [
            {"id": r.id, "bill_number": r.bill_number, "status": r.status.value, "total_amount": float(r.total_amount)}
            for r in rows
        ]

    return results
