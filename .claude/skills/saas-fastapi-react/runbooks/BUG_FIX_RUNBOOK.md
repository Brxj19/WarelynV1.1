# Bug-Fixing Runbook

## Universal debug flow

1. Reproduce the bug with the smallest reliable input.
2. Classify the layer: DB, service, API, frontend, auth, RBAC, migration.
3. Trace the request or render path end to end.
4. Isolate the smallest failing test or scenario.
5. Patch the root cause, not the symptom.
6. Verify the fix and confirm nearby tests still pass.

## Common backend failures

### Silent mutation
- Symptom: API returns 200 but the database stays unchanged.
- Cause: commit missing from the service layer.
- Fix: commit in the service after the business unit of work completes.

### Cross-tenant leak
- Symptom: one tenant sees another tenant’s data.
- Cause: missing tenant filter.
- Fix: add tenant scoping everywhere and test the denial path.

### Missing workflow task
- Symptom: the action completes but no follow-up task appears.
- Cause: side-effect wiring missing or swallowed too aggressively.
- Fix: wire the task creation in the service and log failures explicitly.

### Double-apply retry
- Symptom: a retry duplicates a stock or financial mutation.
- Cause: nondeterministic idempotency key.
- Fix: derive the key from the entity and step, not a random UUID.

## Common frontend failures

### Stale saved state
- Symptom: UI still shows old values after save.
- Cause: local state not synced after mutation.
- Fix: optimistic update plus re-fetch or state sync on success.

### Extra API chatter
- Symptom: a list page fires one request per row.
- Cause: detail fetching in a loop.
- Fix: create a proper list endpoint.

### Role mismatch
- Symptom: sidebar shows a page that the backend denies.
- Cause: frontend permissions broader than backend permissions.
- Fix: align both and trust the backend as the authority.

## When a bug touches authentication

- test both authenticated and unauthenticated behaviour
- test the expected role and a denied role
- check that tokens, refresh flows, and revocation still work
