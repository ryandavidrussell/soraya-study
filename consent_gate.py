"""
consent_gate.py — Soraya Consent Gate

Gate starts LOCKED. Unlocks only after all three disclosure boxes are
checked and the consent record is written to Supabase without error.
Fail-closed: a failed consent DB write locks the gate back.

After successful consent, the participant receives their study ID —
they need it to request data deletion later (withdrawal right per
pilot prospectus).
"""

from __future__ import annotations
import uuid
import logging

from study_config import STUDY_MODE_ENABLED, CONSENT_VERSION

logger = logging.getLogger(__name__)

DISCLOSURE_ITEMS = [
    (
        "cb_messages",
        "I understand that my typed messages to Soraya and Soraya\u2019s responses "
        "may be stored and analysed as part of this research study.",
    ),
    (
        "cb_anonymized",
        "I understand that data will be de-identified before any publication "
        "or sharing outside the research team.",
    ),
    (
        "cb_withdrawal",
        "I understand that I may withdraw at any time and request deletion of "
        "my data by contacting the research team with my study ID.",
    ),
]


class ConsentGate:
    """
    Per-session consent state.
    Instantiate once per Gradio session (gr.State).
    """

    def __init__(self) -> None:
        self._granted: bool = False
        self._participant_id: str | None = None
        self._session_id: str = str(uuid.uuid4())
        self._consent_version: str = CONSENT_VERSION
        self._session_invalid: bool = False

    # ------------------------------------------------------------------
    # Public read properties
    # ------------------------------------------------------------------

    def is_locked(self) -> bool:
        if not STUDY_MODE_ENABLED:
            return False
        return not self._granted

    @property
    def session_invalid(self) -> bool:
        """True once any post-consent turn write has failed. The session
        produced data with holes; analysis should exclude it rather than
        treat it as complete."""
        return self._session_invalid

    def mark_session_invalid(self, reason: str = "") -> None:
        """Flag this session as data-incomplete and persist the flag so
        the export carries it. Called by app.py when a turn write raises.
        Best effort: if the flag write itself fails, the in-memory flag
        still holds for the life of the session."""
        self._session_invalid = True
        if not STUDY_MODE_ENABLED:
            return
        try:
            from db import record_session_invalid
            record_session_invalid(
                participant_id=self.participant_id,
                session_id=self.session_id,
                reason=reason,
            )
        except Exception as exc:
            # never let flag-writing crash the turn
            logger.error(
                "Failed to persist session_invalid for %s/%s: %s",
                self.participant_id,
                self._session_id,
                exc,
            )

    @property
    def participant_id(self) -> str:
        if self._participant_id is None:
            self._participant_id = str(uuid.uuid4())
        return self._participant_id

    @property
    def session_id(self) -> str:
        return self._session_id

    # ------------------------------------------------------------------
    # Consent flow
    # ------------------------------------------------------------------

    def submit(
        self,
        cb_messages: bool,
        cb_anonymized: bool,
        cb_withdrawal: bool,
        participant_id_override: str | None = None,
    ) -> tuple[bool, str]:
        """
        Attempt to grant consent.
        Returns (success: bool, message: str).
        On success, message includes the participant's study ID.
        """
        if not STUDY_MODE_ENABLED:
            self._granted = True
            return True, "Study mode is off \u2014 gate transparent."

        if not (cb_messages and cb_anonymized and cb_withdrawal):
            return False, (
                "Please check all three boxes to continue. "
                "You must acknowledge each item to participate."
            )

        if participant_id_override:
            self._participant_id = participant_id_override

        # Optimistically set granted, then roll back on write failure.
        self._granted = True
        try:
            from db import record_consent
            record_consent(
                participant_id=self.participant_id,
                consent_granted=True,
            )
        except Exception as exc:
            self._granted = False
            logger.error(
                "Consent record write failed for session %s: %s",
                self._session_id,
                exc,
            )
            return False, (
                "There was a problem recording your consent. "
                f"Please refresh and try again. (Error: {exc})"
            )

        logger.info(
            "Consent granted \u2014 participant_id=%s session_id=%s version=%s",
            self.participant_id,
            self._session_id,
            self._consent_version,
        )
        return True, (
            "Consent recorded. Welcome to the study.\n\n"
            f"**Your study ID is: `{self.participant_id}`**\n\n"
            "Please save this ID. You will need it if you want to request "
            "deletion of your study data later."
        )

    def decline(self) -> None:
        """Record a refusal so withdrawal analysis is complete."""
        if not STUDY_MODE_ENABLED:
            return
        try:
            from db import record_consent
            record_consent(
                participant_id=self.participant_id,
                consent_granted=False,
            )
        except Exception as exc:
            logger.warning(
                "Consent refusal record failed (non-fatal) for session %s: %s",
                self._session_id,
                exc,
            )

    # ------------------------------------------------------------------
    # UI helper
    # ------------------------------------------------------------------

    def render_consent_form(self) -> str:
        items_html = "".join(
            f'<div class="disclosure-item"><strong>{label}</strong></div>\n'
            for _, label in DISCLOSURE_ITEMS
        )
        return (
            f'<div class="consent-form">\n'
            f'<p>Before using this version of Soraya, please read and '
            f'acknowledge each of the following:</p>\n\n'
            f'{items_html}'
            f'<p class="consent-meta">'
            f'Consent version: {self._consent_version} | '
            f'Session: {self._session_id[:8]}\u2026'
            f'</p>\n</div>'
        )
