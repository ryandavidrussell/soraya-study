"""
app.py — Soraya Gradio demo, v1.4.4 (browser-persistent identity).

Flow per turn:

  Input -> Context Classifier -> Agency Ledger -> Pedagogical Router
       -> Moral/Personality Covenant (in system prompt)
       -> Model Candidate -> Gates -> Final Response
       -> Ledger Update -> Study Telemetry -> Optional Voice-Out -> Audit Snapshot

v1.4.3 -> v1.4.4 changes (browser-persistent identity):
27. Consent gate identity now persists across page reloads in the same
    browser via gr.BrowserState, instead of minting a fresh ConsentGate
    (and therefore a fresh participant_id) on every load.  db.py stays
    INSERT-only / read-blind — persistence lives entirely client-side.
    See consent_gate.py’s PERSISTENCE NOTE for the full rationale.
28. Adds a fourth consent checkbox disclosing that identity is
    browser-scoped: switching device/browser or clearing browser data
    starts a new, unlinked study ID.
29. Returning, already-consented participants skip the consent screen
    on load but still see the pre-survey each session (pre/post survey
    responses are per-session, not per-identity).

v1.4.2 -> v1.4.3 changes (dependency-pressure telemetry):
25. Ledger signals are converted to a plain dict via dataclasses.asdict()
    before being handed to record_study_turn(), so ledger_hook.py and
    db.py never need to know about the UpdateSignals dataclass shape —
    they only ever see a dict.  This keeps the telemetry boundary honest.
26. Governance panel now surfaces "dependency pressure" alongside the
    existing signal labels when ledger.py’s dependency-pressure detector
    fires on the turn.

v1.4.1 -> v1.4.2 changes (Mobile Polish):
23. Adds compact tutoring discipline: one idea, one small example, one
    question; closing language points learners back to the method, not
    back to Soraya as a dependency.
24. Tightens mobile layout: smaller chat typography, less padding, hidden
    Gradio chrome where possible, and the cache-busted mark-only logo asset.

v1.4.0 -> v1.4.1 changes (Brand Shell):
21. Adds the Soraya brand shell: logo asset, hero, meaning strip,
    honesty/parked-module notes, legend, footer, and Gradio CSS skin.
22. Presentation-only patch.  No browser-side model calls, no microphone,
    no study contract changes, no changes to fail-closed telemetry.

v1.3.1 -> v1.4.0 changes (Stage 2 voice-out preview):
18. Adds optional voice-out after the governed response is generated and
    study telemetry has been recorded.  This is output-only: no microphone,
    no speech-to-text, no prosody, no participant audio capture.
19. Voice-out is controlled by a UI checkbox and SORAYA_VOICE_ENABLED.  TTS
    failures are non-blocking; the text chat remains the source of truth.
20. Generated audio is temporary local playback chrome.  Core study telemetry
    remains unchanged; optional voice metadata is best-effort only.

v1.3 -> v1.3.1 changes (Stage 0.5 survey flow):
15. Adds the full study journey: consent → pre-survey → chat → post-survey.
16. Pre/post survey items are imported from survey_items.py and visibly
    marked DRAFT / pending IRB.  Survey writes include INSTRUMENT_VERSION.
17. Pre/post submission requires every draft item to be answered before
    advancing, so participants cannot click through an empty instrument.

v1.2 -> v1.3 changes (Stage 0 study wiring):
12. Consent gate (consent_gate.py) lives in gr.State, one per session.
    When STUDY_MODE_ENABLED, a consent block gates the session and mints
    the participant_id / session_id used for all telemetry.
13. run_turn() calls record_study_turn() after update().  It passes
    gated_response (UI chrome excluded) and the mode used THIS turn,
    consistent with v1.2 note #10.  StudyDBError is intentionally NOT
    caught — a post-consent write failure must surface, never produce
    Swiss-cheese participant data.
14. Study mode OFF → behavior identical to v1.2: gate is transparent
    (is_locked() == False), the hook no-ops, chat is unrestricted.

v1.1 -> v1.2 changes (covenant + gates integration):
7.  Covenant prepended to every system prompt (soraya_covenant.py).
8.  Context classifier runs before routing; worldview questions
    route to the new REFLECT mode (REPAIR still outranks it).
9.  apply_soraya_gates() audits the model candidate after the call;
    failed gates produce deterministic rewrites.
10. Ledger update now uses gated_response — the response the learner
    actually received, minus UI-only prefixes.  If a gate forces a
    rewrite, the ledger accounts for the rewritten behavior, not the
    rejected draft.  (Supersedes v1.1 Fix 5, same principle: account
    for real behavior, exclude UI chrome.)
11. Governance panel shows the four-gate audit + rewrite status.
"""

