from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.auth import UserRole
from app.models.inventory import MovementType, ReferenceType
from app.schemas.reports import (
    AdminDashboard,
    BatchExpiryReportRow,
    BlockedStockReportRow,
    InventorySummaryReport,
    InventoryDashboard,
    LocationStockReportRow,
    LowStockReportRow,
    OperationalDashboard,
    PurchaseDashboard,
    ProductValuationReport,
    ReconciliationReport,
    ReorderSuggestionRow,
    SalesDashboard,
    SerialStatusReportRow,
    StockMovementReportRow,
    WarehouseStockReportRow,
)  # noqa: F401 - DashboardCharts, DashboardInsight used via OperationalDashboard
from app.services.auth import UserContext
from app.services.reports import ReportsService

router = APIRouter(tags=["reports"])
read_roles = (UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER, UserRole.VIEWER)
dashboard_roles = (
    UserRole.TENANT_ADMIN,
    UserRole.INVENTORY_MANAGER,
    UserRole.SALES_STAFF,
    UserRole.PURCHASE_STAFF,
    UserRole.VIEWER,
)


def common_filters(
    warehouse_id: int | None = None,
    location_id: int | None = None,
    product_id: int | None = None,
    category_id: int | None = None,
    brand_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    movement_type: MovementType | None = None,
    reference_type: ReferenceType | None = None,
    expiry_before: date | None = None,
    expiry_within_days: int | None = Query(default=None, ge=1, le=3650),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
) -> dict:
    return {
        "warehouse_id": warehouse_id,
        "location_id": location_id,
        "product_id": product_id,
        "category_id": category_id,
        "brand_id": brand_id,
        "status": status,
        "search": search,
        "date_from": date_from,
        "date_to": date_to,
        "movement_type": movement_type.value if movement_type else None,
        "reference_type": reference_type.value if reference_type else None,
        "expiry_before": expiry_before,
        "expiry_within_days": expiry_within_days,
        "page": page,
        "page_size": page_size,
    }


@router.get("/reports/inventory-summary", response_model=InventorySummaryReport)
def inventory_summary(context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> InventorySummaryReport:
    return ReportsService(db).inventory_summary(context.tenant_id)


@router.get("/reports/warehouse-stock", response_model=list[WarehouseStockReportRow])
def warehouse_stock(filters: dict = Depends(common_filters), context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[WarehouseStockReportRow]:
    return ReportsService(db).warehouse_stock(context.tenant_id, filters)


@router.get("/reports/location-stock", response_model=list[LocationStockReportRow])
def location_stock(filters: dict = Depends(common_filters), context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[LocationStockReportRow]:
    return ReportsService(db).location_stock(context.tenant_id, filters)


@router.get("/reports/stock-movements", response_model=list[StockMovementReportRow])
def stock_movements(filters: dict = Depends(common_filters), context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[StockMovementReportRow]:
    return ReportsService(db).stock_movements(context.tenant_id, filters)


@router.get("/reports/low-stock", response_model=list[LowStockReportRow])
def low_stock(filters: dict = Depends(common_filters), context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[LowStockReportRow]:
    return ReportsService(db).low_stock(context.tenant_id, filters)


@router.get("/reports/reorder-suggestions", response_model=list[ReorderSuggestionRow])
def reorder_suggestions(filters: dict = Depends(common_filters), context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[ReorderSuggestionRow]:
    return ReportsService(db).reorder_suggestions(context.tenant_id, filters)


@router.get("/reports/product-valuation", response_model=ProductValuationReport)
def product_valuation(filters: dict = Depends(common_filters), context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> ProductValuationReport:
    return ReportsService(db).product_valuation(context.tenant_id, filters)


@router.get("/reports/batch-expiry", response_model=list[BatchExpiryReportRow])
def batch_expiry(filters: dict = Depends(common_filters), context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[BatchExpiryReportRow]:
    return ReportsService(db).batch_expiry(context.tenant_id, filters)


@router.get("/reports/serial-status", response_model=list[SerialStatusReportRow])
def serial_status(filters: dict = Depends(common_filters), context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[SerialStatusReportRow]:
    return ReportsService(db).serial_status(context.tenant_id, filters)


@router.get("/reports/blocked-stock", response_model=list[BlockedStockReportRow])
def blocked_stock(filters: dict = Depends(common_filters), context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> list[BlockedStockReportRow]:
    return ReportsService(db).blocked_stock(context.tenant_id, filters)


@router.get("/reports/reconciliation", response_model=ReconciliationReport)
def reconciliation(context: UserContext = Depends(require_roles(*read_roles)), db: Session = Depends(get_db)) -> ReconciliationReport:
    return ReportsService(db).reconciliation(context.tenant_id)


@router.get("/dashboard/operations", response_model=OperationalDashboard)
def operational_dashboard(
    compare_previous: bool = False,
    context: UserContext = Depends(require_roles(*dashboard_roles)),
    db: Session = Depends(get_db),
) -> OperationalDashboard:
    return ReportsService(db).operational_dashboard(context.tenant_id, compare_previous=compare_previous)


@router.get("/dashboard/sales", response_model=SalesDashboard)
def sales_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    context: UserContext = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.SALES_STAFF)),
    db: Session = Depends(get_db),
) -> SalesDashboard:
    return ReportsService(db).sales_dashboard(context.tenant_id, days=days)


@router.get("/dashboard/purchasing", response_model=PurchaseDashboard)
def purchase_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    context: UserContext = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.PURCHASE_STAFF, UserRole.INVENTORY_MANAGER)),
    db: Session = Depends(get_db),
) -> PurchaseDashboard:
    return ReportsService(db).purchase_dashboard(context.tenant_id, days=days)


@router.get("/dashboard/inventory", response_model=InventoryDashboard)
def inventory_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    context: UserContext = Depends(require_roles(UserRole.TENANT_ADMIN, UserRole.INVENTORY_MANAGER)),
    db: Session = Depends(get_db),
) -> InventoryDashboard:
    return ReportsService(db).inventory_dashboard(context.tenant_id, days=days)


@router.get("/dashboard/admin", response_model=AdminDashboard)
def admin_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    context: UserContext = Depends(require_roles(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db),
) -> AdminDashboard:
    return ReportsService(db).admin_dashboard(context.tenant_id, days=days)


@router.get("/reports/{report_key}/export.csv")
def export_report_csv(
    report_key: str,
    filters: dict = Depends(common_filters),
    context: UserContext = Depends(require_roles(*read_roles)),
    db: Session = Depends(get_db),
) -> Response:
    allowed = {
        "inventory-summary",
        "warehouse-stock",
        "location-stock",
        "stock-movements",
        "low-stock",
        "reorder-suggestions",
        "product-valuation",
        "batch-expiry",
        "serial-status",
        "blocked-stock",
        "reconciliation",
    }
    if report_key not in allowed:
        from app.core.exceptions import AppError

        raise AppError("REPORT_NOT_FOUND", "Report export endpoint was not found.", 404)
    csv_content = ReportsService(db).export_csv(context.tenant_id, report_key, filters)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{report_key}.csv"'},
    )
