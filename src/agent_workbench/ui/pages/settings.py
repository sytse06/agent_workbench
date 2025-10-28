"""
Settings page - configuration interface.

Phase 1: Placeholder implementation
Phase 2: Full settings with model controls, persistence, etc.
See: docs/architecture/decisions/phase2/UI-005-settings-page.md
"""

from typing import Any, Dict

import gradio as gr


def render(config: Dict[str, Any], user_state: gr.State) -> None:
    """
    Render settings interface.

    Args:
        config: Mode configuration from mode_factory
        user_state: Shared user session state

    Note: Phase 1 placeholder - Phase 2 will add full settings implementation
    """

    # Header with back button
    with gr.Row():
        back_btn = gr.Button("← Back to Chat", size="sm")
        gr.Markdown("# ⚙️ Settings")

    # Placeholder content
    gr.Markdown(
        """
    ## Settings Page

    **Phase 1:** Placeholder implementation

    **Phase 2 will include:**
    - Model provider and model selection
    - Model parameters (temperature, max tokens)
    - Theme selection (Light/Dark/Auto)
    - Business profile (SEO coach mode)
    - Advanced options

    See: `docs/architecture/decisions/phase2/UI-005-settings-page.md`
    """
    )

    # Placeholder settings sections
    with gr.Accordion("Account", open=False):
        gr.Markdown("User authentication and profile management")

    with gr.Accordion("Models", open=False):
        gr.Markdown("AI model configuration (provider, model, parameters)")

    with gr.Accordion("Appearance", open=False):
        gr.Markdown("Theme selection and UI customization")

    with gr.Accordion("Advanced", open=False):
        gr.Markdown("Debug mode and experimental features")

    # Event: Navigate back to chat
    back_btn.click(fn=None, js="() => { window.location.href = '/'; }")
