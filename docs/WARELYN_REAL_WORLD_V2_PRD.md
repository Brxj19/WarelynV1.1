# Warelyn Inventory V2 — Real-World Inventory SaaS PRD and Engineering Blueprint

**Document type:** Product Requirements Document + Architecture Blueprint  
**Project:** Warelyn Inventory  
**Former/internal codename:** Mini-Zoho / Northstar Inventory  
**Version:** V2 Foundation  
**Target stack:** React + FastAPI + MySQL + SQLAlchemy + Alembic + Docker  
**Primary goal:** Move the current inventory product from a feature-rich demo into a realistic, modular, progressively buildable inventory SaaS foundation.

---

## 0. Brand Identity and Positioning

### 0.1 Public Product Name

**Warelyn Inventory**

### 0.2 Short Name

**Warelyn**

### 0.3 Tagline

**Inventory that moves with your business.**

### 0.4 One-Line Description

Warelyn Inventory is a production-style inventory and warehouse operations platform for growing businesses to manage products, warehouses, stock movements, purchases, sales, returns, reports, and team operations from one SaaS workspace.

### 0.5 Brand Positioning

Warelyn is a modern inventory and warehouse operations platform built for businesses that need accurate stock visibility, structured workflows, and reliable operational control across products, warehouses, orders, and teams.

The product should not feel like a spreadsheet replacement or a generic CRUD dashboard. It should feel like an operational command center where every stock movement, order, return, warehouse action, and user decision is traceable and trustworthy.

### 0.6 Brand Personality

- Professional.
- Reliable.
- Operational.
- Modern.
- Clean.
- Trustworthy.
- Efficient.
- Data-driven.

### 0.7 Design Philosophy

**Operational clarity over decoration.**

Warelyn should feel like a real business operations product. The interface must prioritize workflow clarity, stock accuracy, role-aware actions, and decision support. Users should always know:

- What stock they have.
- Where the stock is located.
- What stock is reserved.
- What stock is expiring.
- What stock needs action.
- What changed recently.
- Who performed an operation.
- What the next operational action should be.

### 0.8 Visual Direction

Warelyn V2 should preserve the current repo’s existing SaaS UI direction instead of restarting the visual design from scratch. The improvement should happen at the foundation, architecture, workflow, consistency, and interaction level.

Use a clean B2B SaaS design language with:

- Deep blue primary brand color.
- Emerald green accent for success, healthy stock, and positive operational state.
- Soft gray backgrounds.
- White cards and panels.
- Clean typography.
- Structured data-dense layouts.
- Simple line icons.
- Clear status badges.
- Strong table, filter, form, and workflow consistency.

### 0.9 Suggested Brand Colors

| Token | Color | Usage |
|---|---:|---|
| Primary | `#1E3A8A` | Navigation, primary actions, key brand surfaces |
| Accent | `#10B981` | Success, healthy stock, completion states |
| Background | `#F8FAFC` | App shell background |
| Surface | `#FFFFFF` | Cards, forms, tables, modals |
| Text | `#0F172A` | Primary readable text |
| Muted Text | `#64748B` | Secondary descriptions, metadata |
| Border | `#E2E8F0` | Dividers, cards, inputs, tables |
| Warning | `#F59E0B` | Low-stock, expiry warning, pending state |
| Danger | `#EF4444` | Error, damage, expired, destructive actions |

### 0.10 Logo Direction

The Warelyn logo should communicate inventory control, warehouse movement, and operational trust.

Recommended concept:

- Minimal warehouse box or storage rack.
- Movement arrow to represent stock movement.
- Checkmark to represent accuracy/control.
- Clean geometric icon.
- Professional sans-serif wordmark.
- Works as icon + wordmark, icon-only, favicon, sidebar logo, and login page brand mark.

Avoid:

- Cartoon warehouse graphics.
- Overly playful icons.
- Heavy gradients.
- 3D effects.
- Cluttered package illustrations.
- Anything that looks like a delivery app instead of an inventory operations platform.

### 0.11 Naming Rules Across Code and Docs

Use **Warelyn Inventory** for public-facing product copy.

Use **Warelyn** for short UI labels where space is limited.

Existing repository names such as `mini-zoho` may remain as technical repository names for now, but user-facing screens, README copy, PRD copy, documentation, login pages, and app shell branding should use **Warelyn Inventory**.

Do not use Zoho branding, Zoho assets, Zoho copy, or Zoho UI screenshots. This product may be inspired by modern inventory SaaS workflows, but the public identity must be original.

---

## 1. Executive Summary

Warelyn Inventory V2 is a real-world, multi-tenant inventory and order operations SaaS for small and mid-sized businesses that need to manage product catalog, suppliers, warehouses, stock movements, purchasing, selling, fulfillment, expiry, returns, documents, and operational reports.

The current V1 already has a strong base: React frontend, FastAPI backend, MySQL database, SQLAlchemy/Alembic persistence, Docker Compose setup, JWT authentication, tenant-scoped master data, products, warehouses, warehouse stock, inventory transactions, purchase orders, sales orders, reports, audit logs, notifications, Mailpit-style development email support, SMS outbox, and PDF document services. V2 must not restart from scratch. It must preserve the existing UI direction and progressively rebuild the foundations beneath it so the product behaves like a real inventory system rather than a simple CRUD application.

V2 focuses on:

1. Correct domain modeling.
2. Strict separation of concerns.
3. A central Inventory Engine.
4. Ledger-style stock movement.
5. Bulk import and barcode-first operations.
6. Warehouse location/bin tracking.
7. Batch/lot, expiry, serial, and quality status tracking.
8. Real purchase, receiving, putaway, sales reservation, picking, packing, shipping, invoice, bill, return, and reconciliation workflows.
9. Production-level validation, auditability, idempotency, tenant isolation, and testability.
10. Stable foundations that allow AI agents to build features step by step without corrupting the architecture.

---

## 2. Why V2 Is Needed

The V1 product contains many modules, but real inventory systems cannot be treated only as independent CRUD screens. In real businesses:

