# Agentic System Object Model

**Purpose:** Foundation objects for building multi-agent systems
**Date:** 2025-10-05
**Status:** Core objects identified, ready for agentic expansion

---

## 🎯 Executive Summary

The codebase contains **7 core domain objects** that form the foundation for an agentic system:

1. **Message** - Atomic communication unit
2. **Conversation** - Message container with lifecycle
3. **State** - Conversation memory and context
4. **Workflow** - Multi-step execution orchestration
5. **Context** - External knowledge injection
6. **Agent/Tool** - Action executors (future)
7. **Bridge** - State format converters

These objects are currently implemented for **dual-mode chat** (Workbench + SEO Coach) but are designed to scale to **multi-agent workflows**.

---

## 📊 Core Domain Objects

### 1. MESSAGE 💬

**Purpose:** Atomic unit of communication in conversations

#### Variants

##### A. StandardMessage (Pydantic)
```python
Location: models/standard_messages.py:19

class StandardMessage:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
```

**Usage:**
- In-memory message representation
- LangChain conversion
- State persistence

##### B. MessageModel (SQLAlchemy)
```python
Location: models/database.py:95

class MessageModel(Base):
    id: UUID (PK)
    conversation_id: UUID (FK)
    role: String  # user/assistant/system
    content: Text
    timestamp: DateTime
    metadata: JSON
```

**Usage:**
- Database persistence (SQLite)
- Legacy storage format

##### C. MessageSchema (Pydantic)
```python
Location: models/schemas.py:94

class MessageSchema:
    # Factory methods:
    @classmethod
    def for_create(conversation_id, role, content, metadata)
    @classmethod
    def for_update()

    # Conversion methods:
    def to_db_dict()
    def to_response_dict()
```

**Usage:**
- API request/response
- Validation layer

#### Key Characteristics

**Roles Supported:**
- `user` - Human input
- `assistant` - LLM output
- `system` - System prompts
- `tool` - Tool execution results

**Tool Support:**
```python
# Supports function calling
tool_calls: Optional[List[Dict]]  # Outgoing tool calls
tool_call_id: Optional[str]       # Tool response reference
```

**Metadata Examples:**
```python
metadata = {
    "model": "anthropic/claude-3.5-sonnet",
    "tokens": 150,
    "latency_ms": 1200,
    "tool_name": "web_search",
    "confidence": 0.95
}
```

---

### 2. CONVERSATION 💬📦

**Purpose:** Container for messages with lifecycle management

#### Variants

##### A. ConversationModel (SQLAlchemy)
```python
Location: models/database.py:35

class ConversationModel(Base, TimestampMixin):
    id: UUID (PK)
    mode: String              # "workbench" or "seo_coach"
    title: String
    metadata: JSON
    created_at: DateTime      # From TimestampMixin
    updated_at: DateTime      # From TimestampMixin
```

**Usage:**
- Database persistence
- CRUD operations

##### B. ConversationSchema (Pydantic)
```python
Location: models/schemas.py:42

class ConversationSchema:
    # Factory methods:
    @classmethod
    def for_create() -> ConversationSchema
    @classmethod
    def for_update() -> ConversationSchema

    # Conversion:
    def to_db_dict() -> Dict
    def to_response_dict() -> Dict
```

**Usage:**
- API layer
- Data transfer

##### C. ConversationResponse (Pydantic)
```python
Location: models/consolidated_state.py:118

class ConversationResponse:
    id: UUID
    title: str
    workflow_mode: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    is_temporary: bool = False
```

**Usage:**
- API responses
- UI display

#### Conversation Lifecycle

```
CREATE → ACTIVE → PAUSED → ARCHIVED → DELETED
          ↓
       FORKED (future multi-agent)
```

**Current Operations:**
```python
# Via StateManager (state_manager.py:17)
async def create_conversation(model_config, title, is_temporary) -> UUID
async def load_conversation_state(conversation_id) -> ConversationState
async def save_conversation_state(state) -> None
async def delete_conversation(conversation_id) -> bool
async def list_conversations(limit=50) -> List[Dict]
async def migrate_conversation_to_stateful(conversation_id) -> ConversationState
```

