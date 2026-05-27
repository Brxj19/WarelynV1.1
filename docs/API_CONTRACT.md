# Warelyn API Contract

Source of truth: `docs/WARELYN_REAL_WORLD_V2_PRD.md` plus implemented backend routes.

Current implementation is complete through Phase 14 communication/verification/notifications foundation.

## Response Shape

Successful responses return endpoint-specific JSON.

Errors use a consistent envelope:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password.",
    "request_id": "..."
  }
}
```

Validation errors include `details`.

## Health

### `GET /api/health`

Returns service status.

```json
{
  "status": "ok",
  "service": "Warelyn Inventory API"
}
```

## Auth And Tenant Foundation

Status: completed in implementation commit `dbd9752 implement Warelyn auth and tenant foundation` and documented in planning alignment commit `0137f69 update backlog with auth and tenant foundation phase`.

Current implemented auth endpoints are:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/me`
- `POST /api/auth/logout`

### `POST /api/auth/register`

Creates a tenant and its first `TENANT_ADMIN` user. Does not return tokens.

Request:

```json
{
  "company_name": "Acme Warehousing",
  "name": "Acme Admin",
  "email": "admin@example.com",
  "phone": "+15550100",
  "password": "StrongPass123!"
}
```

Response `201`:

```json
{
  "tenant": {
    "id": 1,
    "company_name": "Acme Warehousing",
    "contact_email": "admin@example.com",
    "phone": "+15550100",
    "address": null,
    "gst_number": null,
    "business_type": null,
    "status": "ACTIVE",
    "created_at": "...",
    "updated_at": "..."
  },
  "user": {
    "id": 1,
    "tenant_id": 1,
    "name": "Acme Admin",
    "email": "admin@example.com",
    "phone": "+15550100",
    "role": "TENANT_ADMIN",
    "status": "ACTIVE",
    "email_verified_at": null,
    "phone_verified_at": null,
    "last_login_at": null,
    "created_at": "...",
    "updated_at": "..."
  }
}
```

Duplicate email returns `409 DUPLICATE_EMAIL`.

### `POST /api/auth/login`

Authenticates active users and active tenants.

Request:

```json
{
  "email": "admin@example.com",
  "password": "StrongPass123!"
}
```

Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "user": { "id": 1, "tenant_id": 1, "role": "TENANT_ADMIN" },
  "tenant": { "id": 1, "company_name": "Acme Warehousing" }
}
```

Failure codes:

- `INVALID_CREDENTIALS`
- `DISABLED_USER`
- `DISABLED_TENANT`

### `POST /api/auth/refresh`

Validates a stored refresh token and issues a new access token.

Request:

```json
{
  "refresh_token": "..."
}
```

Response:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Failure codes:

- `INVALID_TOKEN`
- `EXPIRED_TOKEN`
- `DISABLED_USER`
- `DISABLED_TENANT`

### `GET /api/auth/me`

Protected route. Requires `Authorization: Bearer <access_token>`.

Response:

```json
{
  "user": { "id": 1, "tenant_id": 1, "role": "TENANT_ADMIN" },
  "tenant": { "id": 1, "company_name": "Acme Warehousing" },
  "role": "TENANT_ADMIN"
}
```

Missing token returns `401 MISSING_TOKEN`.

### `POST /api/auth/logout`

Revokes a refresh token if supplied. Local frontend logout should still clear local auth state if the server token is already invalid.

Request:

```json
{
  "refresh_token": "..."
}
```

Response:

```json
{
  "success": true
}
```

## Tenant Isolation Contract

- Tenant users do not pass arbitrary `tenant_id` for normal business APIs.
- Backend dependencies resolve tenant context from the authenticated access token and current user row.
- Future tenant-owned modules must derive `tenant_id` from authenticated user context.
- `SUPER_ADMIN` users are platform users and have `tenant_id = null`.
- Role checks are enforced by backend dependencies, not frontend navigation alone.

## Catalog Foundation

All catalog routes require a bearer token and derive `tenant_id` from authenticated user context. Product CRUD does not mutate stock.

Writer roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`.

