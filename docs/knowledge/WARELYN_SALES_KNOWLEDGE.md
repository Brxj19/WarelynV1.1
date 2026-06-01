# Warelyn Sales Knowledge

## Sales order lifecycle

A sales order moves through these statuses: DRAFT → CONFIRMED → PARTIALLY_FULFILLED or FULFILLED → CLOSED or CANCELLED.

**DRAFT** — The order has been created but not confirmed. Stock is not yet reserved. The order can be edited or cancelled.

**CONFIRMED** — The order is confirmed. Stock is now reserved for the customer. A PICK_ORDER task is created for INVENTORY_MANAGER. The order cannot be edited.

**PARTIALLY_FULFILLED** — Some items in the order have been fulfilled. Stock for fulfilled items has been deducted.

**FULFILLED** — All items have been fulfilled. Full stock deduction has been made. A CREATE_INVOICE task is created for SALES_STAFF.

**CLOSED** — The order is fully complete including invoice and payment.

**CANCELLED** — The order was cancelled. All stock reservations are released. All open workflow tasks for this order are cancelled.

## Why is my sales order stuck at CONFIRMED?

A confirmed sales order stays at CONFIRMED until the fulfillment is committed. The steps needed: INVENTORY_MANAGER must pick the items, create a package, and then commit the fulfillment. If picking has not been started, check My Tasks for a PICK_ORDER task. If picking is done but the order is still CONFIRMED, check if a package has been created.

## How to pick a sales order

Go to the sales order detail page. Click the Pick button. On the pick page, create a pick task if one does not exist. Select the warehouse locations and quantities to pick. Click Pick Items to confirm. This creates the reservation and marks items as picked.

## How to pack a sales order

After picking, go to the sales order detail page. Click the Package button. Create a package for the picked items. Add the picked items to the package. Click Pack to confirm. The package status becomes PACKED.

## How to fulfill a sales order

After packing, go to the sales order detail page. Click the Fulfill button. Select the packed package. Add fulfillment lines. Click Commit Fulfillment. This deducts the stock, updates the order to FULFILLED or PARTIALLY_FULFILLED, and creates a CREATE_INVOICE workflow task.

## How to create an invoice for a sales order

After fulfillment, go to Invoices, click Create Invoice. Select the sales order. The invoice lines are pre-filled from the order. Set the due date. Click Create and then Send to deliver the invoice to the customer by email.

## How to cancel a sales order

Go to the sales order detail page. Click Cancel. Stock reservations are released. All open workflow tasks are cancelled. The order cannot be un-cancelled.

## What is a sales return?

A sales return is when a customer sends items back. Go to Returns, click Create Return. Select the fulfilled sales order. The form pre-fills with the remaining returnable quantities. Adjust quantities if it is a partial return. Submit the return. A RETURN_QC task is created for INVENTORY_MANAGER.

## Why does the invoice not appear?

Invoices are created by SALES_STAFF after fulfillment. Check if a CREATE_INVOICE task exists in My Tasks. If no task exists, check if the fulfillment was committed on the order. If the fulfillment exists and the task is completed, the invoice may already exist in the Invoices list.

## What is the fulfillment rate?

Fulfillment rate is the percentage of confirmed sales order items that have been fulfilled in the selected time period. A low fulfillment rate indicates picking or packing bottlenecks.

## How does stock reservation work in sales?

When a sales order is confirmed, Warelyn calls the inventory engine to reserve the ordered quantity. Reserved stock is not available for other orders. The reservation is released if the order is cancelled. The reservation is converted to a deduction when the fulfillment is committed.

## Why can I not confirm a sales order?

A sales order cannot be confirmed if there is insufficient available stock for any line item. Check the stock report for the relevant product. Available stock = on hand minus reserved minus blocked. If stock is low, a purchase order may be needed first.

## What does partially fulfilled mean?

A sales order is PARTIALLY_FULFILLED when at least one but not all items have been fulfilled. This happens when the order has multiple lines and only some were included in the committed fulfillment. The remaining items still need picking, packing, and fulfillment.
