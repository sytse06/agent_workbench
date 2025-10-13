# LLM-001C: Unified Dual-Mode Workflow System

## Status

**Status**: Ready for Implementation  
**Date**: September 16, 2025  
**Decision Makers**: Human Architect  
**Task ID**: LLM-001C-unified-dual-mode-workflow  
**Dependencies**: LLM-001B (conversation persistence), CORE-002 (database extensions)

## Context

Consolidate workbench and seo_coach operational modes into a unified LangGraph-powered workflow system. Integrates completed LLM-001B conversation persistence with production-proven LangGraph state orchestration to support both technical AI development workflows and Dutch SEO business coaching through a single, consolidated service architecture.

## Architecture Scope

### What's Included:

- LangGraph workflow orchestration with production-proven TypedDict state models
- Complete preservation of LLM-001B conversation persistence and context injection
- Dual-mode operation supporting workbench and seo_coach workflows
- Bridge pattern between LLM-001B ConversationState and LangGraph WorkbenchState
- Mode-specific handlers for workbench (technical) and seo_coach (Dutch business) processing
- Enhanced database schema supporting business profiles and workflow execution tracking
- Migration utilities for upgrading from LLM-001B without data loss
- Streaming workflow execution with real-time step monitoring

### What's Explicitly Excluded:

- MCP tool integration (Phase 2)
- UI integration or Gradio components (UI-001C)
- Document processing beyond context injection (Phase 2)
- Vector embeddings or semantic search capabilities
- Authentication or user management
- Breaking changes to existing LLM-001B APIs

## Architectural Decisions

### 1. Consolidated Service Architecture

**Core Integration Pattern**: Bridge between LLM-001B persistence and LangGraph orchestration

```python
class ConsolidatedWorkbenchService:
    """Main service integrating LLM-001B persistence with LangGraph workflows"""
    
    def __init__(self):
        # Preserve all LLM-001B components
        self.state_manager = StateManager()  # From LLM-001B
        self.conversation_service = ConversationService()  # From LLM-001B
        self.context_service = ContextService()  # From LLM-001B
        self.llm_service = ChatService()  # From LLM-001
        
        # Add LangGraph orchestration
        self.workflow = self._build_consolidated_workflow()
        self.state_bridge = LangGraphStateBridge()
        
        # Add dual-mode support
        self.mode_detector = ModeDetector()
        self.mode_handlers = {
            "workbench": WorkbenchModeHandler(self.llm_service, self.context_service),
            "seo_coach": SEOCoachModeHandler(self.llm_service, self.context_service)
        }
```

### 2. LangGraph State Model

**Comprehensive TypedDict following GAIA agent patterns**:

```python
class WorkbenchState(TypedDict):
    # Core conversation state
    conversation_id: UUID
    user_message: str
    assistant_response: Optional[str]
    
    # Model and provider configuration
    model_config: ModelConfig
    provider_name: str
    
    # Context and conversation memory
    context_data: Dict[str, Any]
    active_contexts: List[str]
    conversation_history: List[StandardMessage]
    
    # Workflow orchestration
    workflow_mode: Literal["workbench", "seo_coach"]
    workflow_steps: List[str]
    current_operation: Optional[str]
    execution_successful: bool
    
    # Error handling and recovery
    current_error: Optional[str]
    retry_count: int
    
    # SEO Coach specific state
    business_profile: Optional[Dict[str, Any]]
    seo_analysis: Optional[Dict[str, Any]]
    coaching_context: Optional[Dict[str, Any]]
    coaching_phase: Optional[Literal["analysis", "recommendations", "implementation", "monitoring"]]
    
    # Workbench specific state
    debug_mode: Optional[bool]
    parameter_overrides: Optional[Dict[str, Any]]
    
    # Phase 2 extensions (empty for now)
    mcp_tools_active: List[str]
    agent_state: Optional[Dict[str, Any]]
    workflow_data: Optional[Dict[str, Any]]
```

### 3. State Bridge Architecture

**Bidirectional conversion between LLM-001B and LangGraph state**:

```python
class LangGraphStateBridge:
    """Bridge between LLM-001B ConversationState and LangGraph WorkbenchState"""
    
    def __init__(self, state_manager: StateManager, context_service: ContextService):
        self.state_manager = state_manager
        self.context_service = context_service
    
    async def load_into_langgraph_state(
        self, 
        conversation_id: UUID, 
        user_message: str,
        workflow_mode: str,
        business_profile: Optional[Dict[str, Any]] = None
    ) -> WorkbenchState:
        """Load LLM-001B conversation state into LangGraph format"""
        
        try:
            # Load existing conversation state
            conversation_state = await self.state_manager.load_conversation_state(conversation_id)
            
            # Convert to LangGraph state
            lg_state = WorkbenchState(
                conversation_id=conversation_id,
                user_message=user_message,
                assistant_response=None,
                
                # Preserve LLM-001B state
                model_config=conversation_state.model_config,
                provider_name=conversation_state.model_config.provider,
                context_data=conversation_state.context_data,
                active_contexts=conversation_state.active_contexts,
                conversation_history=conversation_state.messages,
                
                # Initialize workflow state
                workflow_mode=workflow_mode,
                workflow_steps=[],
                current_operation=None,
                execution_successful=True,
                current_error=None,
                retry_count=0,
                
                # Mode-specific initialization
                business_profile=business_profile,
                seo_analysis=None,
                coaching_context=None,
                coaching_phase=None,
                debug_mode=None,
                parameter_overrides=None,
                
                # Phase 2 placeholders
                mcp_tools_active=[],
                agent_state=None,
                workflow_data=None
            )
            
            return lg_state
            
        except Exception as e:
            # Create new conversation state
            return await self._create_new_langgraph_state(
                conversation_id, user_message, workflow_mode, business_profile
            )
    
    async def save_from_langgraph_state(self, lg_state: WorkbenchState) -> None:
        """Save LangGraph state back to LLM-001B persistence"""
        
        # Convert to LLM-001B ConversationState
        conversation_state = ConversationState(
            conversation_id=lg_state["conversation_id"],
            messages=lg_state["conversation_history"],
            model_config=lg_state["model_config"],
            context_data=lg_state["context_data"],
            active_contexts=lg_state["active_contexts"],
            metadata={
                "workflow_mode": lg_state["workflow_mode"],
                "execution_successful": lg_state["execution_successful"],
                "last_workflow_steps": lg_state["workflow_steps"],
                "business_profile": lg_state.get("business_profile")
            },
            updated_at=datetime.utcnow()
        )
        
        # Save using LLM-001B infrastructure
        await self.state_manager.save_conversation_state(conversation_state)
        
        # Save workflow execution record
        await self._save_workflow_execution(lg_state)
    
    async def _save_workflow_execution(self, lg_state: WorkbenchState) -> None:
        """Save workflow execution details for monitoring"""
        
        execution_record = WorkflowExecution(
            conversation_id=lg_state["conversation_id"],
            workflow_mode=lg_state["workflow_mode"],
            execution_steps=lg_state["workflow_steps"],
            execution_successful=lg_state["execution_successful"],
            error_details=lg_state.get("current_error"),
            created_at=datetime.utcnow()
        )
        
        # Save to database (implement in database service)
        await self.state_manager.save_workflow_execution(execution_record)
```

### 4. LangGraph Workflow Definition

**Consolidated workflow supporting both modes**:

