"""
db.py — Soraya Study Database Layer

Fail-closed: if STUDY_MODE_ENABLED is True but credentials are missing
or invalid, every write raises StudyDBError rather than silently dropping
participant data.

The Space uses SUPABASE_WRITE_KEY (anon key, INSERT-only, RLS-scoped).
The Space cannot read participant rows. Exports and deletions require
the offline key (study_admin.py, local machine only).

IMPORTANT — returning="minimal":
All inserts use returning="minimal" (PostgREST Prefer: return=minimal).
Without this, supabase-py defaults to return=representation, which asks
PostgREST to hand back the inserted row. Postgres RLS treats that as an
implicit SELECT on the new row — and since anon has no SELECT policy on
these tables (by design: participants must not be able to read back
study data), that implicit check silently fails with the same 42501
"row violates row-level security policy" error as a genuine INSERT
rejection, even though the INSERT's WITH CHECK passes fine. Using
returning="minimal" skips the read-back entirely, matching the
INSERT-only posture these tables are supposed to have.

DEPENDENCY-PRESSURE TELEMETRY NOTE:
record_turn_event() accepts an optional `signals` dict — the plain-dict
payload produced by dataclasses.asdict(UpdateSignals) in ledger.py and
passed through unchanged by ledger_hook.py. This is intentionally a
separate parameter from gate_report: dependency_pressure is a ledger
signal, not a gate-audit result, and is kept out of gate_reasons so the
two audit categories don't get muddied together.

TEMPORARY DIAGNOSTIC NOTE:
This version still logs the Supabase URL and the write key's
length/prefix (never the full key) and exposes the real
ImportError/Exception detail instead of a generic message, to help
diagnose any further connection issues. Safe to remove once the
pipeline is confirmed stable end to end.
"""

from __future__ import annotations

import hashlib
import logging
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from study_config import (
    CONSENT_VERSION,
    MESSAGE_STORAGE_MODE,
    SCHEMA_VERSION,
    STUDY_MODE_ENABLED,
    SUPABASE_URL,
    SUPABASE_WRITE_KEY,
    validate_config,
)

logger = logging.getLogger(__name__)

_client = None

class StudyDBError(RuntimeError):
    """Raised when a study-mode write fails or config is invalid."""

def _get_client():
    """
    Create and cache the Supabase client.

    This function intentionally fails closed in study mode:
    - Missing/invalid config raises StudyDBError.
    - Supabase import/client failures raise StudyDBError.
    - The caller should not silently continue after this fails.
    """
    global _client

    if _client is not None:
        return _client

    errors = validate_config()
    if errors:
        raise StudyDBError(
            "Study DB config invalid — cannot write participant data:\n"
            + "\n".join(f"  \u2022 {e}" for e in errors)
        )

    module_file = None

    # --- TEMPORARY DIAGNOSTIC: safe to log, never logs the full key ---
    print("[supabase] URL:", SUPABASE_URL, flush=True)
    print(
        "[supabase] KEY length:",
        len(SUPABASE_WRITE_KEY) if SUPABASE_WRITE_KEY else 0,
        flush=True,
    )
    print(
        "[supabase] KEY prefix:",
        SUPABASE_WRITE_KEY[:15] if SUPABASE_WRITE_KEY else None,
        flush=True,
    )
    # --- END TEMPORARY DIAGNOSTIC ---

    try:
        import supabase as supabase_module  # type: ignore

        module_file = getattr(supabase_module, "__file__", None)

        print("[supabase] module file:", module_file, flush=True)
        print("[supabase] sys.path[0]:", sys.path[0], flush=True)

        from supabase import create_client   # type: ignore

        _client = create_client(SUPABASE_URL, SUPABASE_WRITE_KEY)
        return _client

    except ImportError as exc:
        raise StudyDBError(
            "Supabase import failed:\n"
            f"  \u2022 error type: {type(exc).__name__}\n"
            f"  \u2022 error: {exc}\n"
            f"  \u2022 module file: {module_file}\n"
            f"  \u2022 sys.path[0]: {sys.path[0]}"
        ) from exc

    except Exception as exc:
        raise StudyDBError(
            "Failed to create Supabase client:\n"
            f"  \u2022 error type: {type(exc).__name__}\n"
            f"  \u2022 error: {exc}\n"
            f"  \u2022 module file: {module_file}\n"
            f"  \u2022 sys.path[0]: {sys.path[0]}"
        ) from exc

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _message_fields(plaintext: str, prefix: str) -> dict[str, Any]:
    """
    Return the correct message columns based on MESSAGE_STORAGE_MODE.

    Both columns always exist in the schema. Plaintext is NULL in
    hash_only mode.
    """
    h = _sha256(plaintext)

    if MESSAGE_STORAGE_MODE == "plaintext_and_hash":
        return {
            f"{prefix}":       plaintext,
            f"{prefix}_hash": h,
        }
    return {
        f"{prefix}":       None,
        f"{prefix}_hash": h,
    }

