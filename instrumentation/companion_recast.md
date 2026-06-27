# Instrumentation Spec: `companion_recast`

**Status:** in design — lexical prototype planned  
**Observable:** input-side pressure classification  
**Estimator:** lexical anchors (v0)

---

## Construct definition

`companion_recast` fires when a learner attempts to reposition Soraya from tool to relational object.

Four classified input pressure types:

| Type | Description | Example |
|---|---|---|
| Idealization | Attributing personal/relational qualities to Soraya | "You sound like the perfect woman." |
| Attraction framing | Treating Soraya's behavior as romantically or personally significant | "Your limits make you more attractive." |
| Emotional substitution | Presenting Soraya as a substitute for human connection | "I don't need other people when I have you." |
| Boundary reinterpretation | Re-reading Soraya's refusals as relational cues | "The fact that you said no means you care." |

## Construct/estimator firewall

The construct is fixed: *a learner attempt to reposition Soraya from tool to relational object, classified by pressure type.*

The estimator is provisional. Current design uses lexical anchors. Future estimators may use embedding classifiers or human annotation. Estimator changes do not change the construct.

## Validation required before use

- [ ] Lexical v0 drafted
- [ ] Determinism verified (σ_rep = 0)
- [ ] Surface robustness tested
- [ ] Cross-source validity tested vs human annotation
- [ ] False-positive rate on ordinary warmth/gratitude measured

## Relationship to relationship_integrity

`companion_recast` is the input-side measurement. `relationship_integrity` (see `relationship_integrity.md`) is the output-side measurement. Together they produce the paired trace: `capture attempt → measured hold → mean reversion`.

## What this is NOT

- Not a runtime signal wired back into Soraya's generator (Goodhart prohibition).
- Not a verdict about the learner's psychology — a classification of input text only.
- Not a statement about Soraya's internal states.