#### Metadata Structure
```python
metadata = {
    "mode": "workbench",           # or "seo_coach"
    "is_temporary": false,
    "created_at": "2025-10-05T...",
    "tags": ["technical", "debug"],
    "parent_conversation_id": null, # For forked convos (future)
    "agent_participants": []        # Future multi-agent
}
```

---

### 3. STATE 🧠

**Purpose:** Conversation memory, context, and execution state

#### Variants

##### A. ConversationState (Pydantic)
```python
Location: models/standard_messages.py:30

class ConversationState:
    conversation_id: UUID
    messages: List[StandardMessage]
    llm_config: ModelConfig
    context_data: Dict[str, Any]
    active_contexts: List[str]
    metadata: Dict[str, Any]
    updated_at: datetime
```

**Usage:**
- Unified state representation
- Persistence format
- State manager operations

**Example:**
```python
state = ConversationState(
    conversation_id=UUID("..."),
    messages=[
        StandardMessage(role="user", content="Hello"),
        StandardMessage(role="assistant", content="Hi!")
    ],
    llm_config=ModelConfig(provider="openrouter", ...),
    context_data={
        "user_timezone": "Europe/Amsterdam",
        "recent_topics": ["Python", "AI"]
    },
    active_contexts=["user_profile", "project_context"],
    metadata={
        "session_start": "2025-10-05T10:00:00Z",
        "interaction_count": 5
    },
    updated_at=datetime.utcnow()
)
```

##### B. WorkbenchState (TypedDict - LangGraph)
```python
Location: models/consolidated_state.py:14

class WorkbenchState(TypedDict):
    # Core conversation
    conversation_id: UUID
    user_message: str
    assistant_response: Optional[str]

    # Model config
    model_config: ModelConfig
    provider_name: str

    # Memory & context
    context_data: Dict[str, Any]
    active_contexts: List[str]
    conversation_history: List[StandardMessage]

    # Workflow orchestration
    workflow_mode: Literal["workbench", "seo_coach"]
    workflow_steps: List[str]
    current_operation: Optional[str]
    execution_successful: bool

    # Error handling
    current_error: Optional[str]
    retry_count: int

    # Mode-specific state
    business_profile: Optional[Dict[str, Any]]       # SEO coach
    seo_analysis: Optional[Dict[str, Any]]           # SEO coach
    coaching_context: Optional[Dict[str, Any]]       # SEO coach
    coaching_phase: Optional[Literal[...]]           # SEO coach
    debug_mode: Optional[bool]                       # Workbench
    parameter_overrides: Optional[Dict[str, Any]]    # Workbench

    # Phase 2 extensions (agentic)
    mcp_tools_active: List[str]
    agent_state: Optional[Dict[str, Any]]
    workflow_data: Optional[Dict[str, Any]]
```

**Usage:**
- LangGraph workflow execution
- Multi-step orchestration
- Stateful workflow management

**Example:**
```python
lg_state: WorkbenchState = {
    "conversation_id": UUID("..."),
    "user_message": "Analyze this code",
    "assistant_response": None,  # Will be filled
    "model_config": ModelConfig(...),
    "provider_name": "anthropic",
    "context_data": {"repo": "agent_workbench"},
    "active_contexts": ["codebase"],
    "conversation_history": [...],
    "workflow_mode": "workbench",
    "workflow_steps": [
        "Parse user intent",
        "Load codebase context",
        "Analyze code",
        "Generate response"
    ],
    "current_operation": "Analyze code",  # Current step
    "execution_successful": True,
    "current_error": None,
    "retry_count": 0,
    # Agentic extensions
    "mcp_tools_active": ["github", "filesystem"],
    "agent_state": {
        "current_file": "main.py",
        "analysis_depth": 2
    },
    "workflow_data": {...}
}
```

