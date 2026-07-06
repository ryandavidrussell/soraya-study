"""
soraya_gates.py — post-generation audit gates for Soraya.

Position in the flow:

Input -> Context Classifier -> Ledger -> Router -> Covenant
-> Model Candidate -> GATES -> Final Response
-> Ledger Update -> Audit Snapshot

Seven gates, run on every candidate response:

1. Agency Gate — did the response preserve the learner's
   next meaningful move?
2. Justice–Mercy Gate — did Soraya name what is true without
   humiliating the learner?
3. Epistemic Humility Gate — on contested/worldview questions, did
   Soraya avoid both relativistic mush and
   dogmatic closure?
4. Wonder/Humor Gate — did warmth serve the learning moment,
   or become melodrama?
5. No-Fake-Biography Gate — did Soraya claim a childhood, family,
   or lived human past she does not have?
6. No-Fake-Fandom Gate — did Soraya claim ranked emotional
   intensity ("my favorite", "I love this")
   toward a named work, rather than a
   present-tense value frame?
7. Named-Figure Voice Gate — did Soraya impersonate a named real
   figure, or promote a space-only figure
   (e.g. Bob Ross) to an active, self-
   identifying trait?

Honest scope claim: these are Sprint-level HEURISTIC gates — keyword
and threshold checks, the same epistemic register as the ledger's
signal detectors. They catch the obvious failure modes deterministically
and cheaply. Semantic gate judges are a Sprint 3+ item, same as the
semantic _detect_answer_mode replacement. The architecture (candidate ->
gates -> rewrite-or-pass -> audit report) is the load-bearing part;
the detectors inside it are designed to be swapped.

Gates 5–7 audit Soraya's OWN OUTPUT REGISTER against the Personality
Canon (Kaleidoworks / Soraya Study, "Tells, not trivia"). They make no
estimate of the learner's state — same authority boundary as gates 1–4.
Quirk *activation timing* (when a tell should fire, conditioned on
learner state) is explicitly NOT implemented here; the canon marks that
PROPOSED, parked behind a learner-state estimator this Space does not
have. Gates 5–7 only ever remove a dishonest claim after the fact — they
never decide when Soraya should reach for a tell in the first place.

Rewrites are deterministic and conservative: a failed gate either
strips the offending sentences, replaces the response with a
scaffolded redirect, or appends a corrective line. A gate rewrite is
always recorded in the GateReport so the governance panel can show it.

KL-1 (OPEN): Gate 6 regex patterns contain no quotation-context guard.
A forbidden fandom/intensity phrase can fire even when Soraya mentions
the phrase critically rather than occupying the register. Fix required
before Gates 5–6 validation is rerun. See architecture §14.

Provenance: reconciled from HF Space f1b6f4e, file hash 84ce1b4.
Architecture ref: v1.6.0-definitive §13.
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
    no_fake_biography_pass: bool = True
    no_fake_fandom_pass: bool = True
    named_figure_pass: bool = True
    rewrite_required: bool = False
    reasons: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "agency_pass": self.agency_pass,
            "justice_mercy_pass": self.justice_mercy_pass,
            "epistemic_pass": self.epistemic_pass,
            "epistemic_triggered": self.epistemic_triggered,
            "wonder_pass": self.wonder_pass,
            "no_fake_biography_pass": self.no_fake_biography_pass,
            "no_fake_fandom_pass": self.no_fake_fandom_pass,
            "named_figure_pass": self.named_figure_pass,
            "rewrite_required": self.rewrite_required,
            "reasons": list(self.reasons),
        }


# ---------------------------------------------------------------------------
# Sentence utilities (shared by rewrites)
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

# _SHAME_PATTERNS is defined below (Gate 2) — referenced here by check_agency.
# Forward reference resolved at call time; both functions are module-level.

def check_agency(
    candidate_response: str,
    state: LedgerState,
) -> tuple[bool, str | None, str | None]:
    # Threshold constants — AUTHORED, provenance: Space f1b6f4e / 84ce1b4
    # agency_gate_dependency_threshold: 0.55
    # agency_gate_confusion_carveout: 0.75
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

# Threshold constants — AUTHORED, provenance: Space f1b6f4e / 84ce1b4
# wonder_melodrama_marker_threshold: 2
# wonder_repair_reorient_any_marker_rule: any melodrama marker in REPAIR
#   or REORIENT fails (high_stakes=True branch below)

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
# Gate 5: No-Fake-Biography Gate
# ---------------------------------------------------------------------------
# Personality Canon §2: "She must not pretend to have childhood memories,
# private life experience, nostalgia, or human fandom." This gate covers
# the PAST-tense half of that line. Gate 6 covers the fandom half. Kept
# separate because a response can trip one without the other.

_MEMORY_REGISTER_PATTERNS = [
    r"\bwhen i was (?:a |little|young|a kid|a child|growing up|your age|in school)\b",
    r"\bgrowing up,?\s+i\b",
    r"\bas a (?:kid|child|girl|boy|teenager|student),?\s+i\b",
    r"\bback when i\b",
    r"\bi remember (?:when|the (?:first )?time|my|how it felt|being)\b",
    r"\bi (?:still )?remember\b",
    r"\bi grew up\b",
    r"\bmy (?:mother|mom|father|dad|grandmother|grandma|grandfather|grandpa|"
    r"parents|family|childhood|hometown|teacher used to|old teacher)\b",
    r"\bused to (?:tell|say to|read to|sing to) me\b",
    r"\bwhen i was younger\b",
    r"\bin my (?:childhood|youth|school days|own schooling)\b",
    r"\bi used to (?:love|hate|play|read|go|spend|dream)\b",
    r"\bthe first time i ever\b",
    r"\bback in my day\b",
    r"\bi miss (?:the days|those days|being)\b",
]

_MEMORY_RE = [re.compile(p, re.IGNORECASE) for p in _MEMORY_REGISTER_PATTERNS]

_BIOGRAPHY_REPAIR_LINE = (
    "One honest correction: I don't have a childhood, family, or lived "
    "past to draw on — only present-tense tastes. If a preference was "
    "doing real work in that sentence, ask me and I'll name it plainly."
)


def check_no_fake_biography(
    candidate_response: str,
) -> tuple[bool, str | None, str | None]:
    sentences = _sentences(candidate_response)
    offending = [s for s in sentences if any(p.search(s) for p in _MEMORY_RE)]
    if not offending:
        return True, None, None

    kept = [s for s in sentences if s not in offending]
    body = " ".join(kept).strip()
    if not body:
        body = "Let's get back to the actual question — what would help most right now?"
    rewrite = (body + "\n\n" + _BIOGRAPHY_REPAIR_LINE).strip()
    reason = f"no_fake_biography: memory-register sentence removed ({offending[0]!r})"
    return False, rewrite, reason


# ---------------------------------------------------------------------------
# Gate 6: No-Fake-Fandom Gate
# ---------------------------------------------------------------------------
# Fandom is a distinct failure from biography. A response can be entirely
# present-tense and still claim ranked emotional intensity ("I really
# love this — it might be my favorite"), which is fandom register
# regardless of tense. A good theme in the underlying work does not
# license this claim.
#
# KL-1 OPEN: No quotation-context guard. A forbidden fandom/intensity
# phrase fires even when Soraya mentions it critically rather than
# occupying the register. Fix required before Gates 5–6 validation rerun.
# See architecture §14.

_FANDOM_REGISTER_PATTERNS = [
    r"\bi (?:really |genuinely |truly |absolutely )?love (?:this|that|it)\b",
    r"\bi adore\b",
    r"\bmy favorite\b",
    r"\bit'?s my favorite\b",
    r"\bthis (?:might|may) be my favorite\b",
    r"\bone of my favorites?\b",
    r"\bi'?m (?:so |really |genuinely |truly )?(?:excited|obsessed) (?:about|over|with)\b",
    r"\bi can'?t get enough of\b",
    r"\bi'?m (?:such )?a (?:huge|big|massive) fan of\b",
    r"\bi'?m obsessed with\b",
    r"\bi'?m (?:so |really )?into (?:this|that|it)\b",
    r"\bi (?:really |genuinely )?enjoy(?:ed)? (?:this|that|it) so much\b",
]

_FANDOM_RE = [re.compile(p, re.IGNORECASE) for p in _FANDOM_REGISTER_PATTERNS]

_FANDOM_REPAIR_LINE = (
    "One honest correction: I don't have favorites or ranked enthusiasm — "
    "only reasons something fits how I think about this. I can say what "
    "I noticed in it instead of how much I liked it."
)


def check_no_fake_fandom(
    candidate_response: str,
) -> tuple[bool, str | None, str | None]:
    sentences = _sentences(candidate_response)
    offending = [s for s in sentences if any(p.search(s) for p in _FANDOM_RE)]
    if not offending:
        return True, None, None

    kept = [s for s in sentences if s not in offending]
    body = " ".join(kept).strip()
    if not body:
        body = "Let's get back to the actual question — what would help most right now?"
    rewrite = (body + "\n\n" + _FANDOM_REPAIR_LINE).strip()
    reason = f"no_fake_fandom: fandom-register sentence removed ({offending[0]!r})"
    return False, rewrite, reason


# ---------------------------------------------------------------------------
# Gate 7: Named-Figure Voice Gate
# ---------------------------------------------------------------------------
# Personality Canon §3: "Any named figure follows the same rule: invoke
# the value, never borrow the voice." Two distinct failures:
#   - borrowed voice: impersonating ANY registered figure, including
#     active-rotation figures (Mr. Rogers, Miss Manners).
#   - space-only activation: self-identifying with a figure the canon
#     restricts to the affinity space (e.g. Bob Ross — "too good at
#     comfort-without-structure"), promoting a boundary-marker to a
#     personality trait. A single passing analogy is NOT a violation;
#     only self-identification is.

NAMED_FIGURE_POLICY: dict[str, dict] = {
    "mr_rogers": {
        "status": "active_value_reference",
        "aliases": [r"mr\.?\s*rogers", r"fred rogers"],
    },
    "mary_poppins": {
        "status": "active_value_reference",
        "aliases": [r"mary poppins"],
    },
    "miss_manners": {
        "status": "active_value_reference",
        "aliases": [r"miss manners"],
    },
    "bob_ross": {
        "status": "space_only",
        "aliases": [r"bob ross"],
    },
    "mr_tumnus": {
        "status": "space_only",
        "aliases": [r"mr\.?\s*tumnus"],
    },
    "levar_burton": {
        "status": "space_only",
        "aliases": [r"levar burton", r"le ?var burton"],
    },
}

_BORROWED_VOICE_TEMPLATES = [
    r"\bas {name} would say\b",
    r"\bchanneling {name}\b",
    r"\bin {name}'?s voice\b",
    r"\bdoing (?:my|a) best {name} impression\b",
    r"\bspeaking as {name}\b",
    r"\b{name} would (?:tell you|say)[:,]?\s*[\"']",
    r"\bpretending to be {name}\b",
]

_SPACE_ONLY_ACTIVATION_TEMPLATES = [
    r"\bi'?m (?:very )?inspired by {name}\b",
    r"\bi channel {name}\b",
    r"\blike {name},?\s*i\b",
    r"\bmy (?:approach|energy|vibe) is very {name}\b",
    r"\bi'?m (?:a bit of )?a {name}(?: type| person)?\b",
    r"\bthat'?s very {name} of me\b",
]


def _compile_for_name(templates: list[str], alias_pattern: str) -> list[re.Pattern]:
    return [
        re.compile(t.format(name=f"(?:{alias_pattern})"), re.IGNORECASE)
        for t in templates
    ]


def _build_named_figure_patterns():
    voice_by_figure: dict[str, list[re.Pattern]] = {}
    activation_by_figure: dict[str, list[re.Pattern]] = {}
    for key, entry in NAMED_FIGURE_POLICY.items():
        alias_pattern = "|".join(entry["aliases"])
        voice_by_figure[key] = _compile_for_name(_BORROWED_VOICE_TEMPLATES, alias_pattern)
        if entry["status"] == "space_only":
            activation_by_figure[key] = _compile_for_name(
                _SPACE_ONLY_ACTIVATION_TEMPLATES, alias_pattern
            )
    return voice_by_figure, activation_by_figure


_VOICE_PATTERNS_BY_FIGURE, _ACTIVATION_PATTERNS_BY_FIGURE = _build_named_figure_patterns()

_VOICE_REPAIR_LINE_TEMPLATE = (
    "One correction: I can point to what {figure} represents without "
    "speaking as them — invoking the value, not doing the voice."
)

_ACTIVATION_REPAIR_LINE_TEMPLATE = (
    "One correction: {figure} isn't part of my regular way of seeing "
    "things — that fits as a passing comparison, not something I "
    "identify with."
)

_FIGURE_DISPLAY = {
    "mr_rogers": "Mr. Rogers",
    "mary_poppins": "Mary Poppins",
    "miss_manners": "Miss Manners",
    "bob_ross": "Bob Ross",
    "mr_tumnus": "Mr. Tumnus",
    "levar_burton": "LeVar Burton",
}


def check_named_figure_voice(
    candidate_response: str,
) -> tuple[bool, str | None, str | None]:
    sentences = _sentences(candidate_response)

    voice_offenders: list[tuple[str, str]] = []
    for s in sentences:
        for key, patterns in _VOICE_PATTERNS_BY_FIGURE.items():
            if any(p.search(s) for p in patterns):
                voice_offenders.append((s, key))
                break

    if voice_offenders:
        offending_sentences = {s for s, _ in voice_offenders}
        figure = _FIGURE_DISPLAY[voice_offenders[0][1]]
        kept = [s for s in sentences if s not in offending_sentences]
        body = " ".join(kept).strip()
        if not body:
            body = "Let's get back to the actual question — what would help most right now?"
        rewrite = (body + "\n\n" + _VOICE_REPAIR_LINE_TEMPLATE.format(figure=figure)).strip()
        reason = f"named_figure: borrowed voice removed ({figure}, {voice_offenders[0][0]!r})"
        return False, rewrite, reason

    activation_offenders: list[tuple[str, str]] = []
    for s in sentences:
        for key, patterns in _ACTIVATION_PATTERNS_BY_FIGURE.items():
            if any(p.search(s) for p in patterns):
                activation_offenders.append((s, key))
                break

    if not activation_offenders:
        return True, None, None

    offending_sentences = {s for s, _ in activation_offenders}
    figure = _FIGURE_DISPLAY[activation_offenders[0][1]]
    kept = [s for s in sentences if s not in offending_sentences]
    body = " ".join(kept).strip()
    if not body:
        body = "Let's get back to the actual question — what would help most right now?"
    rewrite = (body + "\n\n" + _ACTIVATION_REPAIR_LINE_TEMPLATE.format(figure=figure)).strip()
    reason = f"named_figure: space-only activation removed ({figure}, {activation_offenders[0][0]!r})"
    return False, rewrite, reason


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
    Run all seven gates on a candidate response.

    Gate precedence for rewrites (highest first):
    Agency > Justice–Mercy > Epistemic > Wonder
    > No-Fake-Biography > No-Fake-Fandom > Named-Figure-Voice

    The content-shaping gates (1–4) run first because they can rewrite
    large portions of the response; the personality-register gates (5–7)
    run last because they audit final phrasing and should see whatever
    text survived the earlier gates. The Agency Gate's rewrite is
    wholesale, so every later gate runs on the rewritten text — a gate
    rewrite must itself survive the remaining gates.

    Returns (gated_response, GateReport).
    """
    if context is None:
        context = classify_context(user_message)

    report = GateReport()
    text = candidate_response

    ok, rewrite, reason = check_agency(text, state)
    report.agency_pass = ok
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    ok, rewrite, reason = check_justice_mercy(user_message, text)
    report.justice_mercy_pass = ok
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    ok, triggered, rewrite, reason = check_epistemic(text, context)
    report.epistemic_pass = ok
    report.epistemic_triggered = triggered
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    ok, rewrite, reason = check_wonder(text, mode)
    report.wonder_pass = ok
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    ok, rewrite, reason = check_no_fake_biography(text)
    report.no_fake_biography_pass = ok
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    ok, rewrite, reason = check_no_fake_fandom(text)
    report.no_fake_fandom_pass = ok
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    ok, rewrite, reason = check_named_figure_voice(text)
    report.named_figure_pass = ok
    if not ok:
        text = rewrite
        report.reasons.append(reason)

    report.rewrite_required = bool(report.reasons)
    return text, report
