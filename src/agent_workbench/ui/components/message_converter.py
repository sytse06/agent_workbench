"""Convert StandardMessage / dict to gr.ChatMessage for UI rendering."""

from typing import Dict, Union

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