Reader rules:

- Categories and brands: any tenant user.
- Products: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `VIEWER`, `SALES_STAFF`, `PURCHASE_STAFF`.
- Vendors: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `VIEWER`, `PURCHASE_STAFF`.
- Customers: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `VIEWER`, `SALES_STAFF`.

Implemented endpoints:

- `GET /api/catalog/categories`
- `POST /api/catalog/categories`
- `PATCH /api/catalog/categories/{category_id}`
- `GET /api/catalog/brands`
- `POST /api/catalog/brands`
- `PATCH /api/catalog/brands/{brand_id}`
- `GET /api/catalog/vendors`
- `POST /api/catalog/vendors`
- `PATCH /api/catalog/vendors/{vendor_id}`
- `GET /api/catalog/customers`
- `POST /api/catalog/customers`
- `PATCH /api/catalog/customers/{customer_id}`
- `GET /api/catalog/products`
- `POST /api/catalog/products`
- `PATCH /api/catalog/products/{product_id}`

`GET /api/catalog/products` accepts optional `search` and matches tenant-scoped product `name`, `sku`, or `barcode`.

Duplicate tenant-scoped unique values return `409 DUPLICATE_RECORD`.

## Product Import

All product import routes require a bearer token and derive `tenant_id` from authenticated user context. Product import creates or updates product master data only; it does not mutate stock, create `warehouse_stock`, create `stock_ledger_entries`, create `stock_reservations`, or call `InventoryEngine`.

Writer roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`.

Implemented endpoints:

- `POST /api/imports/products/upload`
- `GET /api/imports/products/{job_id}`
- `GET /api/imports/products/{job_id}/rows`
- `POST /api/imports/products/{job_id}/validate`
- `POST /api/imports/products/{job_id}/commit`
- `POST /api/imports/products/{job_id}/cancel`

Upload request is `multipart/form-data`:

- `file`: CSV file.
- `mode`: `create_only`, `update_existing`, or `upsert`.
- `create_missing_references`: `true` or `false`.

Malformed or non-UTF-8 CSV uploads return `400 INVALID_IMPORT_FILE` with the standard error envelope.

Required CSV columns:

- `name`
- `sku`
- `unit`

Optional CSV columns:

- `barcode`
- `description`
- `category_name`
- `brand_name`
- `vendor_name`
- `cost_price`
- `selling_price`
- `reorder_level`
- `track_batch`
- `track_expiry`
- `track_serial`
- `status`

Import modes:

- `create_only`: rows with existing tenant SKUs are errors.
- `update_existing`: rows without existing tenant SKUs are errors.
- `upsert`: existing tenant SKUs are updated and missing tenant SKUs are created.

Validation catches required fields, invalid numeric/boolean/status values, duplicate SKUs or barcodes in the file, existing SKU conflicts, and tenant barcode collisions. Commit skips invalid rows. Vendor names can be validated or created as vendor master data, but products are not linked to vendors in this phase because product-vendor linking is not implemented yet.

Response shape for upload, validate, commit, and cancel:

```json
{
  "job": {
    "id": 1,
    "status": "VALIDATED",
    "mode": "create_only",
    "total_rows": 1,
    "valid_rows": 1,
    "error_rows": 0,
    "warning_rows": 0,
    "created_count": 0,
    "updated_count": 0,
    "skipped_count": 0
  },
  "rows": []
}
```

## Warehouse Foundation

All warehouse routes require a bearer token and derive `tenant_id` from authenticated user context. Warehouse and location CRUD does not mutate stock.

Reader roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `VIEWER`, `PURCHASE_STAFF`.

Writer roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`.

Implemented endpoints:

- `GET /api/warehouses`
- `POST /api/warehouses`
- `PATCH /api/warehouses/{warehouse_id}`
- `GET /api/warehouses/{warehouse_id}/locations`
- `POST /api/warehouses/{warehouse_id}/locations`
- `PATCH /api/warehouses/{warehouse_id}/locations/{location_id}`

