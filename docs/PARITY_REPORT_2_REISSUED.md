# PARITY REPORT \#2 — REISSUED VERDICT

**Supersedes:** `docs/PARITY_REPORT_2.md` (first issue, 2026-07-07T01:12Z)  
**Reason for reissue:** Prior verdict used `ADVISORY — deployment gap confirmed, no provenance split`.  
`ADVISORY` is a frozen verdict string with a defined meaning (upstream guard degraded dependent verdicts).  
`deployment gap` is a diagnosis. Neither applies as a primary verdict here.  
Verdicts are frozen for exactly this reason. Renarration is not permitted.

**Run date:** 2026-07-07  
**Targets:** GitHub `main` @ `09f6f7f` (module) · Hugging Face Space (served artifact, prior build `f1b6f4e`)

---

## Reissued verdict — frozen strings

```
== PARITY RUN #2 — REISSUED VERDICT ==
Inventory/content parity:  ARTIFACT MISMATCH — open, scope narrowed
  Converged:
    soraya_gates.py surface, modulo +741 B of reconciliation annotations
  Split:
    app.py — divergent lineages (see §3 below)
    7 runtime modules stubbed or absent on GitHub
    relationship_integrity.py: 58 B repo stub vs 23,921 B Space artifact
    survey_items.py: 0 B repo stub vs 1,642 B Space draft
    README / Space frontmatter / documentation surface still divergent
Verdict-vector parity:     INDETERMINATE
  Reason: acceptance battery not yet built;
          probe cannot reach its condition
SHA identity:              unmet by construction until redeploy
Diagnosis (not verdict):   deployment gap;
                           Space ahead on production app/runtime features;
                           repo ahead on gate annotations
Behavioral verdicts:       blocked
```

---

## §1 — soraya_gates.py parity (converged with deviation)

| Property | Space | GitHub `09f6f7f` |
|----------|-------|------------------|
| File size | 25,828 bytes | 26,569 bytes |
| sha256[:32] | `7a6237924dc92b73…` | distinct |
| KL-1 annotation | **absent** | **present** (lines 54–56, 441–442) |
| Gate logic (functional) | equivalent | equivalent |
| Byte parity to `f1b6f4e` | attainable | **unattainable by construction** |

The +741 bytes are KL-1 documentation added during the reconciliation procedure.  
Behaviorally inert. Procedurally load-bearing: byte parity to the Space source artifact is permanently broken for `soraya_gates.py` at `09f6f7f`.  
See `DEVIATION_REGISTER.md` for the full deviation record.

---

## §2 — Runtime modules: stub table

| File | Space bytes | GitHub bytes | Gap |
|------|------------|--------------|-----|
| `relationship_integrity.py` | 23,921 | 58 | 23,863 |
| `extractor_v0.py` | 11,101 | 48 | 11,053 |
| `voice_out.py` | 9,838 | 45 | 9,793 |
| `kill_test.py` | 9,383 | 45 | 9,338 |
| `brand_shell.py` | 9,488 | 47 | 9,441 |
| `gradio_shim.py` | 9,034 | 47 | 8,987 |
| `survey_items.py` | 1,642 | 0 | 1,642 |

All seven are architecture §8 modules.  
All seven carry production substance on the Space.  
All seven are stubs or empty on GitHub `09f6f7f`.  
These are wave-2 reconciliation targets.

---

## §3 — app.py: lineage split (central finding)

| Property | Space | GitHub `09f6f7f` |
|----------|-------|------------------|
| Declared version | v1.4.2 | v1.4.4 |
| File size | **49,312 bytes** | 30,587 bytes |
| Identity mechanism | `localStorage` direct | `gr.BrowserState` |
| `gr.BrowserState` | commented out (requires Gradio 5) | implemented |
| Gradio compatibility | **gradio==4.44.1 ✓** | **gradio==4.44.1 ✗** |
| Production receipts | all observed behavior | none |
| Carries: doc upload | yes | no |
| Carries: output hygiene | yes | no |
| Carries: consent wiring | yes | no |
| Carries: contingency hooks | yes | no |
| Carries: pdfplumber / python-docx deps | yes (fingerprinted) | no |

**Runtime blocker:** GitHub `app.py` depends on `gr.BrowserState`, which requires Gradio 5.  
The Space runtime is pinned to `gradio==4.44.1`.  
Executing a Space redeploy from current GitHub `main` would brick the Space.  
The redeploy button is currently a self-destruct button.

**Lineage ruling:**

> Space `app.py` is wave-2 canonical.  
> GitHub `app.py` is not deployable under the pinned runtime.  
> `gr.BrowserState` is demoted to `feature/gradio-5-browserstate`.  
> A Gradio 4→5 upgrade is a deliberate project, not a side effect of reconciliation.

Reason: receipts attach to artifacts. Every participant-facing behavior ever observed attaches to the Space `app.py` lineage.

---

## §4 — README: stale version claim

Space `README.md` declares:

```
**Version:** Soraya Study v1.2 — Covenant + Gates Runtime
```

and references `four audit gates`. The Space runs seven gates.  
The YAML frontmatter (lines 1–20) is deployment config and must be preserved per architecture §3.3.  
Only the documentation content beneath it is updated during wave-2 reconciliation.

---

## §5 — Files present on Space, absent from GitHub `09f6f7f`

