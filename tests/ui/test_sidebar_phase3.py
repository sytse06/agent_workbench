"""
Tests for Phase 3 - Conversation History Sidebar (Component Tests Only).

Tests cover:
- Sidebar component rendering
- Toggle logic
- Conversation loading
- API integration
- Accessibility

NOTE: Integration tests that create Gradio Blocks are in test_sidebar.py
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


class TestConversationLoading:
    """Tests for conversation loading functionality."""

    def test_load_empty_conversation(self):
        """Test loading empty conversation."""
        from src.agent_workbench.ui.pages.chat import (
            load_conversation_into_chat,
        )

        result = load_conversation_into_chat(None)

        assert result == ([], [])

    def test_load_conversation_with_messages(self):
        """Test loading conversation with messages."""
        from src.agent_workbench.ui.pages.chat import (
            load_conversation_into_chat,
        )

        conv_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ]
        }

        chatbot_hist, conv_state = load_conversation_into_chat(conv_data)

        # Should convert to chatbot format (user, assistant pairs)
        assert len(chatbot_hist) == 1
        assert chatbot_hist[0] == ("Hello", "Hi there")
        assert chatbot_hist == conv_state

    def test_load_conversation_with_multiple_exchanges(self):
        """Test loading conversation with multiple exchanges."""
        from src.agent_workbench.ui.pages.chat import (
            load_conversation_into_chat,
        )

        conv_data = {
            "messages": [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Second question"},
                {"role": "assistant", "content": "Second answer"},
            ]
        }

        chatbot_hist, conv_state = load_conversation_into_chat(conv_data)

        # Should have 2 exchanges
        assert len(chatbot_hist) == 2
        assert chatbot_hist[0] == ("First question", "First answer")
        assert chatbot_hist[1] == ("Second question", "Second answer")

    def test_load_conversation_with_odd_messages(self):
        """Test loading conversation with odd number of messages."""
        from src.agent_workbench.ui.pages.chat import (
            load_conversation_into_chat,
        )

        conv_data = {
            "messages": [
                {"role": "user", "content": "Question 1"},
                {"role": "assistant", "content": "Answer 1"},
                {"role": "user", "content": "Question 2"},
            ]
        }

        chatbot_hist, conv_state = load_conversation_into_chat(conv_data)

        # Should only include complete pairs
        assert len(chatbot_hist) == 1
        assert chatbot_hist[0] == ("Question 1", "Answer 1")
