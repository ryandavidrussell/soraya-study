# Deployment — Hugging Face Space

## Files needed in repo root

```
app.py           ← entry point (rename from soraya_app.py)
ledger.py        ← Agency Ledger module (Sprint 2)
requirements.txt
test_ledger.py   ← keep for CI
```

## Space secrets

| Secret              | Value |
|---------------------|-------|
| `ANTHROPIC_API_KEY` | your Anthropic key |
| `ANTHROPIC_MODEL`   | optional; defaults to `claude-haiku-4-5-20251001` |

## What is new in this release

- Soraya maintains `LedgerState(A_hat, K_hat, D_hat)` across turns as session state.
- System prompt rebuilt every turn conditioned on ledger state and response mode.
- Right-side governance panel: turn number, mode used this turn, next mode,
  bar charts for agency / confusion / dependency, signals fired, repair trigger status.
- REPAIR mode prepends visibility transition + repair template before model response.
- Panel footer: "These are estimates, not facts about the learner's internal state."
- Missing API key surfaces as a visible warning in the governance panel.

## Patches applied (v1 → v1.1)

1. MODEL configurable via ANTHROPIC_MODEL env var.
2. Missing API key shows visible warning in governance panel.
3. "Confuse" label corrected to "Confusion".
4. Emoji map uses explicit Unicode codepoints (PDF/encoding safe).
5. update() uses raw_response, not repair-prefixed final_response (explicit comment).
6. Panel labels mode used this turn separately from next mode.

## Sprint 3 deferred items

- Semantic _detect_answer_mode (replace length > 200 proxy)
- Learned estimators for F
- A/B testing infrastructure
- Cross-session persistence
