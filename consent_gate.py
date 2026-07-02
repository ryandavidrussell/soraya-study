"""
consent_gate.py — Soraya Consent Gate

Gate starts LOCKED. Unlocks only after all three disclosure boxes are checked
and the consent record is written to Supabase without error.

Fail-closed: a failed consent DB write locks the gate back.

After successful consent, the participant receives their study ID — they need
it to request data deletion later (withdrawal right per pilot prospectus).

PERSISTENCE NOTE (added):
  db.py's anon key is INSERT-only under RLS — the Space cannot SELECT
  participant_id back from Supabase to check "have we seen this person
  before."  So persistent identity cannot be resolved server-side without
  weakening that write-only posture.

  Instead, identity persistence lives client-side: app.py hands this class
  whatever (participant_id, consent_granted) pair it finds in gr.BrowserState
  on load.  If both are present, the gate opens immediately with the restored
  participant_id — no new DB row, no new uuid, no intake shown.  If the
  browser has nothing stored (first visit, cleared storage, new device),
  behavior is exactly as before: fresh id, locked gate, intake required.

  This trades cross-device continuity for keeping the Space fully
  read-blind on participant data, which was the deliberate design point.
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
    (
        "cb_device_persistence",
        "I understand that my study ID is stored only in this browser. "
        "Returning on this same device and browser lets the study recognize "
        "me as the same participant. Switching devices or browsers, or "
        "clearing this browser\u2019s data, will start a new, unlinked study ID "
        "\u2014 so if I want my data treated as one continuous record, I should "
        "keep using the same browser on the same device.",
    ),
]


class ConsentGate:
    """
    Per-session consent state.  Instantiate once per Gradio session (gr.State).

    CHANGED: __init__ now optionally accepts a restored identity from
    gr.BrowserState so returning participants in the same browser skip
    intake.  Nothing about the DB write path changed — db.py stays
    INSERT-only and this class never queries it.
    """

    def __init__(
        self,
        restored_participant_id: str | None = None,
        restored_consent_granted: bool = False,
    ) -> None:
        self._session_id: str = str(uuid.uuid4())
        self._consent_version: str = CONSENT_VERSION

        if restored_participant_id and restored_consent_granted:
            # Returning participant, same browser — trust the client-side
            # record.  We can\u2019t verify against Supabase (write-only key),
            # so this is a client-asserted claim, same trust model as the
            # informed-consent checkboxes themselves.
            self._participant_id: str | None = restored_participant_id
            self._granted: bool = True
            logger.info(
                "Consent gate restored — participant_id=%s session_id=%s",
                restored_participant_id,
                self._session_id,
            )
        else:
            self._participant_id = None
            self._granted = False

    # ------------------------------------------------------------------
    # Public read properties
    # ------------------------------------------------------------------

    def is_locked(self) -> bool:
        if not STUDY_MODE_ENABLED:
            return False
        return not self._granted

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
        cb_device_persistence: bool,
        participant_id_override: str | None = None,
    ) -> tuple[bool, str]:
        """
        Attempt to grant consent.  Returns (success: bool, message: str).

        On success, message includes the participant\u2019s study ID.

        Unchanged from before, except: on success, the caller (app.py) is now
        responsible for writing (participant_id, True) into gr.BrowserState so
        the NEXT load skips intake.  This function itself still only touches
        Supabase, never browser storage.
        """
        if not STUDY_MODE_ENABLED:
            self._granted = True
            return True, "Study mode is off — gate transparent."

        if not (cb_messages and cb_anonymized and cb_withdrawal and cb_device_persistence):
            return False, (
                "Please check all four boxes to continue. "
                "You must acknowledge each item to participate."
            )

        if participant_id_override:
            self._participant_id = participant_id_override

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
            "Consent granted — participant_id=%s session_id=%s version=%s",
            self.participant_id,
            self._session_id,
            self._consent_version,
        )

        return True, (
            "Consent recorded. Welcome to the study.\n\n"
            f"Your study ID is `{self.participant_id}`. Please save this ID. "
            "You will need it if you later want to request deletion of your "
            "study data.\n\n"
            "**Important:** this study ID is stored only in this browser on "
            "this device. To continue as the same participant, return using "
            "this same browser on this same device. If you switch browsers, "
            "switch devices, use private/incognito mode, or clear browser "
            "data, the study will start a new, unlinked ID."
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
            f'<li style="margin-bottom:0.5em">{text}</li>'
            for _, text in DISCLOSURE_ITEMS
        )
        return (
            f'<div style="max-width:620px;padding:1.2em 1.5em;'
            f'border:1px solid #d4d1ca;border-radius:8px;'
            f'background:#f9f8f5;font-family:sans-serif;font-size:0.95em">'
            f'<h3 style="margin-top:0">Study Participation \u2014 Informed Consent</h3>'
            f'<p>Before using this version of Soraya, please read and '
            f'acknowledge each of the following:</p>'
            f'<ul style="padding-left:1.2em">{items_html}</ul>'
            f'<p style="color:#7a7974;font-size:0.85em">'
            f'Consent version: {self._consent_version}&nbsp;|&nbsp;'
            f'Session: {self._session_id[:8]}\u2026'
            f'</p></div>'
        )
