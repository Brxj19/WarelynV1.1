# Warelyn Reorder Rules and Suggestions Knowledge

## What is a reorder rule?

A reorder rule defines the automatic trigger conditions for restocking a product. When available stock falls below the reorder level, Warelyn creates a REORDER_STOCK task for PURCHASE_STAFF and shows the product in the Reorder Suggestions report.

## How to set a reorder level

Edit the product. Set the Reorder Level field to the minimum acceptable available quantity. Example: if you always want at least 50 units available, set reorder level to 50. When available stock drops below 50, a reorder task is created.

## What is the Reorder Suggestions page?

Go to Reports, Reorder Suggestions. This page shows all products that are currently below their reorder level, sorted by urgency. Each row shows: product name, SKU, current available quantity, reorder level, and a suggested order quantity. The Create PO button on each row opens a new purchase order pre-filled with the product.

## How is the suggested order quantity calculated?

Suggested order quantity = (reorder level × 2) minus current available. This gives you enough stock to reach double the reorder level. You can override the quantity when creating the purchase order.

## How to prevent duplicate reorder tasks?

Warelyn checks if an open REORDER_STOCK task already exists for a product before creating a new one. If an open task exists, no duplicate is created. Once the task is completed (purchase order created), the system will create a new task the next time stock drops below the reorder level.

## What happens if I ignore a reorder task?

The task stays in OPEN status indefinitely. If stock continues to decrease, more sales orders may fail to confirm due to insufficient available stock. If a product reaches zero available, all pending sales orders for that product cannot be fulfilled. TENANT_ADMIN can see all overdue REORDER_STOCK tasks in My Tasks.

## What is a reorder rule vs manual reorder?

A reorder rule is an automatic trigger. A manual reorder is when PURCHASE_STAFF decides to buy more stock without waiting for the automatic trigger. Both result in a purchase order. The reorder rule automates the decision point; manual reorders are discretionary.
