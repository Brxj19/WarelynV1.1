from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.inventory import InventoryBatchStatus, InventorySerialStatus, MovementType, ReferenceType


class InventorySummaryReport(BaseModel):
    total_products: int
    active_products: int
    total_skus_with_stock: int
    total_on_hand_quantity: Decimal
    total_available_quantity: Decimal
    total_reserved_quantity: Decimal
    total_stock_value_cost: Decimal
    low_stock_count: int
    out_of_stock_count: int
    expiring_soon_batch_count: int
    expired_batch_count: int
    damaged_blocked_qc_count: int
    reconciliation_mismatch_count: int
    currency_code: str = "USD"


class WarehouseStockReportRow(BaseModel):
    warehouse_id: int
    warehouse_name: str
    product_id: int
    product_name: str
    sku: str
    on_hand: Decimal
    reserved: Decimal
    available: Decimal
    cost_price: Decimal
    stock_value: Decimal
    reorder_level: int | None = None
    stock_status: str


class LocationStockReportRow(WarehouseStockReportRow):
    location_id: int
    location_code: str
    location_name: str
    location_type: str


class StockMovementReportRow(BaseModel):
    ledger_id: int
    movement_type: MovementType
    reference_type: ReferenceType
    reference_id: str | None = None
    product_id: int
    product_name: str
    sku: str
    warehouse_id: int
    warehouse_name: str
    location_id: int
    location_name: str
    batch_id: int | None = None
    serial_id: int | None = None
    quantity_delta: Decimal
    reserved_delta: Decimal
    available_delta: Decimal
    created_by: int
    created_at: datetime
    note: str | None = None


class LowStockReportRow(BaseModel):
    product_id: int
    product_name: str
    sku: str
    warehouse_id: int
    warehouse_name: str
    available: Decimal
    reserved: Decimal
    on_hand: Decimal
    reorder_level: int
    suggested_reorder_quantity: Decimal
    status: str


class ReorderSuggestionRow(BaseModel):
    product_id: int
    product_name: str
    sku: str
    default_vendor_id: int | None = None
    default_vendor_name: str | None = None
    warehouse_id: int
    warehouse_name: str
    available: Decimal
    reorder_level: int
    suggested_quantity: Decimal
    reason: str


class ProductValuationReport(BaseModel):
    total_stock_value: Decimal
    total_units: Decimal
    currency_code: str = "USD"
    rows: list[WarehouseStockReportRow]


class BatchExpiryReportRow(BaseModel):
    batch_id: int
    batch_number: str
    product_id: int
    product_name: str
    sku: str
    warehouse_id: int
    warehouse_name: str
    location_id: int
    location_name: str
    expiry_date: date | None = None
    quantity_on_hand: Decimal
    quantity_available: Decimal
    quantity_reserved: Decimal
    status: InventoryBatchStatus
    days_to_expiry: int | None = None
    expiry_status: str


class SerialStatusReportRow(BaseModel):
    serial_id: int
    serial_number: str
    product_id: int
    product_name: str
    sku: str
    warehouse_id: int
    warehouse_name: str
    location_id: int
    location_name: str
    batch_id: int | None = None
    status: InventorySerialStatus
    warranty_until: date | None = None
    expires_on: date | None = None
    created_at: datetime


class BlockedStockReportRow(BaseModel):
    source_type: str
    product_id: int
    product_name: str
    sku: str
    warehouse_id: int
    warehouse_name: str
    location_id: int
    location_name: str
    batch_id: int | None = None
    serial_id: int | None = None
    quantity: Decimal
    status: str
    reason: str | None = None
    created_at: datetime


class ReconciliationReportMismatch(BaseModel):
    product_id: int
    product_name: str | None = None
    sku: str | None = None
    warehouse_id: int
    warehouse_name: str | None = None
    location_id: int
    location_name: str | None = None
    expected_on_hand: Decimal
    actual_on_hand: Decimal
    expected_reserved: Decimal
    actual_reserved: Decimal
    expected_available: Decimal
    actual_available: Decimal


class ReconciliationReport(BaseModel):
    tenant_id: int
    mismatch_count: int
    mismatches: list[ReconciliationReportMismatch]


class PendingAction(BaseModel):
    label: str
    count: int
    tone: str = "neutral"


