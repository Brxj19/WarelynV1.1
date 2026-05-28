---
name: warelyn-api-contract-check
description: Check Warelyn frontend service calls against backend FastAPI routes and schemas. Use when fixing API mismatches, route paths, payload shapes, response fields, auth headers, and error handling.
---

# Warelyn API Contract Check

Inspect:

- backend/app/api
- backend/app/schemas
- frontend/src/services
- frontend/src/pages

For every frontend API call, verify:

- backend endpoint exists
- method matches
- payload shape matches schema
- response shape is handled correctly
- auth token is sent
- tenant context is respected
- errors are displayed cleanly

Output:

- Broken endpoint list
- Missing backend route list
- Wrong payload list
- Wrong response handling list
- Suggested patches
- Tests needed