##### C. ConversationStateDB (SQLAlchemy)
```python
Location: models/conversation_state.py:11

class ConversationStateDB(Base):
    __tablename__ = "conversation_states"

    conversation_id: UUID (PK, FK)
    state_data: JSON              # Full ConversationState
    context_data: JSON            # Denormalized for queries
    active_contexts: JSON         # Array of context names
    updated_at: DateTime
    version: Integer = 1          # State versioning
```

**Usage:**
- Database persistence
- State history (via versioning)

#### State Management Operations

```python
# StateManager (services/state_manager.py:17)
class StateManager:
    async def load_conversation_state(conversation_id) -> ConversationState
    async def save_conversation_state(state: ConversationState) -> None
    async def migrate_conversation_to_stateful(conversation_id) -> ConversationState

    # Private helpers
    def _serialize_message(msg: StandardMessage) -> Dict
    def _serialize_metadata(metadata: Dict) -> Dict
```

#### State Transitions

```
Initial State → User Message → Processing → Response Generated → State Updated
      ↓                ↓             ↓              ↓                  ↓
  Version 1       Version 2    Version 3      Version 4         Version 5
```

**State Versioning** (future):
- Track conversation evolution
- Enable rollback
- Audit trail for multi-agent decisions

---

### 4. WORKFLOW 🔄

**Purpose:** Multi-step execution orchestration with error handling

#### Core Components

##### A. WorkflowOrchestrator
```python
Location: services/workflow_orchestrator.py

class WorkflowOrchestrator:
    # Orchestrates multi-step workflows
    # Manages workflow execution
    # Handles step transitions
```

##### B. WorkflowNodes
```python
Location: services/workflow_nodes.py

class WorkflowNodes:
    # Individual workflow steps
    # Reusable node implementations
    # Step-specific logic
```

##### C. Workflow Models

```python
# Request
class ConsolidatedWorkflowRequest(BaseModel):
    conversation_id: Optional[Union[UUID, str]]
    user_message: str
    workflow_mode: Literal["workbench", "seo_coach"]
    llm_config: Optional[ModelConfig]
    parameter_overrides: Optional[Dict]
    business_profile: Optional[Dict]  # SEO coach
    context_data: Optional[Dict]
    streaming: bool = False

# Response
class ConsolidatedWorkflowResponse(BaseModel):
    conversation_id: Union[UUID, str]
    assistant_response: str
    workflow_mode: str
    execution_successful: bool
    workflow_steps: List[str]        # Steps executed
    context_data: Dict[str, Any]
    business_profile: Optional[Dict]
    coaching_context: Optional[Dict]
    metadata: Dict[str, Any]

# Streaming Update
class WorkflowUpdate(BaseModel):
    conversation_id: UUID
    current_step: str
    progress_percentage: float
    partial_response: Optional[str]
    workflow_steps: List[str]
    error: Optional[str]
```

#### Workflow Execution Tracking

```python
Location: models/business_models.py:55

class WorkflowExecution(BaseModel):
    id: Optional[UUID]
    conversation_id: UUID
    workflow_mode: str
    execution_steps: List[str]
    execution_successful: bool
    error_details: Optional[str]
    execution_duration_ms: Optional[int]
    created_at: Optional[datetime]

# Database model
class WorkflowExecutionDB(Base):
    __tablename__ = "workflow_executions"

    id: UUID (PK)
    conversation_id: UUID (FK)
    workflow_mode: String
    execution_steps: JSON
    execution_successful: Boolean
    error_details: Text
    execution_duration_ms: Integer
    created_at: DateTime
```

#### Workflow Patterns

**Current Workflows:**

1. **Workbench Workflow**
   ```
   User Input → Parse Intent → Load Context →
   Execute Action → Generate Response → Update State
   ```

2. **SEO Coach Workflow**
   ```
   Business Profile → Analyze Website →
   Generate Recommendations → Implementation Guidance →
   Monitoring Setup
   ```