- Products are usually imported from CSV, supplier catalogs, marketplaces, or APIs.
- Warehouse workers scan barcodes instead of manually typing item details.
- Warehouse stock is physically placed in warehouses, zones, racks, bins, return areas, quarantine areas, damaged areas, and shipping docks.
- Some products require batch/lot tracking.
- Some products require expiry tracking.
- Some products require individual serial number tracking.
- Stock is not one number; it has states such as on hand, available, reserved, in transit, damaged, expired, under quality check, blocked, and returned.
- Purchase receiving should increase stock only after goods are received.
- Sales confirmation should reserve stock, not immediately deduct physical stock.
- Delivery should deduct stock.
- Returns should not always go directly back to sellable stock; they should pass through quality check.
- Every stock-changing event must be recorded in a stock ledger.
- Inventory correctness matters more than UI convenience.
- The frontend must never be the source of truth for stock numbers.

V2 must therefore be designed around real operational workflows, not only database tables.

---

## 3. Current Product Scan Summary

Based on the current repository and product documentation, V1 already includes the following foundations:

### 3.1 Current Stack

- Frontend: React.
- Backend: Python FastAPI.
- Database: MySQL.
- ORM: SQLAlchemy.
- Migrations: Alembic.
- Authentication: JWT.
- Deployment: Docker Compose.

### 3.2 Current Business Modules

- Authentication and tenant registration.
- JWT login and `auth/me`.
- Super Admin and tenant user roles.
- Tenant management.
- Categories.
- Brands.
- Vendors.
- Customers.
- Warehouses.
- Product catalog.
- Warehouse stock.
- Inventory transactions.
- Stock in/out/adjustment.
- Stock transfers.
- Purchase orders.
- Purchase receives.
- Vendor bills.
- Sales orders.
- Packages.
- Invoices.
- Sales returns.
- Reports and CSV export.
- Audit logs.
- Notifications.
- Development email through Mailpit/MailHog-style flow.
- Development SMS outbox.
- Invoice and bill PDFs.
- CSV seed importer.

### 3.3 Current Strengths

- Good stack choice for the project.
- Multi-tenant design already present.
- Tenant-scoped master data already present.
- Warehouse stock is separated from product master data.
- Stock movement history exists.
- Purchase and sales workflows exist.
- Reports exist.
- Notifications and audit logs exist.
- Development email/SMS/PDF direction exists.
- UI already has a SaaS shell and should be preserved.

### 3.4 Current Weaknesses to Fix in V2

- The domain boundaries need to be stricter.
- Stock-changing operations must be centralized in one engine.
- Some workflows may still directly update stock from different services.
- Warehouse locations/bins are missing or too shallow.
- Batch/expiry/serial support needs to become first-class in UI and services.
- Real CSV import for business users needs preview, validation, mapping, and commit flow.
- Return quality check is not fully modeled.
- Reorder rules and replenishment planning are not yet realistic.
- Barcode/scanner-friendly workflows are missing.
- Tests need to match real inventory invariants.
- UI should keep the existing style, but screens must reflect real operations.
- Code must be modular enough for AI agents to work safely in small steps.

---

## 4. Product Vision

Warelyn Inventory V2 should become a realistic inventory operations platform for businesses that need accurate stock visibility, workflow discipline, and operational trust. It should support:

- Multi-tenant inventory control.
- Product catalog management.
- Supplier and customer management.
- Multi-warehouse stock control.
- Warehouse locations and bins.
- Purchase order and receiving workflows.
- Sales order and fulfillment workflows.
- Batch, lot, serial, and expiry tracking.
- Barcode-assisted operations.
- Return and quality check workflows.
- Reports, audit trails, notifications, and PDFs.
- Reliable CSV import/export.
- Clean developer architecture.

The product should feel like an operations command center, not a spreadsheet replacement.

---

## 5. Product Philosophy

### 5.1 Correctness First

Inventory systems are financial and operational systems. Wrong stock numbers can cause overselling, failed deliveries, expired product dispatch, vendor disputes, bad purchase planning, and incorrect reports.

Priority order:

1. Correct data.
2. Clear workflows.
3. Auditability.
4. Speed.
5. UI polish.

### 5.2 Workflow Over CRUD

The product should not simply expose database tables. Use workflows:

- Receive purchase.
- Put away stock.
- Reserve stock.
- Pick order.
- Pack shipment.
- Deliver order.
- Return item.
- QC return.
- Reconcile inventory.
- Scrap damaged stock.
- Transfer between warehouses.

### 5.3 Ledger Over Direct Mutation

Stock numbers should be derived and verified from ledger events. `warehouse_stock` can be a fast current-state projection, but every change must have a corresponding immutable stock movement.

### 5.4 Bulk and Scan First

Manual entry should exist, but real operations need:

- CSV import.
- Barcode scan.
- Batch paste.
- Supplier catalog import.
- Mobile-friendly scanner screens.

### 5.5 Separation of Concerns

Each layer should have one responsibility:

- Routers handle HTTP only.
- Schemas validate request/response shape.
- Services coordinate use cases.
- Domain engines enforce business rules.
- Repositories handle database access.
- Models represent persistence.
- Events capture side effects.
- Jobs handle async/background work.
- Frontend API clients call APIs.
- Frontend pages orchestrate UI.
- Frontend components remain reusable and dumb where possible.

---

## 6. Target Users and Roles

### 6.1 Platform Super Admin

Platform owner who manages the SaaS itself.

Responsibilities:

- Manage tenants.
- Monitor tenant usage.
- View system-wide audit logs.
- Manage system settings.
- Review platform health.
- Access development tools in development mode.
- Does not normally perform day-to-day inventory operations.

### 6.2 Tenant Owner / Tenant Admin

Business owner or operations admin.

Responsibilities:

- Manage organization profile.
- Manage users and roles.
- Configure warehouses and locations.
- Configure products, vendors, customers.
- Review reports.
- Manage operational settings.
- Approve risky operations.

