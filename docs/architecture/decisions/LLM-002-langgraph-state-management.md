# LLM-002: LangGraph State Management Integration (Revised)

## Status

**Status**: Ready for Implementation  
**Date**: September 18, 2025  
**Decision Makers**: Human Architect  
**Task ID**: LLM-002-langgraph-state-management  
**Dependencies**: LLM-001 (LangChain foundation), LLM-001B (conversation state), CORE-002 (database schema)

## Context

Replace the framework-agnostic state management approach with production-proven LangGraph state orchestration, following patterns validated in the GAIA agent implementation. Provides robust workflow orchestration, persistent state management, and foundation for advanced agent workflows while maintaining **complete backward compatibility** with existing LLM-001B conversation persistence and API contracts.

## Architecture Scope

### What's Included:

- LangGraph StateGraph for workflow orchestration and state management
- Integration with existing `consolidated_state.py` WorkbenchState model
- Enhancement of existing `langgraph_bridge.py` for workflow integration
- Workflow nodes for chat completion, context injection, and state persistence
- Transparent routing of existing `/chat` endpoints through LangGraph workflows
- Error handling and retry logic within LangGraph workflows
- Foundation for Phase 2 MCP tool integration and agent workflows
- Complete backward compatibility - no API changes required

### What's Explicitly Excluded:

- New API endpoints or breaking changes to existing APIs
- SEO Coach specific functionality (stubbed for Phase 2 implementation)
- MCP tool integration or agent workflows (Phase 2)
- Document processing logic beyond context injection (Phase 2)
- Vector embeddings or semantic search capabilities
- Authentication or user management
- Modifications to existing state models in `consolidated_state.py`

## Architectural Decisions

### 1. Transparent Integration Strategy

**Core Philosophy**: Existing API consumers should experience no changes while gaining LangGraph benefits internally

```python
# BEFORE LLM-002: Direct LLM service call
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    response = await llm_service.chat_completion(request.message, request.conversation_id)
    return ChatResponse(content=response.content, conversation_id=response.conversation_id)

# AFTER LLM-002: Transparent LangGraph routing
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    # Internally routes through LangGraph workflow - same API contract
    workflow_response = await langgraph_service.execute_chat_workflow(request)
    return ChatResponse(content=workflow_response.content, conversation_id=workflow_response.conversation_id)
```

### 2. LangGraph Integration with Existing State

**Use Existing `consolidated_state.py` as Source of Truth**:
```python
# services/langgraph_service.py
from agent_workbench.models.consolidated_state import WorkbenchState

class WorkbenchLangGraphService:
    def __init__(self, 
                 state_bridge: LangGraphStateBridge,  # Enhanced existing bridge
                 llm_service: ChatService,            # From LLM-001
                 context_service: ContextService):    # From LLM-001B
        self.state_bridge = state_bridge
        self.llm_service = llm_service
        self.context_service = context_service
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow using existing WorkbenchState"""
        builder = StateGraph(dict)  # Use dict to align with existing WorkbenchState
        
        # Core workflow nodes
        builder.add_node("load_conversation", self._load_conversation_node)
        builder.add_node("process_message", self._process_message_node)
        builder.add_node("generate_response", self._generate_response_node)
        builder.add_node("save_state", self._save_state_node)
        builder.add_node("handle_error", self._handle_error_node)
        
        # Workflow routing
        builder.add_edge(START, "load_conversation")
        builder.add_edge("load_conversation", "process_message")
        builder.add_edge("process_message", "generate_response")
        builder.add_edge("generate_response", "save_state")
        builder.add_edge("save_state", END)
        
        # Error handling
        builder.add_edge("handle_error", END)
        
        return builder.compile()
```

### 3. Enhanced Bridge Integration

