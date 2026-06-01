# Warelyn Product Catalog Knowledge

## What is a product in Warelyn?

A product is a purchasable and sellable item tracked in inventory. Products have: name, SKU (stock keeping unit), category, brand, cost price, selling price, unit of measure, and tracking settings (standard, batch, serial).

## Product tracking types

**Standard** — Tracked by total quantity only. No batch or serial granularity.

**Batch tracked** — Stock is grouped into batches (also called lots). Each batch has a batch number and optional expiry date. Used for products like food, pharmaceuticals, or chemicals where traceability is required.

**Serial tracked** — Each individual unit has a unique serial number. Used for electronics, machinery, or high-value items where unit-level traceability is needed.

## How to create a product

Go to Catalog, Products, click Create Product. Fill in: name (required), SKU (must be unique), category, brand, cost price, selling price, unit of measure, reorder level, and tracking type. Click Save. The product is now available for purchase orders and sales orders.

## How to import products from CSV

Go to Catalog, Products, click Import. Download the sample CSV template. Fill it in with your product data. Upload the file. Review the import preview showing which rows will be created or updated. Click Confirm Import. Products with existing SKUs will be updated; new SKUs will be created.

## What is a SKU?

SKU stands for Stock Keeping Unit. It is a unique identifier for a product. No two products in the same tenant can have the same SKU. SKUs are used when scanning barcodes, in CSV imports, and in reports.

## What is the reorder level?

The reorder level is the minimum available stock quantity at which Warelyn should alert you to reorder. When available stock drops below this level, a REORDER_STOCK task is created for PURCHASE_STAFF and the product appears in the Low Stock Report and Reorder Suggestions.

## What is cost price vs selling price?

Cost price is what you pay to the vendor to buy the product. Selling price is what you charge the customer. The product valuation report uses cost price to calculate inventory value. Invoices use selling price unless overridden on the sales order line.

## What are categories and brands?

Categories group products by type (e.g. Electronics, Clothing, Food). Brands identify the manufacturer. Both are optional but improve filtering and reporting. Go to Catalog, Categories or Catalog, Brands to manage them.

## How to manage vendors (suppliers)?

Vendors are the companies you buy from. Go to Catalog, Vendors. Create a vendor with name, contact, and address. When creating a purchase order, you select a vendor. Reports can show spend per vendor.

## How to manage customers?

Customers are the companies or individuals you sell to. Go to Catalog, Customers. Create a customer with name, contact, and address. When creating a sales order, you select a customer.

## What is a unit of measure?

Unit of measure defines how a product is counted: pieces, kilograms, litres, boxes, etc. Set it on the product. It appears on order lines, receipts, and documents. All quantities for a product use the same unit of measure.
