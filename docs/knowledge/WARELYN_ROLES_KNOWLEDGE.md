# Warelyn Roles and Permissions Knowledge

## Role overview

Warelyn has six roles. Each role sees only what is relevant to their job function.

**SUPER_ADMIN** — Platform administrator. Manages all tenants. Cannot see any tenant's business data (orders, stock, reports). Lives in the admin panel at /admin.

**TENANT_ADMIN** — The business owner or manager. Can see and do everything within their tenant: manage users, settings, templates, all workflows, all reports, all approvals.

**INVENTORY_MANAGER** — Manages warehouse operations. Can manage stock, products, warehouses, picking, putaway, cycle counts, returns QC. Cannot manage users or company settings.

**SALES_STAFF** — Manages customer-facing sales. Can create and manage sales orders, create invoices, create returns, view customers and products. Cannot manage purchase orders or warehouse settings.

**PURCHASE_STAFF** — Manages vendor-facing purchasing. Can create and manage purchase orders, receive stock, record bills, manage vendors. Cannot manage sales orders or customer data.

**VIEWER** — Read-only access. Can see stock, reports, orders, and movements. Cannot create, edit, or delete anything. No workflow tasks.

## What TENANT_ADMIN can do

- Create, edit, disable, and delete users
- Manage company settings: company name, timezone, currency
- Manage document templates: invoice, bill, email templates, PDF templates
- Approve high-value purchase orders
- See all workflow tasks across all roles
- Access all reports
- Complete any workflow task
- View the full audit log
- View assistant telemetry

## What INVENTORY_MANAGER can do

- Manage products: create, edit, import
- Manage warehouses and locations
- Manage stock: adjustments, transfers, cycle counts, reconciliation
- Complete pick tasks
- Complete putaway tasks
- Inspect and process sales returns (QC)
- View inventory reports, warehouse reports, reconciliation reports
- View their own workflow tasks and all inventory-related tasks

## What SALES_STAFF can do

- Create and confirm sales orders
- Cancel sales orders
- Manage customers: create, edit
- Create and send invoices
- Create sales returns (submit only, cannot inspect)
- View fulfillment status of their orders
- View their own workflow tasks (CREATE_INVOICE tasks)

## What SALES_STAFF cannot do

- Inspect or process returns (403 if they try)
- Create or manage purchase orders
- Manage products or warehouses
- Manage users
- Access company settings or templates

## What PURCHASE_STAFF can do

- Create and submit purchase orders
- Receive stock by committing purchase receipts
- Record vendor bills
- Manage vendors: create, edit
- View purchase reports
- View their own workflow tasks (RECORD_BILL, REORDER_STOCK tasks)

## What PURCHASE_STAFF cannot do

- Create or manage sales orders
- Create invoices
- Manage customers
- Inspect returns
- Manage users or settings

## What VIEWER can do

- View all reports: stock, orders, movements, valuations, reconciliation
- View the dashboard (read-only)
- View product catalog
- View warehouses and stock levels

## What VIEWER cannot do

- Create, edit, or delete anything
- See any workflow tasks
- Access My Tasks
- Approve orders
- Access settings beyond their own profile

## Why am I getting Access Denied?

If you see Access Denied, your role does not have permission for that action or page. Common examples:
- SALES_STAFF accessing the return inspect page → 403, only INVENTORY_MANAGER can inspect
- PURCHASE_STAFF accessing the sales order creation form → 403, not a sales function
- VIEWER clicking any write action → blocked, Viewer is read-only

Contact your TENANT_ADMIN to check if your role is correct or if you need elevated access.

## What is the difference between TENANT_ADMIN and INVENTORY_MANAGER for settings?

TENANT_ADMIN can change company settings (name, currency, timezone), manage document templates, and manage user roles. INVENTORY_MANAGER can edit document templates but cannot change company settings or manage user accounts.