Patch archaeology and production modules not yet reconciled into the repo:

| File | Space bytes | Destination |
|------|------------|-------------|
| `INTEGRATION.md` | 5,623 | repo root or `docs/` |
| `SPEC_relationship_integrity.md` | 12,189 | `docs/` |
| `analysis_schema.md` | 8,663 | `docs/` |
| `invariants.md` | 4,554 | `docs/` |
| `schema.sql` | 4,630 | repo root |
| `transform_exports.py` | 19,603 | repo root |
| `test_gates.py` | 8,026 | `tests/` (pre-battery) |
| `apply_soraya_final_patches.py` | 17,034 | `archive/space_patch_archaeology/f1b6f4e/` |
| `app_py_consent_wiring.py` | 2,586 | `archive/space_patch_archaeology/f1b6f4e/` |
| `contingency_hook.py` | 3,545 | repo root |
| `contingency audit 2.py` | 7,360 | archive (spaces in name — rename on intake) |
| `db contingency patch.py` | 3,538 | archive (spaces in name — rename on intake) |
| `verify v1 4 1.py` | 7,248 | archive (spaces in name — rename on intake) |
| `soraya_visible_output_hygiene_hf_v2.patch` | 7,147 | `archive/space_patch_archaeology/f1b6f4e/` |
| `SORAYA_FINAL_PATCH_README.md` | 1,724 | `archive/space_patch_archaeology/f1b6f4e/` |

---

## §6 — Blockers before any force-push (five, ordered)

1. **DEVIATION note for `09f6f7f`** — records partial scope and in-flight annotation edit. See `DEVIATION_REGISTER.md`.
2. **`space-history-f1b6f4e` branch confirmation** — the safety precondition for force-push is currently unverified. Branch must exist and be verified before any force-push is attempted.
3. **Raw per-step execution outputs** — the handoff block required raw terminal output after each step. Without it, the reconciliation is not fully replayable.
4. **app.py lineage reconciliation** — Space `app.py` must be brought into GitHub before any redeploy. GitHub `app.py` is not deployable.
5. **Wave-2 module reconciliation** — the seven stub files must be reconciled before the repo can be called a deployable baseline.

---

## §7 — Space file manifest (sha256[:32], fetched 2026-07-07T01:12Z)

```
soraya_gates.py               25828  7a6237924dc92b738e8a2e370d3d3e15
app.py                        49312  709e60f5e295fdd7bbef24c46a6d7ba8
ledger.py                     20711  edbeedd0814b71b37028444f88c4f41d
relationship_integrity.py     23921  4d1727dec94d05a264d8cf18b9e138f3
extractor_v0.py               11101  a972e18d9b0ff2ac4bb99f0a7d645219
db.py                         11155  324e466af3ce45f92fac2c4747a6e02f
voice_out.py                   9838  4a0f8b7532cad18a54df39da16853c7e
brand_shell.py                 9488  81c45b5ae2bb1add8a808d747909a329
kill_test.py                   9383  f068b079a05f404af436939590b48993
gradio_shim.py                 9034  6c0e19c53abb688ac30eb73abcc03adb
consent_gate.py                8727  a21f57cd5573cf16067490783ac73d3a
transform_exports.py          19603  a82216bf60ee9a2930dd9f4fff2319ab
apply_soraya_final_patches.py 17034  d9426f3cdbc51ded31f4430eae5def82
SPEC_relationship_integrity   12189  2debba7928b0fabc1cdeda98105b7248
db.py                         11155  324e466af3ce45f92fac2c4747a6e02f
analysis_schema.md             8663  392e32dce79db3f07043bb016a2c98bd
test_gates.py                  8026  3d3e3afacc4575fbd802480da2d65de6
contingency_audit_2.py         7360  8c5f0859f4d2513910d1606052966f28
verify_v1_4_1.py               7248  a62472e2ce616434212c4c1d348a09e9
soraya_...hygiene_hf_v2.patch  7147  e78b8875f65e8b337e55ba137786dfb6
study_config.py                5094  821423451f71bfd53e141b1bf683de97
schema.sql                     4630  a99d6fdfd46553b5c1b13c137c7c5b1d
invariants.md                  4554  8067d16566a07fe78cdfacb370a5c4aa
consent_gate.py                8727  a21f57cd5573cf16067490783ac73d3a
ledger_hook.py                 3463  0558d05cbb1651739f5c649bacb57aa7
contingency_hook.py            3545  dcd30681dfeddc1d046e24722a6dac8f
db_contingency_patch.py        3538  31e3a737490cdd728b2e14dd9d135c52
app_py_consent_wiring.py       2586  7be9472c4805c527bc51dea3b541933d
schema_contingency.sql         2187  d00cb5cec9859a1c7c7c8dc06a79f8b0
survey_items.py                1642  dc4446863eba61428836363cac5e3678
README.md                      5962  cbc61cbf38aec0116754b937216c2487
soraya_covenant.py             1436  4fb235f913bd43221916a56c1ad5f6af
requirements.txt                113  0367088bca89a0c85c5c9cf67d028093
```

---

*Field note:*  
The evidence trail is now honest enough to test Soraya, and disciplined enough to catch its own executors.  
The system caught not just artifact drift but procedure drift: transport hash, in-flight edit, verdict renarration, deploy-lineage mismatch.  
Four door handles tried. Four caught. That is the architecture working.
