---
name: warelyn-test-runner
description: Run Warelyn backend and frontend verification commands after changes. Use before committing or after implementing a feature.
---

# Warelyn Test Runner

Run:

Backend:
cd backend
python -m compileall app
PYTHONPATH=. pytest -q

Frontend:
cd frontend
npm run build

If tests fail:

- summarize failing command
- summarize root cause
- fix minimal issues
- rerun focused tests first
- rerun full verification

Never claim success unless commands pass.