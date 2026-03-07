"""Unit tests for the MessageConverter UI boundary utility."""

import gradio as gr

from agent_workbench.models.standard_messages import StandardMessage
from agent_workbench.ui.components.message_converter import (
    _GRADIO_META_KEYS,
    to_chat_message,
)


def test_dict_input_extracts_role_and_content():
    msg = {"role": "user", "content": "hello"}
    result = to_chat_message(msg)
    assert result.role == "user"
    assert result.content == "hello"


def test_dict_input_defaults_role_to_assistant():
    msg = {"content": "hi"}
    result = to_chat_message(msg)
    assert result.role == "assistant"


def test_dict_input_defaults_content_to_empty():
    msg = {"role": "user"}
    result = to_chat_message(msg)
    assert result.content == ""


def test_standard_message_input_extracts_role_and_content():
    msg = StandardMessage(role="assistant", content="response text")
    result = to_chat_message(msg)
    assert result.role == "assistant"
    assert result.content == "response text"


def test_returns_gr_chat_message():
    result = to_chat_message({"role": "user", "content": "hi"})
    assert isinstance(result, gr.ChatMessage)


def test_known_metadata_keys_pass_through():
    for key in _GRADIO_META_KEYS:
        msg = {"role": "assistant", "content": "x", "metadata": {key: "value"}}
        result = to_chat_message(msg)
        assert key in result.metadata
        assert result.metadata[key] == "value"


def test_unknown_metadata_keys_are_stripped():
    msg = {
        "role": "assistant",
        "content": "x",
        "metadata": {"status": "done", "unknown_key": "should_be_stripped"},
    }
    result = to_chat_message(msg)
    assert "status" in result.metadata
    assert "unknown_key" not in result.metadata


def test_none_metadata_produces_empty_dict():
    msg = {"role": "assistant", "content": "x", "metadata": None}
    result = to_chat_message(msg)
    assert result.metadata == {}


def test_missing_metadata_produces_empty_dict():
    msg = {"role": "user", "content": "x"}
    result = to_chat_message(msg)
    assert result.metadata == {}


def test_standard_message_metadata_filtered():
    msg = StandardMessage(
        role="assistant",
        content="x",
        metadata={"title": "Tool call", "irrelevant": "drop"},
    )
    result = to_chat_message(msg)
    assert "title" in result.metadata
    assert "irrelevant" not in result.metadata


def test_standard_message_none_metadata_produces_empty_dict():
    msg = StandardMessage(role="user", content="x", metadata=None)
    result = to_chat_message(msg)
    assert result.metadata == {}


def test_full_gradio_metadata_passthrough():
    meta = {
        "title": "Thinking",
        "log": "tool_call()",
        "status": "done",
        "duration": 1.5,
    }
    msg = {"role": "assistant", "content": "result", "metadata": meta}
    result = to_chat_message(msg)
    assert result.metadata == meta
