"""
Unit tests for Phase 3 - Conversation History Sidebar.

Tests cover:
- Sidebar rendering (feature-flagged)
- Toggle logic (hybrid approach)
- Sidebar component functionality
- Accessibility features
"""

import gradio as gr

from src.agent_workbench.ui.components.sidebar import render_sidebar


class TestSidebarComponent:
    """Tests for sidebar component rendering."""

    def test_sidebar_renders_when_enabled(self):
        """Test sidebar renders when feature flag is true."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        # render_sidebar must be called within Gradio Blocks context
        with gr.Blocks():
            result = render_sidebar(config, user_state)

        # Should return tuple with 5 elements
        assert result is not None
        assert len(result) == 5

        # Elements should exist
        (
            sidebar_visible,
            conv_dropdown,
            new_chat_btn,
            collapse_btn,
            clear_storage_btn,
        ) = result
        assert sidebar_visible is not None
        assert conv_dropdown is not None
        assert new_chat_btn is not None
        assert collapse_btn is not None
        assert clear_storage_btn is not None

    def test_sidebar_hidden_when_disabled(self):
        """Test sidebar returns None when feature flag is false."""
        config = {"show_conv_browser": False}
        user_state = gr.State(None)

        result = render_sidebar(config, user_state)

        # Should return None tuple when disabled
        assert result == (None, None, None, None, None)

    def test_sidebar_default_disabled(self):
        """Test sidebar defaults to disabled when flag not set."""
        config = {}  # No show_conv_browser key
        user_state = gr.State(None)

        result = render_sidebar(config, user_state)

        # Should default to disabled
        assert result == (None, None, None, None, None)

    def test_dropdown_configured_for_dom_presence(self):
        """Test dropdown is configured to stay in DOM and is visible."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        # render_sidebar must be called within Gradio Blocks context
        with gr.Blocks():
            result = render_sidebar(config, user_state)

        # Get the dropdown component
        _, conv_dropdown, _, _, _ = result

        # Dropdown should be visible (no CSS hiding in native approach)
        assert conv_dropdown is not None
        assert conv_dropdown.visible is True
        assert conv_dropdown.elem_id == "conv-dropdown"


class TestSidebarToggleLogic:
    """Tests for sidebar toggle behavior."""

    def test_sidebar_visible_state_created(self):
        """Test sidebar visibility state is created."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        # render_sidebar must be called within Gradio Blocks context
        with gr.Blocks():
            sidebar_visible, _, _, _, _ = render_sidebar(config, user_state)

        # State should be created
        assert sidebar_visible is not None
        assert isinstance(sidebar_visible, gr.State)

    def test_sidebar_visible_state_default_true(self):
        """Test sidebar visible state defaults to True."""
        config = {"show_conv_browser": True}
        user_state = gr.State(None)

        # render_sidebar must be called within Gradio Blocks context
        with gr.Blocks():
            sidebar_visible, _, _, _, _ = render_sidebar(config, user_state)

        # Initial state should be True (visible)
        assert sidebar_visible.value is True
