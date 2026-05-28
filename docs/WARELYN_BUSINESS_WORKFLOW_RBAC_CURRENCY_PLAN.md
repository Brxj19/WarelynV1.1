# Warelyn Business Workflow, RBAC, Feature Gap, Claude Skills, and Currency Implementation Plan

**Project:** Warelyn Inventory SaaS  
**Purpose:** Deep business-context planning for a multi-role inventory SaaS platform.  
**Focus areas:** Business model, role-based workflow handoff, missing features, RBAC alignment, Claude Code skills/plugins, and currency selection implementation across the application.

---

## 1. Executive Summary

Warelyn already has many strong SaaS building blocks: authentication, tenant settings, inventory modules, sales and purchase modules, documents, templates, notifications, reports, empty states, app loading, and role-based concepts.

However, the main weakness is that the project is currently **module-rich but not fully workflow-aware**.

A real multi-role SaaS platform should not only show separate screens for products, sales, purchases, invoices, bills, warehouses, templates, users, and reports. It should also answer this business question:

> When one role completes a workflow step, does the next step automatically move to the correct concerned role?

Right now, Warelyn needs stronger planning around:

- Role ownership of each workflow step.
- Automatic next-step task assignment.
- Notifications to the correct role or user.
- Dashboards that show role-specific pending work.
- Frontend route access matching backend API access.
- Business-event-driven workflow transitions.
- Currency selection and consistent money display across the whole app.

The next major product phase should be called:

> **Workflow-Aware SaaS Maturity Phase**

---

## 2. Current Role Model

Warelyn currently uses these roles:

```text
SUPER_ADMIN
TENANT_ADMIN
INVENTORY_MANAGER
SALES_STAFF
PURCHASE_STAFF
VIEWER
```

### Intended role meaning

| Role | Intended Business Responsibility |
|---|---|
| `SUPER_ADMIN` | Platform-level administration across tenants. |
| `TENANT_ADMIN` | Company-level administration, users, settings, templates, approvals, reports. |
| `INVENTORY_MANAGER` | Products, warehouses, stock, transfers, adjustments, picking, putaway, inventory reports. |
| `SALES_STAFF` | Customers, sales orders, invoices, sales returns, customer communication. |
| `PURCHASE_STAFF` | Suppliers, purchase orders, receipts, bills, procurement operations. |
| `VIEWER` | Read-only access to allowed screens and reports. |

---

## 3. Main Business-Context Problems

### 3.1 Roles exist, but workflow ownership is incomplete

The system has roles, but each business step needs a clear owner.

For example:

```text
Sales order confirmed
        ↓
Who receives the next task?
        ↓
Inventory Manager should receive picking/reservation task
```

This kind of automatic handoff is not yet fully mature.

### 3.2 The app behaves more like separate modules than one connected workflow

Current modules may exist separately:

```text
Products
Warehouses
Sales Orders
Invoices
Purchase Orders
Bills
Receipts
Reports
Templates
Users
Notifications
```

But real SaaS workflow should behave like:

```text
Business action happens
        ↓
Domain event is created
        ↓
Workflow rule decides the next step
        ↓
Task is assigned to role/user
        ↓
Notification is sent
        ↓
Next role sees it in dashboard/My Tasks
```

### 3.3 There is no central workflow task inbox

Warelyn needs a common task system:

```text
My Tasks
Assigned to My Role
Pending Approval
Overdue Tasks
Completed Tasks
```

Without this, users must manually check different modules to know what to do next.

### 3.4 Frontend role access and backend permissions can drift apart

A common SaaS problem is:

```text
Frontend shows a screen/action
        ↓
User clicks
        ↓
Backend returns 403
```

This means the frontend role matrix and backend permission matrix are not aligned.

Warelyn needs one shared permission map and audit.

### 3.5 Notifications are not enough unless they are tied to business events

Generic notifications are useful, but workflow notifications must be tied to domain events.

Examples:

```text
Sales order confirmed -> notify Inventory Manager
Receipt committed -> notify Inventory Manager for putaway
Putaway completed -> notify Purchase Staff to record bill
Low stock detected -> notify Purchase Staff or Tenant Admin
Return submitted -> notify Inventory Manager for QC
```

### 3.6 Reports should be role-specific

Different users need different report views.

| Role | Report Focus |
|---|---|
| Tenant Admin | Full tenant business overview. |
| Inventory Manager | Stock, valuation, low stock, transfers, adjustments. |
| Sales Staff | Sales orders, invoices, customers, receivables. |
| Purchase Staff | Purchase orders, suppliers, bills, payables. |
| Viewer | Read-only summaries. |