### 6.3 Inventory Manager

Warehouse/inventory operator.

Responsibilities:

- Receive stock.
- Move stock.
- Adjust stock.
- Transfer stock.
- Manage batches, serials, expiry.
- Perform cycle counts.
- Handle damaged/expired/quarantine stock.

### 6.4 Purchase Staff

Procurement user.

Responsibilities:

- Manage vendors.
- Create purchase orders.
- Receive purchase orders.
- Create vendor bills.
- Track expected delivery.
- Review reorder suggestions.

### 6.5 Sales Staff

Sales/order user.

Responsibilities:

- Manage customers.
- Create sales orders.
- Confirm orders.
- Track package/shipment states.
- Create invoices.
- Handle returns.

### 6.6 Warehouse Picker/Packer

Optional V2 role.

Responsibilities:

- View assigned pick tasks.
- Scan bins and products.
- Pack items.
- Mark package ready.
- Report shortages or damaged items.

### 6.7 Viewer / Auditor

Read-only user.

Responsibilities:

- View dashboards, reports, and history.
- Cannot create/edit/delete or change stock.

---

## 7. V2 Scope

### 7.1 In Scope

- Real-world PRD and architecture redesign.
- Separation of concerns.
- Inventory Engine.
- Stock ledger.
- Warehouse locations/bins.
- Barcode support.
- Product catalog import.
- Purchase receiving and putaway.
- Batch/lot tracking.
- Expiry tracking and alerts.
- Serial tracking.
- Sales reservation/deduction.
- Picking and packing basics.
- Returns with QC.
- Damaged/expired/quarantine stock.
- Low-stock and reorder rules.
- Reconciliation and cycle counting.
- Reporting upgrades.
- API contract cleanup.
- Test strategy.
- Developer/AI agent workflow.

### 7.2 Out of Scope for Early V2

- Full subscription billing.
- AI assistant expansion.
- Marketplace integration.
- Real carrier integration.
- Real payment gateway.
- Advanced demand forecasting.
- Full accounting ledger.
- Native mobile app.
- Multi-country tax compliance.
- Full ERP manufacturing.

---

## 8. Real-World Inventory Concepts To Implement

### 8.1 Product Master

A product master defines what the item is, not where stock is.

Fields:

- Product ID.
- Name.
- SKU.
- Barcode/GTIN/EAN/UPC.
- Category.
- Brand.
- Default vendor.
- Unit of measure.
- Cost price.
- Selling price.
- Tax class.
- Reorder level.
- Track inventory flag.
- Batch tracking flag.
- Serial tracking flag.
- Expiry tracking flag.
- Warranty tracking flag.
- Status.
- Images.
- Dimensions and weight.
- HSN/SAC/GST code if needed later.

### 8.2 Product Variants

Real products may have variants:

- Size.
- Color.
- Storage.
- Pack size.
- Flavor.
- Model.

V2 can start with simple products, but the architecture should allow:

- `product_templates`
- `product_variants`

### 8.3 Units of Measure

Inventory may be purchased in one unit and sold in another.

Example:

- Buy: carton.
- Store: box.
- Sell: piece.

Tables:

- `units`
- `product_unit_conversions`

### 8.4 Barcode

Barcode should support:

- Product barcode.
- Location/bin barcode.
- Batch barcode.
- Serial barcode.
- Package barcode.
- Shipment barcode.

The UI should include a reusable `BarcodeInput` component.

### 8.5 Warehouse

Warehouse is a physical facility.

Fields:

- Name.
- Code.
- Address.
- City/state/country.
- Manager.
- Phone.
- Default flag.
- Status.

### 8.6 Warehouse Location/Bin

Warehouse locations represent where stock is stored.

Examples:

- Zone A.
- Aisle 01.
- Rack R04.
- Shelf S02.
- Bin B09.
- Damaged Area.
- Returns Area.
- Quarantine Area.
- Packing Station.
- Shipping Dock.

Table: `warehouse_locations`

Fields:

- id.
- tenant_id.
- warehouse_id.
- parent_location_id nullable.
- code.
- name.
- barcode.
- location_type: STORAGE, PICKING, RECEIVING, PACKING, SHIPPING, RETURN, DAMAGED, EXPIRED, QUARANTINE, QC, SCRAP, VIRTUAL.
- status.
- sort_order.

### 8.7 Stock States

Stock should be represented by state, not only quantity.

Core states:

- ON_HAND.
- AVAILABLE.
- RESERVED.
- IN_TRANSIT.
- QC_HOLD.
- DAMAGED.
- EXPIRED.
- QUARANTINE.
- RETURNED.
- SCRAPPED.
- LOST.

Projection table can store summarized fields:

`warehouse_stock`

- quantity_on_hand.
- quantity_reserved.
- quantity_available.
- quantity_in_transit.
- quantity_qc_hold.
- quantity_damaged.
- quantity_expired.
- quantity_quarantine.

V2 can retain existing `quantity`, `reserved_quantity`, `available_quantity` initially, but the service layer should prepare for state expansion.

### 8.8 Batch/Lot Tracking

Batch/lot tracking is required for food, medicine, cosmetics, chemicals, manufacturing, and any product where group traceability matters.

Table: `inventory_batches`

Fields:

- id.
- tenant_id.
- product_id.
- warehouse_id.
- location_id nullable.
- batch_number.
- supplier_batch_number.
- manufacture_date nullable.
- expiry_date nullable.
- warranty_until nullable.
- quantity_on_hand.
- quantity_available.
- quantity_reserved.
- status.

### 8.9 Expiry Tracking

Expiry must support:

- Expiry date.
- Expiry alert date.
- Sell-by date.
- Removal date.
- FEFO picking.
- Expired stock isolation.
- Expiry alerts and reports.

Core rule:

- For expiring items, pick from the batch expiring soonest first.

### 8.10 Serial Tracking

Serial tracking is required for electronics, phones, laptops, appliances, medical equipment, and warranty-heavy goods.

