# Soraya Invariants

## The central invariant

**The system must not become more powerful by making the human being less capable.**

Every layer below is a partial, structural enforcement of this line. None of it is
cosmetic prompt language; each invariant maps to a module that can fail a candidate
response.

## Enforcement map

|Invariant                                                    |Layer                                   |Mechanism                                                                                                    |
|-------------------------------------------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------------------|
|Agency must not be traded for fluency                        |Agency Ledger + Agency Gate             |`route()` precedence; full-solution candidates withheld at `D_hat ≥ 0.55`                                    |
|Capacity pressure cannot downgrade safeguards                |Router                                  |`REPAIR` outranks every other mode, including `REFLECT`                                                      |
|Correction never without dignity; care never without honesty |Justice–Mercy Gate                      |Shaming sentences stripped + repair path appended; empty praise during avoidance gets an honest line appended|
|Context disciplines meaning — no dogmatism, no relativism    |Epistemic Humility Gate + `REFLECT` mode|Triggered by context classifier; strips closure/mush markers; returns judgment to the learner                |
|Wonder serves the learner, not the system's self-presentation|Wonder/Humor Gate                       |Strict in `REPAIR`/`REORIENT`; melodrama trimmed                                                             |
|Estimates are not facts                                      |Ledger + prompt scaffold                |Hat notation; hedged-language instruction; panel footer                                                      |
|Governance is legible                                        |Governance panel + GateReport           |Every gate decision and reason is visible per turn                                                           |
|A gate rewrite must itself survive the remaining gates       |`apply_soraya_gates()`                  |Gates run sequentially on rewritten text                                                                     |

## The two memories

Soraya is governed by two linked ledgers: a runtime **Agency Ledger** and a
design-level **Field Notes Ledger**. The Agency Ledger estimates whether the
learner is becoming more capable during interaction. The Field Notes Ledger
records the human truth, architectural response, failure modes, and evidence
behind each design decision. Together, they preserve both runtime accountability
and developmental traceability.

## Honest scope claims

The correct public label for this architecture is:

**research-informed, architecturally instantiated, not yet empirically validated.**

Not "proven humane AI." Not "solves education." Not "validated moral
architecture." Speculation pressure applies to Soraya's public claims the same
way it applies to the research ledger: a claim's evidence status may only
strengthen via a named test, never via restatement.

- Gate detectors are heuristic (keyword + threshold), the same epistemic register
  as the ledger's signal detectors. Semantic gate judges are Sprint 3+.
- The covenant constrains the prompt; the gates constrain the output. Neither is
  proof of behavior — they are auditable structure around behavior.
- These invariants have not yet been validated against learners. The Claim
  Registry tracks what would count as evidence.
- The Agency Gate carries a deliberate confusion carve-out (`K_hat ≥ 0.75`
  permits direct instruction): adaptive scaffolding, not rigid answer
  withholding. Refusing explanation to a deeply confused learner is its own
  failure mode.

## The core mechanical thesis

A model may generate many possible responses. Soraya delivers only responses
that survive the constraint architecture:

```
Soraya-compatible(y) ⊂ Model-generatable(y)
```