---

## 4. Recommended Workflow Architecture

### 4.1 Core workflow pattern

Every major business action should follow this pattern:

```text
User performs action
        ↓
Backend validates permission
        ↓
Entity status changes
        ↓
Domain event is created
        ↓
Workflow task is created if next step exists
        ↓
Task is assigned to role/user
        ↓
Notification is sent
        ↓
Audit log is written
        ↓
Next role sees the task in dashboard/My Tasks
```

### 4.2 Suggested new backend tables

#### `workflow_events`

Stores business events.

```text
id
tenant_id
event_type
entity_type
entity_id
actor_user_id
payload_json
created_at
```

Example event types:

```text
SALES_ORDER_CONFIRMED
PURCHASE_ORDER_SUBMITTED
RECEIPT_COMMITTED
PUTAWAY_COMPLETED
INVOICE_SENT
BILL_RECORDED
LOW_STOCK_DETECTED
RETURN_SUBMITTED
```

#### `workflow_tasks`

Stores next-step tasks.

```text
id
tenant_id
workflow_type
entity_type
entity_id
step_key
title
description
assigned_role
assigned_to_user_id
status
priority
action_url
created_by
completed_by
created_at
due_at
completed_at
metadata_json
```

Possible statuses:

```text
OPEN
IN_PROGRESS
BLOCKED
COMPLETED
CANCELLED
```

#### `workflow_rules`

Configurable rules for next-step generation.

```text
id
tenant_id
workflow_type
trigger_event
next_step_key
assigned_role
is_active
conditions_json
created_at
updated_at
```

#### `workflow_approvals`

Approval engine for high-value or risky actions.

```text
id
tenant_id
entity_type
entity_id
approval_type
requested_by
approver_role
approver_user_id
status
reason
created_at
approved_at
rejected_at
```

---

## 5. Sales Workflow Planning

### 5.1 Ideal sales workflow

```text
Customer created
        ↓
Sales order draft
        ↓
Sales Staff confirms/submits order
        ↓
Inventory reservation check
        ↓
Pick task assigned to Inventory Manager
        ↓
Picking completed
        ↓
Packing task created
        ↓
Packing completed
        ↓
Fulfillment/shipping task completed
        ↓
Invoice task created
        ↓
Invoice generated and sent
        ↓
Payment status tracked
        ↓
Return flow if needed
```

### 5.2 Required role handoff

| Step | Actor Role | Next Step | Next Role |
|---|---|---|---|
| Create customer | Sales Staff / Tenant Admin | Create sales order | Sales Staff |
| Confirm sales order | Sales Staff | Reserve/pick stock | Inventory Manager |
| Pick order | Inventory Manager | Pack order | Inventory Manager or Warehouse Staff if added later |
| Pack order | Inventory Manager | Fulfill/ship | Sales Staff / Inventory Manager |
| Fulfill order | Sales Staff / Inventory Manager | Create invoice | Sales Staff |
| Send invoice | Sales Staff | Track payment | Sales Staff / Tenant Admin |
| Return requested | Sales Staff | Return QC | Inventory Manager |

### 5.3 Missing maturity

Warelyn should ensure:

- Sales order confirmation automatically creates a pick task.
- Pick task appears in Inventory Manager dashboard.
- Inventory Manager gets notification.
- After picking, packing task is created.
- After fulfillment, invoice creation task is created.
- Viewer never sees action buttons.
- Purchase Staff does not get sales-specific action buttons.

---

## 6. Purchase Workflow Planning

### 6.1 Ideal purchase workflow

```text
Supplier created
        ↓
Purchase order draft
        ↓
Purchase Staff submits PO
        ↓
Approval if required
        ↓
Purchase order sent/confirmed
        ↓
Goods received
        ↓
Receiving stock enters staging
        ↓
Putaway task assigned to Inventory Manager
        ↓
Putaway completed
        ↓
Bill task created
        ↓
Bill recorded
        ↓
Payment tracked
```

### 6.2 Required role handoff

| Step | Actor Role | Next Step | Next Role |
|---|---|---|---|
| Create supplier | Purchase Staff / Tenant Admin | Create purchase order | Purchase Staff |
| Submit PO | Purchase Staff | Approval if required | Tenant Admin |
| Approve PO | Tenant Admin | Send/order from supplier | Purchase Staff |
| Receive goods | Purchase Staff / Inventory Manager | Putaway | Inventory Manager |
| Complete putaway | Inventory Manager | Record bill | Purchase Staff |
| Record bill | Purchase Staff | Payment tracking | Tenant Admin / Purchase Staff |

