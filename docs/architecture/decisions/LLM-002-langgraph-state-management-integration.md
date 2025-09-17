# LLM-002: LangGraph State Management Integration

## Status

**Status**: Ready for Implementation  
**Date**: September 16, 2025  
**Decision Makers**: Human Architect  
**Task ID**: LLM-002-langgraph-state-management  
**Dependencies**: LLM-001 (LangChain foundation), LLM-001B (conversation state), CORE-002 (database schema)

## Context

Replace the framework-agnostic state management approach with production-proven LangGraph state orchestration, following patterns validated in the GAIA agent implementation. Provides robust workflow orchestration, persistent state management, and foundation for advanced agent workflows while maintaining compatibility with existing LLM-001B conversation persistence.

## Architecture Scope

### What's Included:

- LangGraph StateGraph for workflow orchestration and state management
- TypedDict state models for type-safe state transitions
- Integration with existing LLM-001B conversation persistence
- Workflow nodes for chat completion, context injection, and state persistence
- Conditional routing based on conversation context and user intent
- Error handling and retry logic within LangGraph workflows
- Migration from LLM-001B conversation state to LangGraph state
- Dual-mode workflow support (workbench vs seo_coach)

### What's Explicitly Excluded:

- Framework-agnostic alternatives to LangGraph
- UI integration or Gradio components (UI-001)
- MCP tool integration or agent workflows (Phase 2)
- Document processing logic beyond context injection (Phase 2)
- Vector embeddings or semantic search capabilities
- Authentication or user management

## Architectural Decisions

### 1. LangGraph as Core State Management

**Core Philosophy**: LangGraph provides production-grade state orchestration proven in complex agent workflows

```python
class WorkbenchState(TypedDict):
    # Core conversation state
    conversation_id: UUID
    user_message: str
    assistant_response: Optional[str]
    
    # Model configuration
    model_config: ModelConfig
    provider_name: str
    
    # Context and memory
    context_data: Dict[str, Any]
    active_contexts: List[str]
    conversation_history: List[StandardMessage]
    
    # Workflow control
    workflow_mode: Literal["workbench", "seo_coach"]
    workflow_steps: List[str]
    current_operation: Optional[str]
    execution_successful: bool
    
    # Error handling
    current_error: Optional[str]
    retry_count: int
    
    # SEO Coach specific (when workflow_mode = "seo_coach")
    business_profile: Optional[Dict[str, Any]]
    seo_analysis: Optional[Dict[str, Any]]
    coaching_context: Optional[Dict[str, Any]]
    
    # Future extensions for Phase 2
    mcp_tools_active: List[str]
    agent_state: Optional[Dict[str, Any]]
```

### 2. Workflow Node Architecture

**Following GAIA Agent Patterns**:
```python
class WorkbenchLangGraphService:
    def __init__(self):
        self.workflow = self._build_workflow()
        self.state_manager = StateManager()  # From LLM-001B
        self.conversation_service = ConversationService()  # From LLM-001B
        self.llm_service = ChatService()  # From LLM-001
    
    def _build_workflow(self) -> StateGraph:
        builder = StateGraph(WorkbenchState)
        
        # Core workflow nodes
        builder.add_node("load_conversation", self._load_conversation_node)
        builder.add_node("process_message", self._process_message_node)
        builder.add_node("generate_response", self._generate_response_node)
        builder.add_node("save_state", self._save_state_node)
        builder.add_node("handle_error", self._handle_error_node)
        
        # Mode-specific nodes
        builder.add_node("seo_coaching", self._seo_coaching_node)
        builder.add_node("workbench_chat", self._workbench_chat_node)
        
        # Workflow routing
        builder.add_edge(START, "load_conversation")
        builder.add_edge("load_conversation", "process_message")
        
        builder.add_conditional_edges(
            "process_message",
            self._route_by_mode,
            {
                "workbench": "workbench_chat",
                "seo_coach": "seo_coaching"
            }
        )
        
        builder.add_edge("workbench_chat", "generate_response")
        builder.add_edge("seo_coaching", "generate_response")
        builder.add_edge("generate_response", "save_state")
        builder.add_edge("save_state", END)
        
        return builder.compile()
```

