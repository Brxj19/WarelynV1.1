# Warelyn Frequently Asked Questions

## Q: What needs my attention today?

Check My Tasks for OPEN tasks assigned to your role. Check the dashboard alerts panel for low stock, overdue invoices, or pending approvals. TENANT_ADMIN should check the team task breakdown to see if any role has a backlog.

## Q: Why is an order stuck and not moving forward?

An order gets stuck when the next workflow step has not been completed. For sales orders stuck at CONFIRMED: check if a PICK_ORDER task exists and has been started. For orders stuck after picking: check if a package has been created. For orders stuck after packing: check if the fulfillment has been committed. For purchase orders stuck after submission: check if a PUTAWAY_STOCK task has been started.

## Q: Why are invoices not being created?

Invoices are created by SALES_STAFF after a sales fulfillment is committed. After fulfillment, a CREATE_INVOICE task appears in My Tasks for SALES_STAFF. If SALES_STAFF has not created the invoice, remind them to check their task queue.

## Q: Why are bills not being recorded?

Bills are recorded by PURCHASE_STAFF after putaway is completed. After putaway, a RECORD_BILL task appears in My Tasks for PURCHASE_STAFF. If the bill is not recorded, check if putaway was completed. If putaway is complete, remind PURCHASE_STAFF to check their task queue.

## Q: How do I fix a stock discrepancy?

If physical stock does not match what Warelyn shows: first check the Stock Movement Report to trace recent changes. If the discrepancy is small and explained, use a Stock Adjustment to correct it. If the discrepancy is large or unexplained, run a Cycle Count to physically recount the affected products and reconcile. If the Reconciliation Report shows mismatches, contact TENANT_ADMIN to run the reconciliation process.

## Q: How do I check what stock I have available?

Go to Reports, Inventory Summary for an overview. Go to Reports, Warehouse Stock Report to see stock per warehouse. Available quantity = On Hand minus Reserved minus Blocked. Remember that reserved stock cannot be sold until the order is cancelled or fulfilled.

## Q: How do I process a customer return?

Returns are submitted by SALES_STAFF and inspected by INVENTORY_MANAGER. The SALES_STAFF user creates a return from the sales order detail page. After submission, INVENTORY_MANAGER gets a RETURN_QC task. The manager inspects each item and assigns an outcome: restock, blocked, damaged, scrapped, or rejected. After processing, stock is updated automatically.

## Q: How do I receive stock from a vendor?

Go to Purchases, find the purchase order, and click Receive. Create a new receipt with the actual quantities delivered. Click Commit Receipt. Stock is added to the warehouse. A PUTAWAY_STOCK task is created for INVENTORY_MANAGER to place the stock in its correct location.

## Q: Why is a purchase order waiting for approval?

Your company has a threshold for high-value purchase orders. Orders above this threshold require TENANT_ADMIN approval before they can proceed. An APPROVE_PO task is in the TENANT_ADMIN's My Tasks. Ask your admin to approve it.

## Q: How do I see what changed in my inventory recently?

Go to Reports, Stock Movement Report. Filter by product, warehouse, and date range. This shows every stock change with the reason and the source document that triggered it.

## Q: Which items need to be reordered?

Go to Reports, Reorder Suggestions. This shows products where available stock is at or below the reorder level. Each row shows how urgent the reorder is and links to create a purchase order. PURCHASE_STAFF also gets REORDER_STOCK tasks in their My Tasks queue.

## Q: How do I know if my invoices are overdue?

Go to Documents, Invoices and filter by status SENT with a due date in the past. These are overdue invoices. SALES_STAFF dashboard shows the overdue invoice count and the total overdue value.

## Q: What does CONFIRMED status mean on a sales order?

CONFIRMED means the order is accepted, stock is reserved for the customer, and picking has been requested. The order is in the hands of INVENTORY_MANAGER for picking and packing. You can track progress on the order detail page.

## Q: How do I cancel a sales order?

Go to the sales order detail page. Click Cancel. You can only cancel an order if it has not been fulfilled yet. Cancelling releases all stock reservations and cancels all open workflow tasks for that order.

## Q: How do I add a new warehouse or storage location?

Go to the Warehouses section. Click Create Warehouse. Add the name and details. After creating the warehouse, click on it and add locations (zones, racks, bins) inside the warehouse. TENANT_ADMIN and INVENTORY_MANAGER can create warehouses and locations.

## Q: Why can I not see a report or page?

Your role does not have access to that report or page. Inventory and stock reports are available to TENANT_ADMIN, INVENTORY_MANAGER, and VIEWER. Purchase reports are available to TENANT_ADMIN, PURCHASE_STAFF, and INVENTORY_MANAGER. Sales reports are available to TENANT_ADMIN and SALES_STAFF. Contact your TENANT_ADMIN if you need access.

## Q: How do I change my password?

Go to Settings, My Profile. Click Change Password. Enter your current password and your new password. Click Save. If you forgot your password, click Forgot Password on the login page to receive a reset code by email.

## Q: What is the tenant admin copilot?

The AI Copilot is available to TENANT_ADMIN users at the top right of the app. It can answer operational questions about your tenant's current state: open orders, pending tasks, stock alerts, and workflow bottlenecks. The copilot uses your tenant's current data as context and answers from the Warelyn knowledge base.

## Q: How accurate is the AI assistant?

The AI assistant answers from the Warelyn knowledge base and your tenant's current operational data. For high confidence answers, the assistant cites the source. For low confidence, it says it does not know and suggests checking the relevant report or contacting your admin. Do not rely on AI answers for exact stock numbers — always verify in the actual report.
