# Warelyn Documents Knowledge

## What are documents in Warelyn?

Documents in Warelyn are formal business records: invoices sent to customers and bills received from vendors. Both are linked to their source orders and can be sent by email as PDF attachments.

## Invoice lifecycle

DRAFT → SENT → PAID → CANCELLED (or VOID)

**DRAFT** — Invoice created but not sent. Can be edited.
**SENT** — Invoice emailed to the customer. Cannot be edited.
**PAID** — Payment received. Invoice closed.
**VOID** — Invoice cancelled. Used when an invoice was created in error.

## How to create an invoice

After a sales fulfillment is committed, a CREATE_INVOICE workflow task appears for SALES_STAFF. Go to Documents, Invoices, click Create Invoice. Select the sales order. Lines are pre-filled from the fulfillment. Set the due date. Click Create. To send it to the customer, click Send — this emails the PDF to the customer's email address.

## Bill lifecycle

DRAFT → RECORDED → PAID → CANCELLED

**DRAFT** — Bill created but not yet confirmed.
**RECORDED** — Bill confirmed and recorded in the system. Payment is now due on the due date.
**PAID** — Payment sent to vendor. Bill closed.

## How to record a vendor bill

After putaway is completed, a RECORD_BILL workflow task appears for PURCHASE_STAFF. Go to Documents, Bills, click Create Bill. Select the purchase order. Lines are pre-filled. Enter the vendor's invoice number. Set the due date. Click Record. The bill is now tracked.

## How does the currency snapshot work?

When an invoice or bill is created, the tenant's current currency is snapshotted onto the document. This snapshot never changes even if you later change the tenant currency setting. Historical documents always show the currency they were created in.

## What is the document number format?

Invoices use the format INV-YYYYMMDD-XXXX. Bills use BLL-YYYYMMDD-XXXX. The numbers are auto-generated and cannot be changed.

## How to customise the invoice PDF?

Go to Settings, PDF Templates, select Invoice PDF. Edit the template using Jinja2 variables. Preview the result. Save. New invoices will use the updated template. Existing sent invoices are not affected.

## How to send an invoice by email?

Open the invoice. Click Send Invoice. Enter the recipient email (pre-filled from customer record). Optionally add a message. Click Send. The system emails the PDF using your SMTP settings. The invoice status changes to SENT.

## What happens when an invoice is voided?

A voided invoice is marked VOID and is no longer treated as an outstanding payment. Voiding does not reverse the fulfillment or the stock deduction — it only cancels the document. If the order needs to be reversed, the fulfillment and return processes must be used separately.

## Can I edit an invoice after sending?

No. Once an invoice is SENT, it cannot be edited. If the invoice has an error, void it and create a new one. Always verify the lines before clicking Send.
