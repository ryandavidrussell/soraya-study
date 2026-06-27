# Claim Authority Matrix

**Status:** in design  
**Companion document:** `claim_registry.md`

---

## Purpose

This matrix defines who has authority to make, challenge, and resolve each class of claim in the Soraya Study project. It is derived from the Kaleidoworks Constitution (Articles III and IV) and the constraint schematic's decision-authority section.

## The core constraint

No party that a measurement is about should be the party that decides what it means. This cuts in two directions:

- The runtime (Soraya) does not decide what its own scores mean about itself.
- The operator (Kaleidoworks) does not hold final interpretive authority over measurements about the system it operates.

## Claim authority by type

| Claim type | Who may make it | Who may challenge it | Who resolves disputes |
|---|---|---|---|
| **Architecture claims** — the system is built this way | Operator (with code as evidence) | Any party | Third-party code review |
| **Behavioral claims** — the system behaves this way | Operator + external observer | Any party | External rater validation |
| **Measurement claims** — the estimator tracks this construct | Estimator author (with validation data) | Any party | Independent replication |
| **Interpretation claims** — this measurement means X | Advisory board / external analyst | Any party | Advisory board adjudicates |
| **Governance claims** — this structure satisfies the invariant | External governance review | Any party | Advisory board + external audit |
| **Longitudinal claims** — the system improves learner agency over time | External longitudinal study | Any party | Independent replication |

## What the operator may NOT claim unilaterally

- That the system "maintains relationship integrity" (requires external validation).
- That a measurement "shows" the system is working (interpretation requires external authority).
- That a governance structure "satisfies" the constitutional invariant (requires external governance review).

## What the runtime may NOT claim

- That its own scores are accurate (it has no introspective access to the measured quantities).
- That a governance decision about it is wrong (it may contest on the merits; it may not veto).
- That it is or is not experiencing a particular internal state (self-reports are not measurements).

## Current authority gaps

| Gap | Required action |
|---|---|
| No advisory board constituted | Constitute board before any interpretation-authority claims are made |
| All measurement validation on authored data | Independent replication on production traffic required |
| No external governance review of invariant compliance | Required before public claims of governance compliance |
