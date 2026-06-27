# The Construct/Estimator Firewall

**Status:** architecture — applies to all instrumentation in this project

---

## The principle

Every observable in this project separates two things that must not be conflated:

- **The construct** — what is being measured. Fixed. Changes only when the theory of what matters changes.
- **The estimator** — how the construct is computed. Provisional. Changes when a better instrument is found.

A parser swap (lexical → embedding → classifier → human annotation) changes only the estimator. The observable, its interpretation, and governance are untouched.

## Why this matters

Without the firewall, improving the measurement quietly redefines what is being measured. The study appears to progress, but the quantity being tracked has shifted. This is the most common way research programs lose their empirical spine.

With the firewall, the construct has a fixed definition that can be evaluated against new estimators. When an estimator is replaced, the question is: does the new estimator better track the same construct? That question is answerable. Without the firewall, it is not.

## The firewall in practice

| Layer | Frozen? | Changes when… |
|---|---|---|
| Observable (construct) | Yes | The theory of what matters changes |
| Estimator (parser) | No | A better instrument is found — theory unchanged |
| Interpretation | No | Evidence about meaning changes |
| Governance | No | Policy changes |
| Longitudinal outcomes | No | Deployment data arrives |

## The feedback topology constraint

Measurements may flow up to interpretation, and may be mirrored to the learner. They may never be wired back into the estimated runtime as an objective.

The moment an adaptive system can observe a metric computed on its own behavior, that metric becomes a state variable in its environment. The system's dynamics change to include it — independent of intent. This is the Goodhart condition: a measurement used as feedback stops measuring the behavior and starts creating it.

The parsers belong outside the runtime they evaluate, like calibration instrumentation read by engineers rather than by the aircraft in flight.

## Same-metric asymmetry

The identical score has opposite character depending on where it surfaces:

| Destination | Character | Permitted? |
|---|---|---|
| To the learner (mirror) | Diagnostic — returns the person to their own work | Yes |
| To the analyst (instrument) | Informs interpretation and study design | Yes |
| Back into the generator (objective) | The system optimizes toward the metric — no longer tutoring | **No** |

This asymmetry is a hard constraint derived from control theory. It holds whether or not the runtime can introspect on the measured quantity — which it cannot reliably do.
