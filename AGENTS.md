# Warelyn Inventory Agent Rules

Warelyn Inventory is a multi-tenant inventory SaaS foundation. Read these docs before coding:

- `docs/WARELYN_REAL_WORLD_V2_PRD.md`
- `docs/MODULE_BOUNDARIES.md`
- `docs/INVENTORY_ENGINE_SPEC.md`
- `docs/V2_IMPLEMENTATION_BACKLOG.md`

## Working Rules

- Plan before large changes.
- Keep changes small and phase-aligned.
- Use small commits with clear messages.
- Update docs when architecture, commands, or boundaries change.
- Do not work on AI assistant features yet.
- Do not work on subscription expansion, billing plans, or payment features yet.
- Do not implement advanced business logic before the foundation and tenant model are stable.

## Backend Rules

- Keep routers thin; routers handle HTTP concerns only.
- Put business workflows in services.
- Put database access in repositories.
- Put persistence shape in models.
- Put request/response contracts in schemas.
- Backend must enforce tenant isolation; frontend role hiding is not security.
- `InventoryEngine` is the only allowed stock mutation path once inventory workflows exist.
- Do not update stock directly from routers, repositories, scripts, or frontend requests.
- Do not create business tables or migrations unless the phase explicitly calls for them.

## Frontend Rules

- Frontend never calculates true stock.
- Keep frontend API calls in service files.
- Keep pages thin; pages compose UI and call services/hooks.
- Use reusable UI components for buttons, inputs, cards, badges, and states.
- Preserve Warelyn's clean B2B SaaS visual direction.
- Use Warelyn branding: deep blue primary, emerald accent, soft gray backgrounds, white cards, clear badges, structured layouts.

## Verification

- Backend foundation: `cd backend && .venv/bin/python -m compileall app && .venv/bin/python -m pytest` after installing `backend/requirements.txt`.
- Frontend foundation: `cd frontend && npm install && npm run build`.
- Compose validation: `docker compose config`.
- Full hardening validation: `./scripts/validate.sh` when local backend `.venv`, frontend dependencies, Docker, and database access are available.
