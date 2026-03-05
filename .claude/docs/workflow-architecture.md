# LangGraph Workflow Architecture

All chat interactions flow through LangGraph StateGraph workflows.

## WorkbenchState (TypedDict)

LangGraph execution format. Key fields:

```python
class WorkbenchState(TypedDict):
    conversation_id: UUID
    user_message: str
    assistant_response: Optional[str]
    model_config: ModelConfig
    provider_name: str
    context_data: Dict[str, Any]
    conversation_history: List[StandardMessage]
    workflow_mode: Literal["workbench", "seo_coach"]
    workflow_steps: List[str]
    execution_successful: bool
    # Mode-specific fields
    business_profile: Optional[Dict[str, Any]]       # SEO Coach
    coaching_phase: Optional[Literal["analysis", ...]] # SEO Coach
    debug_mode: Optional[bool]                        # Workbench
    parameter_overrides: Optional[Dict[str, Any]]     # Workbench
    # Phase 2 extensions
    mcp_tools_active: List[str]
    agent_state: Optional[Dict[str, Any]]
```

## Workflow Implementations

**SimpleChatWorkflow** (2-node): Process input -> Generate response. For testing.

**ConsolidatedWorkbenchService** (full): Multi-step StateGraph with state persistence via Bridge. For production.

## Complete Flow

```
User Input (Gradio UI)
  -> POST /api/v1/chat/workflow
  -> ConsolidatedWorkflowRequest (validation)
  -> LangGraphStateBridge.load_into_langgraph_state()
  -> LangGraph StateGraph Execution
     (parse intent -> load context -> generate response -> format output)
  -> LangGraphStateBridge.save_from_langgraph_state()
  -> ConsolidatedWorkflowResponse
  -> Return to Gradio UI
```
