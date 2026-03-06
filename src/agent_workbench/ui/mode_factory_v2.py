"""
Mode Factory V2 - Creates Gradio app based on APP_MODE environment variable.

Pattern:
    create_app() → create_workbench_app() OR create_seo_app()
                → build_gradio_app(config)

No code duplication - single builder, different configurations.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

import gradio as gr

from .pages import chat, settings

logger = logging.getLogger(__name__)


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
        "load_custom_js": False,  # Workbench: plain Gradio, no custom JS
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
        "show_conv_browser": os.getenv("SHOW_CONV_BROWSER", "true").lower()
        == "true",  # Show conversation sidebar
        # Default model config
        "available_providers": ["openrouter", "google"],
        "default_provider": "openrouter",
        "available_models": [
            "gpt-5-mini",
            "qwen3-30b-a3b",
            "gemini-2.5-flash",
            "gemini-2.0-flash-lite",
        ],
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
        "load_custom_js": True,  # SEO Coach: full custom UI, load ui-init.js
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
        "show_conv_browser": os.getenv("SHOW_CONV_BROWSER", "false").lower()
        == "true",  # Hide conversation sidebar in SEO coach
        # Default model config (locked to best model)
        "available_providers": ["openrouter"],
        "default_provider": "openrouter",
        "available_models": ["qwen3-30b-a3b"],
        "default_model": "qwen3-30b-a3b",
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

    # Create Blocks instance with unified CSS
    # main.css imports fonts.css + shared.css (all core styles)
    # Critical CSS inlined to bypass browser caching issues

    # Tell Gradio to serve the static directory as static files
    # This allows gr.Button(icon="...") to serve icons without permission checks
    # Ref: https://www.gradio.app/docs/gradio/set_static_paths
    static_dir = Path(__file__).resolve().parent.parent / "static"
    gr.set_static_paths(paths=[str(static_dir)])

    # Load custom CSS directly - @import doesn't work in Gradio's inline styles
    # Must load tokens.css first for CSS variables, then styles.css
    css_dir = static_dir / "assets" / "css"
    tokens_css = (
        (css_dir / "tokens.css").read_text()
        if (css_dir / "tokens.css").exists()
        else ""
    )
    styles_css = (
        (css_dir / "styles.css").read_text()
        if (css_dir / "styles.css").exists()
        else ""
    )

    # Remove @import statements (tokens.css loaded separately)
    styles_css = "\n".join(
        line
        for line in styles_css.split("\n")
        if not line.strip().startswith("@import")
    )

    demo = gr.Blocks(
        title=config["title"],
        theme=config["theme"],
        css=f"""
        /* Google Fonts loaded via FastAPI middleware (main.py:inject_google_fonts)
           Gradio's Constructable Stylesheets don't support @import for external URLs */

        /* Design tokens (CSS variables) */
        {tokens_css}

        /* Custom component styles */
        {styles_css}

        /* Critical fix: prevent input bar wrapping (Phase 4.3) */
        .agent-workbench-input-bar {{
            flex-wrap: nowrap !important;
        }}
        """,
    )

    # Define shared state BEFORE routes so all routes can access them
    with demo:
        user_state = gr.State(None)  # User session/auth data
        conversation_state = gr.State([])  # Current conversation messages

        # Settings state - persisted via gr.BrowserState for guest users
        # Database persistence remains primary for authenticated users
        settings_state = gr.State({})  # Session state (resets on page refresh)

    # Route 1: Chat page (default, shown at root "/" path)
    with demo:
        # Capture BrowserState and Dataset list returned from chat page
        conversations_list_storage, conv_list = chat.render(
            config, user_state, conversation_state, settings_state
        )

        logger.debug(
            "After chat.render(): conversations_list_storage=%s, conv_list=%s",
            conversations_list_storage,
            conv_list,
        )

        # Auto-load conversation history into Dataset list from BrowserState
        # on page load (only for guest users - auth users use database)
        if conversations_list_storage and conv_list:
            logger.debug(
                "Sidebar enabled — wiring demo.load event for conversation list"
            )

            @demo.load(
                inputs=[user_state, conversations_list_storage], outputs=[conv_list]
            )
            def load_conversations_from_browser(user_state_val, stored_conversations):
                """
                Load conversation history from BrowserState (localStorage).

                For guest users only - authenticated users use database.
                """
                logger.debug(
                    "load_conversations_from_browser: user_state=%s, stored=%d items",
                    user_state_val,
                    len(stored_conversations or []),
                )

                from .pages.chat import populate_list

                result = populate_list(user_state_val, stored_conversations or [])
                logger.debug("populate_list returned: %s", result)
                return result

        else:
            logger.debug(
                "Sidebar load event NOT wired: storage=%s, conv_list=%s",
                conversations_list_storage,
                conv_list,
            )

        # Conditional JS injection: SEO Coach only
        # Workbench is plain Gradio — no custom JS loaded
        if config.get("load_custom_js"):
            demo.load(
                fn=None,
                js="""
                () => {
                    const s = document.createElement('script');
                    s.src = '/static/js/ui-init.js';
                    document.head.appendChild(s);
                }
                """,
            )

    # Route 2: Settings page with BrowserState auto-load
    with demo.route("Settings", "settings") as settings_route:
        # Capture components returned from settings.render()
        (
            model_dropdown,
            temperature_slider,
            max_tokens_slider,
            theme_radio,
            context_name,
            context_url,
            context_description,
            settings_storage,  # BrowserState component
        ) = settings.render(config, user_state, settings_state)

        # Auto-load settings from BrowserState on page load
        # This is the elegant Gradio way - no JavaScript workarounds needed!
        @settings_route.load(
            inputs=[settings_storage],
            outputs=[
                model_dropdown,
                temperature_slider,
                max_tokens_slider,
                theme_radio,
                context_name,
                context_url,
                context_description,
            ],
        )
        def load_settings_from_browser(stored_settings: dict):
            """
            Load settings from BrowserState (localStorage) for guest users.

            For authenticated users, database persistence is primary.
            This only activates when no user is logged in.
            """
            if not stored_settings:
                # Return defaults if nothing in localStorage
                return [
                    "openrouter: gpt-5-mini",  # model_dropdown
                    0.2,  # temperature
                    1000,  # max_tokens
                    "Auto",  # theme
                    "",  # context_name
                    "",  # context_url
                    "",  # context_description
                ]

            # Extract model config
            model_config = stored_settings.get("model_config", {})
            provider = model_config.get("provider", "openrouter")
            model = model_config.get("model", "gpt-5-mini")
            model_display = f"{provider}: {model}"

            # Extract appearance
            appearance = stored_settings.get("appearance", {})
            theme = appearance.get("theme", "Auto")

            # Extract context
            context = stored_settings.get("context", {})

            return [
                model_display,  # ✅ Works for dropdowns!
                model_config.get("temperature", 0.2),
                model_config.get("max_tokens", 1000),
                theme,
                context.get("name", ""),
                context.get("url", ""),
                context.get("description", ""),
            ]

    return demo