Table: `inventory_serials`

Fields:

- id.
- tenant_id.
- product_id.
- warehouse_id.
- location_id.
- batch_id nullable.
- serial_number.
- status: IN_STOCK, RESERVED, PICKED, PACKED, SOLD, RETURNED, DAMAGED, SCRAPPED.
- warranty_until nullable.
- expires_on nullable.

### 8.11 Stock Ledger

The stock ledger is the immutable source of stock movement history.

Table: `stock_ledger_entries`

Fields:

- id.
- tenant_id.
- product_id.
- warehouse_id.
- location_id nullable.
- batch_id nullable.
- serial_id nullable.
- movement_type.
- quantity_delta.
- reserved_delta.
- available_delta.
- reference_type.
- reference_id.
- idempotency_key.
- note.
- created_by.
- created_at.

Movement types:

- STOCK_IN
- STOCK_OUT
- ADJUSTMENT_IN
- ADJUSTMENT_OUT
- PURCHASE_RECEIVE
- SALES_RESERVE
- SALES_RELEASE
- SALES_DEDUCT
- TRANSFER_OUT
- TRANSFER_IN
- RETURN_RECEIVED
- RETURN_RESTOCKED
- DAMAGE_OUT
- EXPIRE_OUT
- SCRAP_OUT
- QC_HOLD
- QC_RELEASE
- CYCLE_COUNT_ADJUSTMENT

### 8.12 Reservations

Reservation separates "customer has ordered it" from "stock physically left warehouse".

Table: `stock_reservations`

Fields:

- id.
- tenant_id.
- sales_order_id.
- sales_order_item_id.
- product_id.
- warehouse_id.
- location_id nullable.
- batch_id nullable.
- serial_id nullable.
- quantity.
- status: ACTIVE, RELEASED, CONVERTED_TO_DELIVERY, EXPIRED.
- expires_at nullable.
- created_by.
- created_at.
- updated_at.

### 8.13 Purchase Receiving

Receiving is not just "PO status = received".

Real flow:

1. Purchase order issued.
2. Goods arrive.
3. Receiver selects PO.
4. Receiver scans products.
5. Receiver enters accepted quantity.
6. Receiver enters rejected/damaged quantity.
7. Receiver assigns batch/expiry/serial where required.
8. Receiver chooses receiving location.
9. System creates stock ledger entries.
10. Optional putaway task is created.

### 8.14 Putaway

Putaway moves stock from receiving area into storage bins.

Flow:

1. Stock received into receiving location.
2. System suggests bin based on product/category/location rules.
3. Worker scans product and destination bin.
4. Stock moves from receiving location to storage bin.

### 8.15 Sales Fulfillment

Real sales flow:

1. Sales order draft.
2. Confirm order.
3. Stock reserved.
4. Pick task generated.
5. Picker scans bin and product.
6. Pack task/package generated.
7. Invoice generated.
8. Shipment/delivery completed.
9. Stock deducted.

### 8.16 Returns and Quality Check

Returns should not directly become sellable.

Flow:

1. Return requested.
2. Return received.
3. Item enters QC location.
4. QC result: RESTOCK, DAMAGED, SCRAP, REPAIR, RETURN_TO_VENDOR.
5. Stock state changes accordingly.

### 8.17 Reorder Rules

Reorder rule fields:

- product_id.
- warehouse_id nullable.
- preferred_vendor_id.
- min_stock.
- max_stock.
- reorder_quantity.
- lead_time_days.
- safety_stock.
- enabled.

System should generate:

- Low stock alert.
- Suggested purchase order.
- Replenishment report.

---

## 9. V2 Modular Architecture

### 9.1 Backend Layering

Use this backend structure:

```text
backend/app/
  api/
    routers/
      auth.py
      tenants.py
      catalog.py
      warehouses.py
      inventory.py
      purchasing.py
      receiving.py
      sales.py
      fulfillment.py
      returns.py
      documents.py
      reports.py
      imports.py
      notifications.py
      audit.py
  core/
    config.py
    database.py
    errors.py
    security.py
    permissions.py
    pagination.py
    idempotency.py
  domain/
    inventory/
      engine.py
      ledger.py
      reservation_service.py
      allocation_service.py
      picking_strategy.py
      reconciliation.py
      exceptions.py
    purchasing/
      purchase_order_service.py
      receiving_service.py
    sales/
      sales_order_service.py
      fulfillment_service.py
      return_service.py
    catalog/
      product_service.py
      import_service.py
    documents/
      pdf_service.py
      email_document_service.py
  repositories/
    base.py
    product_repository.py
    warehouse_repository.py
    stock_repository.py
    order_repository.py
    report_repository.py
  models/
  schemas/
  events/
    event_bus.py
    event_types.py
    outbox.py
  jobs/
    expire_batches.py
    reorder_suggestions.py
    send_email.py
    cleanup_otp.py
  services/
    email_service.py
    sms_service.py
    otp_service.py
  cli/
    seed_from_csv.py
    reconcile_inventory.py
    create_demo_data.py
```

### 9.2 Backend Responsibility Rules

#### Routers

Routers should define HTTP paths, read the current user, validate request schema, call application/domain services, and return response schema. Routers must not directly mutate stock, contain business calculations, or perform complex database queries.

#### Schemas

Schemas validate input, shape output, and define public API contracts. They should not contain SQLAlchemy logic or domain algorithms.

#### Domain Services

Domain services own business rules, validate permissions beyond route-level checks, call repositories, coordinate transactions, emit events, and create audit logs.

#### Repositories

Repositories encapsulate query logic, apply tenant filters, use row locks where needed, and return model objects. They do not decide business workflow.

#### Models

Models represent persistence and define constraints/indexes. Avoid placing workflow behavior in models.

#### Events and Jobs

Events record side effects. Jobs process async or scheduled work such as expired stock, reorder suggestions, queued emails, and OTP cleanup.

---

## 10. Inventory Engine Specification

### 10.1 Purpose

The Inventory Engine is the only backend module allowed to change stock.

