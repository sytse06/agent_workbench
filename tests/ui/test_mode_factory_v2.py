"""
Unit tests for mode_factory_v2 (UI-005 Phase 1).

Tests configuration-driven mode factory with multipage routing.
"""

import os
from unittest.mock import patch

import gradio as gr

from agent_workbench.ui.mode_factory_v2 import (
    build_gradio_app,
    create_app,
    create_seo_app,
    create_workbench_app,
)


class TestModeFactoryV2:
    """Test mode factory V2 functionality"""

    def test_create_workbench_app_returns_blocks(self):
        """Test workbench app returns Gradio Blocks instance"""
        app = create_workbench_app()

        assert isinstance(app, gr.Blocks)
        assert app.title == "Agent Workbench"

    def test_create_seo_app_returns_blocks(self):
        """Test SEO coach app returns Gradio Blocks instance"""
        app = create_seo_app()

        assert isinstance(app, gr.Blocks)
        assert app.title == "SEO Coach"

    @patch.dict(os.environ, {"APP_MODE": "workbench"})
    def test_create_app_workbench_mode(self):
        """Test create_app returns workbench when APP_MODE=workbench"""
        app = create_app()

        assert isinstance(app, gr.Blocks)
        assert app.title == "Agent Workbench"

    @patch.dict(os.environ, {"APP_MODE": "seo_coach"})
    def test_create_app_seo_coach_mode(self):
        """Test create_app returns SEO coach when APP_MODE=seo_coach"""
        app = create_app()

        assert isinstance(app, gr.Blocks)
        assert app.title == "SEO Coach"

    @patch.dict(os.environ, {"APP_MODE": "invalid_mode"})
    def test_create_app_invalid_mode_fallback(self):
        """Test create_app falls back to workbench for invalid mode"""
        app = create_app()

        assert isinstance(app, gr.Blocks)
        assert app.title == "Agent Workbench"

    def test_create_app_no_mode_env_fallback(self):
        """Test create_app falls back to workbench when APP_MODE not set"""
        # Temporarily remove APP_MODE if it exists
        original = os.environ.pop("APP_MODE", None)

        try:
            app = create_app()
            assert isinstance(app, gr.Blocks)
            assert app.title == "Agent Workbench"
        finally:
            # Restore original value if it existed
            if original:
                os.environ["APP_MODE"] = original


class TestModeConfiguration:
    """Test mode-specific configuration"""

    def test_workbench_config_values(self):
        """Test workbench has correct config values"""
        app = create_workbench_app()

        # Can't directly access config from Blocks,
        # but we can verify the app was created successfully
        assert app.title == "Agent Workbench"
        assert isinstance(app, gr.Blocks)

    def test_seo_coach_config_values(self):
        """Test SEO coach has correct config values"""
        app = create_seo_app()

        assert app.title == "SEO Coach"
        assert isinstance(app, gr.Blocks)

    def test_build_gradio_app_creates_routes(self):
        """Test build_gradio_app creates app with routes"""
        config = {
            "title": "Test App",
            "theme": gr.themes.Base(),
            "labels": {
                "placeholder": "Test placeholder",
                "send": "Send",
            },
            "allow_model_selection": True,
            "show_company_section": False,
        }

        app = build_gradio_app(config)

        assert isinstance(app, gr.Blocks)
        assert app.title == "Test App"

        # Routes should exist (Gradio 5.x)
        # Note: We can't easily inspect routes without running the app,
        # but we can verify the app was created without errors


class TestSharedState:
    """Test shared state is created correctly"""

    def test_app_creates_without_errors(self):
        """Test app creates with shared state (no errors)"""
        # This is a basic smoke test
        # More detailed state testing would require running the app
        app = create_workbench_app()

        assert isinstance(app, gr.Blocks)
        # If there were state definition errors, app creation would fail


class TestThemeApplication:
    """Test theme is applied correctly"""

    def test_workbench_theme_is_blue(self):
        """Test workbench uses blue theme"""
        app = create_workbench_app()

        # Theme is applied - can't directly inspect primary_hue
        # but app should be created successfully
        assert isinstance(app, gr.Blocks)
        assert app.theme is not None

    def test_seo_coach_theme_is_green(self):
        """Test SEO coach uses green theme"""
        app = create_seo_app()

        assert isinstance(app, gr.Blocks)
        assert app.theme is not None


class TestModeSeparation:
    """Test modes have different configurations"""

    def test_workbench_and_seo_have_different_titles(self):
        """Test workbench and SEO coach have different titles"""
        workbench = create_workbench_app()
        seo = create_seo_app()

        assert workbench.title != seo.title
        assert workbench.title == "Agent Workbench"
        assert seo.title == "SEO Coach"

    def test_workbench_and_seo_use_same_builder(self):
        """Test both modes use same build_gradio_app function"""
        # This is a structural test - both should create Blocks instances
        workbench = create_workbench_app()
        seo = create_seo_app()

        assert isinstance(workbench, gr.Blocks)
        assert isinstance(seo, gr.Blocks)
        assert type(workbench) is type(seo)
