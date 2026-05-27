# Phase 12: PRD Gap Audit & Roadmap Merge

**Audit date:** 2026-05-22
**Audit scope:** Complete codebase (backend + frontend + docs) against `docs/WARELYN_REAL_WORLD_V2_PRD.md` and user-requested features
**Phase 11 baseline:** 91 passing backend tests, 0 business tables added in Phase 10/11

---

## 1. Executive Summary

Warelyn Inventory has completed 12 backend phases through Phase 11. The core inventory workflow (auth, catalog, warehouse, inventory engine with ledger, product import, purchase receiving, batch/expiry/serial, sales reservation/fulfillment, pick/pack, returns QC, reports) is **fully implemented and tested** (91 tests).

However, a **deep audit reveals that 12 of the 12 user-requested features plus 8 additional PRD-required features are entirely missing** from the codebase. The codebase is strong on inventory operations but has **zero infrastructure for communication (email/SMS/notifications/toasts), documents (invoices/bills/PDFs), platform admin, settings, audit logs, events/jobs, or advanced operational workflows** (putaway, cycle counts, stock state expansion).

**Estimated coverage:** Core inventory workflows ~85% complete. Supporting infrastructure ~0–5% complete. Overall project ~40% complete against the full PRD scope.

---

## 2. Current Implementation Coverage by Module

| Module | Coverage | Status |
|--------|----------|--------|
| Auth/Tenant foundation | 90% | Missing email/phone verification, admin routes |
| Catalog (product, categories, brands, vendors, customers) | 95% | Product variants, unit conversion missing |
| Warehouses & locations | 90% | Location types all exist; putaway missing |
| Inventory Engine & ledger | 85% | Stock state expansion fields missing (blocked quantities) |
| Product import (CSV) | 85% | XLSX, column mapping UI, template download missing |
| Purchase orders & receiving | 90% | Bill/invoice link missing |
| Batch/expiry/serial tracking | 80% | FEFO, expiry jobs, stock state transitions missing |
| Sales orders & fulfillment | 85% | Invoices missing |
| Pick/pack | 80% | Mobile scanner, carrier integration missing |
| Returns QC & blocked stock | 80% | Full QC workflow exists |
| Reports (12 endpoints) | 90% | CSV export, audit log viewer missing |
| Reorder rules | 50% | Query-based only; no persisted `reorder_rules` table |
| **Super Admin** | **5%** | Seed/dependency exist; no routes, no admin pages |
| **Email verification** | **2%** | DB column only |
| **Phone/SMS verification** | **2%** | DB column only, no OTP, no SMS |
| **In-app notifications** | **0%** | Not implemented |
| **Toast notifications** | **0%** | Not implemented |
| **Invoices & bills** | **0%** | Not implemented |
| **PDF generation** | **0%** | Not implemented |
| **CSV export** | **0%** | Not implemented (import only) |
| **XLSX import/export** | **0%** | Not implemented |
| **Settings** | **0%** | Not implemented |
| **Email templates** | **0%** | Not implemented |
| **PDF templates** | **0%** | Not implemented |
| **Events/jobs/outbox** | **0%** | Not implemented |
| **Audit logs** | **0%** | Not implemented |
| **CI/deployment** | 70% | CI exists, deployment docs exist, production infra still needed |

---

## 3. PRD vs Implementation Matrix

