"""
Integration tests for conversation loading functionality (Phase 3).

Tests cover:
- Loading conversations from API
- Converting messages to chatbot format
- Wiring custom events
"""

from src.agent_workbench.ui.pages.chat import load_conversation_into_chat


class TestConversationLoading:
    """Tests for conversation loading into chat."""

    def test_load_empty_conversation(self):
        """Test loading empty conversation returns empty lists."""
        result = load_conversation_into_chat(None)

        assert result == ([], [])

    def test_load_conversation_with_messages(self):
        """Test loading conversation with single exchange."""
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
        conv_data = {
            "messages": [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Second question"},
                {"role": "assistant", "content": "Second answer"},
                {"role": "user", "content": "Third question"},
                {"role": "assistant", "content": "Third answer"},
            ]
        }

        chatbot_hist, conv_state = load_conversation_into_chat(conv_data)

        # Should have 3 exchanges
        assert len(chatbot_hist) == 3
        assert chatbot_hist[0] == ("First question", "First answer")
        assert chatbot_hist[1] == ("Second question", "Second answer")
        assert chatbot_hist[2] == ("Third question", "Third answer")

    def test_load_conversation_with_odd_messages(self):
        """Test loading conversation with odd number of messages."""
        conv_data = {
            "messages": [
                {"role": "user", "content": "Question 1"},
                {"role": "assistant", "content": "Answer 1"},
                {"role": "user", "content": "Question 2"},
                # Missing final assistant response
            ]
        }

        chatbot_hist, conv_state = load_conversation_into_chat(conv_data)

        # Should only include complete pairs
        assert len(chatbot_hist) == 1
        assert chatbot_hist[0] == ("Question 1", "Answer 1")

    def test_load_conversation_with_empty_messages_list(self):
        """Test loading conversation with empty messages list."""
        conv_data = {"messages": []}

        chatbot_hist, conv_state = load_conversation_into_chat(conv_data)

        # Should return empty lists
        assert chatbot_hist == []
        assert conv_state == []

    def test_load_conversation_returns_same_for_both_outputs(self):
        """Test that chatbot_hist and conv_state are identical."""
        conv_data = {
            "messages": [
                {"role": "user", "content": "Q"},
                {"role": "assistant", "content": "A"},
            ]
        }

        chatbot_hist, conv_state = load_conversation_into_chat(conv_data)

        # Both should be same
        assert chatbot_hist == conv_state

    def test_load_conversation_preserves_message_content(self):
        """Test that message content is preserved exactly."""
        original_user = "What is 2+2?"
        original_assistant = "The answer is 4."

        conv_data = {
            "messages": [
                {"role": "user", "content": original_user},
                {"role": "assistant", "content": original_assistant},
            ]
        }

        chatbot_hist, _ = load_conversation_into_chat(conv_data)

        # Content should be preserved exactly
        assert chatbot_hist[0][0] == original_user
        assert chatbot_hist[0][1] == original_assistant

    def test_load_conversation_handles_special_characters(self):
        """Test loading conversation with special characters."""
        conv_data = {
            "messages": [
                {
                    "role": "user",
                    "content": "What about émojis? 🎉",
                },
                {
                    "role": "assistant",
                    "content": "Émojis work fine! 👍",
                },
            ]
        }

        chatbot_hist, _ = load_conversation_into_chat(conv_data)

        # Special characters should be preserved
        assert "🎉" in chatbot_hist[0][0]
        assert "👍" in chatbot_hist[0][1]

    def test_load_conversation_handles_long_messages(self):
        """Test loading conversation with very long messages."""
        long_message = "x" * 10000  # 10k character message

        conv_data = {
            "messages": [
                {"role": "user", "content": long_message},
                {"role": "assistant", "content": long_message},
            ]
        }

        chatbot_hist, _ = load_conversation_into_chat(conv_data)

        # Long messages should be preserved
        assert len(chatbot_hist[0][0]) == 10000
        assert len(chatbot_hist[0][1]) == 10000

    def test_load_conversation_with_newlines(self):
        """Test loading conversation with newlines in content."""
        user_msg = "Line 1\nLine 2\nLine 3"
        assistant_msg = "Response\nwith\nmultiple\nlines"

        conv_data = {
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg},
            ]
        }

        chatbot_hist, _ = load_conversation_into_chat(conv_data)

        # Newlines should be preserved
        assert "\n" in chatbot_hist[0][0]
        assert "\n" in chatbot_hist[0][1]