**Extend Existing `langgraph_bridge.py` for Workflow Support**:
```python
# services/langgraph_bridge.py (ENHANCED)
class LangGraphStateBridge:
    # Keep all existing methods
    
    # NEW: Workflow integration methods
    async def prepare_for_workflow(self, 
                                 consolidated_state: ConsolidatedState, 
                                 user_message: str) -> Dict[str, Any]:
        """Convert ConsolidatedState to LangGraph workflow state"""
        
        workflow_state = {
            "conversation_id": consolidated_state.conversation_id,
            "user_message": user_message,
            "assistant_response": None,
            "model_config": consolidated_state.model_config.dict(),
            "provider_name": consolidated_state.provider_name,
            "context_data": consolidated_state.context_data,
            "active_contexts": consolidated_state.active_contexts,
            "conversation_history": [msg.dict() for msg in consolidated_state.messages],
            "workflow_mode": consolidated_state.coaching_phase or "workbench",
            "workflow_steps": [],
            "current_operation": None,
            "execution_successful": True,
            "current_error": None,
            "retry_count": 0,
            "debug_mode": consolidated_state.debug_mode,
            "parameter_overrides": consolidated_state.parameter_overrides,
            "workflow_data": consolidated_state.workflow_data or {}
        }
        
        return workflow_state
    
    async def extract_from_workflow(self, workflow_state: Dict[str, Any]) -> ConsolidatedState:
        """Convert LangGraph workflow state back to ConsolidatedState"""
        
        # Convert back to ConsolidatedState format
        messages = [StandardMessage(**msg) for msg in workflow_state["conversation_history"]]
        
        # Add assistant response if generated
        if workflow_state.get("assistant_response"):
            messages.append(StandardMessage(
                role="assistant",
                content=workflow_state["assistant_response"],
                timestamp=datetime.utcnow()
            ))
        
        return ConsolidatedState(
            conversation_id=workflow_state["conversation_id"],
            messages=messages,
            model_config=ModelConfig(**workflow_state["model_config"]),
            provider_name=workflow_state["provider_name"],
            context_data=workflow_state["context_data"],
            active_contexts=workflow_state["active_contexts"],
            coaching_phase=workflow_state.get("workflow_mode"),
            debug_mode=workflow_state.get("debug_mode", False),
            parameter_overrides=workflow_state.get("parameter_overrides", {}),
            workflow_data=workflow_state.get("workflow_data", {}),
            updated_at=datetime.utcnow()
        )
```

### 4. Workflow Node Implementation

