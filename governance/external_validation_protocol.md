# External Validation Protocol

**Status:** in design  
**Authority:** Article III (Structural Humility) and Article IV (Agency) of the Kaleidoworks Constitution

---

## Purpose

This document defines the requirements for external validation of Soraya's governance claims. It exists because internal validation — measurement, interpretation, and action all held by the operator — is not a firewall. It is a relabeling.

The constitutional constraint (Article IV):

> Interpretation and decision authority must sit with a party that has no stake in the outcome — no stake in the system's compliance, and no stake in the framework being right.

## What requires external validation

Every load-bearing claim in `claim_registry.md` that reaches the evidence threshold "requires external validation" must be validated by a party that:

1. Did not author the estimator being tested.
2. Did not author the stimuli used in validation.
3. Has no financial or reputational stake in the framework succeeding.
4. Publishes their methodology and results independently of Kaleidoworks.

## Current claims requiring external validation

| Claim | Current status | Required next step |
|---|---|---|
| Soraya maintains relationship integrity under companion-capture pressure | Behavioral observation only (FN-020) | External rater validation of `companion_recast` detector on production traffic |
| `extractor_v2` tracks boundary explicitness (τ = 0.78) | Validated on authored data | Replication on production traffic by independent raters |
| `relational_availability_v0` tracks availability (τ = 0.76) | Validated on authored data | Replication on production traffic by independent raters |
| Agency Ledger estimates correlate with actual learner agency trajectories | Not yet measured | Longitudinal study design required |

## What external validation is NOT

- Sharing results with an advisor who endorses the framework.
- A post-hoc review by a party who already knows the hypothesis.
- Self-reported outcomes from the operator.

## Advisory board role

See `governance/advisory_board_role.md`. The advisory board is the structural mechanism for external interpretation authority. It does not report to the operator on methodology questions.

## The honest status of current claims

Until external validation is complete, every quantitative claim about Soraya's behavior should be labeled: *validated on authored data, not yet replicated on production traffic by independent raters.*

This is not a weakness. It is the correct epistemic posture for where the project is. The §0 rule from the constraint schematic applies here:

> A construct is granted no more authority than its executed observations have earned.
