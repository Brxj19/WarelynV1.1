# Warelyn Batch Tracking and Serial Number Knowledge

## What is batch tracking?

Batch tracking (also called lot tracking) means grouping units of a product that were produced or received together. Each batch has a batch number and optionally an expiry date. When stock is received for a batch-tracked product, a batch number is recorded. When stock is shipped, the batch it came from is recorded. This enables full traceability from supplier to customer.

## What is serial number tracking?

Serial number tracking means each individual unit of a product has a unique serial number. When a unit is received, its serial number is recorded. When it is sold, the serial number is linked to the sales order. This enables unit-level traceability: you can always look up which customer received serial number X.

## How to set up batch tracking for a product

Edit the product. Under Tracking Type, select Batch Tracked. Save. From now on, purchase receipts for this product require a batch number. The batch number and expiry date (if applicable) are recorded at receipt time.

## How to set up serial tracking for a product

Edit the product. Under Tracking Type, select Serial Tracked. Save. Purchase receipts now require one serial number per unit received. Each serial number is unique per tenant.

## What is an expiry date on a batch?

The expiry date is the date after which the batch is no longer safe or valid to sell. Warelyn monitors batches and warns you when expiry is approaching (within 30 days by default). Expired batches appear in the Batch Expiry Report and cannot be sold in a sales order (they are blocked).

## How to view batches for a product?

Go to the product detail page. Scroll to the Batches section. It shows all batches with their batch numbers, received quantities, remaining quantities, expiry dates, and status.

## How to view serials?

Go to Reports, Serial Status Report. Filter by product. Shows all serial numbers with their current status: AVAILABLE, RESERVED, SOLD, DAMAGED, SCRAPPED, RETURNED.

## What happens to a serial number when a product is sold?

When a sales fulfillment is committed for a serial-tracked product, the serial number is marked as SOLD and linked to the sales order. It cannot be sold again. If returned, it moves to RETURNED status pending QC.

## What happens to expired batches?

Warelyn marks batches as EXPIRED when their expiry date has passed. Expired stock moves to blocked status and cannot be included in sales order reservations. Dispose of expired stock by recording a stock adjustment with reason EXPIRED, or contact TENANT_ADMIN.

## Can I have mixed tracking in one warehouse?

Yes. Some products can be standard-tracked, others batch-tracked, others serial-tracked in the same warehouse. Tracking is per product, not per warehouse.