```python
def _build_consolidated_workflow(self) -> StateGraph:
    """Build LangGraph workflow supporting both workbench and seo_coach modes"""
    
    builder = StateGraph(WorkbenchState)
    
    # Core workflow nodes
    builder.add_node("load_conversation", self._load_conversation_node)
    builder.add_node("validate_input", self._validate_input_node)
    builder.add_node("detect_intent", self._detect_intent_node)
    builder.add_node("process_workbench", self._process_workbench_node)
    builder.add_node("process_seo_coach", self._process_seo_coach_node)
    builder.add_node("generate_response", self._generate_response_node)
    builder.add_node("save_state", self._save_state_node)
    builder.add_node("handle_error", self._handle_error_node)
    
    # Workflow routing
    builder.add_edge(START, "load_conversation")
    builder.add_edge("load_conversation", "validate_input")
    builder.add_edge("validate_input", "detect_intent")
    
    # Conditional routing by mode
    builder.add_conditional_edges(
        "detect_intent",
        self._route_by_mode,
        {
            "workbench": "process_workbench",
            "seo_coach": "process_seo_coach",
            "error": "handle_error"
        }
    )
    
    # Both modes converge at response generation
    builder.add_edge("process_workbench", "generate_response")
    builder.add_edge("process_seo_coach", "generate_response")
    builder.add_edge("generate_response", "save_state")
    builder.add_edge("save_state", END)
    
    # Error handling
    builder.add_edge("handle_error", "save_state")
    
    return builder.compile()

def _route_by_mode(self, state: WorkbenchState) -> str:
    """Route workflow based on mode and validation"""
    
    if state.get("current_error"):
        return "error"
    
    workflow_mode = state["workflow_mode"]
    if workflow_mode in ["workbench", "seo_coach"]:
        return workflow_mode
    
    return "error"
```

### 5. Mode-Specific Handlers

**Workbench Mode Handler**:

```python
class WorkbenchModeHandler:
    """Handle workbench mode processing with technical capabilities"""
    
    def __init__(self, llm_service: ChatService, context_service: ContextService):
        self.llm_service = llm_service
        self.context_service = context_service
    
    async def process_message(self, state: WorkbenchState) -> WorkbenchState:
        """Process workbench mode message with full technical control"""
        
        try:
            # Apply parameter overrides if provided
            model_config = state["model_config"]
            if state.get("parameter_overrides"):
                model_config = self._apply_parameter_overrides(
                    model_config, state["parameter_overrides"]
                )
            
            # Process with technical context
            response = await self.llm_service.chat_completion(
                message=state["user_message"],
                conversation_id=state["conversation_id"]
            )
            
            # Add technical metadata
            technical_metadata = {
                "model_used": f"{model_config.provider}/{model_config.model_name}",
                "temperature": model_config.temperature,
                "max_tokens": model_config.max_tokens,
                "debug_mode": state.get("debug_mode", False)
            }
            
            return {
                **state,
                "assistant_response": response.content,
                "workflow_steps": state["workflow_steps"] + ["Workbench processing completed"],
                "context_data": {**state["context_data"], "technical_metadata": technical_metadata}
            }
            
        except Exception as e:
            return {
                **state,
                "current_error": f"Workbench processing failed: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state["workflow_steps"] + [f"Workbench error: {str(e)}"]
            }
```

**SEO Coach Mode Handler**:

```python
class SEOCoachModeHandler:
    """Handle SEO coach mode processing with Dutch business context"""
    
    def __init__(self, llm_service: ChatService, context_service: ContextService):
        self.llm_service = llm_service
        self.context_service = context_service
        self.dutch_prompts = DutchSEOPrompts()
    
    async def process_message(self, state: WorkbenchState) -> WorkbenchState:
        """Process SEO coaching message with Dutch business context"""
        
        try:
            # Build coaching context
            coaching_context = await self._build_coaching_context(state)
            
            # Update conversation context with coaching data
            await self.context_service.update_conversation_context(
                state["conversation_id"],
                coaching_context,
                ["seo_coaching", "business_profile"]
            )
            
            # Use Dutch SEO coaching configuration
            dutch_config = self._get_dutch_coaching_config(state)
            
            # Generate coaching response
            response = await self.llm_service.chat_completion(
                message=state["user_message"],
                conversation_id=state["conversation_id"]
            )
            
            return {
                **state,
                "assistant_response": response.content,
                "coaching_context": coaching_context,
                "workflow_steps": state["workflow_steps"] + ["SEO coaching completed"],
                "context_data": {**state["context_data"], "coaching_context": coaching_context}
            }
            
        except Exception as e:
            return {
                **state,
                "current_error": f"SEO coaching failed: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state["workflow_steps"] + [f"Coaching error: {str(e)}"]
            }
    
    async def _build_coaching_context(self, state: WorkbenchState) -> Dict[str, Any]:
        """Build Dutch coaching context from business profile and analysis"""
        
        business_profile = state.get("business_profile", {})
        seo_analysis = state.get("seo_analysis", {})
        
        return {
            "business_context": {
                "business_type": business_profile.get("business_type", "algemeen bedrijf"),
                "target_market": business_profile.get("target_market", "Nederland"),
                "experience_level": business_profile.get("seo_experience_level", "beginner")
            },
            "seo_context": seo_analysis,
            "coaching_phase": state.get("coaching_phase", "analysis"),
            "previous_recommendations": state.get("context_data", {}).get("recommendations", [])
        }
    
    def _get_dutch_coaching_config(self, state: WorkbenchState) -> ModelConfig:
        """Get Dutch SEO coaching model configuration"""
        
        return ModelConfig(
            provider="openrouter",
            model_name="openai/gpt-4o-mini",
            system_prompt=self.dutch_prompts.get_coaching_system_prompt(
                business_type=state.get("business_profile", {}).get("business_type", "algemeen")
            ),
            temperature=0.7,
            max_tokens=1500,
            streaming=True
        )
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/api/routes/
└── consolidated_chat.py        # Enhanced chat endpoints using consolidated service

tests/
├── unit/
│   ├── test_consolidated_service.py    # Unit tests for main service
│   ├── test_langgraph_bridge.py       # Bridge functionality tests
│   ├── test_mode_handlers.py          # Mode-specific handler tests
│   └── test_workflow_nodes.py         # Individual node tests
├── integration/
│   ├── test_workflow_execution.py     # End-to-end workflow tests
│   ├── test_dual_mode_operation.py    # Mode switching and routing tests
│   └── test_llm_001b_migration.py     # Migration compatibility tests
└── fixtures/
    ├── conversation_fixtures.py       # Test conversation data
    └── business_profile_fixtures.py   # SEO coach test data
```

### Files to MODIFY:

```
src/agent_workbench/services/llm_service.py     # Add mode-aware configuration loading
src/agent_workbench/models/conversation_state.py # Add workflow_mode and business_context fields
src/agent_workbench/main.py                     # Initialize consolidated service and routing
alembic/versions/                               # Database migration for new schema
```

### Exact Function Signatures:

```python
# services/consolidated_service.py
class ConsolidatedWorkbenchService:
    def __init__(self, 
                 state_manager: StateManager, 
                 conversation_service: ConversationService, 
                 context_service: ContextService,
                 llm_service: ChatService)
    
    async def execute_workflow(self, request: ConsolidatedWorkflowRequest) -> ConsolidatedWorkflowResponse
    async def stream_workflow(self, request: ConsolidatedWorkflowRequest) -> AsyncGenerator[WorkflowUpdate, None]
    async def get_conversation_state(self, conversation_id: UUID) -> WorkbenchState
    async def create_business_profile(self, profile_data: Dict[str, Any], conversation_id: UUID) -> UUID
    async def update_seo_analysis(self, conversation_id: UUID, analysis_data: Dict[str, Any]) -> None

# services/langgraph_bridge.py  
class LangGraphStateBridge:
    async def load_into_langgraph_state(self, conversation_id: UUID, user_message: str, workflow_mode: str, business_profile: Optional[Dict[str, Any]] = None) -> WorkbenchState
    async def save_from_langgraph_state(self, lg_state: WorkbenchState) -> None
    async def migrate_conversation_to_consolidated(self, conversation_id: UUID) -> WorkbenchState
    def _convert_messages_to_standard(self, messages: List[Any]) -> List[StandardMessage]
    def _convert_context_data(self, context: Dict[str, Any]) -> Dict[str, Any]

# services/workflow_orchestrator.py
class WorkflowOrchestrator:
    def _build_consolidated_workflow(self) -> StateGraph
    async def _load_conversation_node(self, state: WorkbenchState) -> WorkbenchState
    async def _validate_input_node(self, state: WorkbenchState) -> WorkbenchState
    async def _detect_intent_node(self, state: WorkbenchState) -> WorkbenchState
    async def _process_workbench_node(self, state: WorkbenchState) -> WorkbenchState
    async def _process_seo_coach_node(self, state: WorkbenchState) -> WorkbenchState
    async def _generate_response_node(self, state: WorkbenchState) -> WorkbenchState
    async def _save_state_node(self, state: WorkbenchState) -> WorkbenchState
    async def _handle_error_node(self, state: WorkbenchState) -> WorkbenchState
    def _route_by_mode(self, state: WorkbenchState) -> str

# services/mode_handlers.py
class WorkbenchModeHandler:
    async def process_message(self, state: WorkbenchState) -> WorkbenchState
    def _apply_parameter_overrides(self, config: ModelConfig, overrides: Dict[str, Any]) -> ModelConfig
    def _build_technical_context(self, state: WorkbenchState) -> Dict[str, Any]

class SEOCoachModeHandler:
    async def process_message(self, state: WorkbenchState) -> WorkbenchState
    async def _build_coaching_context(self, state: WorkbenchState) -> Dict[str, Any]
    def _get_dutch_coaching_config(self, state: WorkbenchState) -> ModelConfig
    async def _update_coaching_phase(self, state: WorkbenchState) -> WorkbenchState

# services/mode_detector.py
class ModeDetector:
    def detect_mode_from_environment(self) -> str
    def detect_mode_from_conversation(self, conversation_id: UUID) -> Optional[str]
    def detect_mode_from_request(self, request: Any) -> Optional[str]
    async def get_effective_mode(self, conversation_id: Optional[UUID] = None, requested_mode: Optional[str] = None) -> str

# models/consolidated_state.py
class WorkbenchState(TypedDict):
    # [Full TypedDict definition as shown above]

class ConsolidatedWorkflowRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    user_message: str = Field(..., min_length=1, max_length=10000)
    workflow_mode: Optional[Literal["workbench", "seo_coach"]] = None
    model_config: Optional[ModelConfig] = None
    parameter_overrides: Optional[Dict[str, Any]] = None
    business_profile: Optional[Dict[str, Any]] = None
    context_data: Optional[Dict[str, Any]] = None
    streaming: bool = False

class ConsolidatedWorkflowResponse(BaseModel):
    conversation_id: UUID
    assistant_response: str
    workflow_mode: str
    execution_successful: bool
    workflow_steps: List[str]
    context_data: Dict[str, Any]
    business_profile: Optional[Dict[str, Any]] = None
    coaching_context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}

class WorkflowUpdate(BaseModel):
    conversation_id: UUID
    current_step: str
    progress_percentage: float
    partial_response: Optional[str] = None
    workflow_steps: List[str]
    error: Optional[str] = None

# models/business_models.py
class BusinessProfile(BaseModel):
    id: Optional[UUID] = None
    conversation_id: UUID
    business_name: str = Field(..., min_length=1, max_length=255)
    website_url: str = Field(..., regex=r'^https?://.+')
    business_type: str = Field(..., max_length=100)
    target_market: str = Field(default="Nederland", max_length=100)
    seo_experience_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    created_at: Optional[datetime] = None

class SEOAnalysisContext(BaseModel):
    website_url: str
    analysis_timestamp: datetime
    technical_issues: List[Dict[str, Any]] = []
    content_recommendations: List[str] = []
    priority_score: int = Field(ge=0, le=100)
    recommendations: List[Dict[str, Any]] = []
    llmstxt_analysis: Optional[Dict[str, Any]] = None

class WorkflowExecution(BaseModel):
    id: Optional[UUID] = None
    conversation_id: UUID
    workflow_mode: str
    execution_steps: List[str]
    execution_successful: bool
    error_details: Optional[str] = None
    execution_duration_ms: Optional[int] = None
    created_at: Optional[datetime] = None

# core/dutch_prompts.py
class DutchSEOPrompts:
    @staticmethod
    def get_coaching_system_prompt(business_type: str = "algemeen") -> str
    
    @staticmethod
    def get_analysis_prompt(website_url: str, business_context: Dict[str, Any]) -> str
    
    @staticmethod
    def get_recommendations_prompt(analysis_results: Dict[str, Any], business_profile: Dict[str, Any]) -> str
    
    @staticmethod
    def get_implementation_guidance_prompt(recommendation: str, experience_level: str) -> str

# API endpoints (consolidated_chat.py)
@router.post("/chat/consolidated", response_model=ConsolidatedWorkflowResponse)
async def consolidated_chat(
    request: ConsolidatedWorkflowRequest,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service)
)

@router.post("/chat/consolidated/stream")
async def consolidated_chat_stream(
    request: ConsolidatedWorkflowRequest,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service)
)

@router.post("/seo/business-profile", response_model=BusinessProfile)
async def create_business_profile(
    profile: BusinessProfile,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service)
)

@router.put("/seo/analysis/{conversation_id}")
async def update_seo_analysis(
    conversation_id: UUID,
    analysis: SEOAnalysisContext,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service)
)

# Enhanced existing endpoints (MODIFY chat.py)
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    # Route through consolidated service while maintaining API compatibility
    consolidated_request = ConsolidatedWorkflowRequest(
        conversation_id=request.conversation_id,
        user_message=request.message,
        workflow_mode=request.workflow_mode or "workbench",
        model_config=request.model_config
    )
    
    consolidated_service = get_consolidated_service()
    workflow_response = await consolidated_service.execute_workflow(consolidated_request)
    
    return ChatResponse(
        content=workflow_response.assistant_response,
        conversation_id=workflow_response.conversation_id,
        model_used=f"consolidated-{workflow_response.workflow_mode}"
    )
```

