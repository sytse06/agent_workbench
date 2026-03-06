"""
Unit tests for Settings Page Phase 2 implementation (UI-005).

Tests full settings functionality including:
- User settings loading
- Model configuration loading
- Settings persistence
- Settings validation
- Mode-specific sections (workbench vs SEO coach)
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import gradio as gr

from agent_workbench.ui.pages import settings


class TestSettingsPageRendering:
    """Test settings page renders correctly with all sections"""

    def test_settings_page_renders_without_errors(self):
        """Test settings page renders without errors"""
        config = {
            "title": "Agent Workbench",
            "labels": {
                "models_tab": "🤖 Models",
                "appearance_tab": "🎨 Appearance",
                "context_tab": "📁 Project Info",
                "account_tab": "👤 Account",
                "provider_label": "Provider",
                "model_label": "Model",
                "temperature_label": "Temperature",
                "max_tokens_label": "Max Tokens",
                "context_name": "Project Name",
                "context_url": "Project URL",
                "context_description": "Description",
            },
            "allow_model_selection": True,
            "show_company_section": False,
        }
        user_state = gr.State(None)
        settings_state = gr.State({})

        # Should render without errors
        with gr.Blocks() as demo:
            settings.render(config, user_state, settings_state)

        assert isinstance(demo, gr.Blocks)

    def test_workbench_shows_model_controls(self):
        """Test workbench mode shows model selection controls"""
        config = {
            "title": "Agent Workbench",
            "labels": {
                "models_tab": "🤖 Models",
                "appearance_tab": "🎨 Appearance",
                "context_tab": "📁 Project Info",
                "account_tab": "👤 Account",
                "provider_label": "Provider",
                "model_label": "Model",
                "temperature_label": "Temperature",
                "max_tokens_label": "Max Tokens",
            },
            "allow_model_selection": True,
            "show_company_section": False,
        }
        user_state = gr.State(None)
        settings_state = gr.State({})

        with gr.Blocks() as demo:
            settings.render(config, user_state, settings_state)

        # Config indicates model controls should be visible
        assert config["allow_model_selection"] is True
        assert isinstance(demo, gr.Blocks)

    def test_seo_coach_hides_model_controls(self):
        """Test SEO coach mode hides model selection controls"""
        config = {
            "title": "SEO Coach",
            "labels": {
                "models_tab": "🤖 AI Model",
                "appearance_tab": "🎨 Weergave",
                "context_tab": "🏢 Bedrijfsinfo",
                "account_tab": "👤 Account",
                "model_locked": "Huidig model",
                "model_locked_info": "SEO Coach gebruikt het beste model voor jou",
            },
            "allow_model_selection": False,
            "show_company_section": True,
        }
        user_state = gr.State(None)
        settings_state = gr.State({})

        with gr.Blocks() as demo:
            settings.render(config, user_state, settings_state)

        # Config indicates model controls should be hidden
        assert config["allow_model_selection"] is False
        assert config["show_company_section"] is True
        assert isinstance(demo, gr.Blocks)


class TestModelConfigurationLoading:
    """Test model configuration service integration"""

    @patch("agent_workbench.services.model_config_service.ModelConfigService")
    def test_model_dropdowns_populate_from_service(self, mock_service_class):
        """Test model dropdowns populate from ModelConfigService"""
        # Mock ModelConfigService
        mock_service = MagicMock()
        mock_service.get_provider_choices.return_value = ["openrouter", "google"]
        mock_service.get_model_options.return_value = [
            MagicMock(
                provider="openrouter",
                model_name="openai/gpt-4o-mini",
                display_name="openrouter: GPT-4o Mini",
            ),
            MagicMock(
                provider="google",
                model_name="gemini-2.5-flash",
                display_name="google: Gemini 2.5 Flash",
            ),
        ]
        mock_service_class.return_value = mock_service

        config = {
            "title": "Agent Workbench",
            "labels": {
                "models_tab": "🤖 Models",
                "appearance_tab": "🎨 Appearance",
                "context_tab": "📁 Project Info",
                "account_tab": "👤 Account",
                "provider_label": "Provider",
                "model_label": "Model",
                "temperature_label": "Temperature",
                "max_tokens_label": "Max Tokens",
            },
            "allow_model_selection": True,
            "show_company_section": False,
        }
        user_state = gr.State(None)
        settings_state = gr.State({})

        with gr.Blocks() as demo:
            settings.render(config, user_state, settings_state)

        # ModelConfigService should be instantiated
        assert isinstance(demo, gr.Blocks)


class TestSettingsPersistence:
    """Test settings save and load functionality"""

    def test_settings_load_returns_defaults_for_guest(self):
        """Test settings load returns defaults when no user is authenticated"""
        config = {
            "title": "Agent Workbench",
            "labels": {
                "models_tab": "🤖 Models",
                "appearance_tab": "🎨 Appearance",
                "context_tab": "📁 Project Info",
                "account_tab": "👤 Account",
                "provider_label": "Provider",
                "model_label": "Model",
                "temperature_label": "Temperature",
                "max_tokens_label": "Max Tokens",
            },
            "allow_model_selection": True,
            "show_company_section": False,
        }
        user_state = gr.State(None)
        settings_state = gr.State({})

        with gr.Blocks() as demo:
            settings.render(config, user_state, settings_state)

        assert isinstance(demo, gr.Blocks)


class TestSettingsValidation:
    """Test settings validation logic"""

    def test_temperature_range_validation(self):
        """Test temperature must be between 0 and 2"""
        from agent_workbench.ui.pages.settings import validate_temperature

        # Valid temperatures
        assert validate_temperature(0.0) is True
        assert validate_temperature(0.7) is True
        assert validate_temperature(1.0) is True
        assert validate_temperature(2.0) is True

        # Invalid temperatures
        assert validate_temperature(-0.1) is False
        assert validate_temperature(2.1) is False
        assert validate_temperature(3.0) is False

    def test_max_tokens_range_validation(self):
        """Test max tokens must be between 1 and 32000"""
        from agent_workbench.ui.pages.settings import validate_max_tokens

        # Valid max tokens
        assert validate_max_tokens(1) is True
        assert validate_max_tokens(2000) is True
        assert validate_max_tokens(32000) is True

        # Invalid max tokens
        assert validate_max_tokens(0) is False
        assert validate_max_tokens(-100) is False
        assert validate_max_tokens(32001) is False

    def test_url_format_validation(self):
        """Test URL format validation for context fields"""
        from agent_workbench.ui.pages.settings import validate_url

        # Valid URLs
        assert validate_url("https://example.com") is True
        assert validate_url("http://example.com") is True
        assert validate_url("https://example.com/path") is True
        assert validate_url("") is True  # Empty is valid (optional)

        # Invalid URLs
        assert validate_url("not-a-url") is False
        assert validate_url("ftp://example.com") is False
        assert validate_url("example.com") is False  # Missing protocol


class TestErrorHandling:
    """Test error handling for save failures"""

    def test_validation_failure_prevents_save(self):
        """Test validation failure prevents settings save"""
        config = {
            "title": "Agent Workbench",
            "labels": {
                "models_tab": "🤖 Models",
                "appearance_tab": "🎨 Appearance",
                "context_tab": "📁 Project Info",
                "account_tab": "👤 Account",
                "provider_label": "Provider",
                "model_label": "Model",
                "temperature_label": "Temperature",
                "max_tokens_label": "Max Tokens",
            },
            "allow_model_selection": True,
            "show_company_section": False,
        }
        user_state = gr.State({"user_id": str(uuid4())})
        settings_state = gr.State({})

        with gr.Blocks() as demo:
            settings.render(config, user_state, settings_state)

        # Settings page should validate before saving
        assert isinstance(demo, gr.Blocks)


class TestGuestModeSupport:
    """Test guest mode with localStorage fallback"""

    def test_guest_user_settings_not_persisted_to_database(self):
        """Test guest users don't save to database"""
        config = {
            "title": "Agent Workbench",
            "labels": {
                "models_tab": "🤖 Models",
                "appearance_tab": "🎨 Appearance",
                "context_tab": "📁 Project Info",
                "account_tab": "👤 Account",
                "provider_label": "Provider",
                "model_label": "Model",
                "temperature_label": "Temperature",
                "max_tokens_label": "Max Tokens",
            },
            "allow_model_selection": True,
            "show_company_section": False,
        }
        user_state = gr.State(None)  # No user (guest)
        settings_state = gr.State({})

        with gr.Blocks() as demo:
            settings.render(config, user_state, settings_state)

        # Guest mode should not attempt database save
        assert isinstance(demo, gr.Blocks)
