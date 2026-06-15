"""
app.py — Soraya Gradio demo, v1.2.

Flow per turn:

Input -> Context Classifier -> Agency Ledger -> Pedagogical Router
-> Moral/Personality Covenant (in system prompt)
-> Model Candidate -> Gates -> Final Response
-> Ledger Update -> Audit Snapshot

v1.1 -> v1.2 changes (covenant + gates integration):
7. Covenant prepended to every system prompt (soraya_covenant.py).
8. Context classifier runs before routing; worldview questions
   route to the new REFLECT mode (REPAIR still outranks it).
9. apply_soraya_gates() audits the model candidate after the call;
   failed gates produce deterministic rewrites.
10. Ledger update now uses gated_response — the response the learner
    actually received, minus UI-only prefixes. If a gate forces a
    rewrite, the ledger accounts for the rewritten behavior, not the
    rejected draft. (Supersedes v1.1 Fix 5, same principle: account
    for real behavior, exclude UI chrome.)
11. Governance panel shows the four-gate audit + rewrite status.
"""

import os

def _patch_huggingface_hub_hffolder():
    """Compatibility shim for Gradio 4.44.x with newer huggingface_hub.

    Gradio 4.44 imports HfFolder from huggingface_hub.oauth. Recent
    huggingface_hub releases removed that symbol. The Space should pin
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
                # Spaces should use environment secrets, not persisted tokens.
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

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = 512

_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
_API_KEY_MISSING = not _API_KEY.strip()

_API_WARNING = (
    "\n\n> \u26a0\ufe0f **ANTHROPIC_API_KEY is not set.** "
    "Responses will return an API error until the key is configured."
    if _API_KEY_MISSING else ""
)

_MODE_EMOJI = {
    ResponseMode.REORIENT: "\U0001F9ED",  # compass
    ResponseMode.HINT:     "\U0001F4A1",  # bulb
    ResponseMode.DELEGATE: "\U0001F331",  # seedling
    ResponseMode.REPAIR:   "\U000026A0",  # warning
    ResponseMode.FULL:     "\U00002705",  # check
    ResponseMode.REFLECT:  "\U0001FA9E",  # mirror
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
    mock_api_fn=None,  # injectable for testing
) -> tuple[list, dict, str, int]:
    if not user_message.strip():
        return chat_history, ledger_dict, "", prev_contribution_length

    state = LedgerState.from_dict(ledger_dict) if ledger_dict else LedgerState()

    # Context classifier BEFORE routing
    context = classify_context(user_message)

    # Route BEFORE model call (REPAIR outranks REFLECT)
    mode = route(state, worldview=context.worldview)
    system_prompt = build_system_prompt(state, mode)  # covenant inside
    visibility_prefix = get_visibility_transition(mode)
    repair_text = get_repair_text(state) if mode == ResponseMode.REPAIR else None

    messages = []
    for h, a in chat_history:
        messages.append({"role": "user", "content": h})
        messages.append({"role": "assistant", "content": a})
    messages.append({"role": "user", "content": user_message})

    # Call model (or mock)
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

    # GATES: audit the candidate before the learner sees it
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

    # Ledger update uses gated_response — the behavior the learner
    # actually received, minus UI-only prefixes.
    new_state, signals = update(
        state,
        user_input=user_message,
        response=gated_response,
        outcome=None,
        prev_contribution_length=prev_contribution_length,
    )

    # Re-route with updated state → this is the NEXT turn's mode
    next_mode = route(new_state)
    snap = capture_snapshot(new_state, next_mode, signals, repair_text is not None)
    panel = _build_panel(new_state, mode, next_mode, snap, signals, gate_report)
    chat_history = chat_history + [(user_message, final_response)]

    return (chat_history, new_state.to_dict(), panel, signals.contribution_length)


def _build_panel(state, this_mode, next_mode, snap, signals,
                 gate_report: GateReport) -> str:
    this_emoji = _MODE_EMOJI.get(this_mode, "")
    next_emoji = _MODE_EMOJI.get(next_mode, "")

    fired = [k for k, v in {
        "attempt detected":      signals.user_attempted,
        "solution requested":    signals.user_requested_solution,
        "goal clarified":        signals.user_clarified_goal,
        "full answer given":     signals.system_gave_full_answer,
        "positive outcome":      signals.outcome_positive,
    }.items() if v]
    signals_str = ", ".join(fired) if fired else "none"

    gate_lines = [
        "**Gate audit**",
        "```",
        f"Agency       {'PASS' if gate_report.agency_pass else 'REWRITE'}",
        f"Justice/Mercy {'PASS' if gate_report.justice_mercy_pass else 'REWRITE'}",
        f"Epistemic    "
        + ('PASS' if gate_report.epistemic_pass else 'REWRITE')
        + (' (triggered)' if gate_report.epistemic_triggered else ' (not triggered)'),
        f"Wonder/Humor {'PASS' if gate_report.wonder_pass else 'REWRITE'}",
        f"Rewrite needed {'yes' if gate_report.rewrite_required else 'no'}",
        "```",
    ]

    if gate_report.reasons:
        gate_lines.append("")
        gate_lines.append("**Gate reasons:**")
        gate_lines.extend(f"- {r}" for r in gate_report.reasons)

    return "\n".join([
        "### Soraya Governance Panel", "",
        f"**Turn {state.turn}**",
        f"Mode used: {this_emoji} `{this_mode.value.upper()}`",
        f"Next mode: {next_emoji} `{next_mode.value.upper()}`",
        "",
        "**Ledger state (estimated)**",
        "```",
        f"Agency     {_bar(state.A_hat)} {state.A_hat:.2f}",
        f"Confusion  {_bar(state.K_hat)} {state.K_hat:.2f}",
        f"Dependency {_bar(state.D_hat)} {state.D_hat:.2f}",
        "```",
        "",
        *gate_lines,
        "",
        f"**Signals this turn:** {signals_str}",
        "",
        f"**Repair triggered:** {'yes ⚠️' if snap.repair_triggered else 'no'}",
        "",
        "---",
        "_These are estimates, not facts about the learner's internal state._",
        _API_WARNING,
    ])


def reset_session():
    init = LedgerState()
    class _FS: repair_triggered = False
    class _FSig:
        user_attempted = user_requested_solution = user_clarified_goal = False
        system_gave_full_answer = outcome_positive = False
        contribution_length = 0
    panel = _build_panel(init, ResponseMode.HINT, ResponseMode.HINT,
                         _FS(), _FSig(), GateReport())
    return [], init.to_dict(), panel, 0


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

def run_turn_ui(user_message, chat_history, ledger_dict, prev_contribution_length):
    """Annotation-free Gradio wrapper to avoid /info schema crashes."""
    return run_turn(user_message, chat_history, ledger_dict, prev_contribution_length)


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


def build_ui():
    import gradio as gr
    _patch_gradio_bool_schema_bug()

    with gr.Blocks(css=CSS, title="Soraya — Governed Tutoring") as demo:
        ledger_state = gr.State({})
        contrib_len = gr.State(0)

        gr.Markdown(
            "## Soraya\n"
            "*Path-dependent state governance — not just chat history.*"
        )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Conversation", height=480,
                                     bubble_full_width=False)
                with gr.Row():
                    msg_box = gr.Textbox(placeholder="Type your message…",
                                        show_label=False, scale=5)
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                    reset_btn = gr.Button("Reset", variant="secondary", scale=1)
            with gr.Column(scale=2):
                panel = gr.Markdown(
                    value="*Governance panel initialises on first turn.*",
                    elem_id="governance-panel", label="Governance Panel",
                )

        send_btn.click(
            fn=run_turn_ui,
            inputs=[msg_box, chatbot, ledger_state, contrib_len],
            outputs=[chatbot, ledger_state, panel, contrib_len],
            api_name=False,
            show_api=False,
        ).then(fn=lambda: "", inputs=None, outputs=msg_box)

        msg_box.submit(
            fn=run_turn_ui,
            inputs=[msg_box, chatbot, ledger_state, contrib_len],
            outputs=[chatbot, ledger_state, panel, contrib_len],
            api_name=False,
            show_api=False,
        ).then(fn=lambda: "", inputs=None, outputs=msg_box)

        reset_btn.click(
            fn=reset_session, inputs=None,
            outputs=[chatbot, ledger_state, panel, contrib_len],
            api_name=False,
            show_api=False,
        )

    return demo


if __name__ == "__main__":
    ui = build_ui()
    ui.launch(server_name="0.0.0.0", server_port=7860, share=False, show_api=False)
