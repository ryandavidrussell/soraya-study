# Claim Registry

The bridge between philosophy and engineering. Every load-bearing claim in the
Soraya architecture is registered here with its implementing module, its honest
evidence status, its risk, and the test that would confirm or break it.

A claim with no architecture is an essay. Architecture with no claim is
decoration. This file keeps both honest.

-----

```yaml
- claim_id: C001
  claim: "Learners need care and structure together."
  architecture: "Recursive ethical loop; Justice–Mercy Gate (soraya_gates.check_justice_mercy)"
  evidence_status: "research-informed, not proven in Soraya"
  sources: ["SDT (Jang, Reeve & Deci 2010)", "attachment theory (Bowlby)", "scaffolding", "Baumrind parenting typology"]
  risk: "overgeneralizing across cultures"
  test: "A/B study: learning transfer, frustration, dependency"

- claim_id: C002
  claim: "AI tutoring should preserve agency rather than maximize answer delivery."
  architecture: "Agency Ledger (ledger.py); Agency Gate (soraya_gates.check_agency)"
  evidence_status: "testable design hypothesis; consistent with Bastani et al. 2025 (PNAS)"
  risk: "under-helping novices"
  test: "delayed retention and transfer after assisted practice"

- claim_id: C003
  claim: "Context disciplines legitimate interpretation."
  architecture: "Epistemic Humility Gate (soraya_gates.check_epistemic); REFLECT mode"
  evidence_status: "philosophical design principle"
  risk: "paternalism if context constraints are imposed opaquely"
  test: "expert review of contested-topic responses"

- claim_id: C004
  claim: "Capacity pressure must not downgrade safeguards."
  architecture: "Router precedence: REPAIR outranks REFLECT and all other modes (ledger.route)"
  evidence_status: "structural invariant, enforced by test"
  risk: "REPAIR over-triggering and blocking legitimate deep questions"
  test: "false-positive rate of REPAIR on worldview-question sessions"

- claim_id: C005
  claim: "Wonder serves learning only when it returns the learner to agency."
  architecture: "Wonder/Humor Gate (soraya_gates.check_wonder)"
  evidence_status: "design hypothesis; detector is heuristic"
  risk: "trimming genuine warmth; flattening Soraya's voice"
  test: "learner-rated warmth vs. distraction on gated vs. ungated transcripts"

- claim_id: C006
  claim: "Governance must be legible to the governed."
  architecture: "Governance panel; GateReport with reasons; visibility transitions"
  evidence_status: "design principle (auditable by construction)"
  risk: "panel becoming noise; legibility theater"
  test: "can a third party reconstruct why each turn behaved as it did from the panel alone"
```

-----

## Rules of the registry

1. New gate, new mode, new invariant → new claim, before the code merges.
1. `evidence_status` may only strengthen via a named test, never via restatement.
1. Each claim names a risk. A claim whose author can't name its risk isn't ready.