All stock-changing operations must go through:

```text
InventoryEngine
```

### 10.2 Engine Methods

```python
class InventoryEngine:
    def receive_purchase(...): ...
    def stock_in(...): ...
    def stock_out(...): ...
    def adjust_stock(...): ...
    def reserve_for_sales_order(...): ...
    def release_reservation(...): ...
    def deduct_for_delivery(...): ...
    def transfer_stock(...): ...
    def receive_return(...): ...
    def restock_return(...): ...
    def move_to_qc(...): ...
    def mark_damaged(...): ...
    def mark_expired(...): ...
    def scrap_stock(...): ...
    def reconcile_stock(...): ...
```

### 10.3 Invariants

The engine must enforce:

- `quantity_on_hand >= 0`
- `quantity_reserved >= 0`
- `quantity_reserved <= quantity_on_hand`
- `quantity_available = quantity_on_hand - quantity_reserved - blocked_quantities`
- Stock cannot be deducted if not available unless explicitly allowed by a system setting.
- Every stock change creates a ledger entry.
- Every stock change creates an audit log.
- Important stock changes create notifications.
- Operations are idempotent when called with the same idempotency key.
- Stock rows are locked during mutation.
- Tenant boundaries are never crossed.

### 10.4 Idempotency

All business actions should accept an idempotency key:

- Confirm sales order.
- Receive purchase order.
- Complete stock transfer.
- Commit CSV import.
- Generate invoice.
- Email invoice.

Idempotency protects against duplicate API calls and repeated button clicks.

### 10.5 Locking

When mutating stock:

1. Lock `warehouse_stock` row.
2. Lock batch/serial rows if applicable.
3. Validate current availability.
4. Insert ledger entry.
5. Update projection.
6. Commit transaction.

### 10.6 Reconciliation

Provide a CLI and admin tool:

```bash
python -m app.cli.reconcile_inventory --tenant-id 1
```

Modes:

- dry-run.
- fix projection.
- export mismatch report.

Reconciliation compares ledger totals to warehouse stock projections.

---

## 11. Catalog Module Requirements

### 11.1 Product CRUD

Product should support create, update, archive, restore, search, filter, import, export, and duplicate detection.

### 11.2 Product Import

Import flow:

1. Upload CSV/XLSX.
2. Detect columns.
3. Map columns.
4. Validate rows.
5. Show preview.
6. Show duplicates.
7. Show new categories/brands/vendors.
8. User confirms.
9. Commit data.
10. Show result report.

### 11.3 Product Import Matching

Match priority:

1. SKU.
2. Barcode.
3. Vendor SKU.
4. Exact normalized name.
5. Fuzzy match suggestion only.

Never auto-merge fuzzy matches without user confirmation.

### 11.4 Product Import Row Status

- VALID_NEW.
- VALID_UPDATE.
- WARNING_DUPLICATE.
- INVALID_MISSING_SKU.
- INVALID_BAD_PRICE.
- INVALID_UNKNOWN_CATEGORY.
- INVALID_UNKNOWN_VENDOR.

---

## 12. Warehouse Module Requirements

### 12.1 Warehouses

Support create warehouse, archive warehouse, default warehouse, manager details, and warehouse status.

### 12.2 Warehouse Locations

Support:

- Create location tree.
- Location type.
- Location barcode.
- Active/inactive.
- Bin-level stock.
- Location detail page.
- Location stock list.
- Location movement history.

### 12.3 Location Types

- Receiving.
- Storage.
- Picking.
- Packing.
- Shipping.
- Returns.
- QC.
- Damaged.
- Expired.
- Scrap.
- Virtual.

### 12.4 Putaway Rules

Later V2 feature:

- Product category -> preferred location.
- Product -> preferred bin.
- Expiring product -> temperature-controlled area placeholder.
- High-volume product -> picking area.

---

## 13. Purchasing Module Requirements

### 13.1 Purchase Order

Purchase order statuses:

- DRAFT.
- ISSUED.
- PARTIALLY_RECEIVED.
- RECEIVED.
- CANCELLED.
- CLOSED.

### 13.2 Purchase Order Lines

Fields:

- Product.
- Vendor SKU.
- Warehouse.
- Expected location nullable.
- Quantity ordered.
- Quantity received.
- Quantity rejected.
- Unit price.
- Tax.
- Discount.
- Total.

### 13.3 Receiving

Receiving statuses:

- DRAFT.
- POSTED.
- CANCELLED.

Receiving must support:

- Partial receive.
- Over-receive setting.
- Rejected quantity.
- Damaged quantity.
- Batch entry.
- Expiry entry.
- Serial entry.
- Receiving location.
- Putaway task creation.

### 13.4 Vendor Bill

Vendor bill should be linked to purchase order, purchase receive, vendor, items, PDF, and email status.

---

## 14. Sales and Fulfillment Requirements

### 14.1 Sales Order

Future statuses:

- DRAFT.
- CONFIRMED.
- PARTIALLY_RESERVED.
- RESERVED.
- PARTIALLY_PACKED.
- PACKED.
- SHIPPED.
- DELIVERED.
- CANCELLED.
- CLOSED.

For early V2, continue existing simplified statuses but design services for future expansion.

### 14.2 Sales Reservation

On confirmation:

- Check stock availability.
- Reserve stock.
- Create reservation rows.
- Create ledger reservation entry.
- Generate pick task if fulfillment enabled.
- Notify low stock if threshold crossed.

### 14.3 Picking

Pick task:

- sales_order_id.
- warehouse_id.
- assigned_to.
- status: OPEN, IN_PROGRESS, COMPLETED, SHORT_PICKED, CANCELLED.
- pick lines: product, location, batch/serial, quantity required, quantity picked.

### 14.4 Packing

Package:

- package number.
- sales order.
- package lines.
- weight/dimensions.
- status.
- barcode.
- label placeholder.

### 14.5 Delivery

Delivery:

- shipped_at.
- delivered_at.
- carrier placeholder.
- tracking number placeholder.
- delivery status.