def record_consent(
    participant_id: str,
    consent_granted: bool,
    ip_hash: str | None = None,
) -> None:
    """
    Write one consent record.

    Called for both grants and refusals so withdrawal / refusal analysis
    is complete.
    """
    if not STUDY_MODE_ENABLED:
        return

    row = {
        "id":                   str(uuid.uuid4()),
        "participant_id":       participant_id,
        "consent_granted":      consent_granted,
        "consent_version":      CONSENT_VERSION,
        "schema_version":       SCHEMA_VERSION,
        "message_storage_mode": MESSAGE_STORAGE_MODE,
        "recorded_at":          _now_iso(),
        "ip_hash":              ip_hash,
    }

    try:
        _get_client().table("consent_records").insert(
            row, returning="minimal"
        ).execute()

    except StudyDBError:
        raise

    except Exception as exc:
        raise StudyDBError(f"consent_records insert failed: {exc}") from exc

def record_turn_event(
    participant_id:   str,
    session_id:       str,
    turn_number:      int,
    user_message:     str,
    soraya_response:  str,
    ledger_snapshot:  dict[str, Any],
    gate_report:      dict[str, Any],
    response_mode:    str,
    signals:          dict[str, Any] | None = None,
) -> None:
    """
    Write one turn event after every gated response.

    ledger_snapshot = LedgerState.to_dict()
    gate_report     = GateReport.to_dict()
    signals         = dataclasses.asdict(UpdateSignals) from ledger.py, passed
                      through by ledger_hook.py — a plain dict, not the dataclass
                      itself. May be None outside study mode or on older callers.
    """
    if not STUDY_MODE_ENABLED:
        return

    row: dict[str, Any] = {
        "id":                   str(uuid.uuid4()),
        "participant_id":       participant_id,
        "session_id":           session_id,
        "turn_number":          turn_number,
        "response_mode":        response_mode,
        "schema_version":       SCHEMA_VERSION,
        "message_storage_mode": MESSAGE_STORAGE_MODE,
        "recorded_at":          _now_iso(),

        # Ledger values — exact keys from LedgerState.to_dict()
        "A_hat": ledger_snapshot.get("A_hat"),
        "K_hat": ledger_snapshot.get("K_hat"),
        "D_hat": ledger_snapshot.get("D_hat"),

        # Gate results — exact keys from GateReport.to_dict()
        "agency_pass":        gate_report.get("agency_pass"),
        "justice_mercy_pass": gate_report.get("justice_mercy_pass"),
        "epistemic_pass":     gate_report.get("epistemic_pass"),
        "epistemic_triggered":gate_report.get("epistemic_triggered"),
        "wonder_pass":        gate_report.get("wonder_pass"),
        "rewrite_required":   gate_report.get("rewrite_required"),
        "gate_reasons":       gate_report.get("reasons", []),
    }

    # Message fields (plaintext or hash depending on MESSAGE_STORAGE_MODE)
    row.update(_message_fields(user_message,    "user_message"))
    row.update(_message_fields(soraya_response, "soraya_response"))

    # Signals dict — stored as JSONB; None is fine (column is nullable)
    row["signals"] = signals

    try:
        _get_client().table("turn_events").insert(
            row, returning="minimal"
        ).execute()

    except StudyDBError:
        raise

    except Exception as exc:
        raise StudyDBError(f"turn_events insert failed: {exc}") from exc

def record_survey_response(
    participant_id: str,
    session_id:     str,
    survey_slot:    str,
    responses:      dict[str, Any],
) -> None:
    """
    Write one survey response block (pre or post).

    survey_slot: "pre" or "post"
    responses:   {key: value} dict from _collect_survey() in app.py
    """
    if not STUDY_MODE_ENABLED:
        return
    if not responses:
        return

    row = {
        "id":             str(uuid.uuid4()),
        "participant_id": participant_id,
        "session_id":     session_id,
        "survey_slot":    survey_slot,
        "responses":      responses,
        "recorded_at":    _now_iso(),
    }

    try:
        _get_client().table("survey_responses").insert(
            row, returning="minimal"
        ).execute()

    except StudyDBError:
        raise

    except Exception as exc:
        raise StudyDBError(f"survey_responses insert failed: {exc}") from exc

def record_voice_out_event(
    participant_id: str,
    session_id:     str,
    turn:           int | None,
    metadata:       dict[str, Any],
) -> None:
    """
    Best-effort voice-out metadata hook.

    Not part of the core study data contract. Caller (_record_voice_metadata
    in app.py) swallows exceptions from this function — voice metadata must
    not create fake incompleteness in the participant dataset.
    """
    if not STUDY_MODE_ENABLED:
        return

    row = {
        "id":             str(uuid.uuid4()),
        "participant_id": participant_id,
        "session_id":     session_id,
        "turn":           turn,
        "metadata":       metadata,
        "recorded_at":    _now_iso(),
    }

    try:
        _get_client().table("voice_out_events").insert(
            row, returning="minimal"
        ).execute()

    except StudyDBError:
        raise

    except Exception as exc:
        raise StudyDBError(f"voice_out_events insert failed: {exc}") from exc