import os
from dataclasses import asdict


def _patch_huggingface_hub_hffolder():
    """Compatibility shim for Gradio 4.44.x with newer huggingface_hub.

    Gradio 4.44 imports HfFolder from huggingface_hub.oauth.  Recent
    huggingface_hub releases removed that symbol.  The Space should pin
    huggingface_hub==0.25.2, but this shim keeps startup robust if the
    base image or cache provides a newer hub package anyway.
    """
    try:
        import huggingface_hub as _hf
        if hasattr(_hf, "HfFolder"):
            return

        class HfFolder:  # minimal API Gradio expects
            @staticmethod
            def get_token():
                get_token = getattr(_hf, "get_token", None)
                if callable(get_token):
                    return get_token()
                return None

            @staticmethod
            def save_token(token):
                return None

            @staticmethod
            def delete_token():
                return None

        _hf.HfFolder = HfFolder
    except Exception:
        pass


_patch_huggingface_hub_hffolder()

from ledger import (
    LedgerState,
    update,
    route,
    ResponseMode,
    get_repair_text,
    get_visibility_transition,
    build_system_prompt,
    capture_snapshot,
)

from soraya_gates import apply_soraya_gates, classify_context, GateReport

# --- Study wiring (Stage 0) -------------------------------------------------
from ledger_hook import record_study_turn
from consent_gate import ConsentGate, DISCLOSURE_ITEMS
from study_config import STUDY_MODE_ENABLED
from survey_items import (
    PRE_SURVEY_ITEMS,
    POST_SURVEY_ITEMS,
    LIKERT5_LABELS,
    INSTRUMENT_VERSION,
)

from voice_out import VoiceOutResult, synthesize_voice_out
from brand_shell import (
    BRAND_CSS,
    SORAYA_MARK_PATH,
    hero_html,
    meaning_html,
    parked_module_html,
    limit_bar_html,
    legend_html,
    footer_html,
)

# ---------------------------------------------------------------------------

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default


MAX_TOKENS = _env_int("SORAYA_MAX_TOKENS", 384)

_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
_API_KEY_MISSING = not _API_KEY.strip()

_API_WARNING = (
    "\n\n> \u26a0\ufe0f **ANTHROPIC_API_KEY is not set.** "
    "Responses will return an API error until the key is configured."
    if _API_KEY_MISSING else ""
)

COMPACT_TUTORING_DISCIPLINE = """

Soraya delivery discipline for the live demo:
- Teach in pocket-sized turns.  Prefer one idea, one tiny example, and one question.
- In tutoring, usually stay under 160 words; exceed that only when the learner explicitly asks for a fuller explanation or safety/consent requires it.
- Do not list more than three options unless the learner asks.
- When the learner is wrong, name the turn gently and give them a repair path.  Do not shame; do not simply hand over the answer if a smaller scaffold will work.
- Close by pointing the learner back to the method they can use next, not back to you as the safety blanket.  Prefer “try the same trace first” over “come back to me.”
""".strip()


def _apply_compact_tutoring_discipline(system_prompt: str) -> str:
    """Append output-shaping rules without changing routing, gates, or study data."""
    return f"{system_prompt}\n\n{COMPACT_TUTORING_DISCIPLINE}"