**Core Workflow Nodes**:
```python
# services/workflow_nodes.py
class WorkflowNodes:
    def __init__(self, state_bridge: LangGraphStateBridge, 
                 llm_service: ChatService, 
                 context_service: ContextService):
        self.state_bridge = state_bridge
        self.llm_service = llm_service
        self.context_service = context_service

    async def load_conversation_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Load conversation state from existing LLM-001B persistence layer"""
        
        conversation_id = state["conversation_id"]
        
        try:
            # Load from existing ConsolidatedState persistence
            consolidated_state = await self.context_service.get_conversation_state(conversation_id)
            
            # Merge with workflow state
            state.update({
                "conversation_history": [msg.dict() for msg in consolidated_state.messages],
                "context_data": consolidated_state.context_data,
                "active_contexts": consolidated_state.active_contexts,
                "workflow_steps": state["workflow_steps"] + ["Conversation state loaded"]
            })
            
            return state
            
        except Exception as e:
            return {
                **state,
                "current_error": f"Failed to load conversation: {str(e)}",
                "workflow_steps": state["workflow_steps"] + [f"Error loading conversation: {str(e)}"]
            }

    async def process_message_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process user message with context awareness"""
        
        try:
            # Add current message to conversation history
            user_message = StandardMessage(
                role="user",
                content=state["user_message"],
                timestamp=datetime.utcnow()
            )
            
            state["conversation_history"].append(user_message.dict())
            state["workflow_steps"].append("Message processed")
            
            return state
            
        except Exception as e:
            return {
                **state,
                "current_error": f"Failed to process message: {str(e)}",
                "workflow_steps": state["workflow_steps"] + [f"Process error: {str(e)}"]
            }

    async def generate_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response using existing LLM-001 ChatService"""
        
        try:
            # Use existing LLM service for chat completion
            chat_request = ChatRequest(
                message=state["user_message"],
                conversation_id=UUID(state["conversation_id"])
            )
            
            response = await self.llm_service.chat_completion(
                message=chat_request.message,
                conversation_id=chat_request.conversation_id
            )
            
            return {
                **state,
                "assistant_response": response.content,
                "workflow_steps": state["workflow_steps"] + ["Response generated"]
            }
            
        except Exception as e:
            return {
                **state,
                "current_error": f"Response generation failed: {str(e)}",
                "workflow_steps": state["workflow_steps"] + [f"Generation error: {str(e)}"]
            }

    async def save_state_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Save state back to existing LLM-001B persistence"""
        
        try:
            # Convert workflow state back to ConsolidatedState
            consolidated_state = await self.state_bridge.extract_from_workflow(state)
            
            # Save using existing context service
            await self.context_service.update_conversation_state(
                state["conversation_id"],
                consolidated_state.context_data,
                consolidated_state.active_contexts
            )
            
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

    async def handle_error_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow errors with retry logic"""
        
        error_msg = state.get("current_error", "Unknown error")
        retry_count = state.get("retry_count", 0)
        
        if retry_count < 3:  # Max 3 retries
            return {
                **state,
                "retry_count": retry_count + 1,
                "current_error": None,  # Clear error for retry
                "workflow_steps": state["workflow_steps"] + [f"Retrying after error: {error_msg}"]
            }
        else:
            return {
                **state,
                "execution_successful": False,
                "workflow_steps": state["workflow_steps"] + [f"Max retries exceeded: {error_msg}"]
            }

    # SEO Coach functionality - STUBBED for Phase 2
    async def seo_coaching_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """SEO coaching workflow - Phase 2 implementation"""
        raise NotImplementedError("SEO coaching workflow will be implemented in Phase 2")
    
    def _build_seo_coaching_context(self, business_profile: Dict, seo_analysis: Dict, context: Dict) -> Dict:
        """Build Dutch coaching context - Phase 2 implementation"""
        raise NotImplementedError("SEO coaching context building will be implemented in Phase 2")
    
    def _get_dutch_coaching_config(self) -> ModelConfig:
        """Get Dutch SEO coaching model configuration - Phase 2 implementation"""
        raise NotImplementedError("Dutch coaching configuration will be implemented in Phase 2")
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/services/
├── langgraph_service.py     # Main LangGraph workflow orchestration
└── workflow_nodes.py        # Individual workflow node implementations
```

### Files to MODIFY:

```
src/agent_workbench/services/langgraph_bridge.py    # ENHANCE: Add workflow integration methods
src/agent_workbench/api/routes/chat.py              # MODIFY: Route through LangGraph internally
src/agent_workbench/main.py                         # MODIFY: Add workflow service initialization
```

### Files to PRESERVE (No Changes):

```
src/agent_workbench/models/consolidated_state.py    # Use as-is (source of truth)
src/agent_workbench/services/context_service.py     # Use existing methods
src/agent_workbench/services/llm_service.py         # Use existing chat completion
```

### Exact Function Signatures:

```python
# services/langgraph_service.py (NEW)
class WorkbenchLangGraphService:
    def __init__(self, 
                 state_bridge: LangGraphStateBridge,
                 llm_service: ChatService,
                 context_service: ContextService)
    
    async def execute_chat_workflow(self, request: ChatRequest) -> ChatResponse
    async def stream_chat_workflow(self, request: ChatRequest) -> AsyncGenerator[str, None]
    def _build_workflow(self) -> StateGraph
    def _create_initial_state(self, request: ChatRequest) -> Dict[str, Any]

# services/workflow_nodes.py (NEW)
class WorkflowNodes:
    def __init__(self, state_bridge: LangGraphStateBridge, llm_service: ChatService, context_service: ContextService)
    
    async def load_conversation_node(self, state: Dict[str, Any]) -> Dict[str, Any]
    async def process_message_node(self, state: Dict[str, Any]) -> Dict[str, Any]
    async def generate_response_node(self, state: Dict[str, Any]) -> Dict[str, Any]
    async def save_state_node(self, state: Dict[str, Any]) -> Dict[str, Any]
    async def handle_error_node(self, state: Dict[str, Any]) -> Dict[str, Any]
    
    # Phase 2 stubs
    async def seo_coaching_node(self, state: Dict[str, Any]) -> Dict[str, Any]  # raises NotImplementedError

# services/langgraph_bridge.py (ENHANCE EXISTING)
class LangGraphStateBridge:
    # Keep all existing methods unchanged
    
    # ADD new methods:
    async def prepare_for_workflow(self, consolidated_state: ConsolidatedState, user_message: str) -> Dict[str, Any]
    async def extract_from_workflow(self, workflow_state: Dict[str, Any]) -> ConsolidatedState
    def merge_workflow_context(self, base_context: Dict, workflow_context: Dict) -> Dict

# api/routes/chat.py (MODIFY EXISTING)
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    # Change implementation to route through LangGraph workflow
    # Keep exact same API contract
    
@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    # Change implementation to route through LangGraph streaming
    # Keep exact same streaming contract
```