class StockMovementByDay(BaseModel):
    date: str
    inbound: int
    outbound: int


class OrderStatusCounts(BaseModel):
    purchase_orders: dict[str, int] = {}
    sales_orders: dict[str, int] = {}


class LowStockByCategory(BaseModel):
    category: str
    count: int


class DashboardCharts(BaseModel):
    stock_movements_by_day: list[StockMovementByDay] = []
    order_status_summary: OrderStatusCounts = OrderStatusCounts()
    low_stock_by_category: list[LowStockByCategory] = []


class DashboardInsight(BaseModel):
    severity: str  # "info" | "warning" | "danger"
    title: str
    message: str
    action_url: str | None = None


class RevenueByDayPoint(BaseModel):
    date: str
    revenue: Decimal


class SpendByDayPoint(BaseModel):
    date: str
    spend: Decimal


class RevenueTopProduct(BaseModel):
    product_name: str
    sku: str
    revenue: Decimal
    units_sold: Decimal


class RevenueTopCustomer(BaseModel):
    customer_name: str
    revenue: Decimal
    order_count: int


class SpendTopVendor(BaseModel):
    vendor_name: str
    spend: Decimal
    order_count: int


class SpendTopProduct(BaseModel):
    product_name: str
    sku: str
    spend: Decimal
    units_received: Decimal


class WarehouseUtilizationRow(BaseModel):
    warehouse_name: str
    used_locations: int
    total_locations: int
    pct: Decimal


class MovementVelocityRow(BaseModel):
    product_name: str
    sku: str
    movement_count: int
    net_delta: Decimal


class InboundOutboundDay(BaseModel):
    date: str
    inbound: Decimal
    outbound: Decimal


class RevenueSpendDay(BaseModel):
    date: str
    revenue: Decimal
    spend: Decimal


class SalesDashboard(BaseModel):
    total_revenue_mtd: Decimal
    total_revenue_prev_month: Decimal
    orders_by_status: dict[str, int]
    revenue_by_day: list[RevenueByDayPoint]
    top_products_by_revenue: list[RevenueTopProduct]
    top_customers_by_revenue: list[RevenueTopCustomer]
    fulfillment_rate: Decimal
    return_rate: Decimal
    avg_order_value: Decimal
    overdue_invoices_count: int
    overdue_invoices_value: Decimal


class PurchaseDashboard(BaseModel):
    total_spend_mtd: Decimal
    total_spend_prev_month: Decimal
    orders_by_status: dict[str, int]
    spend_by_day: list[SpendByDayPoint]
    top_vendors_by_spend: list[SpendTopVendor]
    top_products_by_spend: list[SpendTopProduct]
    pending_receipts_count: int
    pending_bills_count: int
    overdue_bills_count: int
    overdue_bills_value: Decimal


class InventoryDashboard(BaseModel):
    stock_health_score: int
    total_sku_count: int
    low_stock_count: int
    blocked_stock_count: int
    expiring_soon_count: int
    dead_stock_count: int
    warehouse_utilization: list[WarehouseUtilizationRow]
    movement_velocity: list[MovementVelocityRow]
    inbound_outbound_by_day: list[InboundOutboundDay]


class AdminDashboard(BaseModel):
    revenue_mtd: Decimal
    spend_mtd: Decimal
    gross_margin_mtd: Decimal
    open_tasks_by_role: dict[str, int]
    order_health: dict[str, int]
    stock_health: dict[str, int]
    activity_by_day: list[RevenueSpendDay]


class OperationalDashboard(BaseModel):
    kpis: InventorySummaryReport
    previous_kpis: InventorySummaryReport | None = None
    pending_purchase_orders: int
    pending_purchase_receipts: int
    open_sales_orders: int
    active_pick_tasks: int
    pending_returns_qc: int
    blocked_stock_count: int
    expiring_soon_count: int
    reconciliation_mismatch_count: int
    recent_stock_movements: list[StockMovementReportRow]
    low_stock_items: list[LowStockReportRow]
    expiring_batches: list[BatchExpiryReportRow]
    pending_actions: list[PendingAction]
    charts: DashboardCharts = DashboardCharts()
    insights: list[DashboardInsight] = []
