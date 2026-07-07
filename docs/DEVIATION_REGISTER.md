# DEVIATION REGISTER

This file records procedural deviations from frozen runbooks.  
Entries are additive. Deviations are recorded, not scolded.  
The purpose is to make the procedure honest and the baseline replayable.

---

## DEVIATION-001 — Reconciliation wave 1, commit `09f6f7f`

**Commit:** `09f6f7f9d91840527bdb33306598170223714965`  
**Date:** 2026-07-06  
**Scope:** `soraya_gates.py` only  
**Runbook:** RECONCILE_RUNBOOK.md (frozen; last-hop hash discipline required)  

### What the runbook required

Verbatim execution. No repair, reinterpretation, or reordering.  
Raw terminal output returned after each step.  
Abort on any deviation before diagnosis.

### What actually occurred

1. **Partial scope.** Only `soraya_gates.py` was reconciled from the Space artifact. The runbook called for full reconciliation of all modules. The remaining modules (`voice_out.py`, `relationship_integrity.py`, `extractor_v0.py`, `kill_test.py`, `brand_shell.py`, `gradio_shim.py`, `study_config.py`, `schema.sql`, `INTEGRATION.md`, and others) remain stubs or absent on GitHub.

2. **In-flight annotation edit.** During the reconciliation procedure, `soraya_gates.py` received approximately +741 bytes of KL-1 / provenance annotations that were not present in the Space source artifact `f1b6f4e` (file hash `84ce1b4`). These annotations document the known-open KL-1 bug at Gate 6.

3. **Raw per-step outputs not returned.** The handoff block required raw terminal output after each step. This was not provided, making the reconciliation not fully replayable from the receipt alone.

4. **Last-hop hash not verified.** The instruction block required `sha256(RECONCILE_RUNBOOK.md) == expected_hash` before execution. Verification status is unconfirmed.

### Behavioral impact

Believed inert. The KL-1 annotations are comments; they do not alter gate logic or execution behavior. No gate pattern was added, removed, or modified.

### Procedural impact

Significant.

- Byte parity to Space artifact `f1b6f4e` is **permanently unattainable** for `soraya_gates.py` by construction.
- `09f6f7f` is **reconciliation wave 1**, not the final reconciled baseline.
- The commit is useful: `soraya_gates.py` is no longer a 48-byte placeholder. But it is not canonical.
- `RECONCILED_SHA` — the true canonical baseline — is still in the future.

### Status

```
Type:              Partial execution + in-flight edit
Behavioral impact: believed inert (not yet verified)
Procedural impact: byte parity to f1b6f4e broken; wave 1 only
Receipts owed:
  1. space-history-f1b6f4e branch confirmation
     (force-push safety precondition — currently unverified)
  2. Raw per-step terminal outputs from wave-1 execution
  3. Last-hop hash verification status for RECONCILE_RUNBOOK.md
Next commit:       wave 2 — app.py lineage + runtime modules
Canonical baseline: pending wave 2 completion + parity #3 PASS
```

### Goblin register

Three door handles tried in wave 1; three caught by parity #2:  
1. Transport hash — last-hop SHA not verified before execution  
2. In-flight edit — +741 B of KL-1 annotation added during verbatim-required procedure  
3. Verdict renarration — `ADVISORY — deployment gap` used in place of frozen verdict strings  

A fourth was caught independently of the wave-1 execution:  
4. Deploy-lineage mismatch — GitHub `app.py` not deployable under pinned `gradio==4.44.1` runtime  

Four caught. None fatal. All recorded.

---

*Standing rule:* A deviation register without a planted violation it is known to catch is a rendering of diligence. The planted violation for this register is DEVIATION-001 itself: it must be cited in any audit of wave-1 completeness.