| Feature | Source | Current Status | Evidence | Missing Pieces | Risk | Priority | Rec. Phase | Notes |
|---------|--------|---------------|----------|---------------|------|----------|------------|-------|
| Auth & tenant registration | PRD | Implemented end-to-end | `POST /api/auth/register` + tenant/user models + tests (18 auth tests) | Email verification not wired, phone verification not wired | Low | P0 | Complete | Foundation is solid; verification flow is separate feature |
| Super Admin & tenant roles | PRD | Partially implemented | `SUPER_ADMIN` enum, `require_super_admin()` dependency, seed script, seed test | **No admin routes/endpoints, no frontend admin, no tenant management API, no platform health** | High | P0 | Phase 13 | Backend seed works; no way for admin to do anything |
| Tenant management | PRD | Missing | No `tenants.py` router, no tenant CRUD API, no tenant list/detail endpoints | **Backend routes, service, frontend pages** | High | P1 | Phase 13 | Super admin needs tenant list, disable, usage view |
| Product catalog | PRD | Implemented end-to-end | `GET\|POST\|PATCH /api/catalog/products` + categories/brands/vendors/customers CRUD | Product variants not implemented; unit conversion not implemented | Low | P1 | Phase 18 | Core CRUD is solid |
| Product CSV import | PRD | Implemented | `POST /api/imports/products/upload`, validate, commit, preview, dropzone UI | No XLSX, no column mapping UI, no template download, no stock import | Low | P2 | Phase 16 | CSV only; validation/preview/commit exist |
| Product XLSX import | PRD | Missing | No XLSX library (openpyxl absent), no XLSX endpoints | **Backend, frontend, tests, docs** | Medium | P2 | Phase 16 | |
| Warehouses & locations | PRD | Implemented end-to-end | `GET\|POST\|PATCH /api/warehouses/{id}/locations` + all 12 location types | Putaway tasks missing; location stock movement history missing | Low | P1 | Phase 18 | |
| Inventory Engine | PRD | Implemented end-to-end | `InventoryEngine` with 12 methods, stock_in/out/adjust/reserve/release/deduct/transfer/return_restock/blocked/damaged/scrap | Stock state expansion columns missing (`quantity_in_transit`, `quantity_damaged`, etc.) | Low | P1 | Phase 18 | Core is solid; projection fields need expansion |
| Stock ledger | PRD | Implemented | `stock_ledger_entries` table, movement types, idempotency, reconciliation dry-run | All movement types not yet used (PURCHASE_RECEIVE, QC_HOLD, EXPIRE_OUT, etc. defined but unused) | Low | P2 | Phase 18 | |
| Purchase orders | PRD | Implemented end-to-end | 6 statuses, PO CRUD, submit/cancel/close workflows, partial receive, over-receive blocked | Vendor bills missing | Low | P1 | Phase 15 | |
| Purchase receiving | PRD | Implemented end-to-end | Receipt draft/commit/cancel, `InventoryEngine.stock_in()` via PURCHASE_RECEIPT ref | Putaway task creation on receive missing | Low | P2 | Phase 18 | |
| Vendor bills | PRD | Missing | No `Bill` model, no bill routes, no bill PDF, no link to PO/receipt | **Backend, frontend, tests, docs** | High | P1 | Phase 15 | |
| Sales orders | PRD | Implemented end-to-end | SO CRUD, confirm/cancel/close, reservation, explicit location allocation | Invoices missing; serial allocation only during picking (not during confirmation) | Low | P1 | Phase 15 | |
| Invoices | PRD | Missing | No `Invoice` model, no invoice routes, no invoice PDF | **Backend, frontend, tests, docs** | High | P1 | Phase 15 | |
| Pick/pack/fulfillment | PRD | Implemented end-to-end | Pick tasks, pick items, packages, package items, serial allocation, batch allocation | Mobile scanner missing; carrier shipment missing; delivery tracking missing | Low | P2 | Phase 18 | |
| Sales returns & QC | PRD | Implemented end-to-end | Return create/submit, QC inspect, 6 QC outcomes, restock/blocked/damaged/scrap/rejected | Refund/credit note missing; carrier return pickup missing | Low | P2 | Phase 18 | |
| Reports | PRD | Implemented | 12 report endpoints + operational dashboard | **CSV export missing**; report snapshot tables missing; charting missing | Medium | P2 | Phase 16 | |
| CSV export (reports) | PRD | Missing | Reports return JSON only; no CSV serialization | **Backend endpoints, frontend download buttons, tests** | Medium | P2 | Phase 16 | |
| Audit logs | PRD | Missing | No `AuditLog` model, no audit API, no audit UI | **Backend model, service, router, repository, frontend UI, tests** | High | P1 | Phase 13 | Repeatedly mentioned in INV engine spec but never implemented |
| Notifications | PRD | Missing | No `Notification` model, no notification service, no UI | **Backend model, service, router, frontend notification center, tests** | Medium | P2 | Phase 14 | |
| Email service | PRD | Missing | No `email_service.py`, no SMTP/Mailpit integration, no email sending | **Backend service, jobs, templates, tests** | High | P1 | Phase 14 | |
| SMS dev outbox | PRD | Missing | No `sms_service.py`, no SMS sending, no outbox | **Backend service, jobs, tests** | Medium | P2 | Phase 14 | |
| OTP service | PRD | Missing | No `otp_service.py`, no OTP generation/storage/validation/expiry | **Backend service, model, routes, tests** | Medium | P2 | Phase 14 | |
| PDF document service | PRD | Missing | No PDF library, no `pdf_service.py`, no PDF generation | **Backend service, templates, routes, frontend download, tests** | High | P1 | Phase 15 | |
| Document templates | PRD | Missing | No `DocumentTemplate` model, no template editing/preview | **Backend model, service, routes, frontend pages, tests** | Medium | P2 | Phase 17 | |
| Settings | PRD | Missing | No settings model/API/pages; only app config env vars exist | **Backend model, service, router, frontend pages, tests** | Medium | P2 | Phase 13 | Tenant settings, user preferences, inventory settings | 
| Events/jobs/outbox | PRD | Missing | No `events/` dir, no `jobs/` dir, no `cli/` dir, no outbox table | **Backend event bus, outbox, jobs (expire, reorder, email, cleanup), tests** | High | P2 | Phase 14 | Foundation needed before any async work |
| Number sequences | PRD | Missing | No `number_sequences` table; PO/SO/receipt numbers generated differently | **Backend model, service, migration, tests** | Low | P2 | Phase 15 | Should be unified document numbering |
| Reorder rules persistence | PRD | Partially implemented | Query-based reorder suggestions from `Product.reorder_level` | No `reorder_rules` table, no min/max/safety/lead time/auto-PO | Medium | P2 | Phase 18 | |
| Putaway tasks | PRD | Missing | No `putaway_tasks` table, no putaway workflow | **Backend model, service, migration, frontend UI, tests** | Medium | P3 | Phase 18 | |
| Cycle counts | PRD | Missing | No `stock_count_sessions/lines` tables, no reconciliation from counts | **Backend model, service, migration, frontend, tests** | Medium | P3 | Phase 18 | |
| Product variants | PRD | Missing | No `product_templates` or `product_variants` tables | **Backend models, migration, schemas, services, frontend, tests** | Medium | P3 | Phase 18 | |
| Unit conversion | PRD | Missing | No `product_unit_conversions` table | **Backend model, migration, service, tests** | Medium | P3 | Phase 18 | |
| Stock state expansion | PRD | Missing | `warehouse_stock` only has `quantity_on_hand/reserved/available`; blocked state columns absent | **Migration to add columns, engine updates, report updates, tests** | Medium | P2 | Phase 18 | quantity_in_transit, quantity_qc_hold, quantity_damaged, quantity_expired, quantity_quarantine |
| Delivery tracking | PRD | Missing | No carrier/shipment tracking fields on fulfillments | **Backend model fields, frontend UI** | Low | P3 | Phase 18 | |
| Supplier catalog import | PRD | Missing | No `supplier_catalog_items` table | **Backend model, migration, service, tests** | Low | P3 | Future | |