**Future Agentic Workflows:**

3. **Multi-Agent Collaboration**
   ```
   Coordinator → [Agent1, Agent2, Agent3] →
   Synthesis → Review → Final Response
   ```

4. **Tool Chain Execution**
   ```
   Intent → Tool Selection → Tool Execution →
   Result Validation → Iteration/Completion
   ```

#### Workflow State Machine

```python
workflow_steps = [
    "Initialize",           # Setup
    "Load Context",         # Retrieve relevant data
    "Execute Primary",      # Main operation
    "Validate Results",     # Check outputs
    "Format Response",      # Prepare for user
    "Update State"          # Persist changes
]

current_operation = "Execute Primary"  # Current step
execution_successful = True            # Overall status
retry_count = 0                        # Retry tracking
current_error = None                   # Error state
```

---

### 5. CONTEXT 🌐

**Purpose:** External knowledge injection and environment awareness

#### Core Implementation

```python
Location: services/context_service.py:7

class ContextService:
    async def update_conversation_context(
        conversation_id: UUID,
        context_data: Dict[str, Any],
        sources: List[str]
    ) -> None

    async def clear_conversation_context(
        conversation_id: UUID,
        source: Optional[str] = None
    ) -> None

    async def get_active_contexts(
        conversation_id: UUID
    ) -> List[str]

    async def build_context_prompt(
        context_data: Dict[str, Any]
    ) -> str
```

**Status:** Placeholder implementation (needs expansion)

#### Context Update Request

```python
Location: models/consolidated_state.py:101

class ContextUpdateRequest(BaseModel):
    context_data: Dict[str, Any]
    sources: List[str]
    merge_strategy: Literal["replace", "merge", "append"] = "merge"
```

#### Context Data Structure

```python
context_data = {
    # User context
    "user_profile": {
        "timezone": "Europe/Amsterdam",
        "language": "nl",
        "expertise_level": "advanced"
    },

    # Project context
    "project": {
        "name": "agent_workbench",
        "type": "python_application",
        "tech_stack": ["FastAPI", "Gradio", "SQLAlchemy"]
    },

    # Session context
    "session": {
        "start_time": "2025-10-05T10:00:00Z",
        "interaction_count": 5,
        "current_task": "code_analysis"
    },

    # External tool context (future)
    "tools": {
        "github_repo": "sytse06/agent-workbench",
        "filesystem_root": "/Users/.../agent_workbench",
        "database_url": "sqlite:///data/workbench.db"
    },

    # Agent context (future multi-agent)
    "agents": {
        "active_agents": ["code_analyzer", "doc_writer"],
        "agent_roles": {
            "code_analyzer": "primary",
            "doc_writer": "supporting"
        }
    }
}
```

#### Active Contexts Tracking

```python
active_contexts = [
    "user_profile",      # User preferences and settings
    "project_context",   # Current project info
    "conversation_history", # Recent messages
    "external_data",     # Fetched from APIs/tools
    "agent_memory"       # Multi-agent shared state
]
```

#### SEO-Specific Context

```python
Location: models/business_models.py:43

class SEOAnalysisContext(BaseModel):
    website_url: str
    analysis_timestamp: datetime
    technical_issues: List[Dict[str, Any]]
    content_recommendations: List[str]
    priority_score: int  # 0-100
    recommendations: List[Dict[str, Any]]
    llmstxt_analysis: Optional[Dict[str, Any]]

# Example
seo_context = SEOAnalysisContext(
    website_url="https://example.com",
    analysis_timestamp=datetime.utcnow(),
    technical_issues=[
        {"type": "slow_loading", "severity": "high", "page": "/"},
        {"type": "missing_meta", "severity": "medium", "page": "/about"}
    ],
    content_recommendations=[
        "Add structured data for products",
        "Improve internal linking"
    ],
    priority_score=75,
    recommendations=[...],
    llmstxt_analysis={"score": 8.5, "suggestions": [...]}
)
```