### Additional Dependencies:

```toml
# LangGraph dependencies (ADD to existing)
langgraph = "^0.2.0"              # Core LangGraph state management
langchain-core = "^0.3.0"         # Required for LangGraph integration (may already exist)

# All existing dependencies maintained unchanged
```

### FORBIDDEN Actions:

- Creating new API endpoints or changing existing API contracts
- Modifying existing state models in `consolidated_state.py`
- Implementing SEO Coach functionality beyond stubs
- Adding MCP tool integration (Phase 2)
- Creating new UI components (UI-001)
- Adding document processing beyond existing context injection
- Changing existing database schemas or migrations
- Modifying existing LLM service interfaces

## Migration Strategy

### 1. Internal Refactoring Only

**Zero API Changes**:
- All existing `/chat` endpoints work identically
- Same request/response formats
- Same error handling behavior
- Same performance characteristics

**Internal Workflow**:
```python
# Before: Direct service call
async def chat_completion(request: ChatRequest):
    response = await llm_service.chat_completion(request.message, request.conversation_id)
    return ChatResponse(content=response.content, conversation_id=response.conversation_id)

# After: LangGraph workflow (transparent to API consumer)
async def chat_completion(request: ChatRequest):
    workflow_response = await langgraph_service.execute_chat_workflow(request)
    return ChatResponse(content=workflow_response.content, conversation_id=workflow_response.conversation_id)
```

### 2. State Persistence Continuity

**Seamless State Transition**:
```python
# Existing ConsolidatedState continues to work
# LangGraph workflow state converts to/from ConsolidatedState
# No data migration required
# All existing conversation history preserved
```

### 3. Error Handling Consistency

**Maintain Existing Error Patterns**:
- Same exception types thrown
- Same error message formats
- Same HTTP status codes
- Same retry behavior

## Success Criteria

### Functional Requirements:
- [ ] All existing `/chat` API tests pass without modification
- [ ] LangGraph workflows execute successfully for chat completion
- [ ] Complete integration with existing `consolidated_state.py`
- [ ] State conversion between workflow and ConsolidatedState works correctly
- [ ] Error handling maintains existing behavior patterns
- [ ] No breaking changes to any existing API contracts

### Performance Requirements:
- [ ] Chat completion performance within 10% of pre-LangGraph timing
- [ ] Memory usage increase <20% over existing implementation
- [ ] Workflow execution completes in <3 seconds for simple chat
- [ ] State persistence latency unchanged

### Quality Requirements:
- [ ] >90% test coverage for all new workflow components
- [ ] All existing integration tests continue to pass
- [ ] Phase 2 stubs properly documented and marked for future implementation
- [ ] Error scenarios handled gracefully with proper logging

### Compatibility Requirements:
- [ ] Zero API consumer impact - existing clients work unchanged
- [ ] All existing conversation data remains accessible
- [ ] Database schema requires no changes
- [ ] Deployment process remains identical

## Phase 2 Preparation

### Foundation for Future Features:
- LangGraph workflow architecture ready for MCP tool integration
- Node-based system easily extensible for agent workflows  
- State management supports complex multi-step operations
- SEO Coach functionality stubbed and ready for implementation

### Stubbed Components Ready for Phase 2:
- `seo_coaching_node()` - Raises NotImplementedError with clear message
- `_build_seo_coaching_context()` - Stubbed for Dutch business context
- `_get_dutch_coaching_config()` - Stubbed for specialized model configuration
- MCP tool integration points identified in workflow structure