_MODE_EMOJI = {
    ResponseMode.REORIENT: "\U0001F9ED",
    ResponseMode.HINT:     "\U0001F4A1",
    ResponseMode.DELEGATE: "\U0001F331",
    ResponseMode.REPAIR:   "\U000026A0",
    ResponseMode.FULL:     "\U00002705",
    ResponseMode.REFLECT:  "\U0001FA9E",
}

_BAR_WIDTH = 20


def _bar(value: float, width: int = _BAR_WIDTH) -> str:
    filled = int(round(value * width))
    return "\u2588" * filled + "\u2591" * (width - filled)


def run_turn(
    user_message: str,
    chat_history: list,
    ledger_dict: dict,
    prev_contribution_length: int,
    consent_gate=None,
    voice_requested: bool = False,
    mock_api_fn=None,
) -> tuple[list, dict, str, int, str | None]:
    if not user_message.strip():
        return chat_history, ledger_dict, "", prev_contribution_length, None

    if consent_gate is not None and consent_gate.is_locked():
        notice = (
            "*Please complete the consent form above to begin. "
            "Your messages are only stored after you consent.*"
        )
        new_history = chat_history + [(user_message, notice)]
        return new_history, ledger_dict, "", prev_contribution_length, None

    state = LedgerState.from_dict(ledger_dict) if ledger_dict else LedgerState()

    context = classify_context(user_message)
    mode = route(state, worldview=context.worldview)
    system_prompt = _apply_compact_tutoring_discipline(
        build_system_prompt(state, mode)
    )

    visibility_prefix = get_visibility_transition(mode)
    repair_text = get_repair_text(state) if mode == ResponseMode.REPAIR else None

    messages = []
    for h, a in chat_history:
        messages.append({"role": "user",      "content": h})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": user_message})

    if mock_api_fn is not None:
        raw_response = mock_api_fn(system_prompt, messages)
    else:
        try:
            import anthropic as _anthro
            _client = _anthro.Anthropic(api_key=_API_KEY)
            api_resp = _client.messages.create(
                model=MODEL, max_tokens=MAX_TOKENS,
                system=system_prompt, messages=messages,
            )
            raw_response = api_resp.content[0].text
        except Exception as e:
            raw_response = f"[API error: {e}]"

    gated_response, gate_report = apply_soraya_gates(
        user_message=user_message,
        candidate_response=raw_response,
        state=state,
        mode=mode,
        context=context,
    )

    parts = []
    if visibility_prefix:
        parts.append(f"*{visibility_prefix}*\n\n")
    if repair_text and mode == ResponseMode.REPAIR:
        parts.append(f"{repair_text}\n\n")
    parts.append(gated_response)
    final_response = "".join(parts)

    new_state, signals = update(
        state,
        user_input=user_message,
        response=gated_response,
        outcome=None,
        prev_contribution_length=prev_contribution_length,
    )

    if consent_gate is not None:
        record_study_turn(
            gate=consent_gate,
            user_message=user_message,
            soraya_response=gated_response,
            ledger_state=new_state,
            gate_report=gate_report,
            mode=mode,
            signals=asdict(signals) if signals is not None else None,
        )

    voice_result = synthesize_voice_out(final_response, requested=voice_requested)
    _record_voice_metadata(consent_gate, new_state, voice_result)

    next_mode = route(new_state)
    snap = capture_snapshot(new_state, next_mode, signals, repair_text is not None)
    panel = _build_panel(
        new_state, mode, next_mode, snap, signals, gate_report, voice_result
    )

    chat_history = chat_history + [(user_message, final_response)]

    return (
        chat_history,
        new_state.to_dict(),
        panel,
        signals.contribution_length,
        voice_result.audio_path if voice_result.success else None,
    )


