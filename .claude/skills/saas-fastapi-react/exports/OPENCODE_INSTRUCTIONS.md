# Open Code Instructions for FastAPI + React SaaS

Use these instructions in a VS Code extension workflow for a multi-tenant FastAPI + React SaaS project.

## Invoke the right role

Choose one role before editing:
- `saas-backend-fastapi-specialist`
- `saas-frontend-react-specialist`
- `saas-rbac-security-auditor`
- `saas-database-migration-specialist`
- `saas-workflow-architect`
- `saas-testing-qa-specialist`
- `saas-debugging-specialist`
- `saas-ai-rag-specialist`
- `saas-devops-deployment-specialist`

## Never-violate rules

### Backend
1. Domain mutations go through services.
2. `tenant_id` comes from auth context only.
3. Every endpoint needs an explicit role dependency.
4. Every repository query filters by tenant.
5. Repositories never call `commit()`.
6. Every schema change gets Alembic.
7. Workflow side effects stay inside `try/except`.

### Frontend
1. Pages stay thin.
2. All API calls go through service files.
3. Route guards must match backend permissions.
4. Read-only roles cannot see write actions.
5. Money formatting always needs a currency code.
6. Loading and empty states are required.
7. Frontend business totals must not replace backend calculations.

### Security
1. Use revocable tokens.
2. Keep tenant data isolated.
3. Escape rendered content safely.
4. Validate uploads.
5. Never log secrets.
6. Add idempotency for money/stock mutations.
7. Use explicit CORS origins.

## Verification tasks

Run these tasks before you mark work complete:
- `cd backend && .venv/bin/python -m compileall app`
- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm install && npm run build`

## Skill usage in Open Code

- Use the file tree to open the relevant rule file before editing.
- Keep edits aligned to one layer at a time.
- Use the runbook when debugging a failing flow.
- Use the workflow and RAG patterns when building those features.

## Commit guidance

Use the commit rules from `rules/GIT_COMMIT_RULES.md`.
Prefer small, single-purpose commits.
