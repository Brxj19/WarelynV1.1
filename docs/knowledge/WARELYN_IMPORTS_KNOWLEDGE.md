# Warelyn Data Import Knowledge

## What can be imported?

Warelyn supports CSV import for products. You can create new products and update existing ones in bulk by uploading a formatted CSV file.

## How to import products

Go to Catalog, Products. Click Import Products. Download the sample CSV template — this shows the required and optional columns with example values. Fill in your data. Save the CSV. Upload it on the import page. Review the preview table showing which rows will be created and which will be updated. Resolve any validation errors shown. Click Confirm Import.

## What columns are required in the product import CSV?

Required: name, sku. Optional: category, brand, cost_price, selling_price, unit_of_measure, reorder_level, tracking_type (STANDARD, BATCH, or SERIAL), description.

## What happens to existing products on import?

If a product with the same SKU already exists, it is updated with the new values from the CSV. If the SKU does not exist, a new product is created. Existing products not in the CSV are not affected.

## How many products can be imported at once?

The import has a practical limit of 1000 rows per file. For larger imports, split into multiple files and import them sequentially.

## What errors can occur during import?

Common errors: duplicate SKU within the file, invalid tracking_type value, missing required field, SKU too long (max 100 characters), name too long (max 255 characters). All errors are shown in the preview before you confirm. Fix the CSV and re-upload.

## Does import create stock?

No. Product import creates or updates product catalog entries only. Stock is created when purchase receipts are committed through the normal purchasing workflow. Import is catalog-only.