### 3. Integration with LLM-001B State Persistence

**Bridging LangGraph State with Database Persistence**:
```python
async def _load_conversation_node(self, state: WorkbenchState) -> WorkbenchState:
    """Load conversation state from LLM-001B persistence layer"""
    
    conversation_id = state["conversation_id"]
    
    try:
        # Load from LLM-001B conversation state
        conversation_state = await self.state_manager.load_conversation_state(conversation_id)
        
        return {
            **state,
            "conversation_history": conversation_state.messages,
            "context_data": conversation_state.context_data,
            "active_contexts": conversation_state.active_contexts,
            "model_config": conversation_state.model_config,
            "workflow_steps": state["workflow_steps"] + ["Conversation state loaded"]
        }
        
    except Exception as e:
        return {
            **state,
            "current_error": f"Failed to load conversation: {str(e)}",
            "workflow_steps": state["workflow_steps"] + [f"Error loading conversation: {str(e)}"]
        }

async def _save_state_node(self, state: WorkbenchState) -> WorkbenchState:
    """Save conversation state back to LLM-001B persistence"""
    
    try:
        # Convert LangGraph state back to LLM-001B ConversationState
        conversation_state = ConversationState(
            conversation_id=state["conversation_id"],
            messages=state["conversation_history"],
            model_config=state["model_config"],
            context_data=state["context_data"],
            active_contexts=state["active_contexts"],
            metadata={"workflow_mode": state["workflow_mode"]},
            updated_at=datetime.utcnow()
        )
        
        await self.state_manager.save_conversation_state(conversation_state)
        
        return {
            **state,
            "execution_successful": True,
            "workflow_steps": state["workflow_steps"] + ["State saved successfully"]
        }
        
    except Exception as e:
        return {
            **state,
            "current_error": f"Failed to save state: {str(e)}",
            "execution_successful": False,
            "workflow_steps": state["workflow_steps"] + [f"Save error: {str(e)}"]
        }
```

### 4. Mode-Specific Workflow Nodes

**Workbench Mode Node**:
```python
async def _workbench_chat_node(self, state: WorkbenchState) -> WorkbenchState:
    """Handle workbench mode chat with technical capabilities"""
    
    try:
        # Build context-aware messages
        messages = self._build_context_messages(
            state["conversation_history"],
            state["user_message"],
            state["context_data"]
        )
        
        # Use LLM-001 ChatService for completion
        response = await self.llm_service.chat_completion(
            message=state["user_message"],
            conversation_id=state["conversation_id"]
        )
        
        return {
            **state,
            "assistant_response": response.content,
            "workflow_steps": state["workflow_steps"] + ["Workbench chat completed"]
        }
        
    except Exception as e:
        return {
            **state,
            "current_error": f"Workbench chat failed: {str(e)}",
            "workflow_steps": state["workflow_steps"] + [f"Workbench error: {str(e)}"]
        }

async def _seo_coaching_node(self, state: WorkbenchState) -> WorkbenchState:
    """Handle SEO coaching mode with Dutch business context"""
    
    try:
        # Build Dutch coaching context
        coaching_context = self._build_seo_coaching_context(
            state["business_profile"],
            state["seo_analysis"],
            state["context_data"]
        )
        
        # Update conversation context for coaching
        await self.conversation_service.update_conversation_context(
            state["conversation_id"],
            coaching_context,
            ["seo_coaching", "business_profile"]
        )
        
        # Use Dutch SEO coaching model configuration
        dutch_config = self._get_dutch_coaching_config()
        
        # Generate coaching response
        response = await self.llm_service.chat_completion(
            message=state["user_message"],
            conversation_id=state["conversation_id"]
        )
        
        return {
            **state,
            "assistant_response": response.content,
            "coaching_context": coaching_context,
            "workflow_steps": state["workflow_steps"] + ["SEO coaching completed"]
        }
        
    except Exception as e:
        return {
            **state,
            "current_error": f"SEO coaching failed: {str(e)}",
            "workflow_steps": state["workflow_steps"] + [f"Coaching error: {str(e)}"]
        }
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/services/
├── langgraph_service.py     # Main LangGraph workflow orchestration
├── workflow_nodes.py        # Individual workflow node implementations
├── state_bridge.py          # Bridge between LangGraph and LLM-001B state
└── mode_handlers.py         # Mode-specific workflow logic

src/agent_workbench/models/
├── workflow_state.py        # LangGraph TypedDict state definitions
├── workflow_requests.py     # API request models for workflow execution
└── workflow_responses.py    # API response models for workflow results

src/agent_workbench/core/
├── workflow_builder.py      # Workflow construction utilities
└── state_utils.py          # State transformation utilities

src/agent_workbench/api/routes/
└── workflow.py             # Workflow execution endpoints
```

