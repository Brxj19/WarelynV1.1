# Warelyn Troubleshooting Guide

## Order is stuck at CONFIRMED and nothing is happening

The most common reason: no one has started the pick task. When a sales order is confirmed, a PICK_ORDER task is automatically created for INVENTORY_MANAGER. Go to My Tasks as INVENTORY_MANAGER and look for the task. If the task exists, click Start and then go to the sales order to begin picking. If no task exists, the order may have been confirmed before the workflow engine was activated — ask TENANT_ADMIN to check the order and manually trigger the picking process.

## Stock went down but I did not ship anything

Check the Stock Movement Report for that product. Filter by the last 7 days. Look for STOCK_OUT, SALES_DEDUCT, or ADJUSTMENT entries with a negative delta. The reference column shows what caused the change: a sales fulfillment, a manual adjustment, or a transfer. If you see an unexpected ADJUSTMENT, check who made it in the Audit Log.

## I confirmed a purchase receipt but the stock did not increase

A committed purchase receipt increases stock immediately. If stock did not increase, check: (1) the receipt status — it must be COMMITTED, not DRAFT. (2) Check the stock report for the exact product and warehouse selected on the receipt. (3) Run the Reconciliation Report to check if there is a projection mismatch.

## A return was submitted but no QC task appeared

The RETURN_QC task is only created for INVENTORY_MANAGER. Log in as INVENTORY_MANAGER and check My Tasks. The task should be there. If it is not, the return may have been submitted before the workflow engine was set up. TENANT_ADMIN can check the workflow_tasks table directly.

## An invoice was sent but the customer says they did not receive it

Go to Documents, Invoices, find the invoice, and check its status. If the status is SENT, the system attempted delivery. Check the email settings: go to Settings, Company, and verify that SMTP is configured and the from email is correct. If the email delivery mode is set to LOG, emails are only written to the server log and not actually sent. Change the mode to SMTP for live delivery.

## I cannot confirm a sales order — it says insufficient stock

Available stock is lower than the ordered quantity. Check the Warehouse Stock Report for that product. If stock is low, create a purchase order to restock. If stock shows as available but the order still will not confirm, check if there are other confirmed sales orders reserving the same product — their reservations reduce available stock.

## The reconciliation report shows mismatches

Mismatches between the ledger and projection happen when stock changes occurred outside the normal workflow, or when transactions were partially completed. Go to Reports, Reconciliation and note the products with mismatches. Ask TENANT_ADMIN to run the reconciliation process to bring the projection back in sync with the ledger. No stock is created or deleted — only the projection is corrected.

## A product shows negative available stock

Negative available stock should not occur in normal operation. Causes: a fulfillment was committed when stock was zero, a manual adjustment was applied incorrectly, or there is a reconciliation error. Investigate using the Stock Movement Report. To fix: either add stock via a purchase order and receipt, or do a stock adjustment with the correct reason, then run reconciliation.

## I cannot see a task that should be assigned to my role

Tasks are filtered by role. If you are PURCHASE_STAFF, you see RECORD_BILL and REORDER_STOCK tasks. You will never see PICK_ORDER or RETURN_QC tasks — those are for INVENTORY_MANAGER. Check the correct role or ask TENANT_ADMIN to view all tasks across all roles.

## My password reset code is not arriving

Check your spam folder. The code expires in 15 minutes — if you request a new one, the old one is invalidated. Make sure your email address is correct on your profile. If SMTP is not configured, the email will not be sent at all — contact your TENANT_ADMIN to verify email settings.

## A cycle count session shows wrong stock accuracy

Stock accuracy in a cycle count is calculated as: (rows with zero variance / total rows) × 100. If the session was created before the latest purchase receipts or sales fulfillments, the system_quantity used for comparison may be stale. This is a known limitation — always submit and reconcile cycle counts promptly before major stock movements.

## Workflow tasks are stuck in OPEN and no one is working them

This usually means the assigned role has a backlog or did not see the notification. TENANT_ADMIN can see all open tasks by going to My Tasks — they see every role's queue. The dashboard shows a task count per role. If tasks are piling up, investigate why that role is not completing them and reassign or escalate as needed.