---

## 4. User Feature Merge Matrix

| # | User Feature | PRD Alignment | Current Status | Gap Analysis | Rec. Phase | Priority |
|---|-------------|--------------|---------------|-------------|-----------|----------|
| 1 | Super Admin screens — personalized, distinct from tenant user screens | PRD §6.1, §9.1 (tenants.py router) | Dependency exists, **no admin routes or UI** | Need: admin router, tenant management, platform health, audit viewer, personalized admin dashboard | Phase 13 | P0 |
| 2 | Phone number verification using SMS | PRD §16.2, §16.3 | DB column only | Need: `sms_service.py`, `otp_service.py`, verify endpoints, frontend screens, retry/expiry rules | Phase 14 | P1 |
| 3 | Email verification using email services | PRD §16.1, §16.3 | DB column only | Need: `email_service.py`, `otp_service.py`, verify endpoints, email templates, frontend screens | Phase 14 | P1 |
| 4 | In-app notifications | PRD §16 (notifications router) | Not implemented | Need: Notification model, service, routes, frontend notification center/dropdown, read/unread | Phase 14 | P2 |
| 5 | Toast notifications for success/error/backend messages | PRD §18.1 (UI feedback) | Not implemented | Need: Toast provider, global error mapping, consistent frontend toast on API responses | Phase 14 | P2 |
| 6 | Bill and invoice generation | PRD §13.4, §14.6 | Not implemented | Need: Invoice/Bill models, routes, services, statuses, link to orders/receipts, totals/tax/discount | Phase 15 | P1 |
| 7 | Bill/invoice PDF download using PDF templates | PRD §16.4 | Not implemented | Need: PDF library (weasyprint/reportlab), `pdf_service.py`, templates, download endpoints | Phase 15 | P1 |
| 8 | Report CSV export | PRD §17 (reports) | Not implemented | Need: CSV serialization on report endpoints, frontend download buttons, permission checks | Phase 16 | P2 |
| 9 | XLSX import | PRD §11.2 | Not implemented (CSV only) | Need: openpyxl, XLSX upload/parse, column mapping, reuse existing validate/preview/commit flow | Phase 16 | P2 |
| 10 | Settings page, frontend and backend | PRD §9.1 (general infra) | Not implemented | Need: Tenant settings model, user preferences, inventory settings, over-receive, notification prefs, frontend pages | Phase 13 | P2 |
| 11 | Custom email templates with preview and usage settings | PRD §16.1 | Not implemented | Need: Email template model, admin/tenant editor, preview, variable validation, usage in verification/invoice/bill | Phase 17 | P2 |
| 12 | Custom invoice/bill PDF templates with preview | PRD §16.4 | Not implemented | Need: Document template model, editor, preview, tenant logo/address/footer customization | Phase 17 | P2 |

