"""
Unit tests for Phase 3 - Conversation History Sidebar.

Tests cover:
- Sidebar rendering (feature-flagged)
- Toggle logic (hybrid approach)
- Sidebar component functionality
- Accessibility features
"""

import gradio as gr

from src.agent_workbench.ui.components.sidebar import (
    get_sidebar_css,
    render_sidebar,
)


class TestSidebarComponent:
    """Tests for sidebar component rendering."""

    def test_sidebar_renders_when_enabled(self):
        """Test sidebar renders when feature flag is true."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        # render_sidebar must be called within Gradio Blocks context
        with gr.Blocks():
            result = render_sidebar(config, user_state)

        # Should return tuple with 6 elements
        assert result is not None
        assert len(result) == 6

        # Elements should exist
        (
            sidebar_visible,
            conv_list_html,
            new_chat_btn,
            collapse_btn,
            conv_dropdown,
            clear_storage_btn,
        ) = result
        assert sidebar_visible is not None
        assert conv_list_html is not None
        assert new_chat_btn is not None
        assert collapse_btn is not None
        assert conv_dropdown is not None
        assert clear_storage_btn is not None

    def test_sidebar_hidden_when_disabled(self):
        """Test sidebar returns None when feature flag is false."""
        config = {"show_conv_browser": False}
        user_state = gr.State(None)

        result = render_sidebar(config, user_state)

        # Should return None tuple when disabled
        assert result == (None, None, None, None, None, None)

    def test_sidebar_default_disabled(self):
        """Test sidebar defaults to disabled when flag not set."""
        config = {}  # No show_conv_browser key
        user_state = gr.State(None)

        result = render_sidebar(config, user_state)

        # Should default to disabled
        assert result == (None, None, None, None, None, None)

    def test_dropdown_configured_for_dom_presence(self):
        """Test dropdown is configured to stay in DOM (visible=True with CSS hiding)."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        # render_sidebar must be called within Gradio Blocks context
        with gr.Blocks():
            result = render_sidebar(config, user_state)

        # Get the dropdown component
        _, _, _, _, conv_dropdown, _ = result

        # Dropdown should be visible (for events to work)
        # It's hidden via CSS, not via visible=False
        assert conv_dropdown is not None
        assert conv_dropdown.visible is True
        assert conv_dropdown.elem_id == "conv-dropdown"


class TestSidebarCSS:
    """Tests for sidebar CSS generation."""

    def test_css_generated(self):
        """Test CSS code is generated."""
        css = get_sidebar_css()

        assert css is not None
        assert isinstance(css, str)
        assert len(css) > 0

    def test_css_contains_list_styles(self):
        """Test CSS includes conversation list styling."""
        css = get_sidebar_css()

        assert ".conv-list" in css
        assert ".conv-item" in css

    def test_css_contains_card_styles(self):
        """Test CSS includes conversation item styling."""
        css = get_sidebar_css()

        assert ".conv-item" in css
        assert "border-radius" in css
        assert "cursor: pointer" in css

    def test_css_contains_hover_states(self):
        """Test CSS includes hover states."""
        css = get_sidebar_css()

        assert ":hover" in css

    def test_css_contains_selected_state(self):
        """Test CSS includes selected state for items."""
        css = get_sidebar_css()

        assert ".selected" in css
        assert "#1976d2" in css  # Blue accent color

    def test_css_hides_dropdown(self):
        """Test CSS includes rule to hide the dropdown while keeping it in DOM."""
        css = get_sidebar_css()

        # CSS should hide the dropdown with display:none
        assert "#conv-dropdown" in css
        assert "display: none" in css


class TestSidebarToggleLogic:
    """Tests for sidebar toggle behavior."""

    def test_sidebar_visible_state_created(self):
        """Test sidebar visibility state is created."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        # render_sidebar must be called within Gradio Blocks context
        with gr.Blocks():
            sidebar_visible, _, _, _, _, _ = render_sidebar(config, user_state)

        # State should be created
        assert sidebar_visible is not None
        assert isinstance(sidebar_visible, gr.State)

    def test_sidebar_visible_state_default_true(self):
        """Test sidebar visible state defaults to True."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        # render_sidebar must be called within Gradio Blocks context
        with gr.Blocks():
            sidebar_visible, _, _, _, _, _ = render_sidebar(config, user_state)

        # Initial state should be True (visible)
        assert sidebar_visible.value is True


class TestSidebarAccessibility:
    """Tests for sidebar accessibility features."""

    def test_css_contains_transition_for_smooth_ux(self):
        """Test CSS includes transitions for better UX."""
        css = get_sidebar_css()

        assert "transition" in css