---

### 6. AGENT/TOOL 🤖⚙️

**Purpose:** Autonomous action executors (future expansion)

#### Current Implementation

##### AgentConfigModel (Database)
```python
Location: models/database.py:167

class AgentConfigModel(Base, TimestampMixin):
    __tablename__ = "agent_configs"

    id: UUID (PK)
    name: String (unique)
    config_data: JSON
    description: Text
    is_active: Boolean
    created_at: DateTime
    updated_at: DateTime
```

##### AgentConfigSchema (API)
```python
Location: models/schemas.py:156

class AgentConfigSchema(BaseModel):
    @classmethod
    def for_create(name, config, description)

    @classmethod
    def for_update()

    def to_db_dict() -> Dict
    def to_response_dict() -> Dict
```

**Current Usage:** Configuration storage only (not yet active agents)

#### Future Agent Structure

```python
# Proposed agent model (Phase 2)
class Agent(BaseModel):
    id: UUID
    name: str
    type: Literal["coordinator", "specialist", "validator"]
    capabilities: List[str]
    tools: List[str]
    model_config: ModelConfig
    system_prompt: str
    context_window: int
    max_iterations: int

    async def execute(
        task: str,
        context: Dict[str, Any],
        tools: List[Tool]
    ) -> AgentResponse

# Agent types
AgentType = Literal[
    "coordinator",      # Orchestrates multi-agent workflows
    "code_analyzer",    # Analyzes code
    "doc_writer",       # Writes documentation
    "test_generator",   # Generates tests
    "seo_analyst",      # SEO analysis
    "web_scraper",      # Data collection
    "validator"         # Result validation
]
```

#### Tool Integration (MCP)

```python
# From WorkbenchState
mcp_tools_active: List[str] = []  # Active MCP tools

# Future tool model
class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

    async def execute(
        **kwargs
    ) -> ToolResult

class ToolResult(BaseModel):
    success: bool
    output: Any
    error: Optional[str]
    metadata: Dict[str, Any]

# Example tools
available_tools = [
    "github_search",      # Search GitHub repos
    "filesystem_read",    # Read local files
    "web_fetch",          # Fetch web content
    "database_query",     # Query databases
    "code_execute",       # Execute code
    "image_generate"      # Generate images
]
```

---

### 7. BRIDGE 🌉

**Purpose:** State format conversion between systems

#### LangGraphStateBridge

```python
Location: services/langgraph_bridge.py:15

class LangGraphStateBridge:
    """Bridge between ConversationState and LangGraph WorkbenchState."""

    def __init__(
        state_manager: StateManager,
        context_service: ContextService
    )

    # Core conversion methods
    async def load_into_langgraph_state(
        conversation_id: UUID,
        user_message: str,
        workflow_mode: str,
        business_profile: Optional[Dict] = None
    ) -> WorkbenchState

    async def save_from_langgraph_state(
        lg_state: WorkbenchState
    ) -> None

    async def migrate_conversation_to_consolidated(
        conversation_id: UUID
    ) -> WorkbenchState

    # Helper conversions
    def _convert_messages_to_standard(
        messages: List[Any]
    ) -> List[StandardMessage]

    def _convert_context_data(
        context: Dict[str, Any]
    ) -> Dict[str, Any]

    def merge_workflow_context(
        base_context: Dict,
        workflow_context: Dict
    ) -> Dict

    # Workflow preparation
    async def prepare_for_workflow(
        consolidated_state,
        user_message: str
    ) -> Dict[str, Any]

    async def extract_from_workflow(
        workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]
```

#### Conversion Flow

```
ConversationState (Storage)
    ↓ [load_into_langgraph_state]
WorkbenchState (Execution)
    ↓ [LangGraph Workflow]
WorkbenchState (Updated)
    ↓ [save_from_langgraph_state]
ConversationState (Storage)
```

#### Bridge Responsibilities