### Database Migration (MODIFY alembic/versions/):

```python
"""Add consolidated LangGraph state support

Revision ID: llm_001c_consolidation
Revises: llm_001b_final
Create Date: 2025-09-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = 'llm_001c_consolidation'
down_revision = 'llm_001b_final'
branch_labels = None
depends_on = None

def upgrade():
    # Extend conversations table for dual-mode support
    op.add_column('conversations', sa.Column('workflow_mode', sa.String(20), default='workbench'))
    op.add_column('conversations', sa.Column('business_context', sa.JSON, nullable=True))
    op.add_column('conversations', sa.Column('seo_metadata', sa.JSON, nullable=True))
    
    # Create business_profiles table
    op.create_table('business_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('business_name', sa.String(255), nullable=False),
        sa.Column('website_url', sa.String(255), nullable=False),
        sa.Column('business_type', sa.String(100), nullable=False),
        sa.Column('target_market', sa.String(100), default='Nederland'),
        sa.Column('seo_experience_level', sa.String(50), default='beginner'),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # Create workflow_executions table
    op.create_table('workflow_executions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), sa.ForeignKey('conversations.id'), nullable=False),
        sa.Column('workflow_mode', sa.String(20), nullable=False),
        sa.Column('execution_steps', sa.JSON),
        sa.Column('execution_successful', sa.Boolean, default=True),
        sa.Column('error_details', sa.Text, nullable=True),
        sa.Column('execution_duration_ms', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    
    # Add indexes for performance
    op.create_index('idx_conversations_workflow_mode', 'conversations', ['workflow_mode'])
    op.create_index('idx_business_profiles_conversation', 'business_profiles', ['conversation_id'])
    op.create_index('idx_workflow_executions_conversation', 'workflow_executions', ['conversation_id'])
    op.create_index('idx_workflow_executions_mode', 'workflow_executions', ['workflow_mode'])

def downgrade():
    # Remove indexes
    op.drop_index('idx_workflow_executions_mode')
    op.drop_index('idx_workflow_executions_conversation')
    op.drop_index('idx_business_profiles_conversation')
    op.drop_index('idx_conversations_workflow_mode')
    
    # Drop tables
    op.drop_table('workflow_executions')
    op.drop_table('business_profiles')
    
    # Remove columns from conversations
    op.drop_column('conversations', 'seo_metadata')
    op.drop_column('conversations', 'business_context')
    op.drop_column('conversations', 'workflow_mode')
```

