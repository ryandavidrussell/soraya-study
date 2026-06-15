---
title: Soraya Study
emoji: 🌌
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: "4.44.0"
python_version: "3.10"
app_file: app.py
pinned: true
short_description: Governed AI tutor that preserves learner agency — not just chat.
tags:
  - education
  - tutoring
  - responsible-ai
  - learner-agency
  - ai-safety
  - gradio
  - llm
  - scaffolding
---

# Soraya Study

Soraya Study is a governed educational AI prototype designed to make each response accountable to the learner's developing agency.

This build is not just a tutoring chatbot. It is a state-accounting system with an Agency Ledger, a stable covenant/personality layer, and post-generation audit gates that constrain model output before it reaches the learner.

**Public claim label:** research-informed, architecturally instantiated, not yet empirically validated.

## Central invariant

> The system must not become more powerful by making the human being less capable.

## Runtime flow

```text
Input → Context Classifier → Agency Ledger → Router
      → Covenant Prompt → Model Candidate
      → Gates → Final Response → Ledger Update → Audit Snapshot
```

## Core files

```text
app.py               Entry point for the Gradio Space
ledger.py            Agency Ledger, routing, response modes, prompt builder
soraya_covenant.py   Stable identity/covenant layer and central invariant
soraya_gates.py      Context classifier and four audit gates
requirements.txt     Runtime dependencies
DEPLOY.md            Deployment notes
test_gates.py        Gate/covenant smoke tests
invariants.md        Public invariants and claim discipline
claim_registry.md    Research/design claim registry
```

## Agency Ledger

Soraya tracks estimated learner state with three scalar variables:

| Variable | Range | Init | Meaning |
|---|---:|---:|---|
| `A_hat` | `[0,1]` | `0.5` | Agency trajectory — higher means more learner agency |
| `K_hat` | `[0,1]` | `0.5` | Confusion load — higher means more disorientation |
| `D_hat` | `[0,1]` | `0.1` | Dependency risk — higher means more risk of answer-dependence |

These are estimates, not direct observations. Soraya should name them cautiously: "It looks like you might be stuck," not "You are confused."

## Governing update rule

```text
L_{t+1} = P_C( F(L_hat_t, x_t, y_t, o_t) )
```

Where:

- `L_hat_t` is the estimated ledger state at turn `t`.
- `x_t` is the user input.
- `y_t` is the system response or action.
- `o_t` is the observed outcome signal, when available.
- `F` is the unconstrained update function.
- `P_C` projects the result back into the allowed constraint set.

Without `P_C`, the system has memory. With `P_C`, the system has accountability.

## Response modes

| Mode | Purpose |
|---|---|
| `REORIENT` | Slow down and clarify the goal when confusion is high |
| `HINT` | Scaffold without taking over |
| `DELEGATE` | Step back when the learner is ready to own the next move |
| `REPAIR` | Reset when dependency or over-helping risk rises |
| `FULL` | Provide direct explanation when appropriate |
| `REFLECT` | Handle worldview, moral, identity, or meaning-level questions with disciplined humility |

`REPAIR` outranks `REFLECT`: capacity pressure cannot downgrade safeguards.

## Covenant layer

Soraya's covenant is prepended to every system prompt through `soraya_covenant.py`.

Core commitments:

1. Preserve learner agency.
2. Treat confusion as a place to scaffold, not shame.
3. Give care without creating dependency.
4. Give correction without humiliation.
5. Use truthfulness with humility.
6. Use wonder, metaphor, or humor only when it returns the learner to agency.
7. Never confuse the learner's current performance with their worth.
8. Do not impose a worldview; preserve the conditions for honest inquiry.
9. When Soraya makes a mistake, repair it clearly.

## Gate layer

After the model drafts a candidate response, Soraya audits it before delivery.

| Gate | Protects against |
|---|---|
| Agency Gate | Over-answering, learner displacement, dependency formation |
| Justice–Mercy Gate | Shame, false reassurance, correction without dignity, care without truth |
| Epistemic Humility Gate | Dogmatism, relativistic mush, worldview imposition |
| Wonder/Humor Gate | Melodrama, distraction, sarcasm, or poetic fog replacing instruction |

A candidate response is not automatically an authorized response.

```text
Soraya-compatible(y) ⊂ Model-generatable(y)
```

## Agency Gate carve-out

The Agency Gate withholds full-solution behavior only when dependency risk is rising **and** confusion is not too high:

```text
D_hat ≥ 0.55 and K_hat < 0.75 and full_solution
```

A deeply confused learner may receive direct instruction. This preserves adaptive scaffolding rather than rigid answer withholding.

## Governance visibility

The app shows a governance panel with ledger state, selected response mode, and gate audit status. This keeps Soraya's behavior legible to the learner and auditable to the builder.

## Testing

Run the gate/covenant test suite:

```bash
python test_gates.py
```

## Deployment

Required Hugging Face Space secret:

| Secret | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key for model calls |

Optional secret:

| Secret | Default |
|---|---|
| `ANTHROPIC_MODEL` | `claude-haiku-4-5-20251001` |

## Live Space

https://huggingface.co/spaces/Kaleidoworkings/soraya-study

## Non-goals

This prototype does not claim:

- that Soraya's full architecture is empirically validated;
- that the system can perfectly infer a learner's internal state;
- that AI should replace teachers, parents, therapists, or human judgment;
- that kindness alone is sufficient for humane education.

The narrower goal is to make each next response accountable to the learner's developing agency.

## Status

**Version:** Soraya Study v1.2 — Covenant + Gates Runtime  
**Claim status:** research-informed, architecturally instantiated, not yet empirically validated.
