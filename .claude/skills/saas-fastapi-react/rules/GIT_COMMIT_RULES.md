# Git Commit Rules

## Format

```text
type(scope): short imperative summary

Optional body — what and why, not how.
```

## Types

- `feat`
- `fix`
- `refactor`
- `test`
- `docs`
- `chore`
- `perf`
- `security`
- `seed`
- `migration`

## Scope examples

- `(auth)`
- `(rbac)`
- `(workflow)`
- `(inventory)`
- `(sales)`
- `(purchase)`
- `(returns)`
- `(dashboard)`
- `(frontend)`
- `(backend)`
- `(seed)`
- `(docker)`

## Rules

- keep the summary imperative
- keep the summary under 72 characters
- do not end the summary with a period
- one logical change per commit
- do not commit broken tests
- reference the bug report in the body when fixing a known bug

## Phase commits

For large phased work, prefer:

`feat(phase-N): short phase summary`
