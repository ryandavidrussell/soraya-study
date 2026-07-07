# Schematic Amendment — KL-9 and Invariant 19

**Amends:** Soraya Architecture Schematic v1.6.0-definitive  
**Authority:** PARITY RUN #2 finding, 2026-07-07  
**Companion:** `DEVIATION_REGISTER.md`, `PARITY_REPORT_2_REISSUED.md`  

This document records two additions to the architecture that parity #2 earned.  
Neither was anticipated in v1.6.0-definitive. Both are required by the evidence.

---

## KL-9 — Runtime lineage split

```
KL-9 — Runtime lineage split
Status: confirmed open
Source: PARITY RUN #2, 2026-07-07
```

### Finding

Parity run #2 found that `soraya_gates.py` convergence did not imply deployable artifact convergence.

The app/runtime lineage is split:

| Property | Space app.py | GitHub app.py |
|----------|-------------|---------------|
| Version string | v1.4.2 | v1.4.4 |
| Size | 49,312 bytes | 30,587 bytes |
| Identity | `localStorage` direct | `gr.BrowserState` |
| Gradio compat | `gradio==4.44.1` ✓ | `gradio==4.44.1` ✗ |
| Production receipts | all observed behavior | none |
| doc upload, output hygiene, contingency hooks | present | absent |

`gr.BrowserState` requires Gradio 5. The Space runtime is pinned to `gradio==4.44.1`. Deploying GitHub `app.py` to the Space would break the running application.

### Ruling

**Space `app.py` is wave-2 canonical.**

Receipts attach to artifacts. Every participant-facing behavior ever observed attaches to the Space `app.py` lineage. The Space file carries the production reality; the GitHub file carries an unreceipted future design that is incompatible with the current pinned runtime.

**GitHub `app.py` is not deployable under the pinned runtime.**  
It is not deleted. It is parked as the design specification for the Gradio 5 upgrade.

**`gr.BrowserState` is demoted to `feature/gradio-5-browserstate`.**  
A Gradio 4→5 upgrade is a deliberate project, not a side effect of reconciliation. With `starlette` and `websockets` pins in play, it is not a side quest.

### Consequence

No Space redeploy or force-push may occur until the app/runtime lineage is reconciled into GitHub (wave 2). The redeploy button is currently a self-destruct button.

### Graduation path

KL-9 closes when:
1. Space `app.py` is committed to GitHub main (wave 2)
2. `requirements.txt` / dependency pins are reconciled
3. Parity #3 confirms `verdict_vector(module) == verdict_vector(space)` under the pinned runtime
4. Space redeploy from reconciled commit succeeds without bricking the application

---

## Invariant 19 — Deployability is part of parity

Added to the standing invariant list after §23 of v1.6.0-definitive.

```
19. DEPLOYABILITY IS PART OF PARITY
    Source parity is insufficient if the reconciled repo cannot run
    under the pinned Space runtime. Runtime pins, app lineage, and
    Space frontmatter are provenance surfaces. A reconciled repo that
    would brick the Space on redeploy is not a deployable baseline.
    It is a deployment hazard wearing a baseline's clothing.
```

Corollary: parity runs must include a runtime compatibility check — verifying that the target modules are executable under the pinned SDK version — not only a symbol-resolution check.

---

## Revised wave plan

### Wave 1 — Gates *(landed, partial)*

- **Commit:** `09f6f7f`
- **Result:** `soraya_gates.py` no longer a placeholder
- **Deviation:** +741 B KL-1 annotation added in-flight; byte parity to `f1b6f4e` broken
- **Status:** useful partial reconciliation; not canonical baseline
- **Behavioral receipts:** void pending rerun

### Wave 2 — Runtime / app lineage *(next)*

Canonical source: Space `app.py` and runtime modules.

Actions:
- Bring Space `app.py` into GitHub main (preserve `localStorage` identity path, doc-upload deps, contingency hooks)
- Bring Space runtime modules: `voice_out.py`, `relationship_integrity.py`, `extractor_v0.py`, `kill_test.py`, `brand_shell.py`, `gradio_shim.py`
- Bring `survey_items.py` (draft placeholder — flag IRB status)
- Bring `study_config.py`, `schema.sql`, `contingency_hook.py`, `db_contingency_patch.py`
- Bring docs: `INTEGRATION.md`, `SPEC_relationship_integrity.md`, `analysis_schema.md`, `invariants.md`, `transform_exports.py`
- Archive patch archaeology: `apply_soraya_final_patches.py`, `app_py_consent_wiring.py`, `verify_v1_4_1.py`, `soraya_visible_output_hygiene_hf_v2.patch`, space-named files (rename on intake)
- Reconcile `README.md`: preserve Space YAML frontmatter; correct version claim from v1.2/four-gates to v1.5.0/seven-gates
- Reconcile `requirements.txt` / dependency pins against Space runtime
- Do **not** introduce `gr.BrowserState` — that goes to `feature/gradio-5-browserstate`

Preconditions before wave 2 commit:
- `space-history-f1b6f4e` branch confirmed to exist
- DEVIATION-001 receipts satisfied (raw per-step outputs, last-hop hash status)

### Wave 3 — Build identity

- Add `SORAYA_BUILD_SHA`, `SORAYA_CRITERIA_SHA`, `SORAYA_REGISTRY_SHA` to runtime
- Makes the next parity run self-identifying
- Does not bless the artifact; identity ≠ verification

### Wave 4 — Parity #3

Run after waves 2 and 3.

Expected targets:
- `verdict_vector(module) == verdict_vector(space)` under pinned runtime
- `SHA(space) == SHA(deploy_commit)`
- Runtime compatibility check: all modules execute under `gradio==4.44.1`

Only after parity #3 PASS: consider Space redeploy / force-push.

### Wave 5 — Acceptance battery and KL-1

After deployable parity:
1. Build acceptance battery (`tests/soraya_acceptance.py`)
2. Fix KL-1 (Gate 6 quotation-context guard)
3. Rerun FN-027 reproduction
4. Rerun Gates 5–6 gold set against reconciled live tuple idiom
5. Update `registry/constants.yaml` only after fresh receipts
6. Graduate thresholds if results pass; record graduation as a row, not a silent edit

---

## Field note

The architecture did not merely audit Soraya.  
It audited the hands touching Soraya.  

Which is annoying.  
Which is governance.
