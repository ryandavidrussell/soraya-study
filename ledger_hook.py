"""
ledger_hook.py — Study telemetry hook for the Soraya ledger.

Drop into the turn loop in app.py after apply_soraya_gates() and update().

Usage:
    from ledger_hook import record_study_turn
    record_study_turn(
        gate=consent_gate,
        user_message=user_msg,
        soraya_response=final_resp,
        ledger_state=new_state,
        gate_report=gate_report,
        mode=current_mode,
    )

Outside study mode → silent no-op.
Gate locked (not yet consented) → silent no-op.
Post-consent write failure → logs error and RE-RAISES. Do not swallow
StudyDBError in app.py — post-consent holes produce participants who
look complete but have Swiss-cheese data.
"""

from __future__ import annotations
import logging

from study_config import STUDY_MODE_ENABLED

logger = logging.getLogger(__name__)


def record_study_turn(
    gate,             # ConsentGate
    user_message: str,
    soraya_response: str,
    ledger_state,     # LedgerState — must expose .to_dict() and .turn
    gate_report,      # GateReport — must expose .to_dict()
    mode,             # ResponseMode enum — must expose .value
) -> None:
    """
    Write one turn_events row.

    Attribute alignment (verify against your ledger.py / soraya_gates.py):
        ledger_state.to_dict()  → keys: A_hat, K_hat, D_hat, turn
        gate_report.to_dict()   → keys: agency_pass, justice_mercy_pass,
                                         epistemic_pass, epistemic_triggered,
                                         wonder_pass, rewrite_required, reasons
        mode.value              → ResponseMode enum string

    INTEGRATION NOTE: Every line marked "← align" below references an
    attribute name from your classes. Check each one before staging.
    """
    if not STUDY_MODE_ENABLED:
        return

    if gate.is_locked():
        logger.debug(
            "record_study_turn: gate locked — skipping (participant not yet consented)"
        )
        return

    try:
        from db import record_turn_event, StudyDBError
    except ImportError as exc:
        logger.error("ledger_hook: cannot import db: %s", exc)
        return

    try:
        record_turn_event(
            participant_id=gate.participant_id,
            session_id=gate.session_id,
            turn_number=ledger_state.turn,          # ← align: LedgerState.turn
            user_message=user_message,
            soraya_response=soraya_response,
            ledger_snapshot=ledger_state.to_dict(), # ← align: LedgerState.to_dict()
            gate_report=gate_report.to_dict(),      # ← align: GateReport.to_dict()
            response_mode=mode.value,               # ← align: ResponseMode.value
        )
    except Exception as exc:
        logger.error(
            "record_study_turn FAILED — participant=%s turn=%d: %s",
            gate.participant_id,
            getattr(ledger_state, "turn", -1),
            exc,
        )
        raise  # Re-raise so app.py can mark the session data-incomplete
