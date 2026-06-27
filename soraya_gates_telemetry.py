"""
soraya_gates_telemetry.py — Gate telemetry helper (v1.3.2)

Merge this into soraya_gates.py, or import from it.

Usage inside a gate class:
    from soraya_gates_telemetry import summarize_gate_pass

    def evaluate(self, candidate, context):
        ...
        return summarize_gate_pass(
            gate_name="agency",
            result={"pass": True, "rewrite": False, "reasons": []},
            participant_id=context.get("participant_id"),
            turn_number=context.get("turn_number"),
            strict=True,  # default — raises on missing/malformed telemetry
        )

In non-strict mode: logs WARNING and returns a dict with
telemetry_missing=True and telemetry_complete=False instead of raising.
A telemetry gap therefore CANNOT masquerade as clean passing data.
"""

from __future__ import annotations
import logging
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_KEYS = frozenset({"pass", "rewrite", "reasons"})


class GateTelemetryError(ValueError):
    """Raised when gate telemetry is missing or malformed (strict mode)."""


def summarize_gate_pass(
    gate_name: str,
    result: dict[str, Any] | None,
    participant_id: str | None = None,
    turn_number: int | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    """
    Validate and normalize a gate result dict.

    Expected input shape:
        {"pass": bool, "rewrite": bool, "reasons": list[str], ...}

    Returns a normalized dict guaranteed to contain:
        gate_name, pass, rewrite, reasons, telemetry_complete

    Raises GateTelemetryError (strict=True) or logs WARNING and returns a
    telemetry_missing marker dict (strict=False) when result is None,
    not a dict, or missing required keys.
    """
    context = f"gate={gate_name!r} participant={participant_id!r} turn={turn_number!r}"

    if result is None:
        msg = f"Gate telemetry is None — {context}"
        if strict:
            raise GateTelemetryError(msg)
        logger.warning("GateTelemetryError (non-strict): %s", msg)
        return _missing_marker(gate_name, "result is None")

    if not isinstance(result, dict):
        msg = f"Gate telemetry is not a dict (got {type(result).__name__}) — {context}"
        if strict:
            raise GateTelemetryError(msg)
        logger.warning("GateTelemetryError (non-strict): %s", msg)
        return _missing_marker(gate_name, f"result type={type(result).__name__}")

    missing_keys = REQUIRED_KEYS - result.keys()
    if missing_keys:
        msg = f"Gate telemetry missing keys {sorted(missing_keys)} — {context}"
        if strict:
            raise GateTelemetryError(msg)
        logger.warning("GateTelemetryError (non-strict): %s", msg)
        return _missing_marker(gate_name, f"missing keys={sorted(missing_keys)}")

    return {
        "gate_name": gate_name,
        "pass": bool(result["pass"]),
        "rewrite": bool(result["rewrite"]),
        "reasons": list(result.get("reasons", [])),
        "telemetry_complete": True,
        "telemetry_missing": False,
        **{k: v for k, v in result.items() if k not in ("pass", "rewrite", "reasons")},
    }


def _missing_marker(gate_name: str, detail: str) -> dict[str, Any]:
    """
    Explicit telemetry gap marker returned in non-strict mode.
    Contains telemetry_missing=True and telemetry_complete=False so
    downstream consumers cannot treat it as a clean pass.
    """
    return {
        "gate_name": gate_name,
        "pass": False,   # conservative default
        "rewrite": True, # conservative default — flag for rewrite
        "reasons": [f"telemetry_missing:{detail}"],
        "telemetry_complete": False,
        "telemetry_missing": True,
    }
