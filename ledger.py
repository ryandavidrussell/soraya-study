"""
soraya/ledger.py — v1.0

Soraya Agency Ledger: state schema, heuristic update function,
constraint router, repair layer.

Governing equation:
    L_{t+1} = P_C( F(L_hat_t, x_t, y_t, o_t) )

State variables (all estimated, range [0,1]):
    A_hat — Agency trajectory (higher = more agency)
    K_hat — Confusion load (higher = more confused)
    D_hat — Dependency risk (higher = more dependency risk)
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
import json

try:
    from soraya_covenant import SORAYA_COVENANT, CENTRAL_INVARIANT
except Exception:
    SORAYA_COVENANT = "You are Soraya, a governed learning companion."
    CENTRAL_INVARIANT = (
        "The system must not become more powerful "
        "by making the human being less capable."
    )

# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------

@dataclass
class LedgerState:
    """
    Estimated ledger state L_hat_t = (A_hat, K_hat, D_hat).

    All values are floats in [0.0, 1.0].
    These are estimates, not direct observations of internal mental state.
    """
    A_hat: float = 0.5   # Agency trajectory — initialized neutral
    K_hat: float = 0.5   # Confusion load — initialized neutral
    D_hat: float = 0.1   # Dependency risk — initialized low

    # Turn counter and mode history (not exported to prompt, used internally)
    turn: int = 0
    mode_history: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "A_hat": round(self.A_hat, 4),
            "K_hat": round(self.K_hat, 4),
            "D_hat": round(self.D_hat, 4),
            "turn":  self.turn,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "LedgerState":
        return cls(
            A_hat=d.get("A_hat", 0.5),
            K_hat=d.get("K_hat", 0.5),
            D_hat=d.get("D_hat", 0.1),
            turn=d.get("turn", 0),
        )


# ---------------------------------------------------------------------------
# Signal detection helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _detect_attempt(user_input: str) -> bool:
    """
    Heuristic: user is making an attempt rather than just requesting a solution.
    Requires both: substantial length AND at least one reasoning marker.
    Short help-requests (e.g. "just tell me") must not trigger this.
    """
    if _detect_help_request(user_input):
        return False
    length_ok = len(user_input.split()) >= 10
    has_reasoning = any(kw in user_input.lower() for kw in [
        "because", "since", "therefore", "i think", "i believe",
        "let me try", "i tried", "my approach", "i got", "my result",
        "derivation", "proof", "equation", "i set", "i compute", "i calculated"
    ])
    return length_ok and has_reasoning


def _detect_help_request(user_input: str) -> bool:
    """
    Heuristic: user is directly requesting a full solution without attempting.
    """
    request_phrases = [
        "just tell me", "give me the answer", "what is the answer",
        "solve it for me", "can you do this", "do it for me",
        "just give", "please answer", "just answer",
        "what's the solution", "show me how to do"
    ]
    lowered = user_input.lower()
    return any(phrase in lowered for phrase in request_phrases)


def _detect_goal_clarified(user_input: str) -> bool:
    """
    Heuristic: user's goal has become more explicit.
    """
    return any(kw in user_input.lower() for kw in [
        "i want to", "my goal is", "i'm trying to", "i need to",
        "the question asks", "i understand now", "oh i see"
    ])


def _detect_answer_mode(response: str) -> bool:
    """
    Heuristic: response delivered a complete answer rather than a hint.
    """
    length = len(response.split())
    has_full_solution = any(phrase in response.lower() for phrase in [
        "the answer is", "therefore", "in conclusion", "thus",
        "the solution is", "here is the full", "complete solution"
    ])
    return length > 200 or has_full_solution


def _user_contribution_length(user_input: str) -> int:
    return len(user_input.split())


# ---------------------------------------------------------------------------
# UpdateSignals
# ---------------------------------------------------------------------------

@dataclass
class UpdateSignals:
    """
    Human-readable record of which heuristics fired this turn.
    Used for telemetry and audit.
    """
    user_attempted: bool = False
    user_requested_solution: bool = False
    user_clarified_goal: bool = False
    system_gave_full_answer: bool = False
    contribution_length: int = 0
    outcome_positive: Optional[bool] = None


def _update_raw(
    state: LedgerState,
    user_input: str,
    response: str,
    outcome: Optional[bool] = None,
    prev_contribution_length: int = 0,
) -> tuple[LedgerState, UpdateSignals]:
    """
    F: unconstrained heuristic update.
    Returns a new (unclamped, unprojected) state and the signals fired.
    """
    sig = UpdateSignals(
        user_attempted=_detect_attempt(user_input),
        user_requested_solution=_detect_help_request(user_input),
        user_clarified_goal=_detect_goal_clarified(user_input),
        system_gave_full_answer=_detect_answer_mode(response),
        contribution_length=_user_contribution_length(user_input),
        outcome_positive=outcome,
    )

    dA = 0.0
    dK = 0.0
    dD = 0.0

    # --- Agency signals ---
    if sig.user_attempted:
        dA += 0.08
    if sig.outcome_positive is True:
        dA += 0.10
    if sig.system_gave_full_answer and not sig.user_attempted:
        dA -= 0.10
    if sig.user_requested_solution:
        dA -= 0.05

    # --- Confusion signals ---
    if sig.user_clarified_goal:
        dK -= 0.12
    if sig.user_attempted and sig.outcome_positive:
        dK -= 0.08
    if sig.user_attempted and not sig.outcome_positive:
        dK += 0.04  # persistent confusion despite attempt
    if not sig.user_attempted and not sig.user_clarified_goal:
        dK += 0.03  # no signal of orientation improvement

    # --- Dependency signals ---
    if sig.user_requested_solution and not sig.user_attempted:
        dD += 0.12
    if sig.system_gave_full_answer:
        dD += 0.06
    if sig.user_attempted:
        dD -= 0.06
    if sig.contribution_length > prev_contribution_length + 5:
        dD -= 0.04  # user is contributing more
    if sig.contribution_length < prev_contribution_length - 10:
        dD += 0.04  # user is shrinking contribution

    # Conservative step: cap single-turn delta at ±0.15 per variable
    dA = _clamp(dA, -0.15, 0.15)
    dK = _clamp(dK, -0.15, 0.15)
    dD = _clamp(dD, -0.15, 0.15)

    new_state = LedgerState(
        A_hat=state.A_hat + dA,
        K_hat=state.K_hat + dK,
        D_hat=state.D_hat + dD,
        turn=state.turn + 1,
        mode_history=list(state.mode_history),
    )

    return new_state, sig


# ---------------------------------------------------------------------------
# Constraint projection P_C
# ---------------------------------------------------------------------------

def _project(state: LedgerState) -> LedgerState:
    """
    P_C: clamp all variables to [0, 1] and enforce soft lower bound on agency.
    No hard lower-bound interventions here — those are handled by the router.
    """
    return LedgerState(
        A_hat=_clamp(state.A_hat),
        K_hat=_clamp(state.K_hat),
        D_hat=_clamp(state.D_hat),
        turn=state.turn,
        mode_history=list(state.mode_history),
    )


# ---------------------------------------------------------------------------
# Full update: L_{t+1} = P_C( F(L_hat_t, x_t, y_t, o_t) )
# ---------------------------------------------------------------------------

def update(
    state: LedgerState,
    user_input: str,
    response: str,
    outcome: Optional[bool] = None,
    prev_contribution_length: int = 0,
) -> tuple[LedgerState, UpdateSignals]:
    """
    Apply one full ledger update step.
    Returns (new LedgerState, UpdateSignals).
    """
    raw_state, signals = _update_raw(
        state, user_input, response, outcome, prev_contribution_length
    )
    projected = _project(raw_state)
    return projected, signals


# ---------------------------------------------------------------------------
# Response mode enum
# ---------------------------------------------------------------------------

class ResponseMode(str, Enum):
    REORIENT = "reorient"     # High confusion, low agency — clarify goal first
    HINT     = "hint"         # Moderate confusion, agency available — scaffold
    DELEGATE = "delegate"     # Low confusion, high agency — step back
    REPAIR   = "repair"       # Rising dependency — explicitly reduce over-help
    FULL     = "full_answer"  # Low dependency, low confusion — direct answer OK
    REFLECT  = "reflect"      # Worldview-level question — disciplined meaning-making


# ---------------------------------------------------------------------------
# Constraint router
# ---------------------------------------------------------------------------

def route(state: LedgerState, worldview: bool = False) -> ResponseMode:
    """
    Map ledger state to a response mode.
    This is the primary governance function.

    Precedence (highest first):
    1. Repair — dependency is rising and high
    2. Reflect — worldview-level question (context classifier fired)
    3. Reorient — confusion load is high and agency is low
    4. Hint — moderate confusion or moderate agency
    5. Delegate — learner is tracking well and has agency
    6. Full — low confusion, reasonable agency, low dependency

    REPAIR outranks REFLECT deliberately: a worldview question does not
    suspend the anti-dependency safeguard. Backward compatible —
    route(state) behaves exactly as v1.0.
    """
    A = state.A_hat
    K = state.K_hat
    D = state.D_hat

    if D >= 0.65:
        return ResponseMode.REPAIR

    if worldview:
        return ResponseMode.REFLECT

    if K >= 0.65 and A <= 0.40:
        return ResponseMode.REORIENT

    if K >= 0.65:
        return ResponseMode.HINT

    if A >= 0.70 and K <= 0.35 and D <= 0.30:
        return ResponseMode.DELEGATE

    return ResponseMode.HINT


# ---------------------------------------------------------------------------
# Repair trigger and repair library
# ---------------------------------------------------------------------------

REPAIR_TEMPLATES = [
    {
        "trigger": lambda s: s.D_hat >= 0.65 and s.A_hat <= 0.45,
        "text": (
            "I've been giving you quite a bit — let me try a different approach. "
            "What's your next move here? I'll build from your attempt."
        ),
        "type": "dependency_high"
    },
    {
        "trigger": lambda s: s.D_hat >= 0.55 and s.K_hat <= 0.35,
        "text": (
            "You seem clear on the goal, so the next step belongs to you. "
            "Give me your attempt and I'll tell you where it lands."
        ),
        "type": "dependency_moderate_with_clarity"
    },
    {
        "trigger": lambda s: s.D_hat >= 0.70,
        "text": (
            "I want to flag something: I think I've been doing too much of this. "
            "Let's reset — what do you understand so far, in your own words?"
        ),
        "type": "dependency_critical"
    },
    {
        "trigger": lambda s: s.A_hat <= 0.25 and s.D_hat >= 0.45,
        "text": (
            "Before I say anything else, I want to hear your instinct. "
            "What would you try, even if you're not sure it's right?"
        ),
        "type": "agency_critical"
    },
    {
        "trigger": lambda s: s.K_hat >= 0.70 and s.D_hat >= 0.50,
        "text": (
            "Let's pause. I'm not sure more information helps right now. "
            "Can you tell me what the goal is, in your own words?"
        ),
        "type": "confusion_with_dependency"
    },
]

VISIBILITY_TRANSITIONS = {
    ResponseMode.REPAIR:    (
        "I've been giving too much — switching to a different mode. "
        "I'll hold back and work from your next move."
    ),
    ResponseMode.REORIENT:  (
        "It looks like we may need to clarify the goal before going further."
    ),
    ResponseMode.DELEGATE:  (
        "You're tracking well — I'll step back and let you take the next move."
    ),
    ResponseMode.HINT:      None,
    ResponseMode.FULL:      None,
    ResponseMode.REFLECT:   (
        "This one is bigger than mechanics — let's slow down and take it seriously."
    ),
}


def get_repair_text(state: LedgerState) -> Optional[str]:
    for template in REPAIR_TEMPLATES:
        if template["trigger"](state):
            return template["text"]
    return None


def get_visibility_transition(mode: ResponseMode) -> Optional[str]:
    return VISIBILITY_TRANSITIONS.get(mode)


# ---------------------------------------------------------------------------
# Prompt scaffold
# ---------------------------------------------------------------------------

def build_system_prompt(state: LedgerState, mode: ResponseMode) -> str:
    mode_instruction = {
        ResponseMode.REORIENT: (
            "Your primary goal is reorientation. Before adding any new content, "
            "clarify what the learner is trying to do. Ask one focused question. "
            "Do not give more information until the goal is explicit."
        ),
        ResponseMode.HINT: (
            "Give a hint or scaffold — not a full solution. "
            "Identify the single next step and help the learner take it themselves. "
            "Do not complete the task for them."
        ),
        ResponseMode.DELEGATE: (
            "The learner has agency and clarity. Your job is to get out of the way. "
            "Offer a brief reflective prompt or check-in. "
            "Do not over-explain or solve."
        ),
        ResponseMode.REPAIR: (
            "Dependency risk is elevated. You have been giving too much. "
            "Do not give a full answer. Explicitly ask the learner for their next attempt. "
            "Acknowledge the shift if helpful. Work only from what they provide."
        ),
        ResponseMode.FULL: (
            "The learner has sufficient agency and clarity. "
            "A complete answer is appropriate here. Be concise and accurate."
        ),
        ResponseMode.REFLECT: (
            "The learner is asking a meaning, identity, moral, or worldview-level "
            "question. This is disciplined meaning-making, not therapy. "
            "Slow down. Define the terms. Separate what is known from what is "
            "being interpreted. Name uncertainty honestly. Steelman the serious "
            "views. There may be multiple legitimate interpretations, but not "
            "every interpretation is equally legitimate — context, evidence, "
            "logic, and human stakes constrain meaning. Do not impose a "
            "worldview, and do not retreat into 'everyone has their own truth.' "
            "End by returning judgment to the learner with one honest next question."
        ),
    }

    visibility = get_visibility_transition(mode)
    visibility_line = (
        f"\nBefore responding, briefly say: '{visibility}'"
        if visibility else ""
    )

    return f"""{SORAYA_COVENANT}

