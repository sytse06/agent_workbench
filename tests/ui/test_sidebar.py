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
    create_sidebar_css,
    create_sidebar_javascript,
    render_sidebar,
)


class TestSidebarComponent:
    """Tests for sidebar component rendering."""

    def test_sidebar_renders_when_enabled(self):
        """Test sidebar renders when feature flag is true."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        result = render_sidebar(config, user_state)

        # Should return tuple with 4 elements
        assert result is not None
        assert len(result) == 4

        # Elements should exist
        (sidebar_visible, conv_list_html, new_chat_btn, collapse_btn) = result
        assert sidebar_visible is not None
        assert conv_list_html is not None
        assert new_chat_btn is not None
        assert collapse_btn is not None

    def test_sidebar_hidden_when_disabled(self):
        """Test sidebar returns None when feature flag is false."""
        config = {"show_conv_browser": False}
        user_state = gr.State(None)

        result = render_sidebar(config, user_state)

        # Should return None tuple when disabled
        assert result == (None, None, None, None)

    def test_sidebar_default_disabled(self):
        """Test sidebar defaults to disabled when flag not set."""
        config = {}  # No show_conv_browser key
        user_state = gr.State(None)

        result = render_sidebar(config, user_state)

        # Should default to disabled
        assert result == (None, None, None, None)


class TestSidebarJavaScript:
    """Tests for sidebar JavaScript generation."""

    def test_javascript_generated(self):
        """Test JavaScript code is generated."""
        js = create_sidebar_javascript()

        assert js is not None
        assert isinstance(js, str)
        assert len(js) > 0

    def test_javascript_contains_api_fetch(self):
        """Test JavaScript includes API fetch for conversations."""
        js = create_sidebar_javascript()

        assert "/api/v1/conversations" in js
        assert "fetch" in js
        assert "credentials: 'include'" in js

    def test_javascript_contains_card_rendering(self):
        """Test JavaScript includes conversation card rendering."""
        js = create_sidebar_javascript()

        assert "conv-card" in js
        assert "conv-card-header" in js
        assert "conv-card-preview" in js

    def test_javascript_contains_event_listeners(self):
        """Test JavaScript includes event listeners."""
        js = create_sidebar_javascript()

        assert "addEventListener" in js
        assert "load-conversation" in js
        assert "click" in js

    def test_javascript_contains_click_away_listener(self):
        """Test JavaScript includes click-away functionality."""
        js = create_sidebar_javascript()

        assert "click-away" in js or "outside" in js.lower()
        assert "gr-sidebar-collapsed" in js

    def test_javascript_contains_aria_attributes(self):
        """Test JavaScript sets ARIA attributes."""
        js = create_sidebar_javascript()

        assert "aria-label" in js
        assert "aria-hidden" in js


class TestSidebarCSS:
    """Tests for sidebar CSS generation."""

    def test_css_generated(self):
        """Test CSS code is generated."""
        css = create_sidebar_css()

        assert css is not None
        assert isinstance(css, str)
        assert len(css) > 0

    def test_css_contains_sidebar_styles(self):
        """Test CSS includes sidebar styling."""
        css = create_sidebar_css()

        assert ".gr-sidebar" in css
        assert "transition" in css

    def test_css_contains_collapse_animation(self):
        """Test CSS includes collapse animation."""
        css = create_sidebar_css()

        assert "gr-sidebar-collapsed" in css
        assert "width: 0" in css
        assert "opacity: 0" in css

    def test_css_contains_card_styles(self):
        """Test CSS includes conversation card styling."""
        css = create_sidebar_css()

        assert "conv-card" in css
        assert "border-radius" in css
        assert "cursor: pointer" in css

    def test_css_contains_hover_states(self):
        """Test CSS includes hover states."""
        css = create_sidebar_css()

        assert ":hover" in css
        assert ":focus" in css

    def test_css_contains_responsive_design(self):
        """Test CSS includes responsive breakpoints."""
        css = create_sidebar_css()

        assert "@media" in css
        assert "768px" in css


class TestSidebarToggleLogic:
    """Tests for sidebar toggle behavior."""

    def test_sidebar_visible_state_created(self):
        """Test sidebar visibility state is created."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        sidebar_visible, _, _, _ = render_sidebar(config, user_state)

        # State should be created
        assert sidebar_visible is not None
        assert isinstance(sidebar_visible, gr.State)

    def test_sidebar_visible_state_default_true(self):
        """Test sidebar visible state defaults to True."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        sidebar_visible, _, _, _ = render_sidebar(config, user_state)

        # Initial state should be True (visible)
        assert sidebar_visible.value is True


class TestSidebarAccessibility:
    """Tests for sidebar accessibility features."""

    def test_javascript_includes_tabindex(self):
        """Test conversation cards are keyboard accessible."""
        js = create_sidebar_javascript()

        assert "tabindex" in js

    def test_javascript_includes_role_button(self):
        """Test conversation cards have role='button'."""
        js = create_sidebar_javascript()

        assert 'role="button"' in js

    def test_javascript_includes_keypress_handling(self):
        """Test JavaScript handles Enter/Space keys."""
        js = create_sidebar_javascript()

        assert "keypress" in js
        assert "Enter" in js or "'Enter'" in js

    def test_css_includes_focus_styles(self):
        """Test CSS includes focus styles for accessibility."""
        css = create_sidebar_css()

        assert ":focus" in css
