"""
Settings Page - Dedicated 4-tab settings interface for Agent Workbench.

Provides user-specific configuration across:
- Account: Authentication, profile, theme
- Models: LLM provider/model configuration
- Company: Business profile (SEO coach mode only)
- Advanced: Debug mode, experimental features
"""

from typing import Optional

import gradio as gr

from ..services.model_config_service import model_config_service


def create_settings_page(
    user_id: Optional[str] = None, mode: str = "workbench"
) -> gr.Blocks:
    """
    Create dedicated settings page with 4-tab layout.

    Args:
        user_id: Current user's UUID (from Phase 2.0 auth), None for unauthenticated
        mode: App mode ("workbench" or "seo_coach") - controls Company tab visibility

    Returns:
        Gradio Blocks interface with Account, Models, Company, Advanced tabs
    """
    # Load custom CSS with Ubuntu font
    custom_css = """
        @import url('/static/assets/css/fonts.css');

        .settings-header {
            text-align: center;
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
            margin-bottom: 20px;
        }
        .settings-tab {
            padding: 20px;
        }
        .setting-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .success {
            color: #155724;
            background: #d4edda;
            padding: 10px;
            border-radius: 4px;
        }
        .info {
            color: #0c5460;
            background: #d1ecf1;
            padding: 10px;
            border-radius: 4px;
        }
        .warning {
            color: #856404;
            background: #fff3cd;
            padding: 10px;
            border-radius: 4px;
        }
    """

    with gr.Blocks(
        title="Agent Workbench - Settings", css=custom_css, theme=gr.themes.Soft()
    ) as settings_interface:

        # Header with back button
        with gr.Row(elem_classes=["settings-header"]):
            with gr.Column(scale=1):
                back_btn = gr.Button("← Back to Chat", size="sm")
            with gr.Column(scale=3):
                gr.Markdown("# ⚙️ Settings")
            with gr.Column(scale=1):
                gr.HTML("")  # Spacer

        # Status message (shared across tabs)
        status_message = gr.HTML(value="", visible=True)

        # Main tabs
        with gr.Tabs():

            # ============================================================
            # ACCOUNT TAB
            # ============================================================
            with gr.Tab("👤 Account", elem_classes=["settings-tab"]):
                gr.Markdown("## Account Settings")

                # Authentication status
                with gr.Group(elem_classes=["setting-section"]):
                    gr.Markdown("### 🔐 Authentication")

                    if user_id:
                        gr.HTML(
                            f"""
                            <div class='success'>
                                ✅ Signed in<br>
                                <strong>User ID:</strong> {user_id[:8]}...
                            </div>
                        """
                        )
                        logout_btn = gr.Button("Sign Out", variant="secondary")
                    else:
                        gr.HTML(
                            """
                            <div class='info'>
                                ℹ️ Not signed in - using anonymous session<br>
                                <small>Sign in to save settings and history</small>
                            </div>
                        """
                        )
                        # TODO: Wire up login/register handlers in Phase 2.2
                        _login_btn = gr.Button("Sign In", variant="primary")
                        _register_btn = gr.Button("Create Account", variant="secondary")

                # Theme settings
                with gr.Group(elem_classes=["setting-section"]):
                    gr.Markdown("### 🎨 Appearance")
                    theme_selector = gr.Radio(
                        choices=["Light", "Dark", "Auto"],
                        value="Auto",
                        label="Theme",
                        info="Choose your preferred color theme",
                    )
                    save_theme_btn = gr.Button("Save Theme", variant="primary")

                # Data management
                with gr.Group(elem_classes=["setting-section"]):
                    gr.Markdown("### 📦 Data Management")
                    gr.HTML(
                        """
                        <div class='info'>
                            <strong>Export Settings:</strong> Coming in Phase 2.2<br>
                            <strong>Delete Account:</strong> Contact support
                        </div>
                    """
                    )

            # ============================================================
            # MODELS TAB
            # ============================================================
            with gr.Tab("🤖 Models", elem_classes=["settings-tab"]):
                gr.Markdown("## Model Configuration")
                gr.Markdown(
                    "*Configure your preferred LLM provider and model settings*"
                )

                with gr.Group(elem_classes=["setting-section"]):
                    gr.Markdown("### Provider & Model Selection")

                    # Get dynamic configuration
                    provider_choices, default_provider = (
                        model_config_service.get_provider_choices_for_ui()
                    )
                    model_choices, default_model = (
                        model_config_service.get_model_choices_for_ui()
                    )

                    provider_dropdown = gr.Dropdown(
                        choices=provider_choices,
                        value=default_provider,
                        label="Provider",
                        info="Select your LLM provider",
                    )

                    model_dropdown = gr.Dropdown(
                        choices=model_choices,
                        value=default_model,
                        label="Model",
                        info="Select the specific model to use",
                    )

                with gr.Group(elem_classes=["setting-section"]):
                    gr.Markdown("### Model Parameters")

                    temperature_slider = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=model_config_service.default_temperature,
                        step=0.1,
                        label="Temperature",
                        info="Controls randomness (0=deterministic, 2=very creative)",
                    )

                    max_tokens_slider = gr.Slider(
                        minimum=100,
                        maximum=4000,
                        value=model_config_service.default_max_tokens,
                        step=100,
                        label="Max Tokens",
                        info="Maximum length of generated responses",
                    )

                save_models_btn = gr.Button("Save Model Settings", variant="primary")

            # ============================================================
            # COMPANY TAB (SEO Coach only)
            # ============================================================
            with gr.Tab(
                "🏢 Company",
                elem_classes=["settings-tab"],
                visible=(mode == "seo_coach"),
            ):
                gr.Markdown("## Company Profile")
                gr.Markdown(
                    "*Configure business information for personalized coaching*"
                )

                with gr.Group(elem_classes=["setting-section"]):
                    gr.Markdown("### Business Information")

                    company_name = gr.Textbox(
                        label="Company Name",
                        placeholder="e.g., Bakkerij De Korenwolf",
                        info="Your business or brand name",
                    )

                    website = gr.Textbox(
                        label="Website URL",
                        placeholder="https://jouwbedrijf.nl",
                        info="Your company website",
                    )

                    industry = gr.Dropdown(
                        choices=[
                            "Restaurant",
                            "Webshop",
                            "Dienstverlening",
                            "Productie",
                            "Gezondheidszorg",
                            "Onderwijs",
                            "Technologie",
                            "Anders",
                        ],
                        label="Industry / Branche",
                        info="Select your business type",
                    )

                    brand_voice = gr.Dropdown(
                        choices=[
                            "Professional",
                            "Friendly",
                            "Casual",
                            "Authoritative",
                            "Playful",
                        ],
                        label="Brand Voice",
                        info="Preferred communication style",
                    )

                save_company_btn = gr.Button("Save Company Profile", variant="primary")

            # ============================================================
            # ADVANCED TAB
            # ============================================================
            with gr.Tab("🔧 Advanced", elem_classes=["settings-tab"]):
                gr.Markdown("## Advanced Settings")
                gr.Markdown("*Experimental features and debugging options*")

                with gr.Group(elem_classes=["setting-section"]):
                    gr.Markdown("### Debugging")

                    debug_mode_checkbox = gr.Checkbox(
                        label="Debug Mode",
                        value=False,
                        info="Enable verbose logging (for troubleshooting)",
                    )

                with gr.Group(elem_classes=["setting-section"]):
                    gr.Markdown("### Experimental Features")

                    enable_mcp_checkbox = gr.Checkbox(
                        label="Enable MCP Tools",
                        value=False,
                        info="Model Context Protocol tool integration (Phase 2.7)",
                    )

                    enable_firecrawl_checkbox = gr.Checkbox(
                        label="Enable Firecrawl",
                        value=False,
                        info="Advanced web scraping and content extraction",
                    )

                    gr.HTML(
                        """
                        <div class='warning'>
                            ⚠️ Experimental features may be unstable
                        </div>
                    """
                    )

                save_advanced_btn = gr.Button(
                    "Save Advanced Settings", variant="primary"
                )

        # ============================================================
        # EVENT HANDLERS
        # ============================================================

        # Back to chat navigation
        back_btn.click(fn=None, js="window.location.href = '/'")

        # Account tab handlers
        def handle_theme_save(theme: str) -> str:
            """Save theme preference."""
            # TODO: Persist to user settings
            return f"<div class='success'>✅ Theme changed to {theme}</div>"

        def handle_logout() -> str:
            """Handle logout action."""
            # TODO: Clear session
            return """
            <div class='success'>
                ✅ Signed out successfully<br>
                <small>Redirecting to home...</small>
            </div>
            """

        if user_id:
            logout_btn.click(
                fn=handle_logout,
                outputs=[status_message],
                js="setTimeout(() => window.location.href = '/', 2000)",
            )

        save_theme_btn.click(
            fn=handle_theme_save, inputs=[theme_selector], outputs=[status_message]
        )

        # Models tab handler
        def handle_models_save(
            provider: str, model: str, temperature: float, max_tokens: int
        ) -> str:
            """Save model settings."""
            # TODO: Persist to user settings
            return f"""
            <div class='success'>
                ✅ Model settings saved<br>
                <strong>Provider:</strong> {provider}<br>
                <strong>Model:</strong> {model}<br>
                <strong>Temperature:</strong> {temperature}<br>
                <strong>Max Tokens:</strong> {max_tokens}
            </div>
            """

        save_models_btn.click(
            fn=handle_models_save,
            inputs=[
                provider_dropdown,
                model_dropdown,
                temperature_slider,
                max_tokens_slider,
            ],
            outputs=[status_message],
        )

        # Company tab handler (SEO coach only)
        if mode == "seo_coach":

            def handle_company_save(
                comp_name: str, web: str, ind: str, voice: str
            ) -> str:
                """Save company settings."""
                # TODO: Persist to user settings
                return f"""
                <div class='success'>
                    ✅ Company profile saved<br>
                    <strong>Company:</strong> {comp_name}<br>
                    <strong>Website:</strong> {web}
                </div>
                """

            save_company_btn.click(
                fn=handle_company_save,
                inputs=[company_name, website, industry, brand_voice],
                outputs=[status_message],
            )

        # Advanced tab handler
        def handle_advanced_save(debug: bool, mcp: bool, firecrawl: bool) -> str:
            """Save advanced settings."""
            # TODO: Persist to user settings
            features = []
            if debug:
                features.append("Debug Mode")
            if mcp:
                features.append("MCP Tools")
            if firecrawl:
                features.append("Firecrawl")

            enabled_text = ", ".join(features) if features else "None"
            return f"""
            <div class='success'>
                ✅ Advanced settings saved<br>
                <strong>Enabled:</strong> {enabled_text}
            </div>
            """

        save_advanced_btn.click(
            fn=handle_advanced_save,
            inputs=[
                debug_mode_checkbox,
                enable_mcp_checkbox,
                enable_firecrawl_checkbox,
            ],
            outputs=[status_message],
        )

    return settings_interface