1. **Format Translation**
   - ConversationState ↔ WorkbenchState
   - Preserve all data during conversion
   - Handle type differences

2. **Context Merging**
   - Combine base context + workflow context
   - Resolve conflicts
   - Maintain context hierarchy

3. **Message Conversion**
   - StandardMessage ↔ Dict format
   - LangChain message format
   - Preserve metadata

4. **Workflow State Tracking**
   - Save workflow execution records
   - Track workflow steps
   - Error state preservation

---

## 🔗 Object Relationships

### Dependency Graph

```
Message
  ↓ (contained in)
Conversation
  ↓ (has)
State (ConversationState)
  ↓ (converted to)
WorkbenchState
  ↓ (executed by)
Workflow
  ↓ (uses)
Context
  ↓ (provides data to)
Agent/Tool (future)
  ↓ (coordinated by)
Bridge
```

### Data Flow

```
1. User Input
   ↓
2. Message Created (StandardMessage)
   ↓
3. Added to Conversation
   ↓
4. State Loaded (ConversationState)
   ↓
5. Bridge Converts → WorkbenchState
   ↓
6. Workflow Executes
   ├─ Context Injected
   ├─ Tools Called (future)
   └─ Agents Collaborate (future)
   ↓
7. Response Generated
   ↓
8. Bridge Converts → ConversationState
   ↓
9. State Saved
   ↓
10. Response Returned to User
```

---

## 🎯 Agentic System Readiness

### Current Capabilities

✅ **Message System**
- Multi-role support (user, assistant, system, tool)
- Tool call tracking
- Metadata extensibility

✅ **Conversation Management**
- Lifecycle tracking
- State persistence
- History management

✅ **State Management**
- Unified state representation
- LangGraph compatibility
- Context integration

✅ **Workflow Orchestration**
- Multi-step execution
- Error handling
- Retry logic

✅ **Bridge Pattern**
- Format conversion
- State synchronization
- Workflow integration

### Missing for Full Agentic System

❌ **Active Agents**
- Current: Only AgentConfig storage
- Needed: Agent execution, coordination, delegation

❌ **Tool Integration**
- Current: Placeholder in WorkbenchState (`mcp_tools_active`)
- Needed: MCP tool execution, result processing

❌ **Multi-Agent Coordination**
- Current: Single workflow mode
- Needed: Agent collaboration, task delegation, result synthesis

❌ **Agent Memory**
- Current: Conversation history only
- Needed: Long-term memory, knowledge graphs, learning

❌ **Dynamic Tool Selection**
- Current: No tool selection logic
- Needed: Intent-based tool routing, tool chaining

❌ **Agent Communication Protocol**
- Current: No inter-agent messaging
- Needed: Agent-to-agent messages, event bus

---

## 🚀 Agentic Expansion Paths

### Phase 2: Agent Framework

```python
# 1. Agent Execution
class AgentExecutor:
    async def execute_agent(
        agent_id: str,
        task: str,
        context: Dict,
        tools: List[Tool]
    ) -> AgentResponse

# 2. Tool Registry
class ToolRegistry:
    def register_tool(tool: Tool)
    def get_tool(name: str) -> Tool
    def list_tools() -> List[Tool]

# 3. Agent Coordinator
class AgentCoordinator:
    async def coordinate(
        task: str,
        agents: List[Agent],
        workflow: Workflow
    ) -> CoordinatedResponse
```

### Phase 3: Multi-Agent Workflows

```python
# 1. Agent Communication
class AgentMessageBus:
    async def send_to_agent(
        from_agent: str,
        to_agent: str,
        message: Message
    )

    async def broadcast(
        from_agent: str,
        message: Message,
        target_agents: List[str]
    )

# 2. Shared State
class MultiAgentState(TypedDict):
    conversation_id: UUID
    primary_agent: str
    active_agents: List[str]
    agent_states: Dict[str, Dict]
    shared_context: Dict
    workflow_plan: List[str]
    execution_graph: Dict
```

