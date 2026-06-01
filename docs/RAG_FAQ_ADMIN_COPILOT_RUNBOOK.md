# RAG FAQ + Tenant Admin Copilot Runbook

This document covers the read-only AI features implemented on `feature/rag-faq-admin-copilot`.

## Scope

- `FAQ Assistant`: tenant read roles can ask grounded product/workflow questions.
- `AI Copilot`: `TENANT_ADMIN` only, multi-turn assistant with tenant operational context.
- No mutation actions are executed by AI.
- Suggested actions are deep links only.

## Backend endpoints

- `GET /faq/suggestions`
- `POST /faq/ask`
- `POST /assistant/sessions`
- `GET /assistant/sessions/{id}`
- `POST /assistant/sessions/{id}/ask`
- `POST /assistant/messages/{id}/feedback`
- `GET /assistant/telemetry`

## Guardrails

- Citation-first policy:
  - no citations => abstain response
  - low confidence => abstain response
- No cross-tenant retrieval:
  - retrieval scope is `tenant_id` + global docs only.
- Prompt policy:
  - grounded to provided context
  - no hidden/system secret disclosure
  - no write-operation execution.

## Config

Environment variables (prefix `WARELYN_`):

- `GEMINI_API_KEY`
- `GEMINI_BASE_URL` (default `https://generativelanguage.googleapis.com/v1beta`)
- `GEMINI_CHAT_MODEL` (default `gemini-1.5-flash`)
- `GEMINI_EMBEDDING_MODEL` (default `text-embedding-004`)
- `AI_RETRIEVAL_CANDIDATES` (default `24`)
- `AI_RETRIEVAL_TOP_K` (default `6`)
- `AI_MIN_CONFIDENCE` (default `0.42`)

If `GEMINI_API_KEY` is empty, responses degrade gracefully and remain conservative.

## Knowledge indexing

- Bootstrap index occurs on startup when API key is configured and index is empty.
- Knowledge bootstrap runs automatically when the index is empty and Gemini key is configured.
- Reindex uses curated internal docs and workflow references from repository docs.

## Observability

- Audit actions:
  - `ASSISTANT_REINDEX`
  - `ASSISTANT_FAQ_ASK`
  - `ASSISTANT_SESSION_CREATE`
  - `ASSISTANT_COPILOT_ASK`
  - `ASSISTANT_FEEDBACK`
- Telemetry endpoint returns request count, latency, tokens, abstain rate, citation rate.

## AGENTS restriction exception note

The repository AGENTS guide currently disallows AI assistant feature work. This branch is an explicit user-approved exception for this scoped read-only assistant implementation.
