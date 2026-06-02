# Warelyn Frontend Architecture

The repository graph shows `apiRequest()` as a frontend god node with 214 edges. This means service modules should share a single HTTP client path instead of issuing ad hoc fetch calls.

## Frontend Layers

`frontend/src/pages/` contains route-level pages. Pages should be thin: compose components, call services/hooks, manage local UI state, and render loading/error/empty states.

`frontend/src/services/` contains API calls. Each domain has a service file. Service files call `apiRequest()` and should not contain UI code.

`frontend/src/components/` contains reusable UI components. Components should avoid hidden API calls unless their purpose is explicitly data loading.

`frontend/src/context/` contains application state providers, including AuthContext and TenantSettingsContext. AuthContext provides current user and access token. TenantSettingsContext provides tenant-level settings such as currency.

`frontend/src/hooks/` contains reusable UI behavior such as table keyboard navigation, task counts, and toast helpers.

`frontend/src/routes/AppRoutes.jsx` defines route structure and RoleGuard wrapping. Routes are the strongest frontend UX guard, but backend RBAC remains the true security boundary.

`frontend/src/navigation.js` controls sidebar and navigation visibility. Hidden nav links reduce accidental 403s but do not replace backend checks.

`frontend/src/lib/permissions.js` contains route and action permission matrices. These should stay in sync with backend role guards.

## API Request Pattern

All frontend service calls should go through `apiRequest()`. This gives one place for base URL, auth header, error handling, and response parsing. When a screen crashes with a role-related 403, check the route guard, navigation visibility, and the service call that uses `apiRequest()`.

## Role UX Rules

VIEWER should not see create, edit, delete, confirm, cancel, approve, send, reset, or destructive action buttons.

SALES_STAFF should not be routed into purchase-specific screens.

PURCHASE_STAFF should not be routed into sales-specific screens.

TENANT_ADMIN can see tenant-wide operational overviews and user/settings controls.

SUPER_ADMIN uses `/admin/*` routes and should not enter tenant dashboards.

## Money Display Rule

Any component displaying money must receive and pass an explicit currency code to formatting helpers. Historical invoices and bills display their own stored currency snapshot, not the tenant's current setting.

## Assistant UI Rule

FAQ chat is a floating support surface for tenant users. Tenant admin copilot is a guarded admin page. Report data from the copilot renders as a table with citations and action links, but AI never triggers write operations.
