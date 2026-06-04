# Docker + Deployment Pattern

## Compose pattern

Include services for:
- database
- backend API
- frontend or static serving
- optional mail/testing services

## Startup order

1. database becomes healthy
2. migrations run
3. seed script runs if enabled
4. backend starts
5. frontend starts or the static bundle is served

## Environment rules

- use a project-specific prefix for all environment variables
- keep secrets out of source control
- commit `.env.example`, not `.env`
- make seed-on-startup configurable

## Validation pattern

Run a repeatable validation script that checks:
- backend compiles
- backend tests pass
- frontend build passes
- compose file parses

## Production checklist

- debug disabled
- explicit CORS origins
- strong secret values
- seed disabled unless intentionally needed
- database health checks enabled
- rate limiting active on auth endpoints