## InventoryEngine And Stock Ledger Foundation

All inventory routes require a bearer token and derive `tenant_id` from authenticated user context. Normal tenant APIs never accept `tenant_id`.

Read roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `VIEWER`, `SALES_STAFF`, `PURCHASE_STAFF`.

Stock mutation roles for stock in/out/adjust/transfer/reconciliation: `TENANT_ADMIN`, `INVENTORY_MANAGER`.

Reservation roles for reserve/release/deduct: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `SALES_STAFF`.

Implemented endpoints:

- `GET /api/inventory/stock`
- `GET /api/inventory/ledger`
- `GET /api/inventory/batches`
- `GET /api/inventory/batches/{batch_id}`
- `GET /api/inventory/serials`
- `GET /api/inventory/serials/{serial_id}`
- `GET /api/inventory/reconciliation/dry-run`
- `POST /api/inventory/stock-in`
- `POST /api/inventory/stock-out`
- `POST /api/inventory/adjust`
- `POST /api/inventory/reserve`
- `POST /api/inventory/reservations/{id}/release`
- `POST /api/inventory/reservations/{id}/deduct`
- `POST /api/inventory/transfer`

Mutation requests require `idempotency_key`. Reusing the same tenant, operation, and idempotency key with the same request returns the stored response. Reusing the same key with a different request returns `409 IDEMPOTENCY_CONFLICT`.

Stock operations require `product_id`, `warehouse_id`, and `location_id`; `location_id` is required to avoid ambiguous stock dimensions.

`POST /api/inventory/stock-in` accepts optional Phase 5 tracking fields:

- `batch_number`
- `supplier_batch_number`
- `manufacture_date`
- `expiry_date`
- `warranty_until`
- `serial_numbers`

Tracking rules:

- Untracked products reject tracking fields.
- Batch-tracked or expiry-tracked products require `batch_number`.
- Expiry-tracked products require `expiry_date`.
- Serial-tracked products require `serial_numbers`, and the serial count must equal `quantity`.
- For serial-tracked receiving, the engine creates one `STOCK_IN` ledger entry per serial with `serial_id`.
- For batch/expiry non-serial receiving, the engine creates one `STOCK_IN` ledger entry with `batch_id`.

Phase 5 limitations: `warehouse_stock` remains location-level only; batch/serial details are traceability records and ledger references. FEFO allocation, expiry jobs, blocked stock transitions, sales fulfillment serial capture, returns QC, and advanced reporting are not implemented.

## Purchase Receiving Workflow

All purchase routes require a bearer token and derive `tenant_id` from authenticated user context. Purchase order status alone does not mutate stock. Stock increases only when a purchase receipt is committed, and commit calls `InventoryEngine.stock_in()` for each receipt item. Purchase receiving must not directly update `warehouse_stock` or directly insert `stock_ledger_entries`.

Read roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `PURCHASE_STAFF`, `VIEWER`.

Write roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `PURCHASE_STAFF`.

`VIEWER` is read-only. `SALES_STAFF` cannot manage purchase orders. `SUPER_ADMIN` does not use normal tenant purchase APIs.

Implemented endpoints:

- `GET /api/purchase-orders`
- `POST /api/purchase-orders`
- `GET /api/purchase-orders/{po_id}`
- `PATCH /api/purchase-orders/{po_id}`
- `POST /api/purchase-orders/{po_id}/submit`
- `POST /api/purchase-orders/{po_id}/cancel`
- `POST /api/purchase-orders/{po_id}/close`
- `POST /api/purchase-orders/{po_id}/receipts`
- `GET /api/purchase-orders/{po_id}/receipts`
- `GET /api/purchase-receipts/{receipt_id}`
- `PATCH /api/purchase-receipts/{receipt_id}`
- `POST /api/purchase-receipts/{receipt_id}/commit`
- `POST /api/purchase-receipts/{receipt_id}/cancel`

