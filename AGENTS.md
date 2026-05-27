# Warelyn Inventory Agent Rules

Warelyn Inventory is a multi-tenant inventory SaaS platform.

---

## Required Reading Before Coding

Always read these before starting any work:

- `docs/WARELYN_CLAUDE_CODE_PLAN.md` — **Active phase-by-phase implementation plan. Read the relevant phase section first.**
- `docs/WARELYN_BUSINESS_WORKFLOW_RBAC_CURRENCY_PLAN.md` — Business context, workflow architecture, role ownership, and subagent role definitions (see section 16).
- `docs/WARELYN_REAL_WORLD_V2_PRD.md`
- `docs/MODULE_BOUNDARIES.md`
- `docs/INVENTORY_ENGINE_SPEC.md`

---

## Current Implementation Phase

The project is in the **Workflow-Aware SaaS Maturity Phase**.

The central product question is:
> When one role completes a workflow step, does the next step automatically move to the correct concerned role?

Work through phases in the order defined in `docs/WARELYN_CLAUDE_CODE_PLAN.md`. Do not skip phases. Do not move to the next phase until the current phase passes verification.

Active phases in order:
1. Currency Foundation
2. Currency in Documents and Reports
3. Workflow Task Engine
4. Sales Workflow Automation
5. Purchase Workflow Automation
6. My Tasks Page + Role Dashboards
7. RBAC Audit and Permission Cleanup
8. Testing Hardening

---

## Installed Plugins

These plugins are active in this project. Use them — do not manually replicate what they already provide.

### Official Plugins

| Plugin | When to use |
|---|---|
| `pyright-lsp` | All backend Python/FastAPI work. Use for type checking, import resolution, and refactoring. |
| `typescript-lsp` | All frontend React/Vite/JS work. Use for type checking and component intelligence. |
| `github` | Repo search, reading issues and PRs, code review context. |
| `security-guidance` | Run on any new API endpoint, auth change, template rendering, or file generation code. |
| `semgrep` | Deeper security scan on RBAC changes, tenant isolation code, and before any release. |
| `playwright` | E2E browser testing for critical frontend flows (login, task completion, role switching). |
| `chrome-devtools` | Frontend debugging — network calls, console errors, React component state. |
| `code-review` | Use after completing each phase before moving to the next. |
| `pr-review-toolkit` | Use before committing phase work. Checks types, quality, and test coverage. |
| `feature-dev` | Use when starting a new phase to scaffold the structured development flow. |
| `commit-commands` | Use for all commits and PRs. |
| `postman` | API contract testing — use when verifying new endpoints in phases 3–5. |
| `sentry` | Production error debugging. |
| `vercel` | Frontend deployment and build logs. |
| `figma` | Design reference if UI specs exist. |

### Jezweb Skills (installed via `jezweb/claude-skills`)

| Skill | When to use |
|---|---|
| `/frontend:react-patterns` | Before writing any new React component or page. |
| `/frontend:design-review` | After building UI in phases 6 — check visual consistency. |
| `/dev-tools:responsiveness-check` | After My Tasks page and Dashboard widgets are built. |
| `/dev-tools:ux-audit` | After phase 6 to audit the task inbox UX and dashboard flow. |
| `/dev-tools:onboarding-ux` | When reviewing empty states and first-time user flows. |
| `/dev-tools:vitest` | Frontend unit testing setup and test writing. |
| `/dev-tools:project-health` | Run at the start of any new session to assess project state. |
| `/dev-tools:project-docs` | When updating architecture docs after a phase. |
| `/dev-tools:roadmap` | When planning or reviewing phase ordering. |
| `/dev-tools:git-workflow` | For branching, committing, and PR workflow. |
| `/dev-tools:agent-browser` | Browser automation for testing frontend flows. |

---

## Project Skills

These are Warelyn-specific skills in `.claude/skills/`. Invoke them at the points specified in each phase.

| Skill | Invoke as | When to use |
|---|---|---|
| `warelyn-workflow-audit` | `/warelyn-workflow-audit` | Start of phases 4 and 5 — audit current workflow handoffs before wiring them. |
| `warelyn-rbac-audit` | `/warelyn-rbac-audit` | Phase 7 — full RBAC mismatch audit across frontend and backend. |
| `warelyn-api-contract-check` | `/warelyn-api-contract-check` | Phases 1, 3 — verify frontend service calls match backend schemas and routes. |
| `warelyn-security-review` | `/warelyn-security-review` | Phase 7 and 8 — cross with `security-guidance` and `semgrep`. |
| `warelyn-db-migration-check` | `/warelyn-db-migration-check` | Phases 2 and 3 — before and after writing Alembic migrations. |
| `warelyn-test-runner` | `/warelyn-test-runner` | End of every phase — run backend and frontend verification. |
| `warelyn-debug-runbook` | `/warelyn-debug-runbook` | Any time a phase fails verification — debug before moving on. |

---

## Subagent Roles

