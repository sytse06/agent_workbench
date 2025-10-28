"""
Settings page - configuration interface.

Phase 2: Full settings implementation with:
- Model provider and model selection
- Model parameters (temperature, max tokens)
- Theme selection (Light/Dark/Auto)
- Project/business context
- Settings persistence (database + localStorage)
- Validation and error handling

See: docs/architecture/decisions/UI-005-settings-page.md
"""

import re
from typing import Any, Dict, Optional, Tuple

import gradio as gr

from ...services.model_config_service import ModelConfigService
from ...services.user_settings_service import UserSettingsService

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_temperature(value: float) -> bool:
    """
    Validate temperature parameter.

    Args:
        value: Temperature value to validate

    Returns:
        True if valid (0 <= value <= 2), False otherwise
    """
    return 0.0 <= value <= 2.0


def validate_max_tokens(value: int) -> bool:
    """
    Validate max tokens parameter.

    Args:
        value: Max tokens value to validate

    Returns:
        True if valid (1 <= value <= 32000), False otherwise
    """
    return 1 <= value <= 32000


def validate_url(value: str) -> bool:
    """
    Validate URL format.

    Args:
        value: URL string to validate

    Returns:
        True if valid URL format or empty, False otherwise
    """
    if not value:  # Empty is valid (optional field)
        return True

    # Basic URL regex (http or https required)
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return bool(url_pattern.match(value))


# ============================================================================
# SETTINGS HANDLERS
# ============================================================================