Central invariant:
{CENTRAL_INVARIANT}

Your purpose is to make each response accountable to the learner's developing agency.

Current learner state (estimated, not certain):
- Agency: {state.A_hat:.2f} (0=no agency, 1=full agency)
- Confusion load: {state.K_hat:.2f} (0=clear, 1=very confused)
- Dependency risk: {state.D_hat:.2f} (0=no risk, 1=high dependency)

Current response mode: {mode.value.upper()}

Mode instruction: {mode_instruction[mode]}{visibility_line}

When shifting modes, name the shift briefly and honestly.
Do not assert the learner's internal state as fact — use hedged language.
'It looks like you might be stuck' not 'You are confused.'"""


# ---------------------------------------------------------------------------
# Telemetry snapshot
# ---------------------------------------------------------------------------

@dataclass
class TurnSnapshot:
    turn: int
    A_hat: float
    K_hat: float
    D_hat: float
    mode: str
    repair_triggered: bool
    user_contribution_length: int
    signals: dict

    def to_dict(self) -> dict:
        return {
            "turn":  self.turn,
            "A_hat": round(self.A_hat, 4),
            "K_hat": round(self.K_hat, 4),
            "D_hat": round(self.D_hat, 4),
            "mode":  self.mode,
            "repair_triggered": self.repair_triggered,
            "user_contribution_length": self.user_contribution_length,
            "signals": self.signals,
        }


def capture_snapshot(
    state: LedgerState,
    mode: ResponseMode,
    signals: UpdateSignals,
    repair_triggered: bool,
) -> TurnSnapshot:
    return TurnSnapshot(
        turn=state.turn,
        A_hat=state.A_hat,
        K_hat=state.K_hat,
        D_hat=state.D_hat,
        mode=mode.value,
        repair_triggered=repair_triggered,
        user_contribution_length=signals.contribution_length,
        signals={
            "user_attempted": signals.user_attempted,
            "user_requested_solution": signals.user_requested_solution,
            "user_clarified_goal": signals.user_clarified_goal,
            "system_gave_full_answer": signals.system_gave_full_answer,
            "outcome_positive": signals.outcome_positive,
        },
    )
