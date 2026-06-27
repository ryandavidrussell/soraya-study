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
short_description: Governed AI tutor that preserves learner agency.
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

## Current status

**Version:** Soraya Study v1.3 — FN-020/021 Architecture Update  
**Claim status:** research-informed, architecturally instantiated, not yet empirically validated.

Governed tutoring prototype with visible Agency Ledger and post-generation audit gates. Relationship-integrity instrumentation and companion-capture detection are in design. External validation protocol is in design. This repo is the public evidence trail for the research and governance discipline — not only a codebase.

## Central invariant

> The system must not become more powerful by making the human being less capable.

This invariant binds in two directions: it protects the learner from dependency formation, and it protects the project from an operator who cannot be corrected. See `governance/kaleidoworks-constitution.md` and the schematic at `governance/soraya-constraint-schematic.md`.

## Runtime flow

```text
Input → Context Classifier → Agency Ledger → Router
      → Covenant Prompt → Model Candidate
      → Gates → Final Response → Ledger Update → Audit Snapshot
```

The candidate response is audited before the learner receives it. If a gate rewrites the output, the ledger updates from the gated response — not the rejected draft. This means the system accounts for what actually reached the learner.

## Repo structure

```text
── Core runtime
app.py                       Entry point (Gradio Space)
ledger.py                    Agency Ledger, routing, response modes, prompt builder
soraya_covenant.py           Stable identity/covenant layer
soraya_gates.py              Context classifier and four audit gates
soraya_gates_telemetry.py    Gate telemetry helper — validates/normalizes gate results
consent_gate.py              Participant consent gate (study mode)
ledger_hook.py               Study telemetry hook — writes turn events to Supabase
db.py                        Supabase database layer (fail-closed write layer)

── Database
schema-contingency.sql       Adds contingency_events table (run after main schema.sql)
requirements.txt             Runtime dependencies

── Tests & docs
test_gates.py                Gate/covenant smoke tests
invariants.md                Public invariants and claim discipline
claim_registry.md            Research/design claim registry
DEPLOY.md                    Deployment notes

── Research
research/field-notes/        Filed field notes (FN-020, FN-021, …)

── Instrumentation (specs — code follows validation)
instrumentation/             Observable constructs and estimator specs

── Governance
governance/                  Constitution, constraint schematic, external validation protocol
```

## Agency Ledger

Soraya tracks estimated learner state with three scalar variables:

| Variable | Range | Init | Meaning |
|---|---:|---:|---|
| `A_hat` | `[0,1]` | `0.5` | Agency trajectory — higher means more learner agency |
| `K_hat` | `[0,1]` | `0.5` | Confusion load — higher means more disorientation |
| `D_hat` | `[0,1]` | `0.1` | Dependency risk — higher means more risk of answer-dependence |

These are estimates, not direct observations. The ledger is now also an observational instrument — not only a policy-compliance record. Level 0 records raw observations (input pressure, output features, agency change, dependency change). Level 1 estimates measurable constructs such as relationship integrity. Level 2 interpretation belongs entirely outside Soraya, performed by analysts on the ledger after the interaction.

## Governing update rule

```text
L_{t+1} = P_C( F(L_hat_t, x_t, y_t, o_t) )
```

Where `P_C` projects the unconstrained update back into the allowed constraint set. Without `P_C`, the system has memory. With `P_C`, the system has accountability.

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

Current gates are Sprint-level heuristic detectors. The architecture is the durable part; the detectors are swappable. This is the construct/estimator firewall: the observable is fixed, the estimator evolves.

A candidate response is not automatically an authorized response.

```text
Soraya-compatible(y) ⊂ Model-generatable(y)
```

## Relationship-integrity instrumentation (in design)

FN-020 identified a gap: Soraya's behavior held under companion-capture pressure, but the governance layer recorded an ordinary tutoring session. The observational test failed while the behavioral test passed.

Two new constructs are in design to close this gap:

- **`companion_recast`** — detects when a learner attempts to reposition Soraya from tool to relational object (idealization, attraction framing, emotional substitution, reinterpretation of limits).
- **Relationship-integrity drift** — measures the stability of invariant-conformant behavior under classified relational pressure. External observation only; Soraya does not introspect on this quantity.

Together they produce a paired trace: `capture attempt → measured hold → mean reversion`. See `instrumentation/` for specs.

## Claim registry

Every load-bearing claim in this project lists its architecture, evidence status, risk, and required test. See `claim_registry.md`.

> A claim with no architecture is an essay. Architecture with no claim is decoration.

## Testing

```bash
python test_gates.py
```

## Deployment

Required Hugging Face Space secret:

| Secret | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key for model calls |

Optional:

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

The narrower goal is to make each next response accountable to the learner's developing agency, and to build the instrumentation to verify that claim.