---

## 5. Recommended Next Phases After Phase 11

The phase ordering is **correct but needs adjustment**: Audit logs (currently scattered between Phase 13 and Phase 18) should be pulled **earlier** since they are required by the InventoryEngine spec and are a P1 dependency for several workflows.

### Revised Phase Plan

| Phase | Name | Priority | Key Deliverables | Rationale |
|-------|------|----------|-----------------|-----------|
| **12** | **PRD Gap Audit + Roadmap** | P0 | This document | No code changes |
| **13** | **Super Admin Console + Settings Foundation + Audit Logs** | P0 | Admin router (tenant CRUD, platform health), AuditLog model+service+API, Settings model+API, frontend admin/settings pages | Foundation must exist before communication/document features |
| **14** | **Communication Foundation** | P1 | Email service (SMTP/Mailpit), SMS dev outbox, OTP service+model, email verification API+screens, phone verification API+screens, Notification model+API, in-app notification center, toast provider+global error mapping | All communication features depend on email/SMS/OTP foundation |
| **15** | **Documents Foundation** | P1 | Invoice model+workflow+schema, Bill model+workflow+schema, PDF service (weasyprint), PDF generation for invoice/bill, Invoice/bill download endpoints, Document numbering (number_sequences model), Purchase order PDF, Packing slip PDF | Depends on Phase 13 (settings) for tenant company details |
| **16** | **Import/Export Expansion** | P2 | Report CSV export (all 12 reports), Product CSV export, XLSX product import (openpyxl), Import column mapping, Import template download | Depends on Phase 15 for document numbering in exports |
| **17** | **Template Management** | P2 | Email template model+editor+preview, PDF template model+editor+preview, Invoice/bill template customization, Tenant branding settings (logo, address, footer) | Depends on Phase 14 (email) and Phase 15 (PDF) |
| **18** | **Operational Completion** | P2 | Putaway tasks, Cycle counts, Stock state expansion columns, Reorder rules persistence+table, Expiry background job (FEFO, isolation), Events/jobs/outbox infrastructure | Depends on Phase 14 (jobs) for background processing |

