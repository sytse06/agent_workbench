"""AgentGraph — inner ReAct agent sub-graph."""

import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator, List, Optional

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
)
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

from ..models.schemas import ModelConfig
from .providers import provider_registry

logger = logging.getLogger(__name__)

# Context compaction — fires when estimated token count exceeds the threshold.
# Oldest messages (everything except the last COMPACTION_KEEP_RECENT) are
# summarised and replaced with a single SystemMessage.  The checkpointer
# stores the compacted state, so the reduction persists across restarts.
COMPACTION_TOKEN_THRESHOLD: int = 4_000  # ~16 000 chars
COMPACTION_KEEP_RECENT: int = 6  # last 6 messages (~3 turns) kept verbatim


def _token_estimate(messages: list) -> int:
    """Rough token estimate: 1 token ≈ 4 characters."""
    return (
        sum(len(m.content) if isinstance(m.content, str) else 0 for m in messages) // 4
    )


def _should_compact(state: MessagesState) -> str:
    """Routing function: 'compact_node' above threshold, 'llm_node' otherwise."""
    if _token_estimate(state["messages"]) > COMPACTION_TOKEN_THRESHOLD:
        return "compact_node"
    return "llm_node"


class AgentInput(TypedDict):
    messages: List[BaseMessage]


class AgentOutput(TypedDict):
    messages: List[BaseMessage]


@dataclass
class AgentContext:
    model_config: ModelConfig
    # tools removed — fixed at graph build time, not injected at call time


class AgentGraph:
    """Inner ReAct agent sub-graph.

    Self-contained LLM tool loop using MessagesState. Compiled once at
    init; tools fixed at build time, model config injected at invocation
    time via context_schema.

    Schema layers:
        input_schema=AgentInput   — messages in from outer graph
        output_schema=AgentOutput — final AIMessage out to outer graph
        context_schema=AgentContext — model_config at call time
        internal: MessagesState  — add_messages reducer for loop accumulation

    Checkpointing:
        Pass thread_id (= conversation_id) to ainvoke/astream to enable per-thread
        state persistence. The checkpointer accumulates MessagesState across turns,
        enabling time-travel and state management for PR-2.6a Thread Management.

    Usage:
        graph = AgentGraph(model_config, tools=[retriever_tool])
        # Batch
        result = await graph.ainvoke(messages, thread_id="conv-uuid")
        # Streaming
        async for chunk in graph.astream(messages, thread_id="conv-uuid"):
            ...
    """

    def __init__(
        self,
        model_config: ModelConfig,
        tools: list = [],
        checkpointer: Optional[BaseCheckpointSaver] = None,
    ) -> None:
        self._model_config = model_config
        self._tools = list(tools)  # freeze copy
        self._checkpointer: BaseCheckpointSaver = checkpointer or MemorySaver()
        self._graph: CompiledStateGraph = self._build()

    def _build(self) -> CompiledStateGraph:
        tools = self._tools  # closure — fixed at compile time

        async def compact_node(state: MessagesState, runtime: Runtime) -> dict:
            """Summarise old messages to keep context within the token budget."""
            messages = state["messages"]
            to_compact = messages[:-COMPACTION_KEEP_RECENT]
            if not to_compact:
                return {}

            conv_text = "\n\n".join(
                f"{m.type.upper()}: {m.content}"
                for m in to_compact
                if isinstance(m.content, str) and m.content
            )
            summary_prompt = [
                HumanMessage(
                    content=(
                        "Summarise the following conversation concisely "
                        "(2–3 sentences):\n\n" + conv_text
                    )
                )
            ]
            model = provider_registry.create_model(runtime.context.model_config)
            summary = await model.ainvoke(summary_prompt)
            logger.info(
                "Context compaction: removed %d messages, summary: %.80s…",
                len(to_compact),
                summary.content,
            )
            remove_ops = [RemoveMessage(id=m.id) for m in to_compact]
            summary_msg = SystemMessage(
                content=f"[Conversation summary]\n{summary.content}"
            )
            return {"messages": remove_ops + [summary_msg]}

        async def llm_node(state: MessagesState, runtime: Runtime) -> dict:
            model = provider_registry.create_model(runtime.context.model_config)
            if tools:
                model = model.bind_tools(tools)
            response = await model.ainvoke(state["messages"])
            return {"messages": [response]}

        def should_continue(state: MessagesState) -> str:
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return "tool_node"
            return END

        builder = StateGraph(
            MessagesState,
            input_schema=AgentInput,
            output_schema=AgentOutput,
            context_schema=AgentContext,
        )
        builder.add_node("compact_node", compact_node)
        builder.add_node("llm_node", llm_node)
        builder.add_conditional_edges(
            START,
            _should_compact,
            {"compact_node": "compact_node", "llm_node": "llm_node"},
        )
        builder.add_edge("compact_node", "llm_node")

        if tools:
            builder.add_node("tool_node", ToolNode(tools))
            builder.add_conditional_edges(
                "llm_node", should_continue, {"tool_node": "tool_node", END: END}
            )
            builder.add_edge("tool_node", "llm_node")
        else:
            builder.add_conditional_edges("llm_node", should_continue)

        return builder.compile(checkpointer=self._checkpointer)

    def _context(self, model_config: Optional[ModelConfig] = None) -> dict:
        return {"model_config": model_config or self._model_config}

    def _config(self, thread_id: Optional[str]) -> dict:
        if thread_id:
            return {"configurable": {"thread_id": thread_id}}
        return {}

    async def get_state(self, thread_id: str) -> Optional[Any]:
        """Return the latest checkpointed state for thread_id, or None."""
        config = {"configurable": {"thread_id": thread_id}}
        state = await self._graph.aget_state(config)
        return state if state and state.values else None

    async def ainvoke(
        self,
        messages: List[BaseMessage],
        model_config: Optional[ModelConfig] = None,
        thread_id: Optional[str] = None,
    ) -> BaseMessage:
        """Batch invocation. Returns final AIMessage."""
        result = await self._graph.ainvoke(
            {"messages": messages},
            config=self._config(thread_id),
            context=self._context(model_config),
        )
        return result["messages"][-1]

    async def astream(
        self,
        messages: List[BaseMessage],
        model_config: Optional[ModelConfig] = None,
        thread_id: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream chunks from the agent loop using LangGraph v2 streaming format.

        Yields StreamPart dicts. Callers dispatch on chunk["type"]:
          "messages" — (AIMessageChunk, metadata) token chunks
          "custom"   — get_stream_writer() payloads from nodes/tools (PR-2.4+)
        """
        async for chunk in self._graph.astream(
            {"messages": messages},
            config=self._config(thread_id),
            context=self._context(model_config),
            stream_mode=["messages", "custom"],
            version="v2",
        ):
            yield chunk