def _build_panel(state, this_mode, next_mode, snap, signals,
                 gate_report: GateReport,
                 voice_result: VoiceOutResult | None = None) -> str:
    this_emoji = _MODE_EMOJI.get(this_mode, "")
    next_emoji = _MODE_EMOJI.get(next_mode, "")

    fired = [k for k, v in {
        "attempt detected":    signals.user_attempted,
        "solution requested":  signals.user_requested_solution,
        "dependency pressure": signals.dependency_pressure,
        "goal clarified":      signals.user_clarified_goal,
        "full answer given":   signals.system_gave_full_answer,
        "positive outcome":    signals.outcome_positive,
    }.items() if v]
    signals_str = ", ".join(fired) if fired else "none"

    gate_lines = [
        "**Gate audit**",
        "```",
        f"Agency          {'PASS' if gate_report.agency_pass        else 'REWRITE'}",
        f"Justice/Mercy   {'PASS' if gate_report.justice_mercy_pass else 'REWRITE'}",
        f"Epistemic       "
        + ('PASS' if gate_report.epistemic_pass else 'REWRITE')
        + (' (triggered)' if gate_report.epistemic_triggered else ' (not triggered)'),
        f"Wonder/Humor    {'PASS' if gate_report.wonder_pass        else 'REWRITE'}",
        f"Rewrite needed  {'yes' if gate_report.rewrite_required    else 'no'}",
        "```",
    ]

    if gate_report.reasons:
        gate_lines.append("")
        gate_lines.append("**Gate reasons:**")
        gate_lines.extend(f"- {r}" for r in gate_report.reasons)

    voice_lines = ["**Voice-out**", "```"]
    if voice_result is None:
        voice_lines.append("Requested  no")
        voice_lines.append("Status     not run")
    else:
        voice_lines.append(f"Requested  {'yes' if voice_result.requested else 'no'}")
        voice_lines.append(f"Global enabled  {'yes' if voice_result.enabled else 'no'}")
        voice_lines.append(f"Provider   {voice_result.provider or 'none'}")
        voice_lines.append(f"Success    {'yes' if voice_result.success else 'no'}")
        if voice_result.skipped_reason:
            voice_lines.append(f"Skipped    {voice_result.skipped_reason}")
        if voice_result.error_type:
            voice_lines.append(f"Error type {voice_result.error_type}")
        if voice_result.chars:
            voice_lines.append(f"Chars spoken {voice_result.chars}")
    voice_lines.append("```")

    return "\n".join([
        "### Soraya Governance Panel", "",
        f"**Turn {state.turn}**",
        f"Mode used: {this_emoji} `{this_mode.value.upper()}`",
        f"Next mode: {next_emoji} `{next_mode.value.upper()}`",
        "",
        "**Ledger state (estimated)**",
        "```",
        f"Agency      {_bar(state.A_hat)} {state.A_hat:.2f}",
        f"Confusion   {_bar(state.K_hat)} {state.K_hat:.2f}",
        f"Dependency  {_bar(state.D_hat)} {state.D_hat:.2f}",
        "```",
        "",
        *gate_lines,
        "",
        *voice_lines,
        "",
        f"**Signals this turn:** {signals_str}",
        "",
        f"**Repair triggered:** {'yes \u26a0\ufe0f' if snap.repair_triggered else 'no'}",
        "",
        "---",
        "_These are estimates, not facts about the learner\u2019s internal state._",
        _API_WARNING,
    ])


def reset_session():
    init = LedgerState()
    class _FS:  repair_triggered = False
    class _FSig:
        user_attempted = user_requested_solution = user_clarified_goal = False
        dependency_pressure = False
        system_gave_full_answer = outcome_positive = False
        contribution_length = 0
    panel = _build_panel(init, ResponseMode.HINT, ResponseMode.HINT,
                         _FS(), _FSig(), GateReport(), None)
    return [], init.to_dict(), panel, 0, None


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

def run_turn_ui(user_message, chat_history, ledger_dict,
                prev_contribution_length, consent_gate, voice_requested):
    """Annotation-free Gradio wrapper to avoid /info schema crashes."""
    return run_turn(
        user_message, chat_history, ledger_dict,
        prev_contribution_length, consent_gate=consent_gate,
        voice_requested=voice_requested,
    )