Purchase order statuses:

- `DRAFT`
- `SUBMITTED`
- `PARTIALLY_RECEIVED`
- `RECEIVED`
- `CANCELLED`
- `CLOSED`

Purchase receipt statuses:

- `DRAFT`
- `COMMITTED`
- `CANCELLED`

Rules:

- Purchase orders must reference a tenant-owned vendor and tenant-owned products.
- Purchase order updates are allowed only while `DRAFT`.
- Submit requires at least one item.
- Receiving is allowed only for `SUBMITTED` or `PARTIALLY_RECEIVED` purchase orders.
- Cancelled, closed, and fully received purchase orders cannot be received.
- Receipt items must reference tenant-owned products, warehouses, and locations; location must belong to the selected warehouse.
- Received quantity must be positive and cannot exceed the remaining ordered quantity. Phase 4 blocks over-receiving.
- Receipt items may include `batch_number`, `supplier_batch_number`, `manufacture_date`, `expiry_date`, `warranty_until`, and `serial_numbers`; commit forwards these fields to `InventoryEngine.stock_in()`.
- Draft receipts can be edited or cancelled.
- Committed receipts cannot be edited.
- Cancelled receipts do not mutate stock.
- Receipt commit uses `reference_type=PURCHASE_RECEIPT` and `reference_id=receipt_number` on stock ledger entries.

Phase 5 limitations: no vendor bills, supplier payments, invoice accounting, purchase PDFs, sales workflow, returns QC, FEFO auto-allocation, expiry background jobs, mobile scanner workflow, or advanced reports.

## Sales Reservation And Fulfillment Foundation

All sales routes require a bearer token and derive `tenant_id` from authenticated user context. Sales confirmation reserves stock only through `InventoryEngine.reserve_stock()`. Sales cancellation/close releases active reservations only through `InventoryEngine.release_reservation()`. Fulfillment commit deducts reserved stock only through `InventoryEngine.deduct_reserved_stock()`.

Read roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `SALES_STAFF`, `VIEWER`.

Write roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `SALES_STAFF`.

`VIEWER` is read-only. `PURCHASE_STAFF` cannot manage sales orders. `SUPER_ADMIN` does not use normal tenant sales APIs.

Implemented endpoints:

- `GET /api/sales-orders`
- `POST /api/sales-orders`
- `GET /api/sales-orders/{order_id}`
- `PATCH /api/sales-orders/{order_id}`
- `POST /api/sales-orders/{order_id}/confirm`
- `POST /api/sales-orders/{order_id}/cancel`
- `POST /api/sales-orders/{order_id}/close`
- `POST /api/sales-orders/{order_id}/fulfillments`
- `GET /api/sales-orders/{order_id}/fulfillments`
- `GET /api/sales-fulfillments/{fulfillment_id}`
- `PATCH /api/sales-fulfillments/{fulfillment_id}`
- `POST /api/sales-fulfillments/{fulfillment_id}/commit`
- `POST /api/sales-fulfillments/{fulfillment_id}/cancel`

Sales order statuses:

- `DRAFT`
- `CONFIRMED`
- `PARTIALLY_FULFILLED`
- `FULFILLED`
- `CANCELLED`
- `CLOSED`

Sales fulfillment statuses:

- `DRAFT`
- `COMMITTED`
- `CANCELLED`

Rules:

- Sales orders must reference a tenant-owned customer and tenant-owned products.
- Sales order updates are allowed only while `DRAFT`.
- Confirmation requires explicit allocation lines with `sales_order_item_id`, `warehouse_id`, `location_id`, and `quantity`.
- Allocated quantity must equal ordered quantity for each order item.
- Warehouse and location must belong to the tenant; location must belong to the selected warehouse.
- Serial-tracked products can be confirmed only with one-unit reservation lines; explicit `serial_id` selection happens during picking.
- Fulfillment requires active reservations for the same sales order.
- Serial-tracked fulfillment requires a picked serial allocation for the reservation.
- Fulfillment commit creates `SALES_DEDUCT` ledger entries and updates order fulfillment status.
- Cancelled fulfillments do not mutate stock.

