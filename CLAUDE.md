# Soraya Study — Claude Agent Instructions

## Project overview

This is the Soraya study backend (Kaleidoworks). Soraya is a pedagogical AI tutor whose responses are governed by an Agency Ledger and four gates (agency, justice/mercy, epistemic, wonder/humor).

## Supabase project

- **Project ref:** `qwyzniqfcmcrbfzemeht`
- **URL:** `https://qwyzniqfcmcrbfzemeht.supabase.co`
- **MCP server:** configured in `.mcp.json` — use it to introspect live schema before writing queries

## Key tables

| Table | Written by | Notes |
|---|---|---|
| `study_sessions` | `consent_gate.py` | One row per consented session |
| `study_turns` | `ledger_hook.py` | One row per chat turn, includes ledger estimates + gate audit |
| `survey_responses` | `app.py` | Pre/post survey, keyed by `survey_slot` ("pre" / "post") |
| `contingency_events` | `contingency_hook.py` | Fade-property audit, one row per turn |

## RLS policy

- HF Space uses the **anon / publishable key** — INSERT only, no SELECT
- Admin dashboard uses the **service role key** — full read, server-side only
- Never expose the service role key to the browser or commit it to the repo

## Python backend conventions

- `db.py` — all Supabase writes; fail-closed on `StudyDBError`
- `ledger_hook.py` — calls `db.record_study_turn()` after every governed turn
- `consent_gate.py` — mints `participant_id` / `session_id` on consent
- `soraya_gates.py` — four post-generation audit gates; returns `GateReport`
- `ledger.py` — `LedgerState` (A_hat, K_hat, D_hat), routing, system prompt builder
- `app.py` — Gradio UI, `run_turn()` orchestration

## Next.js dashboard (soraya-dashboard/)

- `utils/supabase/admin.ts` — service-role client, server-only
- `utils/supabase/server.ts` — SSR client for Server Components
- `utils/types.ts` — TypeScript mirrors of the Python schema; keep in sync with `db.py`
- API routes under `app/api/` use the admin client — never call these from the browser directly

## Coding conventions

- Python: type-annotated, dataclass-style where possible, no silent error swallowing post-consent
- TypeScript: strict mode, no `any` except where Supabase JSON columns require it
- Supabase queries: always specify columns explicitly (avoid `select *` in production paths)
- Use `count: exact` when paginating
- Prefer `upsert` over separate insert/update for idempotent writes

## What NOT to do

- Do not add `select` RLS policies to study tables — participant data is write-only from the Space
- Do not catch `StudyDBError` in `run_turn()` — surface it so sessions are marked incomplete
- Do not use `localStorage` or `sessionStorage` in the dashboard — the Space runs in a sandboxed iframe
- Do not hardcode the service role key anywhere in source files
