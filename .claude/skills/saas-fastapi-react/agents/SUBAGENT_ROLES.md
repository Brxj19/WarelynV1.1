# Subagent Roles

Use these roles to keep work focused. Act as the role that best matches the current task.

## 1. saas-backend-fastapi-specialist

Use for:
- APIs, services, repositories, models, migrations, background jobs

Does:
- keeps routers thin
- puts business logic in services
- keeps DB access in repositories
- preserves tenant isolation and auth boundaries

Does not:
- commit in repositories
- add business logic to routers
- bypass permissions or tenant filtering

## 2. saas-frontend-react-specialist

Use for:
- React pages, components, hooks, context, routing, and styling

Does:
- keeps pages thin
- puts API calls in service files
- uses reusable UI primitives and shared context

Does not:
- fetch inline inside pages
- compute backend business totals
- duplicate role logic that already exists in permissions metadata

## 3. saas-rbac-security-auditor

Use for:
- auth changes, permission changes, tenant isolation, public surfaces

Checklist:
- endpoint has auth dependency
- backend and frontend permissions match
- cross-tenant access is blocked
- viewer/read-only roles cannot mutate data
- secrets and PII are not exposed in logs or templates

## 4. saas-database-migration-specialist

Use for:
- schema changes, backfills, indexes, enum changes

Rules:
- one logical migration per change
- upgrade and downgrade must both work
- tenant-owned tables need tenant indexes
- never use destructive migration shortcuts without data review

## 5. saas-workflow-architect

Use for:
- business processes that span multiple steps or roles

Pattern:
- action
- permission check
- status change
- domain event
- workflow task
- notification
- audit log

Responsibilities:
- define step keys
- define the next role
- prevent duplicate tasks
- decide what auto-completes and what remains manual

## 6. saas-testing-qa-specialist

Use for:
- test design, fixture design, verification planning

Test categories:
- unit tests for service logic
- integration tests for API contracts
- RBAC 401/403 tests
- tenant isolation tests
- workflow transition tests

Minimum expectation:
- every new endpoint gets happy-path and denial-path coverage
- every mutation is re-fetched to prove persistence

## 7. saas-debugging-specialist

Use for:
- build errors, failing tests, runtime failures, broken flows

Debug flow:
1. reproduce
2. classify
3. trace
4. isolate
5. patch
6. verify

Common culprits:
- missing commit
- wrong role guard
- tenant filter omitted
- stale frontend state
- route mismatch

## 8. saas-ai-rag-specialist

Use for:
- RAG, knowledge bases, AI copilots, report-aware assistants

Responsibilities:
- build Q&A-friendly source docs
- use hybrid retrieval
- keep answers grounded and cited
- detect off-topic questions
- prefer read-only, tenant-scoped live data

## 9. saas-devops-deployment-specialist

Use for:
- Docker, CI, environment config, seed scripts, startup order

Responsibilities:
- migration-before-start
- health-checked services
- explicit env vars
- seed-on-startup toggle
- repeatable validation
