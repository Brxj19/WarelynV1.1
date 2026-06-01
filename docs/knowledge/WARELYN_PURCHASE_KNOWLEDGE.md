# Warelyn Purchase Knowledge

## Purchase order lifecycle

A purchase order moves through: DRAFT → SUBMITTED → PARTIALLY_RECEIVED or RECEIVED → CANCELLED.

**DRAFT** — Order created but not sent to vendor. Can be edited.

**SUBMITTED** — Order sent to vendor. Cannot be edited. If total value is above the approval threshold, a TENANT_ADMIN approval is required first.

**PARTIALLY_RECEIVED** — At least one receipt has been committed but not all ordered quantities have been received.

**RECEIVED** — All items received and receipts committed.

**CANCELLED** — Order cancelled. No stock changes made.

## How to create a purchase order

Go to Purchases, click Create Purchase Order. Select the vendor. Add product lines with quantities and unit prices. Set the expected delivery date. Click Submit to send to vendor.

## How to receive stock from a purchase order

After the vendor delivers goods, go to Purchases, find the order, and click Receive. Create a new receipt. Add the lines of what was actually received (quantities may differ from what was ordered). Click Commit Receipt. This calls the inventory engine to add stock. A PUTAWAY_STOCK task is created for INVENTORY_MANAGER.

## What is putaway?

Putaway is the process of physically placing received stock into the correct warehouse locations. After receiving, INVENTORY_MANAGER goes to the putaway task, confirms the location for each product, and marks the putaway as complete. When putaway is complete, a RECORD_BILL task is created for PURCHASE_STAFF.

## How to record a vendor bill

After putaway, PURCHASE_STAFF receives a RECORD_BILL task. Go to Bills, click Create Bill. Select the purchase order. The bill lines are pre-filled. Enter the invoice number from the vendor. Set the due date. Click Record. The bill is now tracked for payment.

## Why is the stock not increasing after receiving?

Stock only increases when the receipt is committed. A receipt in DRAFT state has not been committed yet. Go to the receipt, check its status, and click Commit if it is ready. If already committed, check the stock report for that product and warehouse to confirm the increase.

## Why is a purchase order waiting for approval?

Purchase orders above a configured value threshold require TENANT_ADMIN approval. An APPROVE_PO task is created in My Tasks for TENANT_ADMIN. The order will not proceed until the admin approves it. Ask your TENANT_ADMIN to check their task queue.

## What is a reorder suggestion?

Warelyn monitors product stock levels against their reorder levels. When available stock drops below the reorder level, a REORDER_STOCK task is created for PURCHASE_STAFF. The reorder suggestions page shows products that need restocking with their current stock, reorder level, and a link to create a purchase order.

## How does average cost pricing work?

When stock is received via a purchase receipt, Warelyn updates the average cost of the product. Average cost = (existing stock value + new receipt value) / (existing stock quantity + received quantity). This is used for product valuation reports.

## What is the difference between ordered and received quantity?

Ordered quantity is what was on the purchase order. Received quantity is what was actually delivered. If a vendor delivers fewer items, you receive the actual quantity. The order shows as PARTIALLY_RECEIVED. You can create another receipt later for the remaining quantity or accept the partial delivery.

## What is lead time?

Lead time is the average number of days between a purchase order being submitted and the receipt being committed. A shorter lead time means the vendor delivers faster. Warelyn calculates this from the gap between PO submit date and receipt commit date.

## Who can create purchase orders?

TENANT_ADMIN, INVENTORY_MANAGER, and PURCHASE_STAFF can create purchase orders. SALES_STAFF and VIEWER cannot.

## Who can receive stock?

TENANT_ADMIN, INVENTORY_MANAGER, and PURCHASE_STAFF can commit purchase receipts. SALES_STAFF and VIEWER cannot.