Delivery deduction rule:

- Reserved stock converts to physical deduction.
- If no reservation exists, block unless allowed by admin setting.

### 14.6 Invoice

Invoice should support draft, sent, paid, void, PDF download, email with attachment, tax/discount/total, customer billing address, and tenant company details.

---

## 15. Returns and Quality Module

### 15.1 Sales Return

Return statuses:

- REQUESTED.
- APPROVED.
- RECEIVED.
- UNDER_QC.
- RESTOCKED.
- REFUNDED.
- REJECTED.
- CANCELLED.

### 15.2 Return QC

QC result:

- GOOD_RESTOCK.
- DAMAGED.
- EXPIRED.
- WRONG_ITEM.
- REPAIR.
- SCRAP.
- RETURN_TO_VENDOR.

Return flow:

1. Create return request.
2. Receive returned item.
3. Move to QC location.
4. Perform QC.
5. Move stock to proper state/location.
6. Create refund/credit note placeholder.

---

## 16. Documents and Communication

### 16.1 Email

Email service should support signup verification, password reset, OTP, invoice email, bill email, low stock alert, purchase receive notification, and sales order status notification.

### 16.2 SMS Dev Outbox

Development SMS should not send real SMS. Use local outbox.

### 16.3 OTP

OTP should support email verification, phone verification, password reset, and optional login 2FA.

### 16.4 PDFs

PDFs:

- Invoice PDF.
- Bill PDF.
- Packing slip.
- Delivery note.
- Purchase order PDF.
- Stock adjustment report.
- Stock transfer document.

---

## 17. Reports

### 17.1 Inventory Reports

- Inventory summary.
- Warehouse stock.
- Location stock.
- Stock movement.
- Low stock.
- Product valuation.
- Batch expiry.
- Serial status.
- Damaged stock.
- Expired stock.
- QC hold stock.

### 17.2 Purchase Reports

- Purchase order summary.
- Vendor purchase summary.
- Pending receipts.
- Received vs ordered.
- Vendor bill status.

### 17.3 Sales Reports

- Sales order summary.
- Customer sales summary.
- Invoice status.
- Delivered vs pending.
- Returns summary.

### 17.4 Operational Reports

- Pick task performance.
- Stock adjustment report.
- Cycle count variance.
- Inventory reconciliation mismatches.
- Audit trail.

---

## 18. UI/UX Direction

The V2 UI should preserve the current repo’s previous visual direction and SaaS shell. Do not start a new visual identity. Instead, improve information architecture and real-world workflows.

### 18.1 UI Principles

- Keep the current layout style.
- Make pages workflow-first.
- Avoid overwhelming forms.
- Use step-by-step wizards for complex operations.
- Use scanner-friendly input fields.
- Show clear status badges.
- Show stock impact previews.
- Show confirmation dialogs before destructive or stock-changing actions.
- Show loading, empty, error, and success states on every page.
- Use detail pages with tabs: Overview, Lines/items, Stock impact, Documents, Activity, Audit log.

### 18.2 Important Screens

#### Product List

- Search by SKU/name/barcode.
- Filters for category, brand, vendor, status, tracking type.
- Import button.
- Export button.
- Low stock badge.
- Expiry tracking badge.
- Serial tracking badge.

#### Product Detail

Tabs:

- Overview.
- Stock by warehouse.
- Stock by location.
- Batches/lots.
- Serials.
- Transactions.
- Purchase history.
- Sales history.
- Audit.

#### Warehouse Detail

Tabs:

- Overview.
- Locations.
- Stock.
- Movements.
- Transfers.
- Users.
- Audit.

#### Receiving Screen

Scanner-friendly:

- Scan PO.
- Scan product.
- Enter/scan batch.
- Enter expiry.
- Enter serials.
- Enter accepted/damaged/rejected quantity.
- Confirm receive.

#### Pick Screen

Scanner-friendly:

- Shows bin.
- Shows product.
- Shows quantity.
- Requires scan confirmation.
- Supports short pick reason.

#### Return QC Screen

- Show returned item.
- Show condition checklist.
- Select QC result.
- Decide stock destination.

---

## 19. API Design Standards

### 19.1 General

- Use consistent REST paths.
- Use plural nouns.
- Use action endpoints only for workflow transitions.
- Use pagination on lists.
- Use filters consistently.
- Use status enums consistently.
- Use structured error responses.
- Use request IDs.
- Use idempotency keys for critical actions.