When working on a specific domain, operate as the relevant subagent persona defined in `docs/WARELYN_BUSINESS_WORKFLOW_RBAC_CURRENCY_PLAN.md` section 16.

| Subagent | Responsibility |
|---|---|
| `warelyn-business-workflow-architect` | Audit workflow handoffs, define next role per step, plan business event transitions. |
| `warelyn-backend-fastapi-specialist` | APIs, services, repositories, event emission, task creation, notifications, audit logs. |
| `warelyn-frontend-react-specialist` | Screens, route guards, role-specific dashboards, task inbox, empty states, loaders, forms. |
| `warelyn-rbac-security-auditor` | Frontend/backend permission mismatches, tenant isolation, viewer read-only enforcement. |
| `warelyn-database-migration-specialist` | Alembic migrations, indexes, tenant isolation fields, FK constraints, backfills. |
| `warelyn-testing-qa-specialist` | pytest, frontend build checks, route guard tests, workflow transition tests, tenant isolation tests. |
| `warelyn-debugging-specialist` | Failing tests, API mismatches, auth bugs, build errors, runtime problems. |
| `warelyn-currency-localization-specialist` | Currency selector, validation, formatting, document snapshots, PDF/email variables, report currency. |

---

## Workflow Engine Rules

- Every major business action must follow: action → permission check → entity status change → domain event logged → workflow task created → notification sent → audit log written.
- `workflow_tasks` and `workflow_events` are the canonical tables for role handoff.
- Sales order confirmed → PICK_ORDER task for INVENTORY_MANAGER.
- Receipt committed → PUTAWAY_STOCK task for INVENTORY_MANAGER.
- Putaway completed → RECORD_BILL task for PURCHASE_STAFF.
- Fulfillment committed → CREATE_INVOICE task for SALES_STAFF.
- Order or PO cancelled → all open workflow tasks for that entity cancelled.
- Wrap all workflow side-effect calls in try/except — a workflow failure must never break the main business operation.
- Do not create duplicate tasks for the same entity + step_key if an OPEN task already exists.

---

## Currency Rules

- Every tenant has a single base currency in `tenant_settings.currency` (ISO 4217, 3-char).
- `formatMoney(value, currencyCode)` must always receive an explicit currency code.
- Invoices and bills must snapshot the tenant's currency at creation time. This snapshot is immutable.
- Historical documents always display using their own `currency_code`, not the tenant's current setting.
- PDF and email templates must receive `currency_code` and `currency_symbol` as template variables.
- Report responses must include `currency_code` metadata.
- Only currencies in `frontend/src/lib/currencies.js` and `backend/app/utils/currency.py` are valid.

---

## RBAC Rules

- Backend `require_roles()` is the security boundary. Frontend role hiding is UX only, not security.
- Every API endpoint must have an explicit `require_roles()` dependency.
- `ROUTE_ACCESS` and `ACTION_ACCESS` in `permissions.js` must stay in sync with backend.
- VIEWER must never see create, edit, delete, confirm, cancel, approve, or send buttons.
- PURCHASE_STAFF must not access sales-specific routes or actions.
- SALES_STAFF must not access purchase-specific routes or actions.
- Every repository query must filter by `tenant_id`. Cross-tenant data must never be returned.
- SUPER_ADMIN routes must be under `/admin/*` and require `require_super_admin()`.

---

## Working Rules

- Plan before large changes.
- Keep changes small and phase-aligned.
- Use `/commit-commands:commit` for all commits.
- Update `docs/WARELYN_PERMISSION_MATRIX.md` when RBAC changes are made.
- Do not work on AI assistant features.
- Do not work on subscription, billing plans, or payment features.
- Do not create business tables or migrations unless the current phase explicitly calls for them.

---

## Backend Rules

- Keep routers thin — HTTP concerns only.
- Business workflows go in services.
- Database access goes in repositories.
- Persistence shape goes in models.
- Request/response contracts go in schemas.
- `InventoryEngine` is the only allowed stock mutation path.
- Workflow service calls go in services, never in routers or repositories.
- All new tables require an Alembic migration. Never use `Base.metadata.create_all()` in production code.

---

## Frontend Rules

- Frontend never calculates true stock.
- API calls go in service files under `frontend/src/services/`.
- Pages are thin — they compose UI and call services/hooks.
- Always pass `currencyCode` to `formatMoney()`. Never call `formatMoney(value)` without a currency code.
- Use `TenantSettingsContext` to get the tenant's current currency in any component displaying money.
- Warelyn visual direction: deep blue primary, emerald accent, soft gray backgrounds, white cards, clear badges, structured layouts.

---

## Verification

Run at the end of every phase. Do not claim a phase complete unless both pass.

```bash
# Backend
cd backend && .venv/bin/python -m compileall app && .venv/bin/python -m pytest -q

# Frontend
cd frontend && npm install && npm run build
```

Or use the project skill:
```
/warelyn-test-runner
```

Full hardening validation (when Docker and DB are available):
```bash
./scripts/validate.sh
```