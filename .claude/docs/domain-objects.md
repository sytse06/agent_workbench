# 8 Core Domain Objects

Phase 1 implements a domain-driven architecture with these core objects.

## 1. MESSAGE
Universal message format supporting agentic workflows.

- `StandardMessage` (Pydantic): In-memory format with tool call support
- `MessageModel` (SQLAlchemy): Database persistence
- Multi-role: user, assistant, system, tool
- Tool calling: `tool_calls` and `tool_call_id` fields

**Location:** `models/standard_messages.py`, `models/database.py`

## 2. CONVERSATION
Conversation lifecycle and persistence.

- `ConversationResponse` (Pydantic): API response
- `ConversationModel` (SQLAlchemy): Database with cascade delete
- `ConversationService`: Business logic layer

**Location:** `models/consolidated_state.py`, `services/conversation_service.py`

## 3. STATE
Dual-format state management (storage vs execution).

- `ConversationState` (Pydantic): Storage format - single source of truth
- `WorkbenchState` (TypedDict): LangGraph execution format
- `ValidatedWorkbenchState` (Pydantic): Validation wrapper

```
ConversationState -> WorkbenchState (via Bridge) -> LangGraph -> WorkbenchState -> ConversationState (via Bridge)
```

**Location:** `models/standard_messages.py`, `models/consolidated_state.py`

## 4. WORKFLOW
LangGraph StateGraph orchestration.

- `SimpleChatWorkflow`: 2-node minimal (testing/debugging)
- `ConsolidatedWorkbenchService`: Full multi-step (production)
- Primary endpoint: `POST /api/v1/chat/workflow`

**Location:** `services/simple_chat_workflow.py`, `services/consolidated_service.py`

## 5. CONTEXT
**Status:** Placeholder - needs Phase 2 implementation.

Current: Basic structure in `WorkbenchState.context_data`

**Location:** `services/context_service.py`

## 6. USER MODE
Persona-based UI and workflow customization. Phase 2 extends this to a full User domain.

- `workbench`: Technical users, full model controls, debug tools
- `seo_coach`: Business users, Dutch language, business forms
- `mode_factory_v2.py` creates mode-specific Gradio interfaces via `APP_MODE` env var
- **Phase 2.0:** extends to full User domain object (HF OAuth, sessions, user profiles)
- **Phase 2.1:** user settings persistence via `UserSettingsService`

**Location (current):** `ui/mode_factory_v2.py`, `ui/pages/`
**Phase 2 services (pre-built, unwired):** `services/auth_service.py`, `services/user_settings_service.py`

## 7. AGENT/TOOL
**Status:** Config storage only - needs Phase 2 implementation.

Current: `AgentConfigModel` for configuration storage.

**Location:** `models/database.py`, `api/routes/agent_configs.py`

## 8. BRIDGE
Convert between storage and execution formats.

- `LangGraphStateBridge`: `ConversationState` <-> `WorkbenchState` conversion
- Context merging, message format translation, workflow state tracking
- **Phase 2 extension:** Bridge gains `user_id` parameter; loads user settings from DB into state

**Location:** `services/langgraph_bridge.py`
**Phase 2 workflow infra (pre-built):** `services/langgraph_service.py` (5-node orchestrator), `services/workflow_nodes.py` (node implementations)

**CRITICAL Phase 2 state pattern:** LangGraph StateGraph owns conversation state (persistent,
keyed by `conversation_id`). Agent gets ephemeral working memory keyed by unique `task_id`
— never `conversation_id`. See `docs/phase2/state_management_critical_pattern.md`.
