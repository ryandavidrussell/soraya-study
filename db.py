""" db.py — Soraya Study Database Layer

Fail-closed: if STUDY_MODE_ENABLED is True but credentials are missing or invalid,
the layer raises StudyDBError rather than silently dropping data.
"""
from __future__ import annotations
import os, uuid, logging
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)

STUDY_MODE_ENABLED = os.getenv("STUDY_MODE_ENABLED", "false").lower() == "true"
SUPABASE_URL       = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY       = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")

_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise StudyDBError("SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY not set")
    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _client
    except Exception as exc:
        raise StudyDBError(f"Supabase init failed: {exc}") from exc


class StudyDBError(RuntimeError):
    pass


@dataclass
class SessionRecord:
    participant_id: str
    session_id: str
    condition: str
    consented_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TurnRecord:
    session_id: str
    participant_id: str
    turn_index: int
    user_message: str
    assistant_message: str
    condition: str
    a_hat: float
    k_hat: float
    d_hat: float
    routing_mode: str
    gate_agency_pass: bool
    gate_justice_pass: bool
    gate_epistemic_pass: bool
    gate_wonder_pass: bool
    gate_repairs: int
    latency_ms: int
    model: str
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SurveyRecord:
    session_id: str
    participant_id: str
    survey_slot: str   # "pre" | "post"
    items: dict        # {item_key: response_value}
    submitted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def record_session(rec: SessionRecord) -> None:
    if not STUDY_MODE_ENABLED:
        return
    db = _get_client()
    try:
        db.table("study_sessions").insert({
            "participant_id": rec.participant_id,
            "session_id":     rec.session_id,
            "condition":      rec.condition,
            "consented_at":   rec.consented_at,
        }).execute()
    except Exception as exc:
        raise StudyDBError(f"record_session failed: {exc}") from exc


def record_study_turn(rec: TurnRecord) -> None:
    if not STUDY_MODE_ENABLED:
        return
    db = _get_client()
    try:
        db.table("study_turns").insert({
            "turn_id":           rec.turn_id,
            "session_id":        rec.session_id,
            "participant_id":    rec.participant_id,
            "turn_index":        rec.turn_index,
            "user_message":      rec.user_message,
            "assistant_message": rec.assistant_message,
            "condition":         rec.condition,
            "a_hat":             rec.a_hat,
            "k_hat":             rec.k_hat,
            "d_hat":             rec.d_hat,
            "routing_mode":      rec.routing_mode,
            "gate_agency_pass":  rec.gate_agency_pass,
            "gate_justice_pass": rec.gate_justice_pass,
            "gate_epistemic_pass": rec.gate_epistemic_pass,
            "gate_wonder_pass":  rec.gate_wonder_pass,
            "gate_repairs":      rec.gate_repairs,
            "latency_ms":        rec.latency_ms,
            "model":             rec.model,
            "created_at":        rec.created_at,
        }).execute()
    except Exception as exc:
        raise StudyDBError(f"record_study_turn failed: {exc}") from exc


def record_survey(rec: SurveyRecord) -> None:
    if not STUDY_MODE_ENABLED:
        return
    db = _get_client()
    try:
        db.table("survey_responses").insert({
            "session_id":     rec.session_id,
            "participant_id": rec.participant_id,
            "survey_slot":    rec.survey_slot,
            "items":          rec.items,
            "submitted_at":   rec.submitted_at,
        }).execute()
    except Exception as exc:
        raise StudyDBError(f"record_survey failed: {exc}") from exc