### 6.3 Missing maturity

Warelyn should ensure:

- PO amount thresholds can trigger approval.
- Receipt commit creates putaway task.
- Putaway completion creates bill-recording task.
- Low stock can generate reorder suggestion.
- Reorder suggestion can generate purchase order draft.
- Sales Staff does not see purchase creation actions.

---

## 7. Inventory Workflow Planning

### 7.1 Ideal inventory workflow

```text
Product created
        ↓
Warehouse/location created
        ↓
Stock received or adjusted
        ↓
Stock movements tracked
        ↓
Transfers between warehouses
        ↓
Cycle count / reconciliation
        ↓
Low stock detection
        ↓
Reorder suggestion
        ↓
Purchase workflow starts
```

### 7.2 Required role ownership

| Step | Primary Role |
|---|---|
| Product creation | Inventory Manager / Tenant Admin |
| Category creation | Inventory Manager / Tenant Admin |
| Warehouse creation | Inventory Manager / Tenant Admin |
| Stock transfer | Inventory Manager |
| Stock adjustment | Inventory Manager, maybe Tenant Admin approval |
| Cycle count | Inventory Manager |
| Low stock review | Inventory Manager / Purchase Staff |
| Reorder creation | Purchase Staff |

### 7.3 Missing maturity

Warelyn should add:

- Approval for large stock adjustments.
- Low-stock tasks.
- Reorder suggestions assigned to Purchase Staff.
- Inventory dashboard tasks.
- Stock valuation reports with selected currency.

---

## 8. Returns Workflow Planning

### 8.1 Sales return flow

```text
Return requested
        ↓
Sales Staff records return request
        ↓
Inventory Manager performs QC
        ↓
Stock disposition selected
        ↓
Refund/credit note task if implemented
        ↓
Inventory updated
```

### 8.2 Purchase return flow

```text
Damaged/wrong supplier goods identified
        ↓
Inventory Manager flags goods
        ↓
Purchase Staff creates supplier return
        ↓
Supplier return processed
        ↓
Bill adjustment/credit tracked
```

### 8.3 Missing maturity

- Return QC should be assigned to Inventory Manager.
- Refund/credit should be assigned to Sales Staff/Tenant Admin.
- Supplier return should be assigned to Purchase Staff.
- Backend and frontend route access must match.

---

## 9. Documents and Billing Workflow

### 9.1 Invoice ownership

Invoices are sales-side documents.

Allowed roles should be:

```text
TENANT_ADMIN
SALES_STAFF
```

Optional read-only access:

```text
VIEWER
```

### 9.2 Bill ownership

Bills are purchase-side documents.

Allowed roles should be:

```text
TENANT_ADMIN
PURCHASE_STAFF
```

Optional read-only access:

```text
VIEWER
```

### 9.3 Template management ownership

Template management should be admin-level.

Allowed roles:

```text
TENANT_ADMIN
```

Optional:

```text
SUPER_ADMIN for platform/system templates
```

### 9.4 Missing maturity

- Invoice/bill template permissions should be separated by purpose.
- Invoice email templates should not be assignable to bill emails.
- Bill PDF templates should not be assignable to invoices.
- Invoice currency should snapshot at creation.
- Bill currency should snapshot at creation.

---

## 10. Business Partner Model Problem

The word “vendor” can become confusing because a vendor may also buy from someone else.

Wrong model:

```text
Vendor has vendor
Vendor's vendor has vendor
```

Better model:

```text
Tenant / Company
        +
Business Partner Relationship
```

A company can be:

```text
Supplier to one tenant
Customer of another tenant
Both supplier and customer for a third tenant
```

### Recommended tables for future phase

#### `tenant_partner_links`

```text
id
tenant_id
partner_tenant_id
relationship_type
status
visibility_level
created_at
updated_at
```

Relationship types:

```text
SUPPLIER
CUSTOMER
BOTH
```

#### `partner_shared_products`

```text
id
owner_tenant_id
product_id
is_visible
shared_name
shared_sku
shared_price
minimum_order_quantity
lead_time_days
stock_visibility_level
share_warehouse_location
created_at
updated_at
```

### Important security rule

Do not expose upstream supplier chains.

Example:

```text
A buys from B
B buys from C
```

Company A should not automatically see Company C. A only sees B’s shared catalog if B allows it.

---

## 11. Approval Workflow Gaps

Warelyn should support approvals for important business actions.

