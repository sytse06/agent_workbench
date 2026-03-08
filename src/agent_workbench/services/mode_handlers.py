"""Mode-specific handlers for workbench and seo_coach workflows."""

import logging
from typing import Any, Dict, List, Literal
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from ..core.dutch_prompts import DutchSEOPrompts
from ..models.consolidated_state import WorkbenchState
from ..models.schemas import ModelConfig
from ..models.standard_messages import StandardMessage
from .agent_service import AgentService
from .context_service import ContextService

logger = logging.getLogger(__name__)


class WorkbenchModeHandler:
    """Handle workbench mode processing with technical capabilities."""

    def __init__(self, agent_service: AgentService, context_service: ContextService):
        self.agent_service = agent_service
        self.context_service = context_service

    async def process_message(self, state: WorkbenchState) -> WorkbenchState:  # type: ignore
        """
        Process workbench mode message with full technical control.

        Args:
            state: Current workflow state

        Returns:
            Updated state with workbench processing results
        """
        try:
            # Apply parameter overrides if provided
            model_config = state["model_config"]
            parameter_overrides = state.get("parameter_overrides")
            if parameter_overrides:
                model_config = self._apply_parameter_overrides(
                    model_config, parameter_overrides
                )

            # Build technical context
            technical_context = self._build_technical_context(state)

            # Update conversation context if needed
            await self.context_service.update_conversation_context(
                state["conversation_id"],
                technical_context,
                ["workbench_session", "technical_context"],
            )

            # Prepare messages for LLM
            messages = await self._build_workbench_messages(state, model_config)

            # Execute via AgentService
            agent_response = await self.agent_service.run(
                messages=[{"role": m.type, "content": m.content} for m in messages],
                task_id=str(uuid4()),
                model_config=model_config,
            )
            response = agent_response.message

            # Add technical metadata
            technical_metadata = {
                "model_used": f"{model_config.provider}/{model_config.model_name}",
                "temperature": model_config.temperature,
                "max_tokens": model_config.max_tokens,
                "debug_mode": state.get("debug_mode", False),
                "parameter_overrides_applied": bool(state.get("parameter_overrides")),
            }

            # Update conversation history with new messages
            # Create a copy of the conversation history (ensuring it's a list)
            # We know conversation_history is a list based on WorkbenchState TypedDict
            conversation_history = state["conversation_history"]
            # Create a properly typed copy
            updated_history: List[StandardMessage] = []
            for msg in conversation_history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    updated_history.append(
                        StandardMessage(role=msg["role"], content=msg["content"])
                    )

            updated_history.append(
                StandardMessage(role="user", content=state["user_message"])
            )
            updated_history.append(StandardMessage(role="assistant", content=response))

            return {
                **state,
                "assistant_response": response,
                "conversation_history": updated_history,
                "workflow_steps": state["workflow_steps"]
                + ["Workbench processing completed"],
                "context_data": {
                    **state["context_data"],
                    "technical_metadata": technical_metadata,
                },
            }

        except Exception as e:
            logger.error(f"Workbench processing failed: {str(e)}")
            return {
                **state,
                "current_error": f"Workbench processing failed: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state["workflow_steps"]
                + [f"Workbench error: {str(e)}"],
            }

    def _apply_parameter_overrides(
        self, config: ModelConfig, overrides: Dict[str, Any]
    ) -> ModelConfig:
        """
        Apply parameter overrides to model configuration.

        Args:
            config: Base model configuration
            overrides: Parameter overrides

        Returns:
            Modified model configuration
        """
        # Create new config with overrides
        config_dict = config.model_dump()
        config_dict.update(overrides)

        return ModelConfig(**config_dict)

    def _build_technical_context(self, state: WorkbenchState) -> Dict[str, Any]:
        """
        Build technical context for workbench processing.

        Args:
            state: Current workflow state

        Returns:
            Technical context data
        """
        context = {
            "session_type": "workbench",
            "debug_mode": state.get("debug_mode", False),
            "conversation_length": len(state["conversation_history"]),
            "active_contexts": state.get("active_contexts", []),
        }

        if state.get("parameter_overrides"):
            context["parameter_overrides"] = state["parameter_overrides"]

        return context

    async def _build_workbench_messages(
        self, state: WorkbenchState, model_config: ModelConfig
    ) -> list[BaseMessage]:
        """
        Build messages for workbench LLM processing.

        Args:
            state: Current workflow state
            model_config: Model configuration

        Returns:
            List of messages for LLM
        """
        messages = []

        # Add system prompt if configured
        if model_config.system_prompt:
            messages.append(SystemMessage(content=model_config.system_prompt))

        # Add context information
        if state.get("context_data"):
            context_parts = []
            for key, value in state["context_data"].items():
                if key != "technical_metadata":  # Exclude metadata from context
                    context_parts.append(f"{key}: {value}")

            if context_parts:
                context_prompt = "Context Information:\n" + "\n".join(context_parts)
                messages.append(SystemMessage(content=context_prompt))

        # Inject attached document context
        if state.get("document_context"):
            fname = state.get("document_filename", "document")
            doc_ctx = state["document_context"]
            messages.append(
                SystemMessage(content=f"[Attached document: {fname}]\n\n{doc_ctx}")
            )

        # Add conversation history (both turns for multi-turn context)
        for msg in state["conversation_history"]:
            if isinstance(msg, dict):
                role, content = msg.get("role"), msg.get("content", "")
            else:
                role, content = getattr(msg, "role", None), getattr(msg, "content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # Add current user message
        messages.append(HumanMessage(content=state["user_message"]))

        return messages


class SEOCoachModeHandler:
    """Handle SEO coach mode processing with Dutch business context."""

    def __init__(self, agent_service: AgentService, context_service: ContextService):
        self.agent_service = agent_service
        self.context_service = context_service
        self.dutch_prompts = DutchSEOPrompts()

    async def process_message(self, state: WorkbenchState) -> WorkbenchState:  # type: ignore
        """
        Process SEO coaching message with Dutch business context.

        Args:
            state: Current workflow state

        Returns:
            Updated state with SEO coaching results
        """
        try:
            # Build coaching context (ensure it's never None)
            coaching_context_result = await self._build_coaching_context(state)
            coaching_context = (
                coaching_context_result if coaching_context_result is not None else {}
            )

            # Update conversation context with coaching data
            await self.context_service.update_conversation_context(
                state["conversation_id"],
                coaching_context,
                ["seo_coaching", "business_profile"],
            )

            # Get Dutch SEO coaching configuration
            dutch_config = self._get_dutch_coaching_config(state)

            # Prepare messages for Dutch coaching
            messages = await self._build_coaching_messages(state, dutch_config)

            # Execute via AgentService with SEO Coach model config
            agent_response = await self.agent_service.run(
                messages=[{"role": m.type, "content": m.content} for m in messages],
                task_id=str(uuid4()),
                model_config=dutch_config,
            )
            response = agent_response.message

            # Update coaching phase if needed
            updated_state = await self._update_coaching_phase(state)

            # Update conversation history safely
            # We know conversation_history is a list based on WorkbenchState TypedDict
            conversation_history = state["conversation_history"]
            # Create a properly typed copy
            updated_history: List[StandardMessage] = []
            for msg in conversation_history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    updated_history.append(
                        StandardMessage(role=msg["role"], content=msg["content"])
                    )

            updated_history.append(
                StandardMessage(role="user", content=state["user_message"])
            )
            updated_history.append(StandardMessage(role="assistant", content=response))

            return {
                **updated_state,
                "assistant_response": response,
                "conversation_history": updated_history,
                "coaching_context": coaching_context,
                "workflow_steps": state["workflow_steps"] + ["SEO coaching completed"],
                "context_data": {
                    **state["context_data"],
                    "coaching_context": coaching_context,
                },
            }

        except Exception as e:
            logger.error(f"SEO coaching failed: {str(e)}")
            return {
                **state,
                "current_error": f"SEO coaching failed: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state["workflow_steps"]
                + [f"Coaching error: {str(e)}"],
            }

    async def _build_coaching_context(self, state: WorkbenchState) -> Dict[str, Any]:
        """
        Build Dutch coaching context from business profile and analysis.

        Args:
            state: Current workflow state

        Returns:
            Coaching context data
        """
        # Default to empty dicts for safety
        business_profile = state.get("business_profile") or {}
        seo_analysis = state.get("seo_analysis") or {}
        context_data = state.get("context_data", {})

        # Handle previous_recommendations safely
        previous_recommendations = []
        if context_data:
            recommendations = context_data.get("recommendations")
            if recommendations is not None:
                previous_recommendations = recommendations

        return {
            "business_context": {
                "business_type": business_profile.get(
                    "business_type", "algemeen bedrijf"
                ),
                "target_market": business_profile.get("target_market", "Nederland"),
                "experience_level": business_profile.get(
                    "seo_experience_level", "beginner"
                ),
                "business_name": business_profile.get("business_name", "het bedrijf"),
                "website_url": business_profile.get("website_url", ""),
            },
            "seo_context": seo_analysis,
            "coaching_phase": state.get("coaching_phase", "analysis"),
            "previous_recommendations": previous_recommendations,
            "session_info": {
                "conversation_length": len(state["conversation_history"]),
                "mode": "seo_coach",
            },
        }

    def _get_dutch_coaching_config(self, state: WorkbenchState) -> ModelConfig:
        """
        Get Dutch SEO coaching model configuration.

        Args:
            state: Current workflow state

        Returns:
            Model configuration for Dutch coaching
        """
        business_type = "algemeen"
        if state.get("business_profile"):
            business_profile = state["business_profile"]
            if business_profile is not None:
                business_type = business_profile.get("business_type", "algemeen")

        system_prompt = self.dutch_prompts.get_coaching_system_prompt(business_type)

        return ModelConfig(
            provider="openrouter",
            model_name="openai/gpt-4o-mini",
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=1500,
            streaming=True,
        )

    async def _build_coaching_messages(
        self, state: WorkbenchState, model_config: ModelConfig
    ) -> list[BaseMessage]:
        """
        Build messages for Dutch SEO coaching.

        Args:
            state: Current workflow state
            model_config: Model configuration

        Returns:
            List of messages for LLM
        """
        messages = []

        # Add Dutch coaching system prompt
        if model_config.system_prompt:
            messages.append(SystemMessage(content=model_config.system_prompt))

            # Add business context - ensure we have dictionaries
        # Initialize with safe default values
        business_type = "onbekend"
        target_market = "Nederland"
        experience = "beginner"
        website = "niet opgegeven"
        phase = "analysis"

        # Get values from state if available
        coaching_context_data = state.get("coaching_context")
        if coaching_context_data and isinstance(coaching_context_data, dict):
            business_context = coaching_context_data.get("business_context")
            if business_context and isinstance(business_context, dict):
                if "business_type" in business_context:
                    business_type = business_context["business_type"]
                if "target_market" in business_context:
                    target_market = business_context["target_market"]
                if "experience_level" in business_context:
                    experience = business_context["experience_level"]
                if "website_url" in business_context:
                    website = business_context["website_url"]

            # Get coaching phase safely
            if "coaching_phase" in coaching_context_data:
                phase = coaching_context_data["coaching_phase"]

            context_msg = f"""Bedrijfsinformatie:
- Bedrijfstype: {business_type}
- Doelmarkt: {target_market}
- SEO ervaring: {experience}
- Website: {website}

Coaching fase: {phase}"""

            messages.append(SystemMessage(content=context_msg))

        # Inject attached document context
        if state.get("document_context"):
            fname = state.get("document_filename", "document")
            doc_ctx = state["document_context"]
            messages.append(
                SystemMessage(content=f"[Bijgevoegd document: {fname}]\n\n{doc_ctx}")
            )

        # Add conversation history (both turns for multi-turn context)
        for msg in state["conversation_history"]:
            if isinstance(msg, dict):
                role, content = msg.get("role"), msg.get("content", "")
            else:
                role = getattr(msg, "role", None)
                content = getattr(msg, "content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        # Add current user message
        messages.append(HumanMessage(content=state["user_message"]))

        return messages

    async def _update_coaching_phase(self, state: WorkbenchState) -> WorkbenchState:
        """
        Update coaching phase based on conversation progress.

        Args:
            state: Current workflow state

        Returns:
            Updated state with coaching phase
        """
        # Simple phase detection based on conversation content
        user_message = state["user_message"].lower()
        current_phase = state.get("coaching_phase", "analysis")

        # Phase transition logic
        # Explicit typing for new_phase
        new_phase: Literal[
            "analysis", "recommendations", "implementation", "monitoring"
        ]

        if "analyse" in user_message or "check" in user_message:
            new_phase = "analysis"
        elif "aanbeveling" in user_message or "wat moet ik" in user_message:
            new_phase = "recommendations"
        elif "hoe" in user_message or "implementeren" in user_message:
            new_phase = "implementation"
        elif "resultaat" in user_message or "monitoring" in user_message:
            new_phase = "monitoring"
        else:
            # Keep current phase, defaulting to "analysis" if None
            new_phase = current_phase or "analysis"

        return {**state, "coaching_phase": new_phase}
