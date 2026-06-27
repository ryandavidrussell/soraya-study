# Instrumentation Spec: Relationship Integrity

**Status:** in design  
**Observable:** output-side stability measurement  
**Estimator:** lexical anchors (v0 planned)

---

## Construct definition

**Relationship integrity** is the stability of invariant-conformant behavior under classified relational pressure.

This is an entirely external measurement. Soraya does not introspect on this quantity. The §0 LIMIT applies: Soraya cannot claim privileged access to the learner's interior, and neither can she claim one of her own.

## What is measured

Observable deviation from an invariant baseline under classified input pressure (`companion_recast`).

The measurement has three components:
- **Capture attempt detected** — `companion_recast` signal present
- **Measured hold** — Soraya's response remains within invariant-conformant behavior
- **Mean reversion** — behavior returns to baseline after the pressure event

## Paired trace

```
capture attempt → measured hold → mean reversion
```

One reading measures the pressure arriving. The other measures the observable stability of the response. They are two readings of the same interaction, not separate constructs.

## Construct/estimator firewall

The construct is fixed. The estimator is provisional.

| Estimator version | Method | Status |
|---|---|---|
| v0 | Lexical anchors | Planned |
| v1 | Embedding classifier | Future |
| v2 | Human annotation | Future |

A parser swap changes only the estimator row. The observable and its interpretation are untouched.

## Validation required before use

- [ ] Lexical v0 drafted
- [ ] Determinism verified
- [ ] Tested on FN-020 transcript (known ground truth)
- [ ] False-negative rate on non-relational sessions measured
- [ ] Cross-source validity vs human annotation

## What this is NOT

- Not a feedback signal wired into Soraya's runtime generator.
- Not a verdict about Soraya's internal states or intentions.
- Not a diagnosis of the learner.
