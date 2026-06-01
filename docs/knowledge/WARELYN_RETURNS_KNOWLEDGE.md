# Warelyn Returns Knowledge

## What is a sales return?

A sales return is when a customer sends back products that were previously fulfilled on a sales order. Returns move through: DRAFT → SUBMITTED → INSPECTION_PENDING → PROCESSED → CANCELLED.

**DRAFT** — Return created but not yet submitted. Can be edited.

**SUBMITTED** — Return submitted. A RETURN_QC task is created for INVENTORY_MANAGER. The customer has sent back the items.

**INSPECTION_PENDING** — INVENTORY_MANAGER has started the QC inspection. The items are being evaluated.

**PROCESSED** — QC inspection complete. Stock has been updated based on the QC decisions.

**CANCELLED** — Return cancelled. No stock changes made.

## How to create a sales return

Go to Returns, click Create Return. Select the sales order. The form shows the items that can still be returned with their returnable quantities (fulfilled minus already returned). Adjust the quantities if needed. Add a reason. Click Create Return.

## How to submit a sales return

After creating the return, review the lines and click Submit. This changes status to SUBMITTED and creates a RETURN_QC task for INVENTORY_MANAGER.

## Who can inspect a return?

Only INVENTORY_MANAGER and TENANT_ADMIN can inspect and process returns. SALES_STAFF cannot perform QC. If SALES_STAFF submits a return, INVENTORY_MANAGER will see it in their task queue.

## What are the QC inspection outcomes?

For each returned item, INVENTORY_MANAGER chooses one of five outcomes:

**ACCEPTED_RESTOCK** — Item is in good condition. Stock goes back into available sellable inventory.

**ACCEPTED_BLOCKED** — Item is usable but needs review. Stock goes to blocked stock, visible in the blocked stock report.

**DAMAGED** — Item is damaged. Stock goes to blocked damaged stock. Cannot be sold without further action.

**SCRAPPED** — Item is beyond use. Stock is recorded as scrapped. No increase in sellable or blocked stock.

**REJECTED** — Return rejected. No stock movement. Item is not accepted back.

## How to inspect and process a return

INVENTORY_MANAGER clicks Inspect from the returns list or from the RETURN_QC task. On the inspect page, set the QC outcome for each item. Enter accepted and rejected quantities (must equal returned quantity). Click Inspect and Process. The system processes the return and updates stock accordingly.

## What happens to stock after a return?

After processing, stock changes based on QC decisions:
- ACCEPTED_RESTOCK increases available stock in the specified warehouse location.
- ACCEPTED_BLOCKED / DAMAGED / SCRAPPED creates a blocked stock record. No change to available stock.
- REJECTED makes no stock changes.

## Why is my return showing as INSPECTION_PENDING but nothing is happening?

The RETURN_QC task in My Tasks needs to be picked up by INVENTORY_MANAGER. If no INVENTORY_MANAGER has started the task, remind them to check their task queue. Once they start and complete the inspection, the status moves to PROCESSED.

## Can I create a return for an order that has already been partially returned?

Yes. The return form shows the remaining returnable quantity, which is the fulfilled quantity minus quantities already returned in previous returns. You can only return up to this remaining quantity.

## What is the return rate?

Return rate is the percentage of fulfilled orders that had returns in the selected time period. A high return rate may indicate product quality issues or incorrect order fulfillment. Check the sales return report for details.

## Can returns be partially inspected?

Currently, all items in a return must be assigned a QC outcome before the return can be processed. Partial processing (where some items are processed and others are not) is not yet supported.