---

## 6. Recommended Immediate Next Phase: Phase 13

**Phase 13: Super Admin Console + Settings Foundation + Audit Logs**

This is the correct next phase for three reasons:
1. **Super Admin** is a P0 dependency — the platform has no way for an admin to manage tenants, view platform health, or perform any super admin operations despite having the seed and dependency ready.
2. **Settings foundation** is a prerequisite for Phases 14-17 (email config, SMS config, document settings, branding).
3. **Audit logs** are specified in the InventoryEngine rules as mandatory for stock mutations but are completely absent.

### Phase 13 Scope

**Backend:**
- Tenant management API (list, detail, disable, enable)
- Platform health endpoint
- AuditLog model + service + API
- Tenant settings model + API
- User preferences model + API
- Wire audit log creation into InventoryEngine stock mutation methods

**Frontend:**
- Admin layout (visually distinct from tenant layout)
- Tenant management page
- Platform health dashboard
- Audit log viewer
- Settings pages (tenant profile, user preferences)

**Explicitly excluded from Phase 13:**
- No stock mutation changes
- No communication features (email, SMS, OTP, notifications, toasts)
- No documents (invoices, bills, PDFs)
- No import/export expansion
- No template management
- No advanced operational workflows (putaway, cycle counts)

---

## 7. Features to Avoid for Now

Based on the PRD and current state, do **NOT** begin work on:

| Feature | Reason |
|---------|--------|
| AI assistant features | Explicitly excluded in AGENTS.md and PRD §7.2 |
| Subscription/billing/payment | Explicitly excluded; PRD §7.2 |
| Carrier integration (real) | Needs Phase 18 foundation; PRD §7.2 |
| Marketplace integration | PRD §7.2 out of scope |
| Native mobile app | PRD §7.2 out of scope |
| Full accounting ledger | PRD §7.2 out of scope |
| Multi-country tax compliance | PRD §7.2 out of scope |
| ERP manufacturing | PRD §7.2 out of scope |
| Supplier catalog import | No dependent features; can wait |
| Product variants | No dependent features; can wait |
| Unit conversion | No dependent features; can wait |

---

## 8. Risks and Dependencies

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Phase 14 (Communication) depends on email/SMTP infrastructure | Phase 14 blocked until email service works | Use Mailpit/MailHog for dev; keep SMTP config via settings from Phase 13 |
| Phase 15 (Documents) depends on PDF library choice | PDF generation blocked until library selected | WeasyPrint is recommended (HTML→PDF, uses existing HTML templates) |
| Phase 17 (Templates) depends on both Phase 14 and Phase 15 | Template management blocked until email/PDF work | Keep template model generic; can be defined in Phase 15 foundation |
| Phase 18 (jobs/outbox) depends on event infrastructure | Async processing blocked | Phase 18 can start with synchronous background tasks using FastAPI's `BackgroundTasks` before building full event bus |
| Audit log retrofitting | Existing InventoryEngine methods don't create audit logs | Add audit log calls to InventoryEngine as part of Phase 13; this touches engine.py (moderate risk) |
| Frontend gets too heavy | Many new pages could bloat the bundle | Keep code-splitting with React.lazy; each phase adds only its own page set |
| Backend test count drops | Adding features without tests will reduce quality | Each phase must include tests; current 91 test baseline must be maintained |