### Files to MODIFY:

```
src/agent_workbench/services/llm_service.py     # Integration with LangGraph workflows
src/agent_workbench/api/routes/chat.py          # Route through LangGraph workflows
src/agent_workbench/main.py                     # Add workflow service initialization
```

### Exact Function Signatures:

```python
# services/langgraph_service.py
class WorkbenchLangGraphService:
    def __init__(self, state_manager: StateManager, conversation_service: ConversationService, llm_service: ChatService)
    async def execute_workflow(self, request: WorkflowRequest) -> WorkflowResponse
    async def stream_workflow(self, request: WorkflowRequest) -> AsyncGenerator[WorkflowUpdate, None]
    def _build_workflow(self) -> StateGraph
    def _route_by_mode(self, state: WorkbenchState) -> str

# services/workflow_nodes.py
class WorkflowNodes:
    async def load_conversation_node(self, state: WorkbenchState) -> WorkbenchState
    async def process_message_node(self, state: WorkbenchState) -> WorkbenchState
    async def generate_response_node(self, state: WorkbenchState) -> WorkbenchState
    async def save_state_node(self, state: WorkbenchState) -> WorkbenchState
    async def handle_error_node(self, state: WorkbenchState) -> WorkbenchState
    async def workbench_chat_node(self, state: WorkbenchState) -> WorkbenchState
    async def seo_coaching_node(self, state: WorkbenchState) -> WorkbenchState

# services/state_bridge.py
class StateBridge:
    async def langgraph_to_conversation_state(self, lg_state: WorkbenchState) -> ConversationState
    async def conversation_to_langgraph_state(self, conv_state: ConversationState, user_message: str, mode: str) -> WorkbenchState
    async def merge_context_data(self, lg_context: Dict[str, Any], conv_context: Dict[str, Any]) -> Dict[str, Any]

# models/workflow_state.py
class WorkbenchState(TypedDict):
    conversation_id: UUID
    user_message: str
    assistant_response: Optional[str]
    model_config: ModelConfig
    provider_name: str
    context_data: Dict[str, Any]
    active_contexts: List[str]
    conversation_history: List[StandardMessage]
    workflow_mode: Literal["workbench", "seo_coach"]
    workflow_steps: List[str]
    current_operation: Optional[str]
    execution_successful: bool
    current_error: Optional[str]
    retry_count: int
    business_profile: Optional[Dict[str, Any]]
    seo_analysis: Optional[Dict[str, Any]]
    coaching_context: Optional[Dict[str, Any]]
    mcp_tools_active: List[str]
    agent_state: Optional[Dict[str, Any]]

class SEOCoachState(TypedDict):
    # Specialized state for SEO coaching workflows
    conversation_id: UUID
    business_profile: Dict[str, Any]
    website_url: str
    seo_analysis: Optional[Dict[str, Any]]
    recommendations: List[str]
    coaching_phase: Literal["analysis", "recommendations", "implementation", "monitoring"]
    user_message: str
    assistant_response: Optional[str]
    workflow_steps: List[str]

# models/workflow_requests.py
class WorkflowRequest(BaseModel):
    conversation_id: UUID
    user_message: str
    workflow_mode: Literal["workbench", "seo_coach"] = "workbench"
    model_config: Optional[ModelConfig] = None
    context_data: Dict[str, Any] = {}
    
    # SEO Coach specific
    business_profile: Optional[Dict[str, Any]] = None
    website_url: Optional[str] = None

class WorkflowResponse(BaseModel):
    conversation_id: UUID
    assistant_response: str
    workflow_mode: str
    execution_successful: bool
    workflow_steps: List[str]
    context_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

# API endpoints (workflow.py)
@router.post("/workflow/execute", response_model=WorkflowResponse)
async def execute_workflow(request: WorkflowRequest, service: WorkbenchLangGraphService = Depends(get_workflow_service))

@router.post("/workflow/stream")
async def stream_workflow(request: WorkflowRequest, service: WorkbenchLangGraphService = Depends(get_workflow_service))

# Enhanced chat endpoints (MODIFY chat.py)
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    # Route through LangGraph workflow instead of direct LLM service
    workflow_request = WorkflowRequest(
        conversation_id=request.conversation_id,
        user_message=request.message,
        workflow_mode=request.workflow_mode or "workbench"
    )
    workflow_response = await workflow_service.execute_workflow(workflow_request)
    
    return ChatResponse(
        content=workflow_response.assistant_response,
        conversation_id=workflow_response.conversation_id,
        model_used=workflow_response.metadata.get("model_used", "unknown")
    )
```