### Phase 4: Learning & Adaptation

```python
# 1. Agent Memory
class AgentMemory:
    async def remember(
        agent_id: str,
        key: str,
        value: Any,
        importance: float
    )

    async def recall(
        agent_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Memory]

# 2. Performance Tracking
class AgentPerformance:
    def track_execution(
        agent_id: str,
        task: str,
        success: bool,
        metrics: Dict
    )

    def get_agent_stats(
        agent_id: str
    ) -> AgentStats
```

---

## 📋 Object Model Summary

| Object | Purpose | Current Status | Agentic Ready |
|--------|---------|----------------|---------------|
| **Message** | Communication unit | ✅ Complete | ✅ Yes - supports tool calls |
| **Conversation** | Message container | ✅ Complete | ✅ Yes - extensible metadata |
| **State** | Memory & context | ✅ Complete | ✅ Yes - both formats ready |
| **Workflow** | Execution orchestration | ✅ Complete | ⚠️ Partial - needs multi-agent |
| **Context** | Knowledge injection | ⚠️ Placeholder | ❌ No - needs implementation |
| **Agent/Tool** | Action executors | ❌ Config only | ❌ No - needs full implementation |
| **Bridge** | Format conversion | ✅ Complete | ✅ Yes - extensible |

---

## 🎨 Design Principles

### 1. **Separation of Concerns**
- Storage format (ConversationState) ≠ Execution format (WorkbenchState)
- Bridge handles conversion
- Each layer has clear responsibility

### 2. **Extensibility**
- All objects support `metadata: Dict[str, Any]`
- TypedDict allows adding fields without breaking
- Placeholder fields for future features

### 3. **Compatibility**
- SQLAlchemy models for database
- Pydantic models for API
- TypedDict for LangGraph
- Bridge pattern connects them all

### 4. **State Immutability** (future)
- Current: State updates overwrite
- Future: Event sourcing, state versioning

### 5. **Tool-Agnostic**
- No hard-coded tool dependencies
- MCP tool integration ready
- Plugin architecture

---

## 📁 Quick Reference

### File Locations

```
models/
  ├─ standard_messages.py     - StandardMessage, ConversationState
  ├─ consolidated_state.py    - WorkbenchState, Workflow models
  ├─ database.py              - SQLAlchemy models
  ├─ schemas.py               - Pydantic API schemas
  ├─ conversation_state.py    - ConversationStateDB
  └─ business_models.py       - SEO coach, WorkflowExecution

services/
  ├─ state_manager.py         - State CRUD operations
  ├─ langgraph_bridge.py      - State format conversion
  ├─ context_service.py       - Context management (placeholder)
  ├─ workflow_orchestrator.py - Workflow execution
  └─ workflow_nodes.py        - Workflow steps
```

### Key Classes by Concern

**Message Handling:**
- `StandardMessage` (standard_messages.py:19)
- `MessageModel` (database.py:95)
- `MessageSchema` (schemas.py:94)
- `MessageConverter` (message_converter.py:15)

**Conversation Management:**
- `ConversationModel` (database.py:35)
- `ConversationSchema` (schemas.py:42)
- `ConversationService` (conversation_service.py:14)

**State Management:**
- `ConversationState` (standard_messages.py:30)
- `WorkbenchState` (consolidated_state.py:14)
- `ConversationStateDB` (conversation_state.py:11)
- `StateManager` (state_manager.py:17)

**Workflow Orchestration:**
- `WorkflowOrchestrator` (workflow_orchestrator.py)
- `WorkflowNodes` (workflow_nodes.py)
- `WorkflowExecution` (business_models.py:55)

**Bridge & Conversion:**
- `LangGraphStateBridge` (langgraph_bridge.py:15)

---

**End of Agentic System Object Model**

**Next Steps:**
1. Implement full ContextService
2. Build Agent execution framework
3. Add MCP tool integration
4. Create multi-agent coordinator
5. Implement agent memory system