async def handle_settings_save(
    user_state: Optional[Dict[str, Any]],
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    theme: str,
    context_name: str,
    context_url: str,
    context_description: str,
) -> Tuple[str, str]:
    """
    Handle settings save.

    Args:
        user_state: User session data (None for guests)
        provider: Selected provider
        model: Selected model
        temperature: Temperature parameter
        max_tokens: Max tokens parameter
        theme: Theme selection (Light/Dark/Auto)
        context_name: Project/business name
        context_url: Project/business URL
        context_description: Project/business description

    Returns:
        Tuple of (success_message, error_message)
    """
    try:
        # Validate inputs
        if not validate_temperature(temperature):
            return "", "❌ Temperature must be between 0 and 2"

        if not validate_max_tokens(max_tokens):
            return "", "❌ Max tokens must be between 1 and 32000"

        if not validate_url(context_url):
            return "", "❌ Invalid URL format (must start with http:// or https://)"

        # Prepare settings dictionary
        settings = {
            "model_config": {
                "provider": provider,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            "appearance": {"theme": theme},
            "context": {
                "name": context_name,
                "url": context_url,
                "description": context_description,
            },
        }

        # Save to database if authenticated, otherwise to localStorage (via JS)
        if user_state and user_state.get("user_id"):
            user_id = user_state["user_id"]
            settings_service = UserSettingsService()

            # Save all settings
            await settings_service.bulk_set_settings(
                user_id=user_id, settings=settings, category="ui", setting_type="active"
            )

            return "✅ Settings saved successfully", ""
        else:
            # Guest mode - settings will be handled by JavaScript localStorage
            # Return success message, actual save happens in JS
            return (
                "✅ Settings saved to browser storage (guest mode)",
                "",
            )

    except Exception as e:
        return "", f"❌ Failed to save settings: {str(e)}"


async def handle_settings_load(user_state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Load user settings from database or return defaults.

    Args:
        user_state: User session data (None for guests)

    Returns:
        Dictionary with settings values
    """
    try:
        # Default settings
        defaults = {
            "provider": "openrouter",
            "model": "openai/gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2000,
            "theme": "Auto",
            "context_name": "",
            "context_url": "",
            "context_description": "",
        }

        # Load from database if authenticated
        if user_state and user_state.get("user_id"):
            user_id = user_state["user_id"]
            settings_service = UserSettingsService()

            all_settings = await settings_service.get_all_settings(user_id)

            # Extract model config
            model_config = all_settings.get("model_config", {})
            if isinstance(model_config, dict) and "value" in model_config:
                model_config = model_config["value"]

            # Extract appearance
            appearance = all_settings.get("appearance", {})
            if isinstance(appearance, dict) and "value" in appearance:
                appearance = appearance["value"]

            # Extract context
            context = all_settings.get("context", {})
            if isinstance(context, dict) and "value" in context:
                context = context["value"]

            # Merge with defaults
            return {
                "provider": model_config.get("provider", defaults["provider"]),
                "model": model_config.get("model", defaults["model"]),
                "temperature": model_config.get("temperature", defaults["temperature"]),
                "max_tokens": model_config.get("max_tokens", defaults["max_tokens"]),
                "theme": appearance.get("theme", defaults["theme"]),
                "context_name": context.get("name", defaults["context_name"]),
                "context_url": context.get("url", defaults["context_url"]),
                "context_description": context.get(
                    "description", defaults["context_description"]
                ),
            }

        # Guest mode - return defaults (JS will load from localStorage)
        return defaults

    except Exception:
        # Return defaults on error
        return {
            "provider": "openrouter",
            "model": "openai/gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2000,
            "theme": "Auto",
            "context_name": "",
            "context_url": "",
            "context_description": "",
        }


# ============================================================================
# RENDER FUNCTION
# ============================================================================


def render(
    config: Dict[str, Any], user_state: gr.State, settings_state: gr.State
) -> None:
    """
    Render settings interface.

    Args:
        config: Mode configuration from mode_factory
        user_state: Shared user session state
        settings_state: Shared settings state (updated here, used in chat)

    Phase 2: Full implementation with:
    - Model selection (provider, model, parameters)
    - Theme selection
    - Project/business context
    - Settings persistence (database + localStorage)
    - Validation and error handling
    - Settings state management for chat integration
    """

    # Initialize services
    model_service = ModelConfigService()

    # Get model options for dropdowns
    model_options = model_service.get_model_options()
    model_choices = [opt.display_name for opt in model_options]
    model_map = {
        opt.display_name: {"provider": opt.provider, "model": opt.model_name}
        for opt in model_options
    }

    # Header with back button
    with gr.Row():
        back_btn = gr.Button("← Back to Chat", size="sm")
        gr.Markdown("# ⚙️ Settings")

    # Status messages
    success_msg = gr.Markdown("", visible=False)
    error_msg = gr.Markdown("", visible=False)

    # Tabs for different settings sections
    with gr.Tabs():
        # Account Tab
        with gr.Tab(config["labels"].get("account_tab", "Account")):
            gr.Markdown("### User Account")
            gr.Markdown("*Authentication and profile management*")

            # Show user info if authenticated
            if user_state.value and user_state.value.get("user_id"):
                gr.Markdown(f"**User ID:** `{user_state.value['user_id']}`")
                gr.Markdown("**Status:** Authenticated")
            else:
                gr.Markdown("**Status:** Guest Mode (settings saved to browser)")

        # Models Tab
        with gr.Tab(config["labels"].get("models_tab", "Models")):
            if config.get("allow_model_selection", True):
                gr.Markdown("### AI Model Configuration")

                # Model selection dropdown
                model_dropdown = gr.Dropdown(
                    label=config["labels"].get("model_label", "Model"),
                    choices=model_choices,
                    value=model_choices[0] if model_choices else None,
                    interactive=True,
                )

                # Temperature slider
                temperature_slider = gr.Slider(
                    label=config["labels"].get("temperature_label", "Temperature"),
                    minimum=0.0,
                    maximum=2.0,
                    value=0.7,
                    step=0.1,
                    interactive=True,
                    info="Controls randomness (0=focused, 2=creative)",
                )

                # Max tokens slider
                max_tokens_slider = gr.Slider(
                    label=config["labels"].get("max_tokens_label", "Max Tokens"),
                    minimum=1,
                    maximum=32000,
                    value=2000,
                    step=100,
                    interactive=True,
                    info="Maximum response length",
                )
            else:
                # SEO coach mode - show locked model info
                gr.Markdown(
                    "### " + config["labels"].get("model_locked", "Current Model")
                )
                gr.Markdown(
                    config["labels"].get(
                        "model_locked_info",
                        "Model selection is locked for this mode",
                    )
                )
                gr.Markdown("**Current Model:** `gpt-4-turbo` (optimized for SEO)")

                # Hidden components (need to exist for event handlers)
                # Must have choices even when hidden to avoid validation errors
                model_dropdown = gr.Dropdown(
                    choices=model_choices,
                    value=model_choices[0] if model_choices else None,
                    visible=False,
                )
                temperature_slider = gr.Slider(
                    minimum=0.0, maximum=2.0, value=0.7, visible=False
                )
                max_tokens_slider = gr.Slider(
                    minimum=1, maximum=32000, value=2000, visible=False
                )

        # Appearance Tab
        with gr.Tab(config["labels"].get("appearance_tab", "Appearance")):
            gr.Markdown("### Theme Preference")

            theme_radio = gr.Radio(
                label="Theme",
                choices=["Light", "Dark", "Auto"],
                value="Auto",
                interactive=True,
                info="Auto follows system preference",
            )

        # Context/Project Info Tab
        with gr.Tab(config["labels"].get("context_tab", "Context")):
            if config.get("show_company_section", False):
                # SEO coach mode - business-focused fields
                gr.Markdown("### Business Information")

                context_name = gr.Textbox(
                    label=config["labels"].get("context_name", "Business Name"),
                    placeholder="Enter your business name",
                    interactive=True,
                )

                context_url = gr.Textbox(
                    label=config["labels"].get("context_url", "Website URL"),
                    placeholder="https://your-website.com",
                    interactive=True,
                )

                context_description = gr.Textbox(
                    label=config["labels"].get("context_description", "Description"),
                    placeholder="Brief description of your business",
                    lines=3,
                    interactive=True,
                )
            else:
                # Workbench mode - project-focused fields
                gr.Markdown("### Project Information")

                context_name = gr.Textbox(
                    label=config["labels"].get("context_name", "Project Name"),
                    placeholder="Enter project name",
                    interactive=True,
                )

                context_url = gr.Textbox(
                    label=config["labels"].get("context_url", "Project URL"),
                    placeholder="https://project-url.com",
                    interactive=True,
                )

                context_description = gr.Textbox(
                    label=config["labels"].get("context_description", "Description"),
                    placeholder="Brief project description",
                    lines=3,
                    interactive=True,
                )

    # Save and Reset buttons
    with gr.Row():
        save_btn = gr.Button("💾 Save Settings", variant="primary")
        reset_btn = gr.Button("🔄 Reset to Defaults")

    # Event: Navigate back to chat
    back_btn.click(fn=None, js="() => { window.location.href = '/'; }")

    # Event: Save settings
    def save_settings_wrapper(
        user_st: Optional[Dict[str, Any]],
        model_sel: str,
        temp: float,
        tokens: int,
        theme: str,
        name: str,
        url: str,
        desc: str,
    ) -> Tuple[str, str, str, str, Dict[str, Any]]:
        """Wrapper to handle async save and update settings state."""
        import asyncio

        # Extract provider and model from selection
        if model_sel in model_map:
            provider = model_map[model_sel]["provider"]
            model = model_map[model_sel]["model"]
        else:
            provider = "openrouter"
            model = "openai/gpt-4o-mini"

        # Call async save handler
        success, error = asyncio.run(
            handle_settings_save(
                user_st, provider, model, temp, tokens, theme, name, url, desc
            )
        )

        # Build updated settings state
        updated_settings = {
            "model_config": {
                "provider": provider,
                "model": model,
                "temperature": temp,
                "max_tokens": tokens,
            },
            "appearance": {"theme": theme},
            "context": {
                "name": name,
                "url": url,
                "description": desc,
            },
        }

        # Return messages with visibility and updated state
        if success:
            return success, "", "visible", "hidden", updated_settings
        else:
            return "", error, "hidden", "visible", updated_settings

    save_btn.click(
        fn=save_settings_wrapper,
        inputs=[
            user_state,
            model_dropdown,
            temperature_slider,
            max_tokens_slider,
            theme_radio,
            context_name,
            context_url,
            context_description,
        ],
        outputs=[
            success_msg,
            error_msg,
            success_msg,
            error_msg,
            settings_state,
        ],
    )

    # Event: Reset to defaults
    def reset_to_defaults():
        """Reset all settings to defaults."""
        return (
            model_choices[0] if model_choices else None,
            0.7,
            2000,
            "Auto",
            "",
            "",
            "",
        )

    reset_btn.click(
        fn=reset_to_defaults,
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