Recommended approval scenarios:

```text
Purchase order above threshold
Large discount on sales order
Large stock adjustment
Stock write-off
Bill payment approval
Return refund approval
User role change
Template publishing
Currency change after transactions exist
```

Suggested table:

```text
approval_rules
approval_requests
approval_steps
```

Example rule:

```text
If purchase_order.total_amount > 50000
then approval_required = true
assigned_role = TENANT_ADMIN
```

---

## 12. RBAC Maturity Plan

### 12.1 Create a central permission matrix

Backend:

```text
backend/app/core/permissions.py
```

Frontend:

```text
frontend/src/lib/permissions.js
```

### 12.2 Use action-based permissions

Instead of checking only screens, define actions:

```text
CREATE_PRODUCT
UPDATE_PRODUCT
VIEW_PRODUCT
CREATE_CUSTOMER
CREATE_SUPPLIER
CREATE_SALES_ORDER
CONFIRM_SALES_ORDER
PICK_ORDER
PACK_ORDER
CREATE_INVOICE
SEND_INVOICE
CREATE_PURCHASE_ORDER
APPROVE_PURCHASE_ORDER
RECEIVE_STOCK
COMPLETE_PUTAWAY
CREATE_BILL
MARK_BILL_PAID
MANAGE_USERS
MANAGE_TEMPLATES
MANAGE_SETTINGS
VIEW_REPORTS
VIEW_AUDIT_LOGS
```

### 12.3 Required checks

For every route/API/action:

```text
Is the frontend route guarded?
Is the sidebar item hidden for unauthorized roles?
Is the action button hidden or disabled?
Does the backend reject unauthorized access?
Does the test suite verify the rule?
```

---

## 13. Role-Based Dashboard Plan

### Tenant Admin dashboard

Should show:

```text
Pending approvals
Users count
Low stock summary
Unpaid invoices
Unpaid bills
Template status
Recent activity
Notifications
Audit events
```

### Inventory Manager dashboard

Should show:

```text
Pick tasks
Putaway tasks
Stock transfers
Inventory adjustments
Low stock
Cycle counts
Blocked/damaged stock
```

### Sales Staff dashboard

Should show:

```text
Open sales orders
Invoices pending send
Overdue invoices
Customers
Returns
Sales performance
```

### Purchase Staff dashboard

Should show:

```text
Open purchase orders
Pending receipts
Bills pending payment
Supplier performance
Reorder suggestions
```

### Viewer dashboard

Should show:

```text
Read-only summaries
No create/edit/delete/send buttons
```

---

## 14. Feature Gaps Not Properly Implemented Yet

### High-priority gaps

```text
Central workflow task engine
Role-based My Tasks inbox
Business-event notifications
Workflow handoff automation
Unified backend/frontend permission matrix
Approval workflow
Role-based dashboards
Currency selector and app-wide money formatting
Template purpose validation
Tenant-scoped user CRUD hardening
```

### Medium-priority gaps

```text
Business partner network
Shared supplier catalog
PO approval thresholds
Stock adjustment approvals
Reorder suggestions
Auto-generated tasks from low stock
Audit log coverage
Email notification templates for workflow events
```

### UI/UX gaps

```text
Role-specific dashboards
Role-specific empty states
Consistent loading states
Consistent error states
Currency-aware money display
Action buttons should disappear for unauthorized roles
Workflow progress indicators
Task inbox filters
```

---

# 15. Currency Selection and Implementation Throughout Warelyn

## 15.1 Current currency state observed in the project

Warelyn already has partial currency support:

- `TenantSettings.currency` exists in the backend and defaults to `USD`.
- Invoice and bill document models have a `currency` field.
- Settings UI currently has a plain text `Currency` input.
- Frontend `formatMoney()` currently formats numbers but does not show a currency symbol/code.
- Product cost and selling price fields exist, but they are not clearly tied to the tenant currency in UI.
- PDF/email templates currently output raw numeric amounts in many places.

So the app has a base currency field, but it is not yet implemented consistently across the product.

## 15.2 Business decision: base currency first, multi-currency later

For the next implementation phase, Warelyn should support **single base currency per tenant**.

This means:

```text
Each tenant chooses one operating currency.
All product prices, sales documents, purchase documents, reports, and dashboard money values use that tenant currency.
```

Do not implement exchange rates in this phase.

Future multi-currency can be added later.

## 15.3 Currency selection UX

Replace the plain text currency input with a dropdown selector.

Recommended location:

```text
Settings -> Company / Organization -> Currency
```

Recommended default:

```text
INR for India-focused tenant onboarding
USD as fallback system default
```

Supported initial currencies:

```text
INR - Indian Rupee - ₹
USD - US Dollar - $
EUR - Euro - €
GBP - British Pound - £
AED - UAE Dirham - د.إ
AUD - Australian Dollar - A$
CAD - Canadian Dollar - C$
SGD - Singapore Dollar - S$
JPY - Japanese Yen - ¥
```

## 15.4 Currency selector component

Create:

```text
frontend/src/components/ui/CurrencySelect.jsx
```

Example API:

```jsx
<CurrencySelect
  label="Currency"
  value={form.currency}
  onChange={(value) => setForm((current) => ({ ...current, currency: value }))}
  disabled={!editing}
/>
```

The dropdown should show:

```text
₹ INR - Indian Rupee
$ USD - US Dollar
€ EUR - Euro
£ GBP - British Pound
```

## 15.5 Currency metadata registry

Create:

```text
frontend/src/lib/currencies.js
```

Example:

```js
export const SUPPORTED_CURRENCIES = [
  { code: 'INR', symbol: '₹', name: 'Indian Rupee', locale: 'en-IN', fractionDigits: 2 },
  { code: 'USD', symbol: '$', name: 'US Dollar', locale: 'en-US', fractionDigits: 2 },
  { code: 'EUR', symbol: '€', name: 'Euro', locale: 'de-DE', fractionDigits: 2 },
  { code: 'GBP', symbol: '£', name: 'British Pound', locale: 'en-GB', fractionDigits: 2 },
  { code: 'AED', symbol: 'د.إ', name: 'UAE Dirham', locale: 'en-AE', fractionDigits: 2 },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar', locale: 'en-AU', fractionDigits: 2 },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar', locale: 'en-CA', fractionDigits: 2 },
  { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar', locale: 'en-SG', fractionDigits: 2 },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen', locale: 'ja-JP', fractionDigits: 0 },
];

export function getCurrencyMeta(code) {
  return SUPPORTED_CURRENCIES.find((currency) => currency.code === code) ?? SUPPORTED_CURRENCIES[1];
}
```

## 15.6 Update frontend money formatter

Current `formatMoney()` should become currency-aware.

Recommended update:

```js
import { getCurrencyMeta } from './currencies';

export function formatMoney(value, options = {}) {
  if (value === null || value === undefined || value === '') return '-';

  const number = Number(value);
  if (Number.isNaN(number)) return String(value);

  const currencyCode = options.currency ?? 'USD';
  const meta = getCurrencyMeta(currencyCode);

  return new Intl.NumberFormat(meta.locale, {
    style: 'currency',
    currency: meta.code,
    minimumFractionDigits: options.minimumFractionDigits ?? meta.fractionDigits,
    maximumFractionDigits: options.maximumFractionDigits ?? meta.fractionDigits,
  }).format(number);
}
```

## 15.7 Add tenant currency context on frontend

Create a provider or hook so every page does not manually pass currency.

Recommended:

```text
frontend/src/context/TenantSettingsContext.jsx
```

Or extend existing auth/settings context carefully.

Hook example:

```js
export function useTenantCurrency() {
  const { tenantSettings } = useTenantSettings();
  return tenantSettings?.currency ?? 'USD';
}
```

Then create:

```js
export function useMoneyFormatter() {
  const currency = useTenantCurrency();
  return (value, options = {}) => formatMoney(value, { currency, ...options });
}
```

Usage:

```jsx
const money = useMoneyFormatter();

<td>{money(product.cost_price)}</td>
```

## 15.8 Places where currency must be applied

### Product/catalog pages

Use selected currency for:

```text
Cost price
Selling price
Product valuation
Import preview price columns
```

### Sales pages

Use selected or document-snapshot currency for:

```text
Sales order line unit price
Sales order total
Invoice subtotal
Invoice tax
Invoice discount
Invoice total
Payment amount
Customer balance
```

### Purchase pages

Use selected or document-snapshot currency for:

```text
Purchase order line cost
Purchase order total
Bill subtotal
Bill tax
Bill total
Payment amount
Supplier payable
```

### Reports

Use tenant currency for:

```text
Inventory valuation
Stock value
Sales totals
Purchase totals
Billing totals
Dashboard KPIs
```

### Documents and PDFs

Use document currency snapshot:

```text
Invoice PDF
Bill PDF
Invoice email
Bill email
PDF preview
Template preview
```

### Dashboard

Use tenant currency for all money cards:

```text
Inventory value
Total sales
Total purchases
Receivables
Payables
Revenue charts
Cost charts
```

## 15.9 Backend currency validation

Create:

```text
backend/app/utils/currency.py
```

Example:

```python
SUPPORTED_CURRENCIES = {
    'INR', 'USD', 'EUR', 'GBP', 'AED', 'AUD', 'CAD', 'SGD', 'JPY'
}

CURRENCY_SYMBOLS = {
    'INR': '₹',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'AED': 'د.إ',
    'AUD': 'A$',
    'CAD': 'C$',
    'SGD': 'S$',
    'JPY': '¥',
}

def normalize_currency(value: str | None, default: str = 'USD') -> str:
    if not value:
        return default
    code = value.strip().upper()
    if code not in SUPPORTED_CURRENCIES:
        raise ValueError(f'Unsupported currency: {value}')
    return code

def currency_symbol(code: str) -> str:
    return CURRENCY_SYMBOLS.get(code.upper(), code.upper())
```

## 15.10 Pydantic schema validation

Update:

```text
backend/app/schemas/settings.py
backend/app/schemas/documents.py
```

Tenant settings update should reject unsupported currency values.

Recommended:

```python
from pydantic import field_validator
from app.utils.currency import normalize_currency

class TenantSettingsUpdate(BaseModel):
    currency: str | None = None

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, value):
        if value is None:
            return value
        return normalize_currency(value)
```

## 15.11 Currency-change business rule

Changing tenant currency after transactions exist can create reporting confusion.

Recommended rule for phase 1:

```text
If tenant has no financial documents, currency can be changed freely.
If tenant already has invoices, bills, payments, sales orders, purchase orders, or product prices, show warning and require confirmation.
Existing documents keep their original currency snapshot.
New documents use the new tenant currency.
```

Backend should not rewrite historical document currency.

## 15.12 Document currency snapshot

When creating invoice or bill:

```text
If payload currency is provided -> validate and use it.
Else use tenant_settings.currency.
Else fallback to USD.
```

Existing invoices/bills already have a `currency` field, so use it properly.

## 15.13 Template context variables

PDF/email template context should include formatted values.

Add:

```text
currency
currency_symbol
formatted_subtotal_amount
formatted_tax_amount
formatted_discount_amount
formatted_total_amount
formatted_unit_price
formatted_line_total
```

Templates should prefer:

```jinja2
{{ invoice.formatted_total_amount }}
```

instead of:

```jinja2
{{ invoice.total_amount }}
```

## 15.14 PDF template updates

Invoice and bill PDF templates should show currency consistently.

Example:

```html
<td>{{ item.formatted_unit_price }}</td>
<td>{{ item.formatted_line_total }}</td>
<td>{{ invoice.formatted_total_amount }}</td>
```

## 15.15 Backend reports

Reports may continue returning numeric values, but should also return currency metadata.

Example response:

```json
{
  "currency": "INR",
  "currency_symbol": "₹",
  "total_inventory_value": "125000.00"
}
```

Frontend should format display values.

## 15.16 Database migration

If `tenant_settings.currency` already exists, migration may only be needed to normalize defaults.

Recommended migration actions:

```text
Ensure tenant_settings.currency is not null.
Backfill null values to USD or INR based on tenant country if safe.
Ensure invoices and bills have currency values.
Backfill document currency from tenant settings where missing.
```

## 15.17 Currency tests

Backend tests:

```text
Tenant settings accepts supported currency.
Tenant settings rejects unsupported currency.
Invoice creation defaults to tenant currency.
Bill creation defaults to tenant currency.
Invoice keeps currency snapshot after tenant currency changes.
Bill keeps currency snapshot after tenant currency changes.
PDF context contains currency symbol and formatted values.
Reports return currency metadata.
```

Frontend checks:

```text
Settings page shows dropdown instead of plain input.
Currency selector saves selected currency.
Product price displays with selected currency.
Invoice totals display with invoice currency.
Bill totals display with bill currency.
Reports display with tenant currency.
Dashboard money cards display with tenant currency.
PDF preview shows selected/document currency.
```

---

# 16. Claude Skills, Plugins, and Subagents for End-to-End Development

## 16.1 Official Claude Code plugins

Recommended official plugins:

```text
github
pyright-lsp
typescript-lsp
security-guidance
sentry
figma
vercel
```

### Mapping by project area

| Area | Plugin |
|---|---|
| Backend FastAPI/Python | `pyright-lsp` |
| Frontend React/Vite | `typescript-lsp` |
| GitHub repo/PR work | `github` |
| Security audit | `security-guidance` |
| Runtime/debugging issues | `sentry` |
| UI/design matching | `figma` |
| Deployment checks | `vercel` |