### Additional Dependencies:

```toml
# Existing LLM-001B dependencies (maintained)
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

# Enhanced validation and utilities
email-validator = "^2.1.0"        # For business profile validation
pydantic[dotenv] = "^2.5.0"       # Enhanced environment handling
```

### FORBIDDEN Actions:

- Breaking any existing LLM-001B API endpoints or contracts
- Removing or replacing LLM-001B conversation persistence infrastructure
- Implementing MCP tool integration (reserved for Phase 2)
- Creating UI components (reserved for UI-001C)
- Adding document processing beyond context injection
- Implementing vector embeddings or semantic search capabilities
- Adding authentication or user management systems

## Backward Compatibility Guarantees

### Existing LLM-001B API Contracts Preserved

**All existing endpoints maintain identical behavior:**

```python
# PRESERVED: Existing chat endpoint works exactly as before
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    # Internal routing through ConsolidatedWorkbenchService
    # BUT external behavior identical to LLM-001B
    pass

# PRESERVED: All conversation endpoints unchanged
@router.get("/conversations", response_model=List[ConversationSummary])
@router.post("/conversations", response_model=ConversationResponse) 
@router.delete("/conversations/{conversation_id}")
# All work identically to LLM-001B implementation

# PRESERVED: All context endpoints unchanged  
@router.put("/conversations/{conversation_id}/context")
@router.delete("/conversations/{conversation_id}/context")
@router.get("/conversations/{conversation_id}/context")
# All work identically to LLM-001B implementation
```

### Database Schema Backward Compatibility

**Zero breaking changes to existing schema:**
- All existing `conversations` table columns preserved
- All existing `messages` table structure unchanged
- All existing `conversation_states` table preserved
- New columns added with `DEFAULT` values or `nullable=True`
- Existing queries continue to work without modification

### Service Layer Compatibility

**LLM-001B services remain functional:**
```python
# PRESERVED: All LLM-001B classes work unchanged
state_manager = StateManager()  # Identical behavior
conversation_service = ConversationService()  # Identical behavior  
context_service = ContextService()  # Identical behavior
llm_service = ChatService()  # Identical behavior

# NEW: ConsolidatedWorkbenchService uses these internally
# but doesn't replace or break them
```

### Data Migration Guarantee

**Existing conversation data remains accessible:**
- All existing conversation histories load correctly
- All existing context data preserved
- All existing model configurations work unchanged
- No data transformation or migration required for existing conversations

### API Response Format Guarantee

**Existing response structures unchanged:**
```python
# LLM-001B ChatResponse format preserved exactly
class ChatResponse(BaseModel):
    content: str                    # UNCHANGED
    conversation_id: UUID          # UNCHANGED 
    message_count: int             # UNCHANGED
    model_used: str                # UNCHANGED
    metadata: Optional[Dict] = None # UNCHANGED
    
# New fields only added to new ConsolidatedWorkflowResponse
# Existing endpoints return identical response structures
```

### Client Code Compatibility

**Zero changes required for existing client code:**
```python
# Existing client code continues to work identically
import httpx

client = httpx.AsyncClient()

# This exact code works before and after LLM-001C
response = await client.post("/chat", json={
    "message": "Hello",
    "conversation_id": "existing-uuid"
})

# Response format identical to LLM-001B
chat_response = ChatResponse(**response.json())
```

### Migration Path Guarantee

**Non-breaking deployment:**
1. **Database Migration**: Adds new tables/columns without touching existing data
2. **Service Addition**: ConsolidatedWorkbenchService added alongside LLM-001B services
3. **API Extension**: New endpoints added without modifying existing endpoints
4. **Gradual Adoption**: Clients can migrate to new endpoints when ready