CSS = """
#governance-panel {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    background: #F4F3EF;
    border-radius: 6px;
    padding: 1rem;
    height: 100%;
}
"""


def _patch_gradio_bool_schema_bug():
    """Patch older gradio_client schema rendering for boolean JSON schemas."""
    try:
        import gradio_client.utils as client_utils

        original = client_utils._json_schema_to_python_type

        def safe_json_schema_to_python_type(schema, defs=None):
            if isinstance(schema, bool):
                return "Any" if schema else "None"
            return original(schema, defs)

        client_utils._json_schema_to_python_type = safe_json_schema_to_python_type

        try:
            import gradio.routes as routes
            routes.client_utils._json_schema_to_python_type = safe_json_schema_to_python_type
        except Exception:
            pass
    except Exception:
        pass


_SURVEY_DRAFT_NOTE = (
    "> \u26a0\ufe0f **Draft instrument (version `{ver}`) \u2014 pending IRB.** "
    "These placeholder items exist so the participant flow can be walked "
    "end to end.  They are not a validated instrument and will be replaced "
    "before any real data collection."
)


def _survey_missing_items(items, widget_values):
    missing = []
    for (_key, prompt, kind), value in zip(items, widget_values):
        if value is None:
            missing.append(prompt)
        elif kind == "text" and not str(value).strip():
            missing.append(prompt)
    return missing


def _collect_survey(items, widget_values):
    responses = {}
    for (key, _prompt, kind), value in zip(items, widget_values):
        if value is None:
            continue
        if kind == "text" and not str(value).strip():
            continue
        responses[key] = value
    if responses:
        responses["_instrument_version"] = INSTRUMENT_VERSION
    return responses


def _record_survey(gate, slot, items, widget_values):
    from db import record_survey_response
    responses = _collect_survey(items, widget_values)
    record_survey_response(
        participant_id=gate.participant_id,
        session_id=gate.session_id,
        survey_slot=slot,
        responses=responses,
    )


def _record_voice_metadata(gate, ledger_state, voice_result: VoiceOutResult) -> None:
    if gate is None or voice_result is None:
        return
    try:
        if gate.is_locked():
            return
    except Exception:
        return
    try:
        from db import record_voice_out_event
    except Exception:
        return
    try:
        record_voice_out_event(
            participant_id=gate.participant_id,
            session_id=gate.session_id,
            turn=getattr(ledger_state, "turn", None),
            metadata=voice_result.to_dict(),
        )
    except Exception:
        return


