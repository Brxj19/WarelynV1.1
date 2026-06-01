# Warelyn Workflow Knowledge

## What is a workflow task?

A workflow task is a unit of work assigned to a specific role in Warelyn. When a business event happens (an order confirmed, a receipt committed, a return submitted), the system automatically creates a task for the role responsible for the next step. Tasks appear in My Tasks under the relevant role's account.

## Workflow task statuses

**OPEN** — The task has been created and is waiting for action. The assigned role has not started working on it yet. OPEN tasks appear in the My Tasks page under the Open tab.

**IN_PROGRESS** — A user has clicked Start on the task, claiming it. The work is actively being done. IN_PROGRESS tasks appear in the In Progress tab.

**COMPLETED** — The task is done. The work step it represents has been completed by the backend (picking done, bill recorded, etc.). COMPLETED tasks appear in the Completed tab.

**CANCELLED** — The parent entity was cancelled (e.g. a sales order was cancelled), so all open tasks for that order are cancelled. Cancelled tasks are removed from the active queue.

## All workflow task types and what creates them

**PICK_ORDER** — Created when a sales order is confirmed. Assigned to INVENTORY_MANAGER. Means: go to the warehouse and pick the items for this order. Action URL: the sales order page.

**PUTAWAY_STOCK** — Created when a purchase receipt is committed. Assigned to INVENTORY_MANAGER. Means: stock has arrived and needs to be placed in warehouse locations. Action URL: the purchase receipt page.

**RECORD_BILL** — Created when putaway is completed. Assigned to PURCHASE_STAFF. Means: record the vendor bill for the received goods. Action URL: create bill form with PO pre-filled.

**CREATE_INVOICE** — Created when a fulfillment is committed. Assigned to SALES_STAFF. Means: create and send the invoice to the customer. Action URL: create invoice form with SO pre-filled.

**RETURN_QC** — Created when a sales return is submitted. Assigned to INVENTORY_MANAGER. Means: inspect the returned items and decide: accept for restock, accept to blocked stock, damaged, scrapped, or rejected. Action URL: the return inspect page.

**APPROVE_PO** — Created when a high-value purchase order is submitted (above the approval threshold). Assigned to TENANT_ADMIN. Means: review and approve the purchase order before it proceeds.

**REORDER_STOCK** — Created when a product falls below its reorder level. Assigned to PURCHASE_STAFF. Means: create a new purchase order for this product.

## Task priority levels

**HIGH** — Urgent. Approval needed, stock critically low, or overdue. Shown with a red badge.
**NORMAL** — Standard operational task. Shown with a blue badge.
**LOW** — Non-urgent monitoring task. Shown with a grey badge.

## What to do if a task is stuck in OPEN

If a task stays in OPEN and no one has acted on it, it usually means one of: the assigned role has not logged in, the action URL is broken, or the upstream step was not completed correctly. Check My Tasks and click Start, then complete the action at the linked URL.

## What to do if a task is missing from My Tasks

Tasks only appear for the role they are assigned to. SALES_STAFF will not see PICK_ORDER tasks. INVENTORY_MANAGER will not see RECORD_BILL tasks. If you expect a task but do not see it, log in as the correct role or ask your TENANT_ADMIN to check.

## TENANT_ADMIN task view

TENANT_ADMIN sees all tasks across all roles in My Tasks. The dashboard shows a breakdown by role: how many tasks are open for INVENTORY_MANAGER, SALES_STAFF, and PURCHASE_STAFF. Clicking a role count navigates to My Tasks filtered to that role.

## Sales order workflow task sequence

1. Sales order confirmed → PICK_ORDER task created for INVENTORY_MANAGER
2. Pick completed → PICK_ORDER task auto-completes
3. Items packed → package created
4. Fulfillment committed → CREATE_INVOICE task created for SALES_STAFF
5. Invoice sent → CREATE_INVOICE task auto-completes

## Purchase order workflow task sequence

1. High-value PO submitted → APPROVE_PO task created for TENANT_ADMIN
2. PO approved or standard PO committed → purchase receipt created
3. Receipt committed → PUTAWAY_STOCK task created for INVENTORY_MANAGER
4. Putaway complete → PUTAWAY_STOCK auto-completes, RECORD_BILL created for PURCHASE_STAFF
5. Bill recorded → RECORD_BILL auto-completes

## Return workflow task sequence

1. Return submitted by SALES_STAFF → RETURN_QC task created for INVENTORY_MANAGER
2. INVENTORY_MANAGER inspects and processes → RETURN_QC auto-completes
3. SALES_STAFF and TENANT_ADMIN notified of QC outcome

## Who can complete which tasks

- INVENTORY_MANAGER can complete PICK_ORDER, PUTAWAY_STOCK, RETURN_QC
- SALES_STAFF can complete CREATE_INVOICE
- PURCHASE_STAFF can complete RECORD_BILL, REORDER_STOCK
- TENANT_ADMIN can complete APPROVE_PO and any task in their tenant
- VIEWER cannot complete any tasks