## Picking, Packing, And Serial Allocation Foundation

All picking and packing routes require a bearer token and derive `tenant_id` from authenticated user context. Picking and packing are operational allocation workflows only: they do not mutate `warehouse_stock`, do not release reservations, and do not create `stock_ledger_entries`. Final deduction remains `InventoryEngine.deduct_reserved_stock()` during sales fulfillment commit. Package data is optional in Phase 7.

Read roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `SALES_STAFF`, `VIEWER`.

Write roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `SALES_STAFF`.

`VIEWER` is read-only. `PURCHASE_STAFF` cannot manage picking or packing. `SUPER_ADMIN` does not use normal tenant picking and packing APIs.

Implemented endpoints:

- `GET /api/pick-tasks`
- `POST /api/sales-orders/{order_id}/pick-tasks`
- `GET /api/sales-orders/{order_id}/pick-tasks`
- `GET /api/pick-tasks/{pick_task_id}`
- `PATCH /api/pick-tasks/{pick_task_id}`
- `POST /api/pick-tasks/{pick_task_id}/start`
- `POST /api/pick-tasks/{pick_task_id}/pick`
- `POST /api/pick-tasks/{pick_task_id}/cancel`
- `POST /api/sales-orders/{order_id}/packages`
- `GET /api/sales-orders/{order_id}/packages`
- `GET /api/packages/{package_id}`
- `PATCH /api/packages/{package_id}`
- `POST /api/packages/{package_id}/pack`
- `POST /api/packages/{package_id}/cancel`

Pick task statuses:

- `PENDING`
- `IN_PROGRESS`
- `PICKED`
- `CANCELLED`

Pick task item statuses:

- `PENDING`
- `PICKED`
- `CANCELLED`

Package statuses:

- `DRAFT`
- `PACKED`
- `CANCELLED`

Picking rules:

- Pick tasks can be generated only for `CONFIRMED` or `PARTIALLY_FULFILLED` sales orders.
- Pick tasks are generated from active `StockReservation` rows.
- Duplicate active pick tasks for the same reservation are blocked.
- Picked quantity cannot exceed required quantity or active reservation quantity.
- Serial-tracked products require explicit `serial_id` during picking.
- Selected serial must belong to the same tenant, product, warehouse, and location, and must be `IN_STOCK`.
- Duplicate serial allocation is blocked within a pick request and across non-cancelled pick tasks.
- Batch allocation is explicit/manual only; selected batch must match tenant, product, warehouse, and location.

Packing rules:

- Packages can be created only from picked task items.
- Package creation and pack action do not deduct stock.
- Cancelled packages do not mutate stock.
- Packages remain optional before fulfillment commit in Phase 7.

Phase 7 limitations: no carrier shipment integration, invoice accounting, payment collection, FEFO auto-allocation, delivery tracking with external carriers, full mobile scanner workflow, advanced reports, or mandatory package-before-fulfillment enforcement.

## Sales Returns QC And Blocked Stock Foundation

All sales return routes require a bearer token and derive `tenant_id` from authenticated user context. Return processing is split from stock authority: returns service owns return workflow state, while sellable restock goes through `InventoryEngine.return_restock()`. Blocked, damaged, and scrapped returned stock is stored in `blocked_return_stock` and is not sellable warehouse stock.

Read roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `SALES_STAFF`, `VIEWER`.

Create/update/submit/cancel roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `SALES_STAFF`.

