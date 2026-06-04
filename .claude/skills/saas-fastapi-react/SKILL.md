---
name: saas-fastapi-react
description: Generalised skill pack for building FastAPI + React SaaS products with layered backend architecture, RBAC, workflow engines, RAG copilots, Docker deployment, and disciplined testing.
---

# FastAPI + React SaaS Skill Pack

Use this skill pack when building or maintaining a multi-tenant SaaS app with:
- FastAPI, SQLAlchemy, Alembic, Pydantic
- React, Vite, Tailwind
- RBAC, workflow tasks, notifications, audit logs
- RAG/copilot or other AI-assisted read-only experiences
- Dockerised local development and CI validation

## When to invoke which sub-skill

- **Backend/API work**: read `rules/BACKEND_RULES.md`, `agents/SUBAGENT_ROLES.md`
- **Frontend/UI work**: read `rules/FRONTEND_RULES.md`
- **Security/RBAC changes**: read `rules/SECURITY_RULES.md` and `rules/BACKEND_RULES.md`
- **Schema changes**: read `rules/BACKEND_RULES.md` and `rules/TESTING_STANDARDS.md`
- **Workflow orchestration**: read `patterns/WORKFLOW_ENGINE_PATTERN.md`
- **RAG/copilot features**: read `patterns/RAG_COPILOT_PATTERN.md`
- **Bug fixing**: read `runbooks/BUG_FIX_RUNBOOK.md`
- **Docker/seed/deployment work**: read `patterns/DOCKER_DEPLOYMENT_PATTERN.md`
- **Commit/PR work**: read `rules/GIT_COMMIT_RULES.md`
- **Architecture discovery**: use `tools/GRAPHIFY_GUIDE.md`

## Operating model

Before writing code:
1. Identify the layer(s) you are changing.
2. Read the relevant rule file(s).
3. State which subagent role you are acting as.
4. Check the request against tenant, RBAC, workflow, and migration constraints.

While writing code:
1. Keep routers thin.
2. Keep pages thin.
3. Put persistence in repositories, logic in services, and contracts in schemas.
4. Wrap workflow side effects in `try/except` so the primary action survives.

Before committing:
1. Run the verification commands in the project instructions.
2. Fix type errors, lint issues, and failing tests.
3. Confirm RBAC and tenant isolation where applicable.
4. Use the commit rules in `rules/GIT_COMMIT_RULES.md`.

## Graphify workflow

When starting a new project or large refactor:
1. Run graphify to build the semantic graph.
2. Read `tools/GRAPHIFY_GUIDE.md`.
3. Use the graph to identify hub abstractions, import cycles, and security-sensitive nodes.
4. Update architecture docs or RAG knowledge only from the graph plus actual code, not memory.

## Output discipline

- Prefer generalisable patterns over project-specific story details.
- Keep decisions explicit.
- Do not hide tradeoffs.
- Never claim completion until the project’s own verification commands pass.

## Core references

- `AGENTS_TEMPLATE.md`
- `agents/SUBAGENT_ROLES.md`
- `rules/BACKEND_RULES.md`
- `rules/FRONTEND_RULES.md`
- `rules/CODE_QUALITY_RULES.md`
- `rules/SECURITY_RULES.md`
- `rules/GIT_COMMIT_RULES.md`
- `runbooks/BUG_FIX_RUNBOOK.md`
- `patterns/WORKFLOW_ENGINE_PATTERN.md`
- `patterns/RAG_COPILOT_PATTERN.md`
- `tools/GRAPHIFY_GUIDE.md`
- `rules/TESTING_STANDARDS.md`
- `patterns/DOCKER_DEPLOYMENT_PATTERN.md`
