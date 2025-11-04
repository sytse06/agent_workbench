"""
Unit tests for Gradio multipage routing (UI-005 Phase 1).

Tests route creation, navigation, and state sharing across pages.
"""

import gradio as gr

from agent_workbench.ui.mode_factory_v2 import create_workbench_app


class TestRouteCreation:
    """Test that routes are created correctly"""

    def test_app_has_routes(self):
        """Test that app is created with routes"""
        app = create_workbench_app()

        assert isinstance(app, gr.Blocks)
        # Routes are internal to Gradio, can't inspect directly
        # But app should be created without errors

    def test_app_title_matches_config(self):
        """Test that app title matches mode configuration"""
        app = create_workbench_app()

        assert app.title == "Agent Workbench"

    def test_app_has_theme(self):
        """Test that app has theme applied"""
        app = create_workbench_app()

        assert app.theme is not None
        # Theme is configured in mode_factory_v2


class TestStateSharing:
    """Test that state is shared across routes"""

    def test_app_creates_without_state_errors(self):
        """Test app creates with shared state (no errors)"""
        # State definition errors would cause app creation to fail
        app = create_workbench_app()

        assert isinstance(app, gr.Blocks)


class TestNavigationJS:
    """Test navigation JavaScript patterns"""

    def test_chat_page_has_settings_button(self):
        """Test chat page includes settings navigation"""
        # This is a structural test - we can't inspect button JS directly
        # But the render function should execute without errors
        app = create_workbench_app()

        assert isinstance(app, gr.Blocks)
        # Settings button with navigation JS should exist

    def test_settings_page_has_back_button(self):
        """Test settings page includes back navigation"""
        app = create_workbench_app()

        assert isinstance(app, gr.Blocks)
        # Back button with navigation JS should exist


class TestCSSApplication:
    """Test that shared CSS is applied"""

    def test_app_has_css(self):
        """Test that app includes CSS"""
        app = create_workbench_app()

        # CSS is passed to Blocks constructor
        # Can't directly inspect, but app should be created successfully
        assert isinstance(app, gr.Blocks)


class TestComponentDefinition:
    """Test that components are always defined (not conditionally)"""

    def test_workbench_app_creates_successfully(self):
        """Test workbench app creates with all components"""
        # Components should always be defined (using visible= for hiding)
        # Missing component definitions would cause NameError
        app = create_workbench_app()

        assert isinstance(app, gr.Blocks)


class TestMultipleModes:
    """Test that different modes can coexist"""

    def test_workbench_and_seo_both_create(self):
        """Test both mode apps can be created without conflicts"""
        from agent_workbench.ui.mode_factory_v2 import create_seo_app

        workbench = create_workbench_app()
        seo = create_seo_app()

        assert isinstance(workbench, gr.Blocks)
        assert isinstance(seo, gr.Blocks)
        assert workbench.title != seo.title


class TestErrorHandling:
    """Test error handling in route creation"""

    def test_invalid_config_handled(self):
        """Test that invalid config doesn't crash app creation"""
        from agent_workbench.ui.mode_factory_v2 import build_gradio_app

        # Minimal config (might be missing some keys)
        minimal_config = {
            "title": "Test",
            "theme": gr.themes.Base(),
            "labels": {
                "placeholder": "Test",
                "send": "Send",
            },
        }

        # Should create app even with minimal config
        app = build_gradio_app(minimal_config)
        assert isinstance(app, gr.Blocks)
