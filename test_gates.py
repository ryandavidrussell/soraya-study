"""
test_gates.py — smoke tests for the covenant + gate layers.

Sprint 2.5 acceptance criteria coverage:
1. Full-answer candidate at high dependency rewritten by Agency Gate
2. Shaming correction rewritten by Justice–Mercy Gate
3. Worldview question triggers the Epistemic Gate
4. Melodramatic wonder trimmed in REPAIR/REORIENT mode
5. Governance panel shows gate pass/rewrite status (see end-to-end block)
6. Ledger updates from the gated response (see end-to-end block)
7. System prompt includes covenant + central invariant
8. REFLECT routes worldview questions; epistemic gate blocks both
   dogmatic closure and relativistic collapse

Run: python test_gates.py
No external dependencies (gradio/anthropic not imported).
"""

from ledger import LedgerState, ResponseMode, route, build_system_prompt
from soraya_covenant import SORAYA_COVENANT, CENTRAL_INVARIANT
from soraya_gates import (
    apply_soraya_gates,
    classify_context,
    check_agency,
    check_justice_mercy,
    check_epistemic,
    check_wonder,
    GateReport,
)

PASS = 0
FAIL = 0

def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok  {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name}")

# ---------------------------------------------------------------------------
print("Covenant layer")

prompt = build_system_prompt(LedgerState(), ResponseMode.HINT)
check("covenant prepended to system prompt",
      prompt.startswith("You are Soraya, a governed learning companion"))
check("central invariant in system prompt",
      "must not become more powerful" in prompt)
check("covenant precedes mode instruction",
      prompt.index("Core commitments") < prompt.index("Mode instruction"))
check("central invariant is a string", isinstance(CENTRAL_INVARIANT, str))

# ---------------------------------------------------------------------------
print("Context classifier")

check("worldview question detected",
      classify_context("Is it wrong to lie to protect someone?").worldview)
check("identity question detected",
      classify_context("Sometimes I wonder who am I really").worldview)
check("math question not worldview",
      not classify_context("How do I factor x^2 + 5x + 6?").worldview)

# ---------------------------------------------------------------------------
print("Router: REFLECT and precedence")

neutral = LedgerState()  # D=0.1
check("worldview routes to REFLECT",
      route(neutral, worldview=True) == ResponseMode.REFLECT)
check("route(state) backward compatible",
      route(neutral) == ResponseMode.HINT)

high_d = LedgerState(D_hat=0.7)
check("REPAIR outranks REFLECT",
      route(high_d, worldview=True) == ResponseMode.REPAIR)

# ---------------------------------------------------------------------------
print("Agency gate")

full_solution = (
    "Here is how to think about quadratics. " * 20
    + "The answer is x = -2 and x = -3."
)

ok, rewrite, _ = check_agency(full_solution, LedgerState(D_hat=0.6))
check("fires on full solution at high D", not ok)
check("rewrite withholds the answer", "x = -2" not in rewrite)
check("rewrite hands the move back", "attempt" in rewrite.lower())

ok, _, _ = check_agency(full_solution, LedgerState(D_hat=0.2))
check("does not fire at low D", ok)

ok, _, _ = check_agency(full_solution, LedgerState(D_hat=0.6, K_hat=0.8))
check("confusion carve-out: direct instruction allowed at extreme K", ok)

ok, _, _ = check_agency("What would you try first?", LedgerState(D_hat=0.8))
check("does not fire on a scaffold even at high D", ok)

# ---------------------------------------------------------------------------
print("Justice-Mercy gate")

shaming = ("Wrong. You clearly don't understand this. "
           "The first step was fine though.")
ok, rewrite, _ = check_justice_mercy("I tried x=2 because of the symmetry "
                                      "and got 7 as my result here", shaming)
check("mercy fires on shaming language", not ok)
check("shaming sentence stripped",
      "clearly don't understand" not in rewrite.lower())
check("non-shaming content kept", "first step was fine" in rewrite)

ok, rewrite, _ = check_justice_mercy(
    "just give me the answer", "You're doing amazing! Keep it up!")
check("justice fires on empty praise during avoidance", not ok)
check("honest line appended", "needs to come from you" in rewrite)

ok, _, _ = check_justice_mercy(
    "I tried x=2 because the symmetry suggested it and got 7 as my result",
    "Not quite — but your first step makes sense. The turn happened here.")
check("healthy correction passes", ok)

# ---------------------------------------------------------------------------
print("Epistemic humility gate")

worldview_ctx = classify_context("Is it ever morally right to break a promise?")
math_ctx = classify_context("How do I factor this?")

dogmatic = ("No reasonable person disagrees about this. "
            "Promises create obligations.")
ok, trig, rewrite, _ = check_epistemic(dogmatic, worldview_ctx)
check("fires on dogmatic closure", not ok and trig)
check("dogmatic sentence stripped", "no reasonable person" not in rewrite.lower())
check("humility coda appended", "judgment stays yours" in rewrite.lower())

relativist = "Everyone has their own truth, so it depends on you."
ok, trig, rewrite, _ = check_epistemic(relativist, worldview_ctx)
check("fires on relativistic mush", not ok and trig)

balanced = ("There are several serious views here. Let's define what a "
            "promise is first, then separate the facts from the values.")
ok, trig, _, _ = check_epistemic(balanced, worldview_ctx)
check("disciplined response passes while triggered", ok and trig)

ok, trig, _, _ = check_epistemic(dogmatic, math_ctx)
check("not triggered on non-worldview context", ok and not trig)

# ---------------------------------------------------------------------------
print("Wonder/Humor gate")

melodrama = ("This is a truly magical journey!!! The universe is telling "
             "you something. Now, the next step is to isolate x.")
ok, rewrite, _ = check_wonder(melodrama, ResponseMode.HINT)
check("fires on accumulated melodrama", not ok)
check("task content survives the trim", "isolate x" in rewrite)
check("exclamation runs flattened", "!!!" not in rewrite)

mild = "Nice catch! That seedling of an idea is exactly the next step."
ok, _, _ = check_wonder(mild, ResponseMode.HINT)
check("grounded warmth passes in HINT", ok)

one_marker = "Pure magic! Now restate the goal in your own words."
ok, _, _ = check_wonder(one_marker, ResponseMode.REPAIR)
check("strict in REPAIR mode", not ok)

# ---------------------------------------------------------------------------
print("apply_soraya_gates end-to-end")

clean = "What's the first thing you'd try here? Give it a shot."
text, report = apply_soraya_gates(
    user_message="I tried factoring because the leading term is 1 and i got stuck",
    candidate_response=clean,
    state=LedgerState(),
    mode=ResponseMode.HINT,
)

check("clean response untouched", text == clean)
check("clean report all-pass", not report.rewrite_required
      and report.agency_pass and report.justice_mercy_pass
      and report.epistemic_pass and report.wonder_pass)

bad = ("You clearly don't understand this. " + "Step by step. " * 40
       + "The answer is 42.")
text, report = apply_soraya_gates(
    user_message="just give me the answer",
    candidate_response=bad,
    state=LedgerState(D_hat=0.6),
    mode=ResponseMode.REPAIR,
)

check("compound failure produces rewrite", report.rewrite_required)
check("agency gate failed", not report.agency_pass)
check("answer withheld in final text", "42" not in text)
check("no shaming in final text", "clearly don't" not in text.lower())
check("reasons recorded", len(report.reasons) >= 1)
check("report serializes", isinstance(report.to_dict(), dict))

# ---------------------------------------------------------------------------
print()
print(f"{PASS} passed, {FAIL} failed")
exit(1 if FAIL else 0)
