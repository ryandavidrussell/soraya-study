# WAVE2_RUNBOOK — repo becomes deployable, Space deploys from repo

**Resolves:** the deployment gap (PARITY_REPORT_2_REISSUED), owed receipt #1,
KL-9 (app.py lineage fork).
**Order is load-bearing. Execute steps in sequence. Return raw terminal
output after each step. Stop on any ABORT. Do not repair, reinterpret, or
reorder.** Last-hop rule (INV17): the executor verifies blob identity from
GitHub before starting (see Step 0). Do not execute pasted copies. Do not
execute r2 (blob b9b3e41).

Authoring principle for this wave: **nothing that already exists is retyped.**
Every existing file travels by git, byte-exact — no intermediary in the loop.
Only four things are authored fresh: this runbook, the deploy guard, the
inert build-identity module, and the README documentation body.

Prerequisites: git; GitHub PAT with push to `ryandavidrussell/soraya-study`;
HF write token for `Kaleidoworkings/soraya-study`.

-----

## Disposition manifest

Pinned inputs: Space `f1b6f4e469beefaec6257286bc5aec0110d570a1` · GitHub
main `0bed015…` · protected gates blob `ae9e958…` (26,569 B, self-citing).

|Disposition                |Files                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |Rule                                                                                                                                                           |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
|**FROM-SPACE** (byte-exact)|app.py · ledger.py · soraya_covenant.py · consent_gate.py · db.py · ledger_hook.py · study_config.py · survey_items.py · voice_out.py · brand_shell.py · gradio_shim.py · relationship_integrity.py · extractor_v0.py · kill_test.py · test_gates.py · transform_exports.py · contingency_hook.py · schema.sql · schema_contingency.sql · requirements.txt · .gitattributes · assets/ · INTEGRATION.md · SPEC_relationship_integrity.md · analysis_schema.md · claim_registry.md · invariants.md · DEPLOY.md · HOTFIX_v1_2_4.md|Runtime tree wins wholesale; Space paths kept exactly (no reorganizing — path moves are edits)                                                                 |
|**KEEP-MAIN** (protected)  |soraya_gates.py (`ae9e958`) · docs/ · governance/ · research/ · instrumentation/ · CLAUDE.md · .mcp.json                                                                                                                                                                                                                                                                                                                                                                                                                       |Main is ahead-by-annotation on gates; governance surfaces are repo-lineage. Direction note: on this one runtime file, **the Space receives the repo's version**|
|**PRESERVE→BRANCH**        |main's v1.4.4 app.py (BrowserState lineage)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |Pushed as `feature/gradio-5-browserstate` **before** replacement — receipts attach to artifacts; nothing is destroyed                                          |
|**MOVE→archive/**          |apply_soraya_final_patches.py · app_py_consent_wiring.py · "contingency audit 2.py" · "db contingency patch.py" · "verify v1 4 1.py" · soraya_visible_output_hygiene_hf_v2.patch · SORAYA_FINAL_PATCH_README.md                                                                                                                                                                                                                                                                                                                |Declared delta: receipts kept, off the serving surface                                                                                                         |
|**DELETE**                 |schema-contingency.sql (hyphen)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |Superseded by Space's underscore twin                                                                                                                          |
|**MERGE**                  |README.md                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |Space frontmatter preserved verbatim; documentation body replaced (Step 5)                                                                                     |
|**NEW**                    |deploy_guard.sh · build_identity.py · archive README                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |Authored below; build_identity ships inert — wiring into app.py is deferred to the KL-1 window so wave-2 app.py stays byte-identical to production             |

Findings opened by this manifest, for the register: **W2-F1** survey_items.py
is a 1,642 B draft on both lineages — locate the live instrument source
(likely inlined in app.py) before study launch. **W2-F2** frontmatter
`sdk_version: 4.44.0` vs `gradio==4.44.1` pin skew — record only, do not
touch pins this wave. **W2-F3** claim_registry.md / invariants.md may differ
between lineages — Step 4 logs the diff; divergence goes to operator ruling,
not silent resolution.

-----

## Step 0 — PRECONDITION + TWO INDEPENDENT ABORTS

**PRECONDITION — revision receipted:**
Diff r2 (blob `b9b3e41dd02cd310fb927d7324636674009539e1`) against the authored
draft (blob `5e74293b…`). Delta must be prose-only: no change inside frozen
regions (commands, heredocs, ABORT strings, manifest rows). Prose-only →
proceed. Any executable-line change → stop; r1 syntax receipts are void;
re-verify embedded scripts from r3 before continuing.

**ABORT 0A — Space pin moved:**

```bash
git clone https://huggingface.co/spaces/Kaleidoworkings/soraya-study space
cd space
git rev-parse HEAD
```

**ABORT** unless it prints `f1b6f4e469beefaec6257286bc5aec0110d570a1` — the
window closed; re-pin before anything else.

**ABORT 0B — instruction identity (non-circular):**

```bash
git remote add github https://github.com/ryandavidrussell/soraya-study.git
git fetch github
git rev-parse github/main:docs/WAVE2_RUNBOOK.md
```

**ABORT** unless it prints the r3 blob SHA (the SHA of this file as landed on
`github/main`). The copy being executed must be that checkout — not a pasted
copy, not r2. Content addressing over the evidence trail is the seal; the
transport surface has no door left to watch.

**Both ABORTs and the precondition must pass before any push touches either
remote.**

```bash
git push github HEAD:refs/heads/space-history-f1b6f4e
git ls-remote github refs/heads/space-history-f1b6f4e
```

Must print `f1b6f4e469b…`. **Receipt #1 closes here.** ABORT on any failure —
everything below presupposes this branch exists.

**ON ABORT:** return the ABORT label (0A or 0B), the exact output that
triggered it, and stop. Do not diagnose. Do not continue.

## Step 1 — Preserve the BrowserState lineage before it leaves main

```bash
git push github github/main:refs/heads/feature/gradio-5-browserstate
git ls-remote github refs/heads/feature/gradio-5-browserstate
```

Must print main's current SHA (`0bed015…`). ABORT otherwise.

## Step 2 — Wave-2 branch, Space-canonical bulk, protected restore

```bash
git checkout -b wave-2 github/main
git checkout f1b6f4e469beefaec6257286bc5aec0110d570a1 -- .
git checkout github/main -- soraya_gates.py
git rm --ignore-unmatch schema-contingency.sql
```

(The bulk checkout only touches paths present in the Space tree; docs/,
governance/, research/, instrumentation/ survive automatically. The single
restore keeps the annotated `ae9e958` gates.)

## Step 3 — Quarantine archaeology (quote every name; several have spaces)

```bash
mkdir -p archive/space_patch_archaeology_f1b6f4e
git mv "apply_soraya_final_patches.py" "app_py_consent_wiring.py" \
       "contingency audit 2.py" "db contingency patch.py" \
       "verify v1 4 1.py" "soraya_visible_output_hygiene_hf_v2.patch" \
       "SORAYA_FINAL_PATCH_README.md" \
       archive/space_patch_archaeology_f1b6f4e/
cat > archive/space_patch_archaeology_f1b6f4e/README.md << 'EOF'
These files were present on Hugging Face Space artifact
f1b6f4e469beefaec6257286bc5aec0110d570a1 (PARITY REPORT #1/#2). Retained as
provenance receipts; not part of the serving runtime surface.
EOF
```

If any file is absent, note it in the completion receipt and continue —
inventory drift since the pin is itself a finding.

## Step 4 — Capture the both-sides evidence (goes in the commit body)

```bash
git diff --stat github/main > /tmp/wave2_diffstat.txt
git diff github/main -- claim_registry.md invariants.md > /tmp/w2f3.txt
wc -c /tmp/w2f3.txt
[ "$(wc -c < /tmp/w2f3.txt)" -gt 0 ] \
  && echo "W2-F3 OPERATOR RULING REQUIRED before Step 7 continues" \
  || echo "W2-F3 clean"
cat /tmp/wave2_diffstat.txt
```

**ABORT Step 7 if W2-F3 OPERATOR RULING REQUIRED — do not resolve silently.**

## Step 5 — README fold (frontmatter preserved mechanically)

```bash
cat > /tmp/README_BODY.md << 'EOF'
# Soraya Study — governed educational AI prototype

**Current baseline:** Wave-2 reconciled build. Runtime reconciled byte-exact
from Space artifact `f1b6f4e469b…`; gate layer carried from GitHub main at
blob `ae9e958` (seven-gate v1.5.0 implementation, self-citing provenance,
KL-1 declared open in-source at Gate 6).

Soraya runs a seven-gate post-generation audit (Agency · Justice/Mercy ·
Epistemic · Wonder/Humor · No-Fake-Biography · No-Fake-Fandom ·
Named-Figure-Voice), an Agency Ledger (A_hat / K_hat / D_hat) driving a
pedagogical router, a fail-closed consent gate, INSERT-only study telemetry,
and an optional output-only voice layer.

A previous README described an older v1.2–v1.3 / four-gate state and was
stale relative to the serving artifact. This repository is the public
evidence trail: architecture schematic v1.6.0-definitive; measurement
schematic MS-R4/MS-R4.1; parity and deviation receipts in `docs/`
(PARITY_REPORT_2_REISSUED.md, DEVIATION_REGISTER.md). The canonical artifact
is the resolved deploy commit SHA; the Hugging Face Space deploys from this
repository and is not independently edited. Verdicts are recomputable from
receipts; renderings — this README included — are legal when labeled.
EOF
python3 - << 'EOF'
import re, pathlib
p = pathlib.Path('README.md'); t = p.read_text()
m = re.match(r'^(---\n.*?\n---\n)', t, re.S)
assert m, "ABORT: no YAML frontmatter found in Space README"
p.write_text(m.group(1) + "\n" + open('/tmp/README_BODY.md').read())
EOF
head -12 README.md
```

The `head` must show the untouched `---` frontmatter block (sdk, app_file)
followed by the new body. ABORT if frontmatter is absent.

## Step 6 — Author the two new modules

```bash
cat > deploy_guard.sh << 'EOF'
#!/usr/bin/env bash
# deploy_guard.sh — mechanical refusal; run before ANY push to the Space.
# ABORT class: KL-9 (BrowserState/Gradio-4 conflict)
set -u
fail(){ echo "DEPLOY GUARD ABORT: $1"; exit 1; }
grep -Eq '^[^#]*gr\.BrowserState' app.py && grep -Eq '^gradio==4\.' requirements.txt \
  && fail "KL-9 unresolved — uncommented gr.BrowserState with a Gradio-4 pin"
for f in app.py ledger.py soraya_gates.py soraya_covenant.py consent_gate.py \
         db.py ledger_hook.py voice_out.py brand_shell.py study_config.py; do
  [ -f "$f" ] || fail "missing runtime file: $f"
  [ "$(wc -c < "$f")" -lt 200 ] && fail "placeholder-sized runtime file: $f"
done
head -1 README.md | grep -qx -- '---' || fail "README lost HF frontmatter"
grep -q '^app_file:' README.md || fail "README frontmatter missing app_file:"
echo "DEPLOY GUARD PASS"
EOF
chmod +x deploy_guard.sh

cat > build_identity.py << 'EOF'
"""build_identity.py — SORAYA_BUILD_SHA resolution chain.

Inert this wave by design: wiring into app.py is a declared post-parity-#3
patch, bundled with the KL-1 fix window (one edit window, one probe rerun,
one redeploy, parity #3.1) so wave-2 app.py stays byte-identical to the
production lineage. Chain: env var -> git rev-parse -> None.

Study mode must block when resolve_build_sha() returns None.
Invariant: no build identity, no study.
"""
import os, subprocess

def resolve_build_sha():
    sha = os.environ.get("SORAYA_BUILD_SHA", "").strip()
    if sha:
        return sha
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except Exception:
        return None
EOF
```

## Step 7 — One boring commit, push to GitHub

**Precondition: W2-F3 must be clean or operator-ruled before this step.**

```bash
git add -A
git commit -F - << EOF
Wave 2: repo becomes deployable; Space-canonical runtime

Runtime reconciled byte-exact from Space f1b6f4e469b. app.py lineage ruling
per KL-9: Space-canonical; BrowserState lineage preserved at
feature/gradio-5-browserstate. Protected: soraya_gates.py ae9e958 (main
ahead-by-annotation; the Space receives the repo's version). Declared deltas:
archaeology -> archive/, README fold under preserved frontmatter,
deploy_guard.sh + inert build_identity.py added, schema-contingency.sql
(hyphen) removed. W2-F1..F3 opened in the register.

Diffstat vs pre-wave main:
$(cat /tmp/wave2_diffstat.txt)
EOF
git push github wave-2:main
git tag wave-2-baseline
git push github --tags
git rev-parse HEAD
```

Record the printed SHA as **RECONCILED_SHA**.

## Step 8 — Guard, then deploy (the button stops being a self-destruct)

```bash
bash deploy_guard.sh
```

**ABORT unless it prints `DEPLOY GUARD PASS`.** Precondition standing from
Step 0: `space-history-f1b6f4e` verified on GitHub.

```bash
git push --force origin wave-2:main
```

## Step 9 — Both remotes point where we think they point

```bash
git ls-remote origin refs/heads/main
git ls-remote github refs/heads/main
```

Both must print RECONCILED_SHA. Then confirm the Space rebuilds and the app
loads (consent gate renders). Any other value or a failed rebuild: **ABORT**
and report — do not retry-push.

## Step 10 — Completion receipt (INV19: partial execution without ABORT is itself a deviation)

Fill and return with the raw outputs:

```
step | command group        | exit | key output line
0    | receipt #1           |      | space-history ls-remote SHA
1    | feature branch       |      | feature ls-remote SHA
2    | bulk + restore       |      | rm/checkout summary
3    | archaeology          |      | files moved / absent
4    | evidence capture     |      | diffstat totals · w2f3 byte count
5    | README fold          |      | head -12 shows frontmatter
6    | new modules          |      | guard + identity created
7    | commit/push/tag      |      | RECONCILED_SHA
8    | guard + deploy       |      | DEPLOY GUARD PASS
9    | verification         |      | both remotes = RECONCILED_SHA
```

-----

**After this runbook:** parity #3's SHA and tree halves close by construction
(both remotes at RECONCILED_SHA); the verdict-vector half stays INDETERMINATE
until the acceptance battery exists — that is honest, not incomplete. Then,
in order: registry-as-code · KL-1 fix **bundled with build-identity wiring
into app.py** (one edit window, one probe rerun, one redeploy, parity #3.1) ·
FN-027 reproduction · Gates 5–6 gold set dead last · graduation by logged row.

-----

Receipt chain (INV17):
  r1 authored draft     blob 5e74293b…   12,189 B   syntax receipts attach here
  r2 operator-amended   blob b9b3e41…    17,241 B   not execution-ready (circular 0B)
  r3 this file          blob <r3 SHA>               Step 0 git-native; execution-ready

Authoring hash (r1, authoring-tier): `f6f694ba1e3afd3a17ea41f7d2c0dcb56736d04ccfe1f904c0699a354896876d`
The executor verifies r3 blob identity from github/main before Step 0. Do not execute r2.
