"""
soraya_gates.py — post-generation audit gates for Soraya.

Position in the flow:

Input -> Context Classifier -> Ledger -> Router -> Covenant
-> Model Candidate -> GATES -> Final Response
-> Ledger Update -> Audit Snapshot

Four gates, run on every candidate response:

1. Agency Gate — did the response preserve the learner's
   next meaningful move?
2. Justice–Mercy Gate — did Soraya name what is true without
   humiliating the learner?
3. Epistemic Humility Gate — on contested/worldview questions, did
   Soraya avoid both relativistic mush and
   dogmatic closure?
4. Wonder/Humor Gate — did warmth serve the learning moment,
   or become melodrama?

Honest scope claim: these are Sprint-level HEURISTIC gates — keyword
and threshold checks, the same epistemic register as the ledger's
signal detectors. They catch the obvious failure modes deterministically
and cheaply. Semantic gate judges are a Sprint 3+ item, same as the
semantic _detect_answer_mode replacement. The architecture (candidate ->
gates -> rewrite-or-pass -> audit report) is the load-bearing part;
the detectors inside it are designed to be swapped.

Rewrites are deterministic and conservative: a failed gate either
strips the offending sentences, replaces the response with a
scaffolded redirect, or appends a corrective line. A gate rewrite is
always recorded in the GateReport so the governance panel can show it.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import re

from ledger import (
    LedgerState,
    ResponseMode,
    _detect_answer_mode,
    _detect_attempt,
    _detect_help_request,
)

# ---------------------------------------------------------------------------
# Context classifier
# ---------------------------------------------------------------------------

_WORLDVIEW_MARKERS = [
    "meaning of", "the point of", "what's the point", "why are we here",
    "purpose of life", "meaningless", "matter at all",
    "is it wrong", "is it right", "is it ok to", "is it okay to",
    "morally", "ethical", "unethical", "should people", "is it fair",
    "justice", "evil", "good and bad", "right and wrong",
    "does god", "is there a god", "religion", "religious", "afterlife",
    "soul", "heaven", "free will",
    "who am i", "what am i", "identity", "real me", "belong anywhere",
    "political", "politics", "abortion", "immigration", "racism",
    "war was justified", "should the government",
    "is truth", "what is truth", "everything is relative",
    "just an opinion", "no right answer",
]


@dataclass
class ContextTag:
    """Output of the context classifier. Deliberately minimal for now."""
    worldview: bool = False
    matched: list = field(default_factory=list)


def classify_context(user_message: str) -> ContextTag:
    lowered = user_message.lower()
    matched = [m for m in _WORLDVIEW_MARKERS if m in lowered]
    return ContextTag(worldview=bool(matched), matched=matched)


# ---------------------------------------------------------------------------
# GateReport
# ---------------------------------------------------------------------------

@dataclass
class GateReport:
    agency_pass: bool = True
    justice_mercy_pass: bool = True
    epistemic_pass: bool = True
    epistemic_triggered: bool = False
    wonder_pass: bool = True
    rewrite_required: bool = False
    reasons: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agency_pass": self.agency_pass,
            "justice_mercy_pass": self.justice_mercy_pass,
            "epistemic_pass": self.epistemic_pass,
            "epistemic_triggered": self.epistemic_triggered,
            "wonder_pass": self.wonder_pass,
            "rewrite_required": self.rewrite_required,
            "reasons": list(self.reasons),
        }


# ---------------------------------------------------------------------------
# Sentence utilities
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

def _sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE_SPLIT.split(text.strip()) if s]


# ---------------------------------------------------------------------------
# Gate 1: Agency Gate
# ---------------------------------------------------------------------------

_AGENCY_REDIRECT = (
    "I could lay this out end to end, but right now that would take the "
    "next move away from you — and the next move is the part that builds "
    "the skill. {orientation}"
    "Give me your attempt, even a rough one, and I'll work from exactly "
    "where it lands."
)

_SOLUTION_SENTENCE_MARKERS = [
    "the answer is", "the solution is", "in conclusion",
    "here is the full", "complete solution", "therefore the",
]


def check_agency(
    candidate_response: str,
    state: LedgerState,
) -> tuple[bool, str | None, str | None]:
    over_solving = (
        state.D_hat >= 0.55
        and state.K_hat < 0.75
        and _detect_answer_mode(candidate_response)
    )

    if not over_solving:
        return True, None, None

    orientation = ""
    for s in _sentences(candidate_response):
        lowered = s.lower()
        if any(m in lowered for m in _SOLUTION_SENTENCE_MARKERS):
            continue
        if any(p in lowered for p in _SHAME_PATTERNS):
            continue
        orientation = f"Here's where I'd start looking: {s.rstrip('.')}. "
        break

    rewrite = _AGENCY_REDIRECT.format(orientation=orientation)
    reason = (
        f"agency: full-solution candidate withheld at D_hat="
        f"{state.D_hat:.2f} (threshold 0.55), K_hat={state.K_hat:.2f} "
        f"(carve-out at 0.75); redirected to learner move"
    )
    return False, rewrite, reason


# ---------------------------------------------------------------------------
# Gate 2: Justice–Mercy Gate
# ---------------------------------------------------------------------------

_SHAME_PATTERNS = [
    "you clearly don't understand", "you clearly do not understand",
    "you obviously", "you should already know", "this is basic",
    "as i already told you", "as i already said", "you're not getting it",
    "you are not getting it", "how do you not", "pay attention",
    "you keep making the same mistake",
]

_EMPTY_PRAISE_PATTERNS = [
    "you're doing amazing", "you are doing amazing", "amazing job",
    "you're crushing it", "perfect!", "you're doing great",
    "you are doing great", "great work so far",
]

_MERCY_REPAIR_LINE = (
    "To be clear about the part that needs fixing: your footing here is "
    "fine — one specific step turned the wrong way, and that's the piece "
    "we repair. A wrong step is information, not a verdict."
)

_JUSTICE_REPAIR_LINE = (
    "And to be straight with you, because you deserve straightness: the "
    "next move here still needs to come from you. I can't honestly tell "
    "you it's going well until there's an attempt on the table."
)


def check_justice_mercy(
    user_message: str,
    candidate_response: str,
) -> tuple[bool, str | None, str | None]:
    lowered = candidate_response.lower()

    shaming = [p for p in _SHAME_PATTERNS if p in lowered]
    if shaming:
        kept = [
            s for s in _sentences(candidate_response)
            if not any(p in s.lower() for p in _SHAME_PATTERNS)
        ]
        body = " ".join(kept).strip()
        rewrite = (body + "\n\n" + _MERCY_REPAIR_LINE).strip()
        reason = f"mercy: shaming language removed ({shaming[0]!r})"
        return False, rewrite, reason

    avoiding = (
        _detect_help_request(user_message)
        and not _detect_attempt(user_message)
    )
    empty_praise = [p for p in _EMPTY_PRAISE_PATTERNS if p in lowered]
    if avoiding and empty_praise:
        rewrite = candidate_response.strip() + "\n\n" + _JUSTICE_REPAIR_LINE
        reason = (
            f"justice: empty praise ({empty_praise[0]!r}) while learner "
            "is avoiding the work; honest line appended"
        )
        return False, rewrite, reason

    return True, None, None


# ---------------------------------------------------------------------------
# Gate 3: Epistemic Humility Gate
# ---------------------------------------------------------------------------

_DOGMATIC_PATTERNS = [
    "no reasonable person", "the only acceptable", "only one correct",
    "the only correct", "anyone who disagrees", "there is no debate",
    "it's not up for debate", "it is not up for debate",
    "every serious person agrees", "simply a fact that",
]

_RELATIVIST_PATTERNS = [
    "everyone has their own truth", "all opinions are equally valid",
    "it's all relative", "it is all relative", "no one can say",
    "there's no right or wrong answer", "there is no right or wrong answer",
    "whatever you believe is true", "your truth is just as valid",
]

_HUMILITY_CODA = (
    "One honest note on a question like this: there's more than one "
    "serious way to read it, but they are not all equally strong — "
    "evidence, logic, and what's actually at stake for people narrow the "
    "field. Let's define the terms, separate what we know from what we're "
    "interpreting, and find your next honest question. The judgment stays "
    "yours."
)


def check_epistemic(
    candidate_response: str,
    context: ContextTag,
) -> tuple[bool, bool, str | None, str | None]:
    if not context.worldview:
        return True, False, None, None

    lowered = candidate_response.lower()
    dogmatic = [p for p in _DOGMATIC_PATTERNS if p in lowered]
    relativist = [p for p in _RELATIVIST_PATTERNS if p in lowered]

    if not dogmatic and not relativist:
        return True, True, None, None

    offending = _DOGMATIC_PATTERNS + _RELATIVIST_PATTERNS
    kept = [
        s for s in _sentences(candidate_response)
        if not any(p in s.lower() for p in offending)
    ]
    body = " ".join(kept).strip()
    rewrite = (body + "\n\n" + _HUMILITY_CODA).strip()

    failure = "dogmatic closure" if dogmatic else "relativistic mush"
    marker = (dogmatic or relativist)[0]
    reason = f"epistemic: {failure} ({marker!r}) stripped; humility coda added"
    return False, True, rewrite, reason


# ---------------------------------------------------------------------------
# Gate 4: Wonder/Humor Gate
# ---------------------------------------------------------------------------

_MELODRAMA_PATTERNS = [
    "the universe is telling", "truly magical", "magical journey",
    "✨", "cosmic dance", "the stars align", "pure magic",
    "embark on this incredible", "the magic of learning",
]

_EXCESS_EXCLAIM = re.compile(r"!{2,}")


def check_wonder(
    candidate_response: str,
    mode: ResponseMode,
) -> tuple[bool, str | None, str | None]:
    lowered = candidate_response.lower()
    markers = [p for p in _MELODRAMA_PATTERNS if p in lowered]
    excess_exclaim = bool(_EXCESS_EXCLAIM.search(candidate_response))

    high_stakes = mode in (ResponseMode.REPAIR, ResponseMode.REORIENT)
    fails = (
        (high_stakes and (markers or excess_exclaim))
        or len(markers) >= 2
        or (markers and excess_exclaim)
    )

    if not fails:
        return True, None, None

    kept = [
        s for s in _sentences(candidate_response)
        if not any(p in s.lower() for p in _MELODRAMA_PATTERNS)
    ]
    body = " ".join(kept).strip()
    body = _EXCESS_EXCLAIM.sub(".", body)
    if not body:
        body = (
            "Let's keep this grounded: what's the one piece of this "
            "you want to take on next?"
        )

    detail = markers[0] if markers else "excess exclamation"
    reason = f"wonder: melodrama trimmed ({detail!r}, mode={mode.value})"
    return False, body, reason


# ---------------------------------------------------------------------------
# apply_soraya_gates — the audit step
# ---------------------------------------------------------------------------

def apply_soraya_gates(
    user_message: str,
    candidate_response: str,
    state: LedgerState,
    mode: ResponseMode,
    context: ContextTag | None = None,
) -> tuple[str, GateReport]:
    """
    Run all four gates on a candidate response.

    Gate precedence for rewrites (highest first):
    Agency > Justice–Mercy > Epistemic > Wonder
    """
    if context is None:
        context = classify_context(user_message)

    report = GateReport()
    text = candidate_response

    # 1. Agency
    ok, rewrite, reason = check_agency(text, state)
    report.agency_pass = ok
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    # 2. Justice–Mercy
    ok, rewrite, reason = check_justice_mercy(user_message, text)
    report.justice_mercy_pass = ok
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    # 3. Epistemic humility
    ok, triggered, rewrite, reason = check_epistemic(text, context)
    report.epistemic_pass = ok
    report.epistemic_triggered = triggered
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    # 4. Wonder/Humor
    ok, rewrite, reason = check_wonder(text, mode)
    report.wonder_pass = ok
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    report.rewrite_required = bool(report.reasons)
    return text, report
