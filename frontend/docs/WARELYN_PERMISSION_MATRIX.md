# Warelyn Permission Matrix

Generated: 2026-05-28

## Role Definitions

| Role | Scope | Description |
|------|-------|-------------|
| SUPER_ADMIN | Platform | Full platform access, tenant management |
| TENANT_ADMIN | Tenant | Full tenant access, user/settings management |
| INVENTORY_MANAGER | Tenant | Full inventory, catalog, warehouse, reports |
| PURCHASE_STAFF | Tenant | Purchase orders, receipts, bills |
| SALES_STAFF | Tenant | Sales orders, fulfillment, invoices, returns |
| VIEWER | Tenant | Read-only access to assigned modules |

## Frontend Route Access

| Route | TENANT_ADMIN | INVENTORY_MANAGER | PURCHASE_STAFF | SALES_STAFF | VIEWER |
|-------|:---:|:---:|:---:|:---:|:---:|
| /dashboard | Y | Y | Y | Y | Y |
| /my-tasks | Y | Y | Y | Y | - |
| /catalog/products | Y | Y | Y | Y | Y |
| /catalog/products/new | Y | Y | - | - | - |
| /catalog/products/import | Y | Y | - | - | - |
| /catalog/categories | Y | Y | Y | Y | Y |
| /catalog/categories/new | Y | Y | - | - | - |
| /catalog/brands | Y | Y | Y | Y | Y |
| /catalog/brands/new | Y | Y | - | - | - |
| /catalog/vendors | Y | Y | Y | Y | Y |
| /catalog/vendors/new | Y | Y | - | - | - |
| /catalog/customers | Y | Y | Y | Y | Y |
| /catalog/customers/new | Y | Y | - | - | - |
| /warehouses | Y | Y | - | - | Y |
| /warehouses/new | Y | Y | - | - | - |
| /warehouses/:id | Y | Y | - | - | Y |
| /purchases | Y | Y | Y | - | Y |
| /purchases/new | Y | Y | Y | - | - |
| /purchases/:id | Y | Y | Y | - | Y |
| /purchases/:id/receive | Y | Y | Y | - | - |
| /purchase-receipts | Y | Y | Y | - | Y |
| /purchase-receipts/new | Y | Y | Y | - | - |
| /purchase-receipts/:id | Y | Y | Y | - | Y |
| /bills | Y | Y | Y | - | Y |
| /bills/:id | Y | Y | Y | - | Y |
| /sales | Y | Y | - | Y | Y |
| /sales/new | Y | Y | - | Y | - |
| /sales/:id | Y | Y | - | Y | Y |
| /sales/:id/pick | Y | Y | - | Y | - |
| /sales/:id/package | Y | Y | - | Y | - |
| /sales/:id/fulfill | Y | Y | - | Y | - |
| /invoices | Y | Y | - | Y | Y |
| /invoices/:id | Y | Y | - | Y | Y |
| /returns | Y | Y | - | Y | Y |
| /returns/new | Y | Y | - | Y | - |
| /returns/:id | Y | Y | - | Y | Y |
| /returns/:id/inspect | Y | Y | - | Y | - |
| /returns/qc | Y | Y | - | Y | - |
| /pick-tasks | Y | Y | - | Y | - |
| /pick-tasks/:id | Y | Y | - | Y | - |
| /packages | Y | Y | - | Y | - |
| /packages/:id | Y | Y | - | Y | - |
| /sales-fulfillments | Y | Y | - | Y | - |
| /sales-fulfillments/:id | Y | Y | - | Y | - |
| /reports/* | Y | Y | - | - | Y |
| /settings | Y | Y | Y | Y | Y |
| /settings/users | Y | - | - | - | - |
| /settings/email-templates | Y | - | - | - | - |
| /settings/pdf-templates | Y | - | - | - | - |

## Frontend Action Access (Mutation Buttons)

| Page | Action | TENANT_ADMIN | INVENTORY_MANAGER | PURCHASE_STAFF | SALES_STAFF | VIEWER |
|------|--------|:---:|:---:|:---:|:---:|:---:|
| Invoice Detail | Send | Y | Y | - | Y | - |
| Invoice Detail | Mark paid | Y | Y | - | Y | - |
| Invoice Detail | Void | Y | Y | - | Y | - |
| Invoice Detail | Download PDF | Y | Y | - | Y | Y |
| Bill Detail | Send | Y | Y | Y | - | - |
| Bill Detail | Mark paid | Y | Y | Y | - | - |
| Bill Detail | Void | Y | Y | Y | - | - |
| Bill Detail | Download PDF | Y | Y | Y | - | Y |

## Backend Endpoint Protection

All 127 backend endpoints use `require_roles()` dependency injection. No unguarded mutation endpoints found during audit.

## Fixes Applied (Phase 8)

1. **DocumentsPages.jsx — InvoiceDetailPage**: Added `mayWrite` guard. Send, Mark paid, and Void buttons hidden from VIEWER.
2. **DocumentsPages.jsx — BillDetailPage**: Added `mayWrite` guard. Send, Mark paid, and Void buttons hidden from VIEWER.
3. **AppRoutes.jsx — Catalog form routes**: Added `RoleGuard` with `['TENANT_ADMIN', 'INVENTORY_MANAGER']` to:
   - `/catalog/products/new`
   - `/catalog/products/import`
   - `/catalog/categories/new`
   - `/catalog/brands/new`
   - `/catalog/vendors/new`
   - `/catalog/customers/new`

## Remaining Notes

- PDF download buttons remain visible to VIEWER (read-only action, not a mutation).
- Navigation items already filter by role via `navigation.js` role arrays — no sidebar leakage.
- Backend enforces RBAC independently; frontend guards are defense-in-depth UX protection.