### Additional Dependencies:

```toml
# Existing LLM-001/001B dependencies (maintained)
langchain = "^0.3.0"
langchain-community = "^0.3.0"
langchain-openai = "^0.2.0"
langchain-ollama = "^0.1.0"
langchain-mistralai = "^0.1.0"
openai = "^1.6.0"
anthropic = "^0.8.0"
mistralai = "^1.0.0"
ollama = "^0.3.0"
httpx = "^0.25.0"
tenacity = "^8.2.0"
aiosqlite = "^0.19.0"
asyncpg = "^0.29.0"
structlog = "^23.2.0"

# LangGraph dependencies (NEW)
langgraph = "^0.2.0"              # Core LangGraph state management
langchain-core = "^0.3.0"         # Required for LangGraph integration

# Enhanced state management
redis = "^5.0.0"                  # Optional: Distributed state caching
```

### FORBIDDEN Actions:

- Replacing existing LLM-001/001B conversation persistence (integrate with it)
- Creating framework-agnostic alternatives to LangGraph
- Implementing MCP tool integration (Phase 2)
- Creating UI components or Gradio integration (UI-001)
- Adding document processing beyond context injection (Phase 2)
- Implementing vector embeddings or semantic search
- Adding authentication or user management

## Migration Strategy

### 1. Gradual Integration Approach

**Phase 1**: LangGraph wrapper around existing services
- Keep all LLM-001B functionality intact
- Route chat requests through simple LangGraph workflows
- Maintain database schema compatibility

**Phase 2**: Enhanced workflow capabilities
- Add MCP tool integration nodes
- Implement advanced routing and decision logic
- Expand state management for complex workflows

### 2. Backward Compatibility

**API Compatibility**:
```python
# Existing LLM-001B endpoints still work
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    # Internally routes through LangGraph but maintains same API contract
    pass

# LangGraph state automatically syncs with conversation state
async def sync_with_conversation_state(lg_state: WorkbenchState):
    # Bidirectional sync ensures no data loss
    pass
```

## Success Criteria

- [ ] LangGraph workflows execute successfully for both workbench and seo_coach modes
- [ ] Complete integration with existing LLM-001B conversation persistence
- [ ] No breaking changes to existing API endpoints
- [ ] State transitions work correctly with proper error handling
- [ ] Migration from LLM-001B to LangGraph state seamless
- [ ] Workflow execution completes in <3 seconds for simple chat
- [ ] >90% test coverage for all workflow nodes
- [ ] Backward compatibility maintained with LLM-001B functionality
- [ ] Foundation ready for Phase 2 MCP and agent integration