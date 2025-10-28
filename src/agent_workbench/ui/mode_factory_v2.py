"""
Mode Factory V2 - Creates Gradio app based on APP_MODE environment variable.

Pattern:
    create_app() → create_workbench_app() OR create_seo_app()
                → build_gradio_app(config)

No code duplication - single builder, different configurations.
"""

import os
from typing import Any, Dict

import gradio as gr

from .pages import chat, settings
from .styles import SHARED_CSS


def create_app() -> gr.Blocks:
    """
    Entry point - creates Gradio app based on APP_MODE environment variable.

    Returns:
        gr.Blocks: Single Gradio Blocks instance with routes
    """
    mode = os.getenv("APP_MODE", "workbench")

    if mode == "workbench":
        return create_workbench_app()
    elif mode == "seo_coach":
        return create_seo_app()
    else:
        # Fallback to workbench
        return create_workbench_app()


def create_workbench_app() -> gr.Blocks:
    """
    Workbench mode configuration - technical users.

    Returns:
        gr.Blocks: Configured Gradio app for workbench mode
    """
    config = {
        "title": "Agent Workbench",
        "theme": gr.themes.Base(primary_hue="blue", font="Roboto"),  # Blue theme
        # English labels
        "labels": {
            # Chat page
            "placeholder": "Type your message...",
            "send": "Send",
            # Settings page
            "models_tab": "🤖 Models",
            "appearance_tab": "🎨 Appearance",
            "context_tab": "📁 Project Info",
            "account_tab": "👤 Account",
            # Model settings
            "provider_label": "Provider",
            "model_label": "Model",
            "temperature_label": "Temperature",
            "max_tokens_label": "Max Tokens",
            # Context fields
            "context_name": "Project Name",
            "context_url": "Project URL",
            "context_description": "Description",
            # Locked model message (not shown in workbench)
            "model_locked": "Current Model",
            "model_locked_info": "Model selection available in this mode",
        },
        # Feature flags
        "allow_model_selection": True,  # Show model controls in settings
        "show_company_section": False,  # Hide business-specific fields
        # Default model config
        "available_providers": ["openai", "anthropic", "groq"],
        "default_provider": "openai",
        "available_models": ["gpt-4-turbo", "claude-3-5-sonnet", "llama-3-70b"],
        "default_model": "gpt-4-turbo",
    }

    return build_gradio_app(config)


def create_seo_app() -> gr.Blocks:
    """
    SEO coach mode configuration - business users.

    Returns:
        gr.Blocks: Configured Gradio app for SEO coach mode
    """
    config = {
        "title": "SEO Coach",
        "theme": gr.themes.Base(primary_hue="green", font="Open Sans"),  # Green theme
        # Dutch labels
        "labels": {
            # Chat page
            "placeholder": "Stel je vraag over SEO...",
            "send": "Verstuur",
            # Settings page
            "models_tab": "🤖 AI Model",
            "appearance_tab": "🎨 Weergave",
            "context_tab": "🏢 Bedrijfsinfo",
            "account_tab": "👤 Account",
            # Model settings
            "provider_label": "AI Provider",
            "model_label": "Model",
            "temperature_label": "Creativiteit",
            "max_tokens_label": "Max Tokens",
            # Context fields (business-oriented)
            "context_name": "Bedrijfsnaam",
            "context_url": "Website URL",
            "context_description": "Beschrijving",
            "business_type": "Type bedrijf",
            "location": "Locatie",
            # Locked model message
            "model_locked": "Huidig model",
            "model_locked_info": "SEO Coach gebruikt het beste model voor jou",
        },
        # Feature flags
        "allow_model_selection": False,  # Lock model in settings
        "show_company_section": True,  # Show business fields
        # Default model config (locked to best model)
        "available_providers": ["openai"],
        "default_provider": "openai",
        "available_models": ["gpt-4-turbo"],
        "default_model": "gpt-4-turbo",
    }

    return build_gradio_app(config)


def build_gradio_app(config: Dict[str, Any]) -> gr.Blocks:
    """
    Single Gradio app builder - shared by all modes.

    This function is called by create_workbench_app() and create_seo_app()
    with different configurations. It builds the SAME component tree for
    both modes - differences are controlled by config values.

    Args:
        config: Mode configuration dictionary

    Returns:
        gr.Blocks: Configured Gradio app with routes

    Critical Pattern:
        - ALL components must be defined (use visible= to hide)
        - Shared state defined at demo level, passed to render functions
        - Single queue() call happens in main.py, not here

    Phase 2: Now includes settings_state for sharing config between pages
    """

    # Create Blocks instance
    demo = gr.Blocks(title=config["title"], theme=config["theme"], css=SHARED_CSS)

    # Define routes OUTSIDE the Blocks context
    # Route 1: Chat page (root) - use None for root path
    with demo.route("Chat", None):
        # Shared state - accessible across all routes
        user_state = gr.State(None)  # User session/auth data
        conversation_state = gr.State([])  # Current conversation messages
        settings_state = gr.State({})  # User settings (model config, etc.)

        chat.render(config, user_state, conversation_state, settings_state)

    # Route 2: Settings page
    with demo.route("Settings", "settings"):
        # Reuse same state instances (Gradio handles state sharing)
        settings.render(config, user_state, settings_state)

    return demo