Install examples:

```text
/plugin install github@claude-plugins-official
/plugin install pyright-lsp@claude-plugins-official
/plugin install typescript-lsp@claude-plugins-official
/plugin install security-guidance@claude-plugins-official
/plugin install sentry@claude-plugins-official
/plugin install figma@claude-plugins-official
/plugin install vercel@claude-plugins-official
```

## 16.2 Jezweb Claude skills/plugins

Recommended install:

```text
/plugin marketplace add jezweb/claude-skills
/plugin install frontend@jezweb-skills
/plugin install dev-tools@jezweb-skills
/plugin install design-assets@jezweb-skills
/plugin install integrations@jezweb-skills
/reload-plugins
```

Useful skills:

| Need | Skill |
|---|---|
| Frontend architecture | `react-patterns` |
| UI polish | `design-review` |
| Mobile/tablet testing | `responsiveness-check` |
| UX flow audit | `ux-audit` |
| Empty states/onboarding | `onboarding-ux` |
| Delivery planning | `roadmap` |
| Frontend testing | `vitest` |
| Git workflow | `git-workflow` |
| Documentation | `project-docs`, `app-docs` |
| Browser checking | `agent-browser` |
| Second opinion | `brains-trust` |

## 16.3 Custom Warelyn subagents

Create these subagents for Claude Code:

```text
warelyn-business-workflow-architect
warelyn-backend-fastapi-specialist
warelyn-frontend-react-specialist
warelyn-rbac-security-auditor
warelyn-database-migration-specialist
warelyn-testing-qa-specialist
warelyn-debugging-specialist
warelyn-devops-ci-specialist
warelyn-currency-localization-specialist
```

### Subagent responsibilities

#### `warelyn-business-workflow-architect`

```text
Audit workflow handoffs.
Define next role per workflow step.
Create workflow task matrix.
Plan business event transitions.
```

#### `warelyn-backend-fastapi-specialist`

```text
Implement APIs, services, repositories, event emission, task creation, notifications, and audit logs.
```

#### `warelyn-frontend-react-specialist`

```text
Implement screens, route guards, role-specific dashboards, task inbox, empty states, loaders, and forms.
```

#### `warelyn-rbac-security-auditor`

```text
Find mismatches between frontend route permissions and backend endpoint permissions.
Check tenant isolation.
Check viewer read-only enforcement.
```

#### `warelyn-database-migration-specialist`

```text
Design Alembic migrations.
Add indexes, tenant isolation fields, foreign keys, soft-delete fields, and backfills.
```

#### `warelyn-testing-qa-specialist`

```text
Add pytest tests, frontend build checks, route guard checks, workflow transition tests, and tenant isolation tests.
```

#### `warelyn-debugging-specialist`

```text
Investigate failing tests, API mismatches, auth bugs, build errors, and runtime problems.
```

#### `warelyn-devops-ci-specialist`

```text
Fix CI commands, PYTHONPATH problems, frontend build warnings, Docker config, and release checks.
```

#### `warelyn-currency-localization-specialist`

```text
Implement currency selector, currency validation, currency formatting, document currency snapshotting, PDF/email currency formatting, and report currency metadata.
```

## 16.4 Custom Warelyn skills

Create project-specific skills in:

```text
.claude/skills/
```

Recommended skills:

```text
warelyn-workflow-audit
warelyn-rbac-audit
warelyn-api-contract-check
warelyn-db-migration-check
warelyn-security-review
warelyn-frontend-role-check
warelyn-currency-check
warelyn-test-runner
warelyn-debug-runbook
warelyn-release-check
```

---

# 17. Recommended Next Implementation Phases

## Phase 1: Business Workflow Audit

Deliverable:

```text
docs/WARELYN_BUSINESS_WORKFLOW_RBAC_AUDIT.md
```

Include:

```text
Current roles
Current route access
Current API access
Workflow handoff matrix
RBAC mismatch list
Missing task/notification list
Implementation phases
```

## Phase 2: Permission Matrix Cleanup

Deliverables:

```text
backend/app/core/permissions.py
frontend/src/lib/permissions.js
docs/WARELYN_PERMISSION_MATRIX.md
```

## Phase 3: Workflow Task Engine

Deliverables:

```text
workflow_events
workflow_tasks
workflow_rules
My Tasks page
Role dashboard task widgets
```

## Phase 4: Sales Workflow Automation