---

## 9. Files Likely to Change Per Future Phase

### Phase 13 — Super Admin + Settings + Audit Logs

**New files:**
- `backend/app/api/routers/admin.py`
- `backend/app/services/admin.py`
- `backend/app/repositories/admin.py`
- `backend/app/models/audit.py`
- `backend/app/schemas/admin.py`
- `backend/app/services/audit.py`
- `backend/app/repositories/audit.py`
- `backend/app/models/settings.py`
- `backend/app/schemas/settings.py`
- `frontend/src/pages/AdminDashboardPage.jsx`
- `frontend/src/pages/TenantsPage.jsx`
- `frontend/src/pages/AuditLogPage.jsx`
- `frontend/src/pages/SettingsPage.jsx`
- `frontend/src/layouts/AdminLayout.jsx`
- `frontend/src/pages/ProfilePage.jsx`

**Modified files:**
- `backend/app/domain/inventory/engine.py` (add audit log calls)
- `backend/app/api/router.py`
- `frontend/src/routes/AppRoutes.jsx`
- `frontend/src/components/SidebarNav.jsx`
- `frontend/src/styles/index.css`
- Alembic migration (new tables)

### Phase 14 — Communication Foundation

**New files:**
- `backend/app/services/email_service.py`
- `backend/app/services/sms_service.py`
- `backend/app/services/otp_service.py`
- `backend/app/models/otp.py`
- `backend/app/schemas/communication.py`
- `backend/app/api/routers/notifications.py`
- `backend/app/services/notifications.py`
- `backend/app/models/notifications.py`
- `backend/app/repositories/notifications.py`
- `backend/app/jobs/send_email.py`
- `backend/app/jobs/cleanup_otp.py`
- `frontend/src/components/ui/Toast.jsx`
- `frontend/src/components/NotificationCenter.jsx`
- `frontend/src/pages/VerifyEmailPage.jsx`
- `frontend/src/pages/VerifyPhonePage.jsx`

**Modified files:**
- `backend/app/api/routers/auth.py`
- `backend/app/services/auth.py`
- `backend/app/domain/inventory/engine.py`
- Alembic migration
- `frontend/src/layouts/MainLayout.jsx`
- `frontend/src/context/AuthContext.jsx`

### Phase 15 — Documents Foundation

**New files:**
- `backend/app/models/documents.py` (Invoice, Bill, DocumentTemplate, NumberSequence)
- `backend/app/schemas/documents.py`
- `backend/app/services/documents/pdf_service.py`
- `backend/app/api/routers/documents.py`
- `backend/app/repositories/documents.py`
- `frontend/src/pages/InvoicesPage.jsx`
- `frontend/src/pages/InvoiceDetailPage.jsx`
- `frontend/src/pages/BillsPage.jsx`
- `frontend/src/pages/BillDetailPage.jsx`
- `frontend/src/services/invoiceService.js`
- `frontend/src/services/billService.js`

**Modified files:**
- `backend/app/api/router.py`
- `backend/app/services/purchasing.py`
- `backend/app/services/sales.py`
- `requirements.txt` (add weasyprint/reportlab)
- Alembic migration
- `frontend/src/routes/AppRoutes.jsx`
- `frontend/src/components/SidebarNav.jsx`

### Phase 16 — Import/Export Expansion

**New files:**
- `frontend/src/pages/ExportReportPage.jsx`
- Import column mapping UI components

**Modified files:**
- `backend/app/api/routers/reports.py`
- `backend/app/services/reports.py`
- `backend/app/services/imports.py`
- `backend/app/schemas/reports.py`
- `requirements.txt` (add openpyxl)
- `frontend/src/pages/ProductImportPage.jsx`
- `frontend/src/components/imports/ImportPreviewTable.jsx`

