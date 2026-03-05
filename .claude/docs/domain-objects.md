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
Persona-based UI and workflow customization.

- `workbench`: Technical users, full model controls, debug tools
- `seo_coach`: Business users, Dutch language, business forms
- `ModeFactory` creates mode-specific Gradio interfaces

**Location:** `ui/mode_factory.py`, `ui/app.py`, `ui/seo_coach_app.py`

## 7. AGENT/TOOL
**Status:** Config storage only - needs Phase 2 implementation.

Current: `AgentConfigModel` for configuration storage.

**Location:** `models/database.py`, `api/routes/agent_configs.py`

## 8. BRIDGE
Convert between storage and execution formats.

- `LangGraphStateBridge`: `ConversationState` <-> `WorkbenchState` conversion
- Context merging, message format translation, workflow state tracking

**Location:** `services/langgraph_bridge.py`