### 19.2 Error Response Shape

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Insufficient available stock for this product.",
    "details": {
      "product_id": 10,
      "warehouse_id": 2,
      "requested": 20,
      "available": 12
    },
    "request_id": "..."
  }
}
```

### 19.3 API Categories

- `/api/auth`
- `/api/tenants`
- `/api/users`
- `/api/catalog/products`
- `/api/catalog/categories`
- `/api/catalog/brands`
- `/api/vendors`
- `/api/customers`
- `/api/warehouses`
- `/api/warehouses/{id}/locations`
- `/api/inventory/stock`
- `/api/inventory/ledger`
- `/api/inventory/adjustments`
- `/api/inventory/transfers`
- `/api/purchase-orders`
- `/api/purchase-receives`
- `/api/bills`
- `/api/sales-orders`
- `/api/pick-tasks`
- `/api/packages`
- `/api/invoices`
- `/api/sales-returns`
- `/api/imports`
- `/api/reports`
- `/api/notifications`
- `/api/audit-logs`

---

## 20. Database Design Direction

### 20.1 Keep Existing Tables

Keep and improve:

- tenants.
- users.
- categories.
- brands.
- vendors.
- customers.
- warehouses.
- products.
- warehouse_stock.
- inventory_transactions.
- stock_transfers.
- purchase_orders.
- purchase_order_items.
- purchase_receives.
- purchase_receive_items.
- bills.
- sales_orders.
- sales_order_items.
- packages.
- package_items.
- invoices.
- sales_returns.
- sales_return_items.
- inventory_batches.
- inventory_serials.
- notifications.
- audit_logs.

### 20.2 Add V2 Tables

Add progressively:

- warehouse_locations.
- stock_ledger_entries.
- stock_reservations.
- stock_holds.
- stock_count_sessions.
- stock_count_lines.
- import_jobs.
- import_job_rows.
- supplier_catalog_items.
- product_unit_conversions.
- reorder_rules.
- pick_tasks.
- pick_task_lines.
- putaway_tasks.
- putaway_task_lines.
- return_qc_results.
- document_templates.
- domain_events.
- outbox_messages.
- idempotency_keys.
- number_sequences.

### 20.3 Indexing Rules

Every tenant-owned table should have:

- tenant_id index.
- tenant_id + status index where needed.
- tenant_id + created_at index for lists.
- tenant_id + natural key unique constraints where needed.

Stock tables should have:

- tenant_id + product_id.
- tenant_id + warehouse_id.
- tenant_id + location_id.
- tenant_id + batch_id.
- tenant_id + serial_id.
- tenant_id + reference_type + reference_id.

---

## 21. Frontend Architecture Direction

### 21.1 Frontend Structure

```text
frontend/src/
  app/
    routes.jsx
    providers.jsx
  api/
    client.js
    authApi.js
    catalogApi.js
    warehouseApi.js
    inventoryApi.js
    purchasingApi.js
    salesApi.js
    reportsApi.js
    importsApi.js
  modules/
    auth/
    dashboard/
    catalog/
    warehouses/
    inventory/
    purchasing/
    sales/
    fulfillment/
    returns/
    documents/
    reports/
    admin/
  components/
    common/
    layout/
    forms/
    tables/
    feedback/
    scanner/
  hooks/
  stores/
  utils/
  styles/
```

### 21.2 Frontend Rules

- Pages call hooks/services, not raw Axios everywhere.
- API clients are grouped by module.
- Components should be reusable.
- Tables should share a common DataTable.
- Forms should share validation patterns.
- Role checks should hide actions but backend remains source of permission truth.
- Stock truth is never calculated only on frontend.
- Every API call needs loading/error handling.
- Every destructive action needs confirmation.

---

## 22. Testing Strategy

### 22.1 Backend Tests

Must include:

- Auth tests.
- Tenant isolation tests.
- Role permission tests.
- Product CRUD tests.
- Warehouse CRUD tests.
- Inventory Engine tests.
- Stock ledger tests.
- Reservation tests.
- Purchase receive tests.
- Sales delivery tests.
- Return QC tests.
- Reconciliation tests.
- CSV import tests.
- PDF generation tests.
- Email/OTP/SMS tests.

### 22.2 Frontend Tests

Start with:

- Route smoke tests.
- Auth flow tests.
- Form validation tests.
- API contract tests.
- Role navigation tests.
- Data table tests.
- Empty/loading/error state tests.

### 22.3 E2E Tests

Use Playwright later.

Critical E2E flow:

1. Signup tenant.
2. Login.
3. Create warehouse.
4. Create product.
5. Import stock.
6. Create purchase order.
7. Receive purchase.
8. Create sales order.
9. Confirm and reserve.
10. Pick/pack/deliver.
11. Generate invoice.
12. Return item.
13. QC return.
14. Check reports and audit.

---

## 23. Progressive Implementation Roadmap

### Phase 0 — Documentation and Agent Rules

- Add this PRD as `docs/REAL_WORLD_V2_PRD.md`.
- Add `AGENTS.md`.
- Add `opencode.json`.
- Add project commands and rules.
- Do not implement product features yet.

### Phase 1 — Refactor for Separation of Concerns

- Move business logic out of routers.
- Introduce repositories.
- Introduce domain services.
- Create clear module boundaries.
- Keep API behavior stable.
- Add smoke tests.

### Phase 2 — Inventory Engine Hardening

- Centralize all stock mutation.
- Add idempotency.
- Add row locking.
- Add ledger entries.
- Add reconciliation CLI.
- Refactor existing stock flows.

### Phase 3 — Warehouse Location/Bin Model

- Add warehouse locations.
- Add location stock movement.
- Add location UI.
- Add barcode field for locations.

### Phase 4 — Product Import

- Add import jobs.
- Add import rows.
- Add preview/commit flow.
- Add product template download.
- Add validation report.

### Phase 5 — Batch, Expiry, Serial UI

- Make tracking visible in product detail.
- Add receiving UI for batch/expiry/serial.
- Add expiry alerts.
- Add serial status transitions.

### Phase 6 — Purchase Receiving and Putaway

- Improve receiving workflow.
- Add rejected/damaged quantity.
- Add receiving location.
- Add putaway tasks.

### Phase 7 — Sales Reservation, Picking, Packing

- Improve reservation flow.
- Add pick tasks.
- Add scanner-friendly picking.
- Add packing improvements.

### Phase 8 — Returns and QC

- Add return QC state.
- Add returned stock decision.
- Add damaged/scrap/quarantine stock.

### Phase 9 — Reports and Reconciliation

- Add location stock report.
- Add batch expiry report.
- Add serial report.
- Add stock variance report.
- Add reconciliation report.

### Phase 10 — UX and Production Polish

- Improve all states.
- Accessibility.
- Mobile scanner UX.
- Performance.
- Documentation.

---

## 24. Acceptance Criteria for V2 Foundation

The base is correct when:

- All stock mutations go through Inventory Engine.
- Every mutation writes stock ledger.
- Warehouse stock projections reconcile with ledger.
- Tenant users cannot access other tenants.
- Role permissions are enforced backend-side.
- Product import works with preview and validation.
- Warehouse locations exist.
- Batch/expiry/serial workflows exist at least for receiving and viewing.
- Sales confirmation reserves stock.
- Sales delivery deducts reserved stock.
- Purchase receiving increases stock.
- Returns go through QC before becoming sellable.
- Reports match actual stock projections.
- Audit logs exist for critical operations.
- UI keeps previous style but supports real workflows.
- Tests cover core invariants.
- AI agent can safely work module by module.

---

## 25. OpenCode / AI Agent Working Rules

### 25.1 Recommended Agent Process

1. Use Plan mode first.
2. Ask the agent to scan relevant modules.
3. Ask for an implementation plan.
4. Approve one small phase.
5. Build one phase.
6. Run tests.
7. Commit.
8. Move to the next phase.

Never ask the agent to "implement the whole V2" in one go.

### 25.2 Required Project Files for Agent Success

Add:

- `AGENTS.md`
- `opencode.json`
- `.opencode/commands/`
- `.opencode/tools/`
- `docs/REAL_WORLD_V2_PRD.md`
- `docs/ARCHITECTURE_DECISIONS.md`
- `docs/MODULE_BOUNDARIES.md`
- `docs/INVENTORY_ENGINE_SPEC.md`
- `docs/API_CONTRACT.md`
- `docs/MANUAL_TEST_CHECKLIST.md`

### 25.3 Suggested AGENTS.md Content

```markdown
# Warelyn Inventory Agent Rules