### Phase 17 — Template Management

**New files:**
- `frontend/src/pages/EmailTemplateEditorPage.jsx`
- `frontend/src/pages/PdfTemplateEditorPage.jsx`
- Template preview components

**Modified files:**
- `backend/app/models/documents.py`
- `backend/app/services/documents/pdf_service.py`
- `backend/app/services/email_service.py`
- `frontend/src/pages/SettingsPage.jsx`

### Phase 18 — Operational Completion

**New files:**
- `backend/app/models/putaway.py`
- `backend/app/models/cycle_count.py`
- `backend/app/models/reorder_rules.py`
- `backend/app/events/event_bus.py`
- `backend/app/events/outbox.py`
- `backend/app/jobs/expire_batches.py`
- `backend/app/jobs/reorder_suggestions.py`
- `backend/app/domain/inventory/picking_strategy.py`
- Various services/repositories/schemas/frontend pages

**Modified files:**
- `backend/app/models/inventory.py` (warehouse_stock field expansion)
- `backend/app/domain/inventory/engine.py` (new methods for stock states)
- Alembic migration
- `backend/app/api/router.py`

---

## 10. Validation Strategy Per Future Phase

| Phase | Validation Commands | Expected Test Count | Additional Verification |
|-------|-------------------|-------------------|----------------------|
| Phase 13 | `cd backend && .venv/bin/python -m compileall app && .venv/bin/python -m pytest` | 91 + ~15 = ~106 | Manual: create super admin, list tenants via admin API, view audit log, verify admin UI distinct from tenant UI |
| Phase 14 | `cd backend && .venv/bin/python -m pytest` | ~106 + ~20 = ~126 | Manual: register user, check OTP sent, verify email, verify phone, check in-app notification appears, toast shows on API error |
| Phase 15 | `cd backend && .venv/bin/python -m pytest` | ~126 + ~25 = ~151 | Manual: confirm sales order, generate invoice, download PDF, create PO, generate bill, verify document number sequence |
| Phase 16 | `cd backend && .venv/bin/python -m pytest` | ~151 + ~15 = ~166 | Manual: export each report as CSV, upload XLSX product import, verify column mapping, verify template download |
| Phase 17 | `cd backend && .venv/bin/python -m pytest` | ~166 + ~15 = ~181 | Manual: edit email template, preview with variables, edit invoice PDF template, preview with tenant data, change logo |
| Phase 18 | `cd backend && .venv/bin/python -m pytest` | ~181 + ~30 = ~211 | Manual: create putaway task, cycle count, verify stock state columns populate, reorder rule generates suggestion, expiry job runs |

---

## 11. Phase Ordering Confirmation

**Your recommended ordering is correct** with one caveat:

**Phase 13 must include audit logs** (your original plan had audit logs scattered between Phase 13 and Phase 18). Since the InventoryEngine spec requires audit logs for ALL stock mutations and the engine is already complete, this is a critical gap that should be resolved in **Phase 13**, not deferred to Phase 18.

### Final Recommended Phase Sequence

```
Phase 12 → PRD Gap Audit + Roadmap Merge                          ← YOU ARE HERE
Phase 13 → Super Admin Console + Settings Foundation + Audit Logs  ← NEXT
Phase 14 → Communication Foundation (email, SMS, OTP, notifications, toasts, verification)
Phase 15 → Documents Foundation (invoices, bills, PDFs, document numbering)
Phase 16 → Import/Export Expansion (CSV export, XLSX import, column mapping, template download)
Phase 17 → Template Management (email/PDF templates, preview, tenant branding)
Phase 18 → Operational Completion (putaway, cycle counts, stock state expansion, reorder rules, events/jobs/outbox)
```

All phases after Phase 12 are estimated at **0% implementation** based on the codebase audit.
