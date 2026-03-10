"""Convert StandardMessage / dict to gr.ChatMessage for UI rendering."""

from typing import Dict, List, Union

import gradio as gr

from ...models.standard_messages import StandardMessage

_GRADIO_META_KEYS = {"title", "log", "status", "duration"}


def to_chat_message(msg: Union[StandardMessage, Dict]) -> gr.ChatMessage:
    """Convert StandardMessage or dict to gr.ChatMessage for UI rendering."""
    if isinstance(msg, dict):
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        metadata = msg.get("metadata") or {}
    else:
        role = msg.role
        content = msg.content
        metadata = msg.metadata or {}

    gr_metadata = {k: v for k, v in metadata.items() if k in _GRADIO_META_KEYS}
    return gr.ChatMessage(role=role, content=content, metadata=gr_metadata)


# Maps SSE event type → (symbol, label_en, label_nl)
# PR-2.3 adds "tool_call" and "tool_result" entries here — no other file changes needed.
_BLOCK_LABELS: Dict[str, tuple] = {
    "thinking_chunk": ("🧠", "Thinking", "Denken"),
    "processing_file": ("📄", "Processing", "Verwerken"),
    # PR-2.3 additions:
    # "tool_call":     ("🔍", "Retrieving", "Ophalen"),
    # "tool_result":   ("📋", "Result",     "Resultaat"),
}


def streaming_event_to_chat_messages(
    event: Dict,
    thinking_content: str = "",
    answer_content: str = "",
    locale: str = "en",
) -> List[gr.ChatMessage]:
    """Map a streaming SSE event dict to a list of gr.ChatMessage for UI rendering.

    Args:
        event: SSE event dict with 'type' and optional 'content'/'filename' keys.
        thinking_content: Accumulated thinking text (updated externally by caller).
        answer_content: Accumulated answer text (updated externally by caller).
        locale: 'en' or 'nl' — selects label language from _BLOCK_LABELS.

    Returns:
        List of gr.ChatMessage to yield to the Gradio UI.
        Empty list if the event produces no visible output.
    """
    event_type = event.get("type")

    if event_type == "processing_file":
        symbol, label_en, label_nl = _BLOCK_LABELS["processing_file"]
        label = label_nl if locale == "nl" else label_en
        fname = event.get("filename", "document")
        return [
            gr.ChatMessage(
                role="assistant",
                content="",
                metadata={"title": f"{symbol} {label} {fname}…", "status": "pending"},
            )
        ]

    if event_type == "thinking_chunk":
        symbol, label_en, label_nl = _BLOCK_LABELS["thinking_chunk"]
        label = label_nl if locale == "nl" else label_en
        return [
            gr.ChatMessage(
                role="assistant",
                content=thinking_content,
                metadata={"title": f"{symbol} {label}", "status": "pending"},
            )
        ]

    if event_type == "answer_chunk":
        symbol, label_en, label_nl = _BLOCK_LABELS["thinking_chunk"]
        label = label_nl if locale == "nl" else label_en
        msgs = []
        if thinking_content:
            msgs.append(
                gr.ChatMessage(
                    role="assistant",
                    content=thinking_content,
                    metadata={"title": f"{symbol} {label}", "status": "done"},
                )
            )
        msgs.append(gr.ChatMessage(role="assistant", content=answer_content))
        return msgs

    return []
