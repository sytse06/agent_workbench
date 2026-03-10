"""Agent service — single execution path for all chat modes."""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from ..models.schemas import ModelConfig
from .providers import provider_registry

logger = logging.getLogger(__name__)

_ROLE_TO_LC: Dict[str, type] = {
    "user": HumanMessage,
    "assistant": AIMessage,
    "system": SystemMessage,
}


class AgentResponse(BaseModel):
    message: str
    status: str = "success"
    reasoning: Optional[str] = None
    task_id: Optional[str] = None


def _split_think_tags(text: str, in_think: bool) -> tuple[List[tuple[str, str]], bool]:
    """Split a text chunk on <think>/<think> tag boundaries.

    Handles the streaming case where tags may arrive in separate chunks.
    Returns (segments, updated_in_think) where each segment is
    ("thinking" | "answer", content).
    """
    segments: List[tuple[str, str]] = []
    remaining = text
    while remaining:
        if in_think:
            end = remaining.find("</think>")
            if end == -1:
                segments.append(("thinking", remaining))
                remaining = ""
            else:
                if end > 0:
                    segments.append(("thinking", remaining[:end]))
                in_think = False
                remaining = remaining[end + len("</think>") :]
        else:
            start = remaining.find("<think>")
            if start == -1:
                segments.append(("answer", remaining))
                remaining = ""
            else:
                if start > 0:
                    segments.append(("answer", remaining[:start]))
                in_think = True
                remaining = remaining[start + len("<think>") :]
    return segments, in_think


class AgentService:
    """Single execution engine for all chat modes.

    Wraps a LangChain chat model with:
    - Batch invocation via run() — used by the LangGraph workflow nodes
    - Token streaming via astream() — used by UI handlers for responsive output

    Notes:
        model_config is the DEFAULT config. run() and astream() accept an optional
        override config for mode-specific settings (e.g. SEO Coach uses a different
        model and system prompt).

        Thinking content is extracted from three sources:
        - content_blocks type "non_standard" — Anthropic extended thinking
        - content_blocks type "reasoning"    — OpenAI o-series, Gemini
        - <think>...</think> tags in text    — Ollama/Qwen3 and compatible models
        All three emit "thinking_chunk" events; non-thinking providers stream
        "answer_chunk" events only.
    """

    def __init__(self, model_config: ModelConfig) -> None:
        self._default_config = model_config
        self._default_model = provider_registry.create_model(model_config)

    def _get_model(self, model_config: Optional[ModelConfig] = None) -> Any:
        if model_config is None or model_config == self._default_config:
            return self._default_model
        return provider_registry.create_model(model_config)

    def _to_lc(self, messages: List[Dict[str, Any]]) -> List[BaseMessage]:
        result: List[BaseMessage] = []
        for msg in messages:
            role = msg.get("role", "user")
            content = str(msg.get("content", ""))
            cls = _ROLE_TO_LC.get(role, HumanMessage)
            result.append(cls(content=content))
        return result

    async def run(
        self,
        messages: List[Dict[str, Any]],
        task_id: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
    ) -> AgentResponse:
        """Batch invocation. Returns a complete AgentResponse.

        Args:
            messages: Conversation messages as role/content dicts.
            task_id: Unique ID for this task's working memory (generated if omitted).
            model_config: Optional override config (e.g. SEO Coach model).
        """
        task_id = task_id or str(uuid4())
        model = self._get_model(model_config)
        response = await model.ainvoke(self._to_lc(messages))
        content = str(response.content) if response.content else ""
        return AgentResponse(message=content, task_id=task_id)

    async def astream(
        self,
        messages: List[Dict[str, Any]],
        task_id: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Token streaming. Yields typed event dicts.

        Event shapes:
            {"type": "thinking_chunk", "content": str}  — Anthropic only
            {"type": "answer_chunk",   "content": str}  — all providers
            {"type": "done", "response": AgentResponse} — final structured response

        Args:
            messages: Conversation messages as role/content dicts.
            task_id: Unique ID for this task's working memory (generated if omitted).
            model_config: Optional override config.
        """
        task_id = task_id or str(uuid4())
        model = self._get_model(model_config)
        answer_acc = ""
        thinking_acc = ""
        in_think = False  # tracks <think> tag state across chunks

        async for chunk in model.astream(self._to_lc(messages)):
            for block in chunk.content_blocks:
                block_type = block.get("type")

                if block_type == "text":
                    text = block.get("text", "")
                    if text:
                        segments, in_think = _split_think_tags(text, in_think)
                        for seg_type, seg_text in segments:
                            if not seg_text:
                                continue
                            if seg_type == "thinking":
                                thinking_acc += seg_text
                                yield {"type": "thinking_chunk", "content": seg_text}
                            else:
                                answer_acc += seg_text
                                yield {"type": "answer_chunk", "content": seg_text}

                elif block_type == "reasoning":
                    # OpenAI o-series, Gemini (standardized in langchain-core 1.x)
                    data = block.get("data", "")
                    if data:
                        thinking_acc += data
                        yield {"type": "thinking_chunk", "content": data}

                elif block_type == "non_standard":
                    # Anthropic extended thinking (not yet normalized in 1.2.17)
                    inner = block.get("value", {})
                    if inner.get("type") == "thinking":
                        text = inner.get("thinking", "")
                        if text:
                            thinking_acc += text
                            yield {"type": "thinking_chunk", "content": text}

        yield {
            "type": "done",
            "response": AgentResponse(
                message=answer_acc,
                reasoning=thinking_acc or None,
                task_id=task_id,
            ),
        }