Implement:

```text
Sales order confirmation -> pick task
Pick complete -> packing task
Fulfillment complete -> invoice task
Return submit -> QC task
```

## Phase 5: Purchase Workflow Automation

Implement:

```text
PO submit -> approval if needed
Receipt commit -> putaway task
Putaway complete -> bill task
Low stock -> reorder suggestion
```

## Phase 6: Currency Selection and App-Wide Money Formatting

Implement:

```text
CurrencySelect
Currency metadata registry
Backend validation
Tenant currency context
Currency-aware formatMoney
Document currency snapshots
PDF/email formatted currency variables
Report currency metadata
```

## Phase 7: Role-Based Dashboards

Implement:

```text
Tenant Admin dashboard
Inventory Manager dashboard
Sales Staff dashboard
Purchase Staff dashboard
Viewer dashboard
```

## Phase 8: Business Partner Network

Implement:

```text
tenant_partner_links
partner_shared_products
supplier catalog
shared sales catalog
no transitive supplier visibility
```

## Phase 9: Testing and Security Hardening

Add:

```text
Backend RBAC tests
Frontend route guard tests
Workflow transition tests
Tenant isolation tests
Currency tests
Notification tests
Audit log tests
```

---

# 18. Master Prompt for Claude Opus

```markdown
# Warelyn Workflow-Aware SaaS Maturity Phase

You are Claude Opus working inside the Warelyn repository.

Perform a deep business workflow, RBAC, currency, security, database, frontend, backend, and testing implementation phase.

The main product question is:

When one role completes a workflow step, does the next step correctly move to the designated concerned role?

Do not rewrite the app from scratch. Inspect the current code first.

## Goals

1. Audit current business workflows.
2. Identify RBAC mismatches between frontend and backend.
3. Design workflow task handoff system.
4. Add role-based next-step task planning.
5. Add role-specific dashboards and My Tasks planning.
6. Implement currency selection throughout the application.
7. Add backend/frontend tests.
8. Produce a detailed implementation report.

## Inspect First

Backend:

```text
backend/app/models
backend/app/api
backend/app/services
backend/app/repositories
backend/app/schemas
backend/tests
```

Frontend:

```text
frontend/src/routes/AppRoutes.jsx
frontend/src/lib/permissions.js
frontend/src/components/navigation.js
frontend/src/pages
frontend/src/services
frontend/src/context/AuthContext.jsx
frontend/src/utils/formatters.js
frontend/src/pages/SettingsPage.jsx
```

## Workflow Audit Matrix

For every major workflow step, document:

```text
Current step
Current role
Action taken
Next status
Expected next role
Is a task created?
Is a notification created?
Is next role dashboard updated?
Is frontend route allowed correctly?
Is backend API allowed correctly?
What is missing?
```

## Currency Implementation Requirements

Implement single base currency per tenant.

Required:

```text
Currency dropdown in settings
Supported currency registry
Backend currency validation
Tenant currency context/hook
Currency-aware formatMoney
Apply currency formatting to products, sales, purchases, bills, invoices, reports, dashboard, templates, and PDFs
Invoice and bill currency snapshot at creation
Existing documents keep their original currency
PDF/email templates receive formatted currency variables
Backend and frontend tests
```

## Suggested Files

Create/update:

```text
frontend/src/lib/currencies.js
frontend/src/components/ui/CurrencySelect.jsx
frontend/src/context/TenantSettingsContext.jsx
frontend/src/utils/formatters.js
backend/app/utils/currency.py
backend/app/schemas/settings.py
backend/app/schemas/documents.py
backend/app/services/documents.py
backend/app/services/reports.py
```

## Commands

Backend:

```bash
cd backend
python -m compileall app
PYTHONPATH=. pytest -q
```

Frontend:

```bash
cd frontend
npm run build
```

## Final Report

Return:

```text
Summary
Business workflow gaps found
RBAC mismatches found
Currency implementation completed
Backend files changed
Frontend files changed
Database migrations
Tests run
Remaining risks
Next recommended phase
```

Do not claim completion unless backend tests and frontend build pass.
```

---

# 19. Final Recommendation

The next serious Warelyn phase should not be only UI polish. It should make the application:

```text
Role-aware
Workflow-aware
Currency-aware
Permission-consistent
Task-driven
Notification-driven
Test-backed
```

The most important product upgrade is the **workflow handoff engine**.

The most important business settings upgrade is **currency selection with consistent formatting and document snapshots**.

Together, these make Warelyn feel much closer to a real production SaaS inventory platform.