### Rollback Safety

**Complete rollback capability:**
```sql
-- If needed, LLM-001C can be completely removed by:
DROP TABLE workflow_executions;
DROP TABLE business_profiles;  
ALTER TABLE conversations DROP COLUMN workflow_mode;
ALTER TABLE conversations DROP COLUMN business_context;
ALTER TABLE conversations DROP COLUMN seo_metadata;

-- System returns to exact LLM-001B state
```

### Testing Guarantee

**Existing tests pass unchanged:**
- All LLM-001B unit tests continue to pass
- All LLM-001B integration tests work identically
- No test modifications required for backward compatibility
- New tests added only for new functionality

### Phase 1: Non-Breaking Integration (Days 1-3)
1. **Database Migration**: Run Alembic migration to add new tables and columns
2. **Service Registration**: Add ConsolidatedWorkbenchService to dependency injection
3. **API Extension**: Add new `/chat/consolidated` endpoints alongside existing endpoints
4. **Backward Compatibility**: Ensure all existing LLM-001B endpoints work unchanged

### Phase 2: Bridge Implementation (Days 4-6)
1. **State Bridge**: Implement bidirectional conversion between LLM-001B and LangGraph state
2. **Mode Detection**: Add environment and request-based mode detection
3. **Workflow Definition**: Implement LangGraph workflow with conditional routing
4. **Error Handling**: Add comprehensive error handling and recovery

### Phase 3: Mode Handlers (Days 7-10)
1. **Workbench Handler**: Implement technical mode with parameter control
2. **SEO Coach Handler**: Implement Dutch coaching with business context
3. **Dutch Prompts**: Create comprehensive Dutch SEO coaching templates
4. **Business Profiles**: Implement business profile creation and management

## Success Criteria

### Technical Integration
- [ ] All existing LLM-001B functionality preserved with zero breaking changes
- [ ] LangGraph workflows execute successfully for both workbench and seo_coach modes
- [ ] Database migration completes without data loss or downtime
- [ ] State bridge maintains perfect bidirectional synchronization
- [ ] Workflow execution completes in <3 seconds for simple interactions

### Mode-Specific Functionality
- [ ] Workbench mode provides full technical control and debugging capabilities
- [ ] SEO Coach mode provides natural Dutch business coaching experience
- [ ] Business profile creation and management works correctly
- [ ] Mode detection automatically routes to appropriate workflows
- [ ] Context injection works seamlessly in both modes

### Quality and Reliability
- [ ] >95% test coverage for all new components
- [ ] Error handling provides appropriate feedback for both user types
- [ ] Workflow steps are tracked and displayed correctly
- [ ] Performance benchmarks met for all workflow operations
- [ ] Migration from LLM-001B requires zero manual intervention

This comprehensive LLM-001C specification consolidates all architectural requirements while preserving completed work and providing a clear implementation path./services/
├── consolidated_service.py      # Main ConsolidatedWorkbenchService
├── langgraph_bridge.py         # LangGraphStateBridge implementation
├── workflow_orchestrator.py    # LangGraph workflow definition
├── mode_handlers.py            # WorkbenchModeHandler and SEOCoachModeHandler
├── mode_detector.py            # APP_MODE detection and routing logic
└── workflow_nodes.py           # Individual workflow node implementations

src/agent_workbench/models/
├── consolidated_state.py       # WorkbenchState TypedDict and related models
├── business_models.py          # BusinessProfile, SEOAnalysisContext models
├── workflow_models.py          # WorkflowExecution, WorkflowRequest/Response models
├── mode_configs.py            # DutchSEOConfig, WorkbenchConfig
└── consolidated_requests.py    # Enhanced API request models

src/agent_workbench/core/
├── dutch_prompts.py            # Dutch SEO coaching prompt templates
├── workflow_utils.py           # Workflow construction and state utilities
└── migration_utils.py          # LLM-001B to LLM-001C migration utilities

src/agent_workbench