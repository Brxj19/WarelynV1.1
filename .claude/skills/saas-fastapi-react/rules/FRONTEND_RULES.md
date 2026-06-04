# Frontend Architecture Rules

## File structure

- `pages/` — thin route-level screens
- `services/` — all API calls through shared `apiRequest()`
- `components/` — reusable UI only
- `components/ui/` — primitive building blocks
- `context/` — auth, tenant settings, and other global state
- `hooks/` — shared logic only when reused in multiple places
- `routes/AppRoutes.jsx` — routes, guards, lazy loading
- `components/navigation.js` — nav visibility and breadcrumbs

## 10 frontend rules

1. Never compute backend business totals in the frontend.
2. All API calls must go through service modules.
3. Pages should stay thin and compositional.
4. Every permissioned route must have a matching route guard.
5. Read-only roles must not see write actions.
6. Money formatting always needs an explicit currency code.
7. Use global tenant settings for currency and branding values.
8. Mutations should update state optimistically and revert on failure.
9. Loading and empty states are required for async views.
10. In chat or feed views, auto-scroll should be deliberate and stable.

## RBAC frontend pattern

- Keep a single permission matrix for routes and actions.
- The frontend may hide actions, but the backend still enforces them.
- If the sidebar shows a route, the route guard must allow it.
- If the backend denies a role, the frontend should not advertise the action.

## API service pattern

```js
export function listX(accessToken, params) {
  return apiRequest(`/x${buildQuery(params)}`, { accessToken });
}

export function createX(accessToken, data) {
  return apiRequest('/x', {
    accessToken,
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

## UI quality reminders

- Prefer semantic HTML.
- Keep keys stable and unique.
- Avoid inline styles unless the value is dynamic.
- Use shared layout and loading primitives consistently.
