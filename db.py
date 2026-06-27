"""
db.py — Soraya Study Database Layer

Fail-closed: if STUDY_MODE_ENABLED is True but credentials are missing
or invalid, every write raises StudyDBError rather than silently dropping
participant data.

The Space uses SUPABASE_WRITE_KEY (anon key, INSERT-only, RLS-scoped).
The Space cannot read participant rows. Exports and deletions require
the offline key (study_admin.py, local machine only).
"""

from __future__ import annotations
import hashlib
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from study_config import (
    STUDY_MODE_ENABLED,
    MESSAGE_STORAGE_MODE,
    SUPABASE_URL,
    SUPABASE_WRITE_KEY,
    SCHEMA_VERSION,
    CONSENT_VERSION,
    validate_config,
)

logger = logging.getLogger(__name__)

_client = None


class StudyDBError(RuntimeError):
    """Raised when a study-mode write fails or config is invalid."""


def _get_client():
    global _client
    if _client is not None:
        return _client

    errors = validate_config()
    if errors:
        raise StudyDBError(
            "Study DB config invalid — cannot write participant data:\n"
            + "\n".join(f" • {e}" for e in errors)
        )

    try:
        from supabase import create_client  # type: ignore
        _client = create_client(SUPABASE_URL, SUPABASE_WRITE_KEY)
        return _client
    except ImportError as exc:
        raise StudyDBError(
            "supabase-py is not installed. Add it to requirements.txt."
        ) from exc
    except Exception as exc:
        raise StudyDBError(f"Failed to create Supabase client: {exc}") from exc


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _message_fields(plaintext: str, prefix: str) -> dict[str, Any]:
    """
    Return the correct message columns based on MESSAGE_STORAGE_MODE.
    Both columns always present in the schema; plaintext is NULL in hash_only mode.
    """
    h = _sha256(plaintext)
    if MESSAGE_STORAGE_MODE == "plaintext_and_hash":
        return {f"{prefix}": plaintext, f"{prefix}_hash": h}
    else:  # hash_only
        return {f"{prefix}": None, f"{prefix}_hash": h}


def record_consent(
    participant_id: str,
    consent_granted: bool,
    ip_hash: str | None = None,
) -> None:
    """
    Write one consent record. Called for both grants and refusals so
    withdrawal analysis is complete.
    """
    if not STUDY_MODE_ENABLED:
        return

    row = {
        "id": str(uuid.uuid4()),
        "participant_id": participant_id,
        "consent_granted": consent_granted,
        "consent_version": CONSENT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "message_storage_mode": MESSAGE_STORAGE_MODE,
        "recorded_at": _now_iso(),
        "ip_hash": ip_hash,
    }

    try:
        _get_client().table("consent_records").insert(row).execute()
    except StudyDBError:
        raise
    except Exception as exc:
        raise StudyDBError(f"consent_records insert failed: {exc}") from exc


def record_turn_event(
    participant_id: str,
    session_id: str,
    turn_number: int,
    user_message: str,
    soraya_response: str,
    ledger_snapshot: dict[str, Any],
    gate_report: dict[str, Any],
    response_mode: str,
) -> None:
    """
    Write one turn event after every gated response.
    ledger_snapshot = LedgerState.to_dict()
    gate_report = GateReport.to_dict()
    """
    if not STUDY_MODE_ENABLED:
        return

    row: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "participant_id": participant_id,
        "session_id": session_id,
        "turn_number": turn_number,
        "response_mode": response_mode,
        "schema_version": SCHEMA_VERSION,
        "message_storage_mode": MESSAGE_STORAGE_MODE,
        "recorded_at": _now_iso(),
        # Ledger values — exact keys from LedgerState.to_dict()
        "A_hat": ledger_snapshot.get("A_hat"),
        "K_hat": ledger_snapshot.get("K_hat"),
        "D_hat": ledger_snapshot.get("D_hat"),
        # Gate results — exact keys from GateReport.to_dict()
        "agency_pass": gate_report.get("agency_pass"),
        "justice_mercy_pass": gate_report.get("justice_mercy_pass"),
        "epistemic_pass": gate_report.get("epistemic_pass"),
        "epistemic_triggered": gate_report.get("epistemic_triggered"),
        "wonder_pass": gate_report.get("wonder_pass"),
        "rewrite_required": gate_report.get("rewrite_required"),
        "gate_reasons": gate_report.get("reasons", []),
    }

    row.update(_message_fields(user_message, "user_msg"))
    row.update(_message_fields(soraya_response, "soraya_msg"))

    try:
        _get_client().table("turn_events").insert(row).execute()
    except StudyDBError:
        raise
    except Exception as exc:
        raise StudyDBError(f"turn_events insert failed: {exc}") from exc


def record_survey_response(
    participant_id: str,
    session_id: str,
    survey_slot: str,
    responses: dict[str, Any],
) -> None:
    """
    Write one survey slot response. An empty responses dict is a no-op —
    safe to call before instruments are finalized.
    """
    if not STUDY_MODE_ENABLED:
        return

    if not responses:
        logger.debug(
            "record_survey_response: empty slot %r — skipping", survey_slot
        )
        return

    row = {
        "id": str(uuid.uuid4()),
        "participant_id": participant_id,
        "session_id": session_id,
        "survey_slot": survey_slot,
        "responses": responses,
        "schema_version": SCHEMA_VERSION,
        "recorded_at": _now_iso(),
    }

    try:
        _get_client().table("survey_responses").insert(row).execute()
    except StudyDBError:
        raise
    except Exception as exc:
        raise StudyDBError(f"survey_responses insert failed: {exc}") from exc


def record_contingency_event(
    participant_id: str,
    session_id: str,
    turn_number: int,
    record: dict[str, Any],
) -> None:
    """
    Write one contingency-audit row. `record` is TurnPairRecord.to_dict()
    (from contingency_audit.audit_turn_pair).

    Mirrors record_turn_event: no-op outside study mode, raises StudyDBError
    on write failure so the caller (contingency_hook) can re-raise and the
    session is flagged data-incomplete.

    Requires a `contingency_events` table — see schema-contingency.sql. The
    Space writes INSERT-only under RLS; it cannot read these rows back.
    """
    if not STUDY_MODE_ENABLED:
        return

    row = {
        "id": str(uuid.uuid4()),
        "participant_id": participant_id,
        "session_id": session_id,
        "turn_number": turn_number,
        "verdict": record.get("verdict"),
        "prev_mode": record.get("prev_mode"),
        "curr_mode": record.get("curr_mode"),
        "prev_rank": record.get("prev_rank"),
        "curr_rank": record.get("curr_rank"),
        "band_prev": record.get("band_prev"),
        "band_curr": record.get("band_curr"),
        "competence_signal": record.get("competence_signal"),
        "signal_attempt_token": record.get("signal_attempt_token"),
        "signal_success_marker": record.get("signal_success_marker"),
        "proxy_warning": record.get("proxy_warning"),
        "note": record.get("note"),
        "schema_version": SCHEMA_VERSION,
        "recorded_at": _now_iso(),
    }

    try:
        _get_client().table("contingency_events").insert(row).execute()
    except StudyDBError:
        raise
    except Exception as exc:
        raise StudyDBError(f"contingency_events insert failed: {exc}") from exc