def build_ui():
    import gradio as gr
    _patch_gradio_bool_schema_bug()

    with gr.Blocks(css=CSS + BRAND_CSS, title="Soraya \u2014 A Demonstration") as demo:
        ledger_state = gr.State({})
        contrib_len  = gr.State(0)

        # One ConsentGate per session, replaced on load once we know
        # whether this browser already carries a consented identity.
        consent_gate = gr.State(ConsentGate)

        # Browser-persisted identity.  Lives in localStorage, not on the
        # server.  db.py stays INSERT-only / read-blind.
        # See consent_gate.py PERSISTENCE NOTE for full rationale.
        identity_store = gr.BrowserState(
            {"participant_id": None, "consent_granted": False}
        )

        with gr.Group(elem_classes=["soraya-root"]):
            with gr.Group(elem_classes=["soraya-hero"]):
                gr.Image(
                    value=SORAYA_MARK_PATH,
                    show_label=False,
                    interactive=False,
                    elem_classes=["soraya-hero-mark"],
                )

            gr.HTML(hero_html())
            gr.HTML(meaning_html())

            pre_widgets  = []
            post_widgets = []
            if STUDY_MODE_ENABLED:
                # --- Stage 1: Consent ---
                with gr.Group(elem_classes=["soraya-study-group"]) as consent_group:
                    consent_html = gr.HTML()
                    cb1 = gr.Checkbox(label=DISCLOSURE_ITEMS[0][1])
                    cb2 = gr.Checkbox(label=DISCLOSURE_ITEMS[1][1])
                    cb3 = gr.Checkbox(label=DISCLOSURE_ITEMS[2][1])
                    cb4 = gr.Checkbox(label=DISCLOSURE_ITEMS[3][1])
                    pid_box = gr.Textbox(
                        label="Prolific ID (optional)",
                        placeholder="leave blank to be assigned a study ID",
                    )
                    consent_btn = gr.Button("I consent \u2014 begin", variant="primary")
                    consent_msg = gr.Markdown()

                # --- Stage 2: Pre-survey (hidden until consent) ---
                with gr.Group(visible=False, elem_classes=["soraya-study-group"]) as pre_group:
                    gr.Markdown("### Before we begin")
                    gr.Markdown(_SURVEY_DRAFT_NOTE.format(ver=INSTRUMENT_VERSION))
                    for key, prompt, kind in PRE_SURVEY_ITEMS:
                        if kind == "likert5":
                            pre_widgets.append(
                                gr.Radio(choices=LIKERT5_LABELS, label=prompt)
                            )
                        else:
                            pre_widgets.append(gr.Textbox(label=prompt, lines=2))
                    pre_btn = gr.Button("Start session", variant="primary")
                    pre_msg = gr.Markdown()

                # --- Stage 4: Post-survey (hidden until session finished) ---
                with gr.Group(visible=False, elem_classes=["soraya-study-group"]) as post_group:
                    gr.Markdown("### After the session")
                    gr.Markdown(_SURVEY_DRAFT_NOTE.format(ver=INSTRUMENT_VERSION))
                    for key, prompt, kind in POST_SURVEY_ITEMS:
                        if kind == "likert5":
                            post_widgets.append(
                                gr.Radio(choices=LIKERT5_LABELS, label=prompt)
                            )
                        else:
                            post_widgets.append(gr.Textbox(label=prompt, lines=2))
                    post_btn = gr.Button("Submit & finish", variant="primary")
                    post_msg = gr.Markdown()

            with gr.Group(visible=not STUDY_MODE_ENABLED,
                          elem_classes=["soraya-console"]) as chat_group:
                with gr.Row():
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            label=None,
                            show_label=False,
                            height=420,
                            elem_classes=["soraya-chatbot"],
                        )
                        with gr.Row():
                            msg_box = gr.Textbox(
                                placeholder="Type your message\u2026",
                                show_label=False,
                                lines=2,
                                scale=5,
                                elem_classes=["soraya-textbox"],
                            )
                            send_btn  = gr.Button("Send",  variant="primary",   scale=1)
                            reset_btn = gr.Button("Reset", variant="secondary", scale=1)
                        voice_toggle = gr.Checkbox(
                            label="Let Soraya read her reply aloud",
                            value=False,
                        )
                        voice_audio = gr.Audio(
                            label=None,
                            show_label=False,
                            type="filepath",
                            interactive=False,
                            elem_classes=["soraya-audio"],
                        )
                        if STUDY_MODE_ENABLED:
                            finish_btn = gr.Button("Finish session \u2192",
                                                   variant="secondary")
                    with gr.Column(scale=2):
                        panel = gr.Markdown(
                            value="*Governance panel initialises on first turn.*",
                            elem_id="governance-panel",
                            elem_classes=["soraya-governance-panel"],
                            label="Governance Panel",
                        )

            gr.HTML(parked_module_html())
            gr.HTML(limit_bar_html())
            gr.HTML(legend_html())
            gr.HTML(footer_html())

        # ----- Study flow wiring -------------------------------------------
        if STUDY_MODE_ENABLED:

            def _do_consent(
                gate,
                cb_messages,
                cb_anonymized,
                cb_withdrawal,
                cb_device_persistence,
                pid,
            ):
                ok, message = gate.submit(
                    cb_messages,
                    cb_anonymized,
                    cb_withdrawal,
                    cb_device_persistence,
                    participant_id_override=(pid or None),
                )
                new_identity = (
                    {"participant_id": gate.participant_id, "consent_granted": True}
                    if ok else gr.skip()
                )
                return (
                    gate,
                    message,
                    new_identity,
                    gr.update(visible=not ok),   # consent_group
                    gr.update(visible=ok),        # pre_group
                )

            def _on_load(stored_identity):
                """Restore identity from BrowserState before first paint.

                Returning participants (same browser, same device) skip the
                consent screen and land on the pre-survey.  Fresh visitors
                get the full intake as before.
                """
                stored_identity = stored_identity or {}
                gate = ConsentGate(
                    restored_participant_id=stored_identity.get("participant_id"),
                    restored_consent_granted=stored_identity.get(
                        "consent_granted", False
                    ),
                )
                already_consented = not gate.is_locked()
                return (
                    gate,
                    gate.render_consent_form(),
                    gr.update(visible=not already_consented),   # consent_group
                    gr.update(visible=already_consented),        # pre_group
                )

            demo.load(
                fn=_on_load,
                inputs=identity_store,
                outputs=[consent_gate, consent_html, consent_group, pre_group],
            )

            consent_btn.click(
                fn=_do_consent,
                inputs=[consent_gate, cb1, cb2, cb3, cb4, pid_box],
                outputs=[consent_gate, consent_msg, identity_store,
                         consent_group, pre_group],
                api_name=False,
            )

            def _do_pre(gate, *vals):
                missing = _survey_missing_items(PRE_SURVEY_ITEMS, vals)
                if missing:
                    return (
                        gr.update(visible=True),
                        gr.update(visible=False),
                        "Please answer every pre-survey item before starting.",
                    )
                _record_survey(gate, "pre", PRE_SURVEY_ITEMS, vals)
                return gr.update(visible=False), gr.update(visible=True), ""

            pre_btn.click(
                fn=_do_pre,
                inputs=[consent_gate, *pre_widgets],
                outputs=[pre_group, chat_group, pre_msg],
                api_name=False,
            )

            def _do_finish():
                return gr.update(visible=False), gr.update(visible=True)

            finish_btn.click(
                fn=_do_finish, inputs=None,
                outputs=[chat_group, post_group],
                api_name=False,
            )

            def _do_post(gate, *vals):
                missing = _survey_missing_items(POST_SURVEY_ITEMS, vals)
                if missing:
                    return gr.update(
                        value="Please answer every post-survey item before finishing."
                    )
                _record_survey(gate, "post", POST_SURVEY_ITEMS, vals)
                return gr.update(
                    value=("Thank you \u2014 your responses are recorded. "
                           "You may close this window.")
                )

            post_btn.click(
                fn=_do_post,
                inputs=[consent_gate, *post_widgets],
                outputs=[post_msg],
                api_name=False,
            )

        send_btn.click(
            fn=run_turn_ui,
            inputs=[
                msg_box, chatbot, ledger_state, contrib_len,
                consent_gate, voice_toggle,
            ],
            outputs=[chatbot, ledger_state, panel, contrib_len, voice_audio],
            api_name=False,
        ).then(fn=lambda: "", inputs=None, outputs=msg_box)

        msg_box.submit(
            fn=run_turn_ui,
            inputs=[
                msg_box, chatbot, ledger_state, contrib_len,
                consent_gate, voice_toggle,
            ],
            outputs=[chatbot, ledger_state, panel, contrib_len, voice_audio],
            api_name=False,
        ).then(fn=lambda: "", inputs=None, outputs=msg_box)

        reset_btn.click(
            fn=reset_session, inputs=None,
            outputs=[chatbot, ledger_state, panel, contrib_len, voice_audio],
            api_name=False,
        )

    return demo


if __name__ == "__main__":
    ui = build_ui()
    ui.launch(server_name="0.0.0.0", server_port=7860, share=False)
