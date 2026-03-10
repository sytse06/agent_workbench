"""Unit tests for the MessageConverter UI boundary utility."""

import gradio as gr

from agent_workbench.models.standard_messages import StandardMessage
from agent_workbench.ui.components.message_converter import (
    _GRADIO_META_KEYS,
    streaming_event_to_chat_messages,
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


# --- streaming_event_to_chat_messages ---


def test_processing_file_en():
    event = {"type": "processing_file", "filename": "report.pdf"}
    msgs = streaming_event_to_chat_messages(event, locale="en")
    assert len(msgs) == 1
    assert "📄" in msgs[0].metadata["title"]
    assert "report.pdf" in msgs[0].metadata["title"]
    assert msgs[0].metadata["status"] == "pending"


def test_processing_file_nl():
    event = {"type": "processing_file", "filename": "rapport.pdf"}
    msgs = streaming_event_to_chat_messages(event, locale="nl")
    assert len(msgs) == 1
    assert "📄" in msgs[0].metadata["title"]
    assert "Verwerken" in msgs[0].metadata["title"]


def test_thinking_chunk_en():
    event = {"type": "thinking_chunk", "content": "some reasoning"}
    msgs = streaming_event_to_chat_messages(
        event, thinking_content="some reasoning", locale="en"
    )
    assert len(msgs) == 1
    assert "🧠" in msgs[0].metadata["title"]
    assert msgs[0].metadata["status"] == "pending"
    assert msgs[0].content == "some reasoning"


def test_thinking_chunk_nl():
    event = {"type": "thinking_chunk", "content": "redenering"}
    msgs = streaming_event_to_chat_messages(
        event, thinking_content="redenering", locale="nl"
    )
    assert "Denken" in msgs[0].metadata["title"]


def test_answer_chunk_without_thinking():
    event = {"type": "answer_chunk", "content": "The answer"}
    msgs = streaming_event_to_chat_messages(
        event, thinking_content="", answer_content="The answer"
    )
    assert len(msgs) == 1
    assert msgs[0].content == "The answer"
    assert msgs[0].metadata == {}


def test_answer_chunk_with_prior_thinking():
    event = {"type": "answer_chunk", "content": "Answer"}
    msgs = streaming_event_to_chat_messages(
        event, thinking_content="My thoughts", answer_content="Answer"
    )
    assert len(msgs) == 2
    thinking_msg = msgs[0]
    answer_msg = msgs[1]
    assert thinking_msg.metadata["status"] == "done"
    assert "🧠" in thinking_msg.metadata["title"]
    assert answer_msg.content == "Answer"
    assert answer_msg.metadata == {}


def test_unknown_event_type_returns_empty():
    event = {"type": "unknown_event", "content": "x"}
    msgs = streaming_event_to_chat_messages(event)
    assert msgs == []


def test_done_event_returns_empty():
    event = {"type": "done"}
    msgs = streaming_event_to_chat_messages(event)
    assert msgs == []
