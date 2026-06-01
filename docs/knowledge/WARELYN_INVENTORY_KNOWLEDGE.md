# Warelyn Inventory Knowledge

## What is stock in Warelyn?

Stock in Warelyn is tracked per product, per warehouse, per location. Every stock change is recorded in the stock ledger as an immutable entry. The current stock level is always computed from the ledger history.

## Stock quantity types

**On Hand** — The total physical quantity in the warehouse.

**Reserved** — Quantity reserved for confirmed sales orders. This stock cannot be sold to another customer.

**Available** — On hand minus reserved minus blocked. This is what can actually be sold. Available = On Hand - Reserved - Blocked.

**Blocked** — Stock that is physically present but not available for sale. Includes damaged, expired, quality hold, and return-blocked stock.

## Stock states

- **ON_HAND** — Standard physical stock in warehouse.
- **RESERVED** — Held for a confirmed sales order.
- **QC_HOLD** — Under quality inspection.
- **DAMAGED** — Damaged stock, cannot be sold.
- **EXPIRED** — Past expiry date, cannot be sold.
- **QUARANTINE** — Isolated for compliance or safety.
- **SCRAPPED** — Written off, no stock recovery.
- **RETURNED** — Received back from customer, pending QC.

## What is a stock ledger entry?

Every stock movement creates a stock ledger entry. Ledger entries are immutable and cannot be deleted. They record: what product, which warehouse, which location, what quantity changed, what type of movement, and what caused the change (purchase receipt, sales fulfillment, return, adjustment, etc.). The ledger is the source of truth for all stock history.

## How to adjust stock

If physical stock differs from what Warelyn shows, use a stock adjustment. Go to Inventory, click Stock Adjustments, and record the adjustment. A positive delta adds stock. A negative delta removes stock. All adjustments are logged with a reason code.

## What is a cycle count?

A cycle count is a scheduled verification of physical stock against what Warelyn shows. You select a warehouse, create a count session, add the products to count, physically count them, record the counted quantities, and submit. The system shows the variance (difference between what Warelyn expected and what you found). On reconciliation, the stock is adjusted to match the physical count.

## How to do a cycle count

1. Go to Cycle Counts, click New Session.
2. Select the warehouse.
3. Add product lines.
4. Go to the warehouse and physically count each item.
5. Record the counted quantity for each line.
6. Submit the session.
7. Review the variances.
8. Click Reconcile to apply adjustments.

## Why is my stock accuracy low?

Low stock accuracy means cycle counts are finding significant differences between system stock and physical stock. Common causes: stock moved without recording it in Warelyn, purchase receipts or sales orders committed incorrectly, returns processed with wrong quantities, or damaged stock not recorded.

## What is a reconciliation mismatch?

A reconciliation mismatch is when the stock ledger shows a different quantity than what the warehouse_stock projection table shows. This can happen after database errors or incomplete transactions. Go to Reports, Reconciliation to see mismatches. Contact your TENANT_ADMIN to run a reconciliation to correct the projection.

## What is blocked stock?

Blocked stock is stock that cannot be sold. It is physically in the warehouse but is excluded from available quantity. Sources of blocked stock: damaged returns, scrapped items, quality hold, expiry-blocked batches. View blocked stock in Reports, Blocked Stock. To unblock stock, INVENTORY_MANAGER or TENANT_ADMIN must process a stock disposition decision.

## What is low stock?

A product is low stock when its available quantity drops below its reorder level. Warelyn detects this automatically and creates a REORDER_STOCK task for PURCHASE_STAFF. View low stock items in Reports, Low Stock.

## How to set a reorder level

Go to the product detail page. Edit the product. Set the Reorder Level field. Save. Warelyn will create a reorder task when stock falls below this level.

## What is an expiring batch?

Products tracked by batch and expiry date show as expiring soon when the batch expiry date is within the configured warning period (default 30 days). View expiring batches in Reports, Batch Expiry. Expiring stock should be sold before the expiry date or disposed of and recorded as expired stock.

## How does stock transfer work?

A stock transfer moves stock from one warehouse location to another within the same tenant. Go to Inventory, Stock Transfers. Select the source location, destination location, product, and quantity. Commit the transfer. The ledger records a TRANSFER_OUT from the source and a TRANSFER_IN at the destination.

## Why does the stock report show negative available stock?

Negative available stock should not normally occur. It may happen if stock was deducted outside the normal workflow, a bulk adjustment was applied incorrectly, or there is a reconciliation error. Check the stock movement report for that product to trace what caused the negative state. Contact TENANT_ADMIN to investigate.