QC inspect/process roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`.

`VIEWER` is read-only. `PURCHASE_STAFF` cannot manage customer returns. `SUPER_ADMIN` does not use normal tenant return APIs.

Implemented endpoints:

- `GET /api/sales-returns`
- `POST /api/sales-returns`
- `GET /api/sales-returns/{return_id}`
- `PATCH /api/sales-returns/{return_id}`
- `POST /api/sales-returns/{return_id}/submit`
- `POST /api/sales-returns/{return_id}/cancel`
- `POST /api/sales-returns/{return_id}/inspect`
- `POST /api/sales-returns/{return_id}/process`

Sales return statuses:

- `DRAFT`
- `SUBMITTED`
- `INSPECTION_PENDING`
- `PARTIALLY_PROCESSED`
- `PROCESSED`
- `CANCELLED`

Sales return item QC statuses:

- `PENDING`
- `ACCEPTED_RESTOCK`
- `ACCEPTED_BLOCKED`
- `DAMAGED`
- `SCRAPPED`
- `REJECTED`

Return rules:

- Returns can be created only for fulfilled sales order quantities.
- Returned quantity cannot exceed fulfilled quantity minus prior non-cancelled returns for the same order item.
- Serial-tracked returns require quantity `1` and an existing sold serial fulfilled by the same sales order.
- `ACCEPTED_RESTOCK` writes `RETURN_RESTOCK` stock ledger entries with `SALES_RETURN` reference type and increases sellable stock.
- `ACCEPTED_BLOCKED`, `DAMAGED`, and `SCRAPPED` create `blocked_return_stock` records and do not increase sellable stock or stock ledger projection totals.
- `REJECTED` does not mutate stock.
- Existing sold serial rows are updated for serial return outcomes; normal `stock_in()` is not used for serial returns.

## Reports, Reorder Rules, And Operational Dashboards

All report routes require a bearer token and derive `tenant_id` from authenticated user context. Reports are read-only and query-based. They do not mutate `warehouse_stock`, do not create `stock_ledger_entries`, do not call `InventoryEngine` mutation methods, and do not create purchase orders.

Read roles: `TENANT_ADMIN`, `INVENTORY_MANAGER`, `VIEWER`.

`SALES_STAFF` and `PURCHASE_STAFF` do not read the Phase 9 consolidated reports. `SUPER_ADMIN` does not use normal tenant report APIs.

Implemented endpoints:

- `GET /api/dashboard/operations`
- `GET /api/reports/inventory-summary`
- `GET /api/reports/warehouse-stock`
- `GET /api/reports/location-stock`
- `GET /api/reports/stock-movements`
- `GET /api/reports/low-stock`
- `GET /api/reports/reorder-suggestions`
- `GET /api/reports/product-valuation`
- `GET /api/reports/batch-expiry`
- `GET /api/reports/serial-status`
- `GET /api/reports/blocked-stock`
- `GET /api/reports/reconciliation`

Common optional filters where applicable:

- `warehouse_id`
- `location_id`
- `product_id`
- `category_id`
- `brand_id`
- `status`
- `search`
- `date_from`
- `date_to`
- `movement_type`
- `reference_type`
- `expiry_before`
- `expiry_within_days`
- `page`
- `page_size`

Report rules:

- Inventory summary aggregates backend stock, product, batch, blocked stock, and reconciliation data.
- Warehouse and location stock reports read `warehouse_stock` projection rows and product current cost.
- Stock movement report reads `stock_ledger_entries` only.
- Low stock uses `Product.reorder_level` and `WarehouseStock.quantity_available`.
- Reorder suggestions are advisory only. Suggested quantity is `max(reorder_level * 2 - available, reorder_level)`.
- Product valuation is current product cost times on-hand quantity; FIFO/LIFO/weighted average are not implemented.
- Batch expiry reports use `InventoryBatch.expiry_date` and report `EXPIRED`, `EXPIRING_SOON`, or `OK`.
- Serial status reports read `InventorySerial` status rows.
- Blocked stock reports combine `blocked_return_stock`, blocked batch statuses, and blocked serial statuses.
- Reconciliation report exposes the current ledger-to-projection dry-run result in report form.

## Super Admin Settings And Audit Logs Foundation

All super admin routes require a bearer token and `SUPER_ADMIN` role. Tenant routes are not affected.

Implemented endpoints:

- `GET /api/admin/tenants`
- `GET /api/admin/tenants/{tenant_id}`
- `PATCH /api/admin/tenants/{tenant_id}`
- `GET /api/admin/users`
- `GET /api/admin/users/{user_id}`
- `PATCH /api/admin/users/{user_id}`
- `GET /api/admin/settings`
- `PATCH /api/admin/settings`
- `GET /api/admin/audit-logs`

All admin endpoints require `require_super_admin()` dependency. Audit logs are query-based and read `audit_logs` table.

## Verification Foundation

All verification routes require a bearer token and derive `user_id` from authenticated user context. Verification does not accept verification codes for third-party accounts.

Implemented endpoints:

- `POST /api/verification/email/send`
- `POST /api/verification/email/confirm`
- `POST /api/verification/phone/send`
- `POST /api/verification/phone/confirm`
- `GET /api/verification/status`

### `POST /api/verification/email/send`

Generates an OTP, supersedes previous active OTPs for the same user/purpose/destination, and sends a verification email via SMTP (MailHog in dev).

Request:

```json
{}
```

Response `200`:

```json
{
  "success": true,
  "message": "Verification code sent to email."
}
```

Failure codes:

- `EMAIL_DELIVERY_FAILED` — SMTP/MailHog not reachable (502).

### `POST /api/verification/email/confirm`

Validates the OTP code, sets `email_verified_at` on the user, creates an audit log entry and a success notification.

Request:

```json
{
  "code": "123456"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Email verified successfully."
}
```

Failure codes:

- `OTP_NOT_FOUND` — no active OTP for this user/purpose.
- `OTP_EXPIRED` — code has expired.
- `OTP_CONSUMED` — code already used.
- `OTP_SUPERSEDED` — a newer code was sent.
- `OTP_MAX_ATTEMPTS` — too many failed attempts.
- `OTP_INVALID` — wrong code.

### `POST /api/verification/phone/send`

Generates an OTP, supersedes previous active OTPs, and creates an SMS outbox record. No real SMS is sent.

Request:

```json
{
  "phone": "+15550100"
}
```

Response `200`:

```json
{
  "success": true,
  "message": "Verification code sent to phone."
}
```

Failure codes:

- `PHONE_REQUIRED` — user does not have a phone number on record (400).

### `POST /api/verification/phone/confirm`

Same logic as email confirm but sets `phone_verified_at`.

### `GET /api/verification/status`

Returns the current user's verification state. Does not expose OTP codes.

Response:

```json
{
  "email": "user@example.com",
  "email_verified": true,
  "email_verified_at": "2026-05-22T12:00:00Z",
  "phone": "+15550100",
  "phone_verified": true,
  "phone_verified_at": "2026-05-22T12:00:00Z"
}
```

## Notifications Foundation

All notification routes require a bearer token and derive `user_id` from authenticated user context. Users can only see and manage their own notifications.

Implemented endpoints:

- `GET /api/notifications`
- `GET /api/notifications/unread-count`
- `POST /api/notifications/{id}/read`
- `POST /api/notifications/read-all`

### `GET /api/notifications`

Returns paginated notifications for the authenticated user, newest first. Accepts `page` and `page_size` query params.

Response:

```json
{
  "items": [
    {
      "id": 1,
      "type": "SUCCESS",
      "category": "VERIFICATION",
      "title": "Email Verified",
      "message": "Your email address has been verified successfully.",
      "is_read": false,
      "created_at": "..."
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

### `GET /api/notifications/unread-count`

Returns the count of unread notifications for the authenticated user.

Response:

```json
{
  "count": 3
}
```

### `POST /api/notifications/{id}/read`

Marks a single notification as read. Validates user ownership.

Response `200`:

```json
{
  "success": true
}
```

Returns `404` if the notification does not exist or does not belong to the user.

### `POST /api/notifications/read-all`

Marks all unread notifications as read for the authenticated user.

Response `200`:

```json
{
  "success": true
}
```
