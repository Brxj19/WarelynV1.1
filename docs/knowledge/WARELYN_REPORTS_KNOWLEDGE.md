# Warelyn Reports Knowledge

## Available reports

Warelyn has the following reports. All are read-only.

**Inventory Summary** — Total products, total on-hand quantity, total available quantity, total reserved quantity, total blocked quantity. Use this for a quick health check of your overall stock position.

**Warehouse Stock Report** — Stock levels by product and warehouse. Shows on hand, reserved, available, and blocked per product per warehouse. Use this to see how stock is distributed across warehouses.

**Location Stock Report** — Stock broken down by individual warehouse location. Useful when you need to know exactly which bin has which product.

**Stock Movement Report** — History of all stock changes over a date range. Shows movement type (STOCK_IN, STOCK_OUT, TRANSFER, ADJUSTMENT, RETURN_RESTOCK, etc.), quantity, and the business event that caused the change. Use this to trace why stock changed.

**Product Valuation Report** — The total value of your inventory using average cost pricing. Shows value per product and total portfolio value. Use this for financial reporting.

**Low Stock Report** — Products whose available quantity is at or below their reorder level. Use this to decide what needs to be purchased. Clicking a row links to the product's detail page.

**Batch Expiry Report** — Batches that are expiring soon or already expired. Grouped by product and warehouse. Use this to prioritise selling expiring stock or disposing of expired stock.

**Blocked Stock Report** — All stock that is blocked from sale: damaged, quality hold, expired, return-blocked. Shows the block reason and quantity per product and warehouse.

**Serial Status Report** — Status of individual serial numbers: sold, available, reserved, damaged, scrapped. Use this for warranty tracking and serial-level traceability.

**Reconciliation Report** — Differences between the stock ledger and the warehouse stock projection. A clean reconciliation shows zero mismatches. Mismatches indicate data integrity issues that need TENANT_ADMIN attention.

**Reorder Suggestions** — Products that need to be purchased, ranked by urgency score. Each row shows the product, current stock, reorder level, and a link to create a purchase order.

## Who can access reports?

TENANT_ADMIN, INVENTORY_MANAGER, and VIEWER can access all inventory and stock reports. SALES_STAFF cannot access warehouse-level stock reports. PURCHASE_STAFF can access purchase and vendor reports.

## How to use the stock movement report to trace a stock discrepancy

1. Go to Reports, Stock Movement Report.
2. Filter by product and date range.
3. Look for unexpected movements: large deductions, unexplained adjustments.
4. The reference_type column shows what caused each movement: PURCHASE_RECEIPT, SALES_FULFILLMENT, STOCK_ADJUSTMENT, RETURN_RESTOCK, etc.
5. Click the reference to navigate to the source document.

## What does the reconciliation report show?

The reconciliation report compares two numbers for each product and warehouse: the running total from the stock ledger (the sum of all ledger entries) and the current projection value in the warehouse_stock table. These should always match. If they differ, the projection is out of sync with the ledger, which means reported stock levels may be incorrect.

## How to fix a reconciliation mismatch

Reconciliation mismatches should be reported to TENANT_ADMIN. The admin can run the reconciliation process which recalculates the projection from the ledger. This is a safe operation that brings the projection back into sync with the immutable ledger. No stock is invented or deleted.

## What does the operational dashboard show?

The dashboard shows role-specific operational metrics:
- TENANT_ADMIN: open sales orders, open purchase orders, team task health, stock alerts
- INVENTORY_MANAGER: low stock count, blocked stock count, expiring batches, pick and putaway queue
- SALES_STAFF: orders in progress, overdue invoices, returns pending QC
- PURCHASE_STAFF: orders awaiting receipt, bills to record, reorder items

## How to export reports?

Most reports have an Export button that downloads a CSV or Excel file. Product catalog export is available from the Products list. Stock reports export from their respective report pages.