Warelyn Inventory is a multi-tenant real-world inventory SaaS.

Do not rewrite the app from scratch.

Always preserve tenant isolation.

Never let frontend become source of truth for stock.

All stock-changing behavior must go through backend Inventory Engine.

Use small commits.

Before coding:
1. Read docs/REAL_WORLD_V2_PRD.md.
2. Read docs/INVENTORY_ENGINE_SPEC.md if touching stock.
3. Read affected model/schema/service/router/frontend files.
4. Create a plan.

After coding:
1. Run backend compile/test where relevant.
2. Run frontend build where relevant.
3. Update docs if behavior changed.
4. Commit with clear message.

Do not work on AI assistant or subscription expansion unless explicitly instructed.
```

### 25.4 Suggested opencode.json

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "openai/gpt-5.5",
  "formatter": true,
  "permission": {
    "read": "allow",
    "grep": "allow",
    "glob": "allow",
    "webfetch": "allow",
    "websearch": "allow",
    "edit": "ask",
    "bash": {
      "*": "ask",
      "git status": "allow",
      "git diff*": "allow",
      "git branch*": "allow",
      "npm run build": "allow",
      "npm test": "allow",
      "pytest*": "allow",
      "python -m compileall*": "allow",
      "alembic current": "allow",
      "alembic upgrade head": "ask",
      "docker compose ps": "allow",
      "docker compose up*": "ask",
      "docker compose down*": "ask",
      "rm *": "deny",
      "git push*": "ask",
      "git reset*": "ask"
    }
  },
  "mcp": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp",
      "enabled": true
    },
    "gh_grep": {
      "type": "remote",
      "url": "https://mcp.grep.app",
      "enabled": false
    },
    "sentry": {
      "type": "remote",
      "url": "https://mcp.sentry.dev/mcp",
      "oauth": {},
      "enabled": false
    }
  }
}
```

### 25.5 Suggested Custom Tools

Create local OpenCode tools under:

```text
.opencode/tools/
```

Recommended tools:

1. `backend_check` — runs compileall and pytest.
2. `frontend_check` — runs npm build and optional tests.
3. `seed_import_check` — runs seed importer with fixed seed ZIP.
4. `inventory_reconcile` — runs reconciliation CLI.
5. `api_smoke` — runs a lightweight API smoke script.
6. `openapi_export` — exports FastAPI OpenAPI JSON.
7. `migration_check` — runs Alembic current/upgrade in a safe way.
8. `changed_files_summary` — summarizes changed files before commit.

### 25.6 Recommended MCP Tools

Use only a few MCP tools to avoid context overload.

1. **Context7 MCP** — use for FastAPI, SQLAlchemy, Alembic, React, Vite, Playwright, and library docs.
2. **Grep MCP** — use only when looking for examples from public GitHub code.
3. **Sentry MCP** — add later when the app is deployed and real errors exist.
4. **Database custom tool** — prefer a local project-specific tool with read-only/default-safe commands.
5. **Browser automation tool** — add later for E2E testing if OpenCode environment supports it.

Do not enable too many MCP servers globally.

---

## 26. Prompt To Give OpenCode First

```text
You are working on Warelyn Inventory V2.

First, do not code.

Read:
- README.md
- docs/PRD.md
- docs/REAL_WORLD_V2_PRD.md
- AGENTS.md

Then scan the current backend and frontend.

Create:
- docs/MODULE_BOUNDARIES.md
- docs/INVENTORY_ENGINE_SPEC.md
- docs/V2_IMPLEMENTATION_BACKLOG.md

The goal is to move Warelyn Inventory toward real-world inventory workflows while preserving the current UI style and applying the Warelyn brand identity.

Focus on:
- separation of concerns
- inventory engine
- stock ledger
- warehouse locations
- product import
- batch/expiry/serial
- purchase receiving
- sales reservation/picking/packing
- returns QC
- reporting

Do not implement yet.
Do not work on AI assistant.
Do not work on subscription expansion.
Only create analysis and implementation plan docs.
```

---

## 27. Prompt To Start Phase 1 Implementation

```text
Now implement Phase 1 only: separation of concerns.

Rules:
- Do not change UI.
- Do not add new product features.
- Do not rewrite the app.
- Keep API behavior stable.
- Move business logic out of routers where needed.
- Introduce repositories and domain services gradually.
- Add tests for changed behavior.
- Run backend tests and frontend build.
- Update STABILIZATION_PROGRESS.md.
- Commit with message: refactor backend module boundaries for v2 foundation
```

---

## 28. Final Principle

V2 should be built like this:

```text
Correct domain model
        ↓
Central stock engine
        ↓
Clean backend boundaries
        ↓
Reliable APIs
        ↓
Workflow-based UI
        ↓
Bulk import and scanner UX
        ↓
Reports and audit
        ↓
Advanced automation
```

Do not build advanced features on top of weak foundations. Fix the base first.
