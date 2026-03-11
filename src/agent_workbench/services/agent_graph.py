"""AgentGraph — inner ReAct agent sub-graph."""

import logging
from dataclasses import dataclass, field
from typing import AsyncGenerator, List, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

from ..models.schemas import ModelConfig
from .providers import provider_registry

logger = logging.getLogger(__name__)


class AgentInput(TypedDict):
    messages: List[BaseMessage]


class AgentOutput(TypedDict):
    messages: List[BaseMessage]


@dataclass
class AgentContext:
    model_config: ModelConfig
    tools: list = field(default_factory=list)


class AgentGraph:
    """Inner ReAct agent sub-graph.

    Self-contained LLM tool loop using MessagesState. Compiled once at
    init; tools and model config injected at invocation time via context_schema.

    Schema layers:
        input_schema=AgentInput   — messages in from outer graph
        output_schema=AgentOutput — final AIMessage out to outer graph
        context_schema=AgentContext — model_config + tools at call time
        internal: MessagesState  — add_messages reducer for loop accumulation

    Usage:
        graph = AgentGraph(model_config)
        # Batch
        result = await graph.ainvoke(messages, tools=[])
        # Streaming
        async for event in graph.astream_events(messages, tools=[]):
            ...
    """

    def __init__(self, model_config: ModelConfig) -> None:
        self._model_config = model_config
        self._graph: CompiledStateGraph = self._build()

    def _build(self) -> CompiledStateGraph:
        async def llm_node(state: MessagesState, runtime: Runtime) -> dict:
            model = provider_registry.create_model(runtime.context.model_config)
            if runtime.context.tools:
                model = model.bind_tools(runtime.context.tools)
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
        builder.add_node("llm_node", llm_node)
        builder.add_conditional_edges("llm_node", should_continue)
        builder.set_entry_point("llm_node")
        return builder.compile()

    def _context(self, tools: list, model_config: Optional[ModelConfig] = None) -> dict:
        return {
            "model_config": model_config or self._model_config,
            "tools": tools,
        }

    async def ainvoke(
        self,
        messages: List[BaseMessage],
        tools: list = [],
        model_config: Optional[ModelConfig] = None,
    ) -> BaseMessage:
        """Batch invocation. Returns final AIMessage."""
        result = await self._graph.ainvoke(
            {"messages": messages},
            context=self._context(tools, model_config),
        )
        return result["messages"][-1]

    async def astream(
        self,
        messages: List[BaseMessage],
        tools: list = [],
        model_config: Optional[ModelConfig] = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream chunks from the agent loop using LangGraph v2 streaming format.

        Yields StreamPart dicts. Callers dispatch on chunk["type"]:
          "messages" — (AIMessageChunk, metadata) token chunks
          "custom"   — get_stream_writer() payloads from nodes/tools (PR-2.4+)
        """
        async for chunk in self._graph.astream(
            {"messages": messages},
            context=self._context(tools, model_config),
            stream_mode=["messages", "custom"],
            version="v2",
        ):
            yield chunk
