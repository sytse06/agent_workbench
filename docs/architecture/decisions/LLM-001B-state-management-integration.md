# LLM-001B: State Management Integration

## Status

**Status**: Ready for Implementation  
**Date**: September 14, 2025  
**Decision Makers**: Human Architect  
**Task ID**: LLM-001B-state-management-integration  
**Dependencies**: LLM-001 (LangChain model integration)

## Context

Extend the existing LLM-001 LangChain-based chat service with stateful conversation capabilities while preserving all existing functionality. This integration adds persistent conversation memory, context injection, and unified API support for both stateless and stateful interactions using the proven LLM-001 infrastructure.

## Architecture Scope

### What's Included:

- State management layer integrated with existing LangChain ChatService
- Unified API endpoint supporting both stateless (LLM-001) and stateful conversations
- LangChain ↔ Standard message conversion for state persistence
- Context integration interface for external systems to inject data
- Temporary conversation support for seamless stateless operation
- Database schema extensions for conversation state storage
- Migration utilities for upgrading existing conversations to stateful
- Background cleanup for temporary conversations

### What's Explicitly Excluded:

- Replacement of existing LangChain infrastructure (preserved from LLM-001)
- Framework-agnostic rewrite (deferred to LLM-002)
- UI integration or Gradio components (UI-001)
- Document processing integration (DOC-001)  
- Agent workflows or tool calling (MCP-001, AGENT-001)
- Vector embeddings or semantic capabilities
- Authentication or user management

## Architectural Decisions

### 1. LangChain Integration Preservation

**Core Approach**: Extend LLM-001 ChatService without breaking existing functionality

- Maintain existing LangChain ChatModels infrastructure
- Add state management as optional layer around existing chat completion
- Preserve all existing provider configurations and parameter handling
- Ensure backward compatibility for all LLM-001 API contracts

### 2. Stateful Conversation Strategy

**State-Aware LangChain Flow**:
```python
# Enhanced LLM-001 ChatService with state management
class ChatService:
    def __init__(self, model_config: ModelConfig):
        # Existing LLM-001 initialization (unchanged)
        self.chat_model = self._create_langchain_model(model_config)
        self.model_config = model_config
        
        # New state management capabilities
        self.state_manager = StateManager()
        self.context_service = ContextService()
```

**Message Flow**:
```
Stateless: Request -> LangChain ChatModel -> Response (LLM-001 behavior)
Stateful:  Request -> Load State -> Build LangChain Messages -> ChatModel -> Save State -> Response
```

### 3. Unified API Design

**Single Endpoint Strategy**:
```python
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None  # None = stateless, UUID = stateful
    model_config: Optional[ModelConfig] = None
    use_context: bool = True
    
# Unified behavior:
# conversation_id = null: Original LLM-001 stateless behavior
# conversation_id = UUID: New stateful behavior with persistent memory
```

### 4. State Persistence Architecture

**Standard Message Format** for storage portability:
```python
class StandardMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationState(BaseModel):
    conversation_id: UUID
    messages: List[StandardMessage]     # Stored in standard format
    model_config: ModelConfig          # Reuse from LLM-001
    context_data: Dict[str, Any]       # External context injection
    active_contexts: List[str]         # Context source tracking
    metadata: Dict[str, Any]           # Conversation metadata
    updated_at: datetime
```

### 5. Context Integration Layer

**LangChain-Compatible Context Injection**:
```python
async def build_context_aware_messages(state: ConversationState, message: str) -> List[BaseMessage]:
    messages = []
    
    # Inject context as system message if available
    if state.context_data:
        context_prompt = self._build_context_prompt(state.context_data)
        messages.append(SystemMessage(content=context_prompt))
    
    # Convert stored messages to LangChain format
    for stored_msg in state.messages:
        if stored_msg.role == "user":
            messages.append(HumanMessage(content=stored_msg.content))
        elif stored_msg.role == "assistant":
            messages.append(AIMessage(content=stored_msg.content))
        elif stored_msg.role == "system":
            messages.append(SystemMessage(content=stored_msg.content))
    
    # Add new user message
    messages.append(HumanMessage(content=message))
    return messages
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/services/
├── state_manager.py         # Conversation state persistence and lifecycle
├── message_converter.py     # LangChain ↔ Standard format conversion
├── context_service.py       # External context integration
└── temporary_manager.py     # Temporary conversation lifecycle

src/agent_workbench/models/
├── conversation_state.py    # State models and database schemas
├── standard_messages.py     # Standard message format definitions
└── state_requests.py        # Enhanced request models with conversation_id

src/agent_workbench/api/routes/
└── context.py              # Context management endpoints
```

### Files to MODIFY:

```
src/agent_workbench/services/llm_service.py     # Add stateful methods to ChatService
src/agent_workbench/api/routes/chat.py          # Enhance with conversation_id support
src/agent_workbench/models/chat_models.py       # Add conversation_id to ChatRequest
```

### Exact Function Signatures:

```python
# MODIFY: services/llm_service.py
class ChatService:
    def __init__(self, model_config: ModelConfig):
        # Existing LangChain initialization (unchanged)
        self.chat_model = self._create_langchain_model(model_config)
        self.model_config = model_config
        
        # Add state management capabilities
        self.state_manager = StateManager()
        self.context_service = ContextService()
        self.message_converter = MessageConverter()
    
    # MODIFY: Enhanced to support both stateless and stateful modes
    async def chat_completion(self, message: str, conversation_id: Optional[UUID] = None) -> ChatResponse
    async def stream_completion(self, message: str, conversation_id: Optional[UUID] = None) -> AsyncGenerator[str, None]
    
    # ADD: Stateful conversation methods
    async def create_conversation(self, title: Optional[str] = None, is_temporary: bool = False) -> UUID
    async def get_conversation_history(self, conversation_id: UUID) -> List[StandardMessage]
    async def update_conversation_context(self, conversation_id: UUID, context_data: Dict[str, Any], sources: List[str]) -> None

# CREATE: services/state_manager.py
class StateManager:
    async def load_conversation_state(self, conversation_id: UUID) -> ConversationState
    async def save_conversation_state(self, state: ConversationState) -> None
    async def create_conversation(self, model_config: ModelConfig, title: Optional[str] = None, is_temporary: bool = False) -> UUID
    async def delete_conversation(self, conversation_id: UUID) -> bool
    async def list_conversations(self, limit: int = 50) -> List[ConversationSummary]
    async def migrate_conversation_to_stateful(self, conversation_id: UUID) -> ConversationState
    async def cleanup_temporary_conversations(self, older_than_minutes: int = 60) -> int

# CREATE: services/context_service.py
class ContextService:
    async def update_conversation_context(self, conversation_id: UUID, context_data: Dict[str, Any], sources: List[str]) -> None
    async def clear_conversation_context(self, conversation_id: UUID, source: Optional[str] = None) -> None
    async def get_active_contexts(self, conversation_id: UUID) -> List[str]
    async def build_context_prompt(self, context_data: Dict[str, Any]) -> str

# CREATE: services/message_converter.py
class MessageConverter:
    @staticmethod
    def to_langchain_messages(messages: List[StandardMessage]) -> List[BaseMessage]
    @staticmethod
    def from_langchain_message(message: BaseMessage) -> StandardMessage
    @staticmethod
    def to_standard_messages(messages: List[BaseMessage]) -> List[StandardMessage]

# CREATE: models/standard_messages.py
class StandardMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

# CREATE: models/conversation_state.py
class ConversationState(BaseModel):
    conversation_id: UUID
    messages: List[StandardMessage]
    model_config: ModelConfig
    context_data: Dict[str, Any]
    active_contexts: List[str]
    metadata: Dict[str, Any]
    updated_at: datetime

class ConversationStateDB(Base):
    __tablename__ = "conversation_states"
    conversation_id = Column(UUID, ForeignKey("conversations.id"), primary_key=True)
    state_data = Column(JSON, nullable=False)
    context_data = Column(JSON)
    active_contexts = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)

# MODIFY: models/chat_models.py
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None      # ADD: Enable stateful mode
    model_config: Optional[ModelConfig] = None  # ADD: Override conversation config
    use_context: bool = True                    # ADD: Context integration control
    temperature: Optional[float] = None         # ADD: Quick parameter overrides
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    content: str
    conversation_id: Optional[UUID] = None      # ADD: Return conversation ID
    message_count: Optional[int] = None         # ADD: Position in conversation
    model_used: str
    is_temporary: Optional[bool] = None         # ADD: Temporary conversation indicator
    metadata: Optional[Dict[str, Any]] = None

class ConversationSummary(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    model_config: Optional[ModelConfig]
    active_contexts: List[str]
    is_temporary: bool

# API endpoints (MODIFY chat.py)
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest, service: ChatService = Depends(get_chat_service))

@router.post("/chat/stream")
async def stream_chat(request: ChatRequest, service: ChatService = Depends(get_chat_service))

# API endpoints (CREATE context.py)
@router.put("/conversations/{conversation_id}/context")
async def update_conversation_context(conversation_id: UUID, request: ContextUpdateRequest)

@router.delete("/conversations/{conversation_id}/context")
async def clear_conversation_context(conversation_id: UUID, source: Optional[str] = None)

@router.get("/conversations/{conversation_id}/context")
async def get_conversation_context(conversation_id: UUID)

# Enhanced conversation endpoints (MODIFY conversations.py)
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest)

@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(limit: int = 50, include_temporary: bool = False)

@router.get("/conversations/{conversation_id}/messages", response_model=List[StandardMessage])
async def get_conversation_messages(conversation_id: UUID)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: UUID)
```

### Additional Dependencies:

```toml
# Existing LLM-001 dependencies (unchanged)
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

# Additional dependencies for state management
aiosqlite = "^0.19.0"      # Enhanced async SQLite support
asyncpg = "^0.29.0"        # PostgreSQL support (optional)
apscheduler = "^3.10.0"    # Background task scheduling for cleanup
structlog = "^23.2.0"      # Structured logging for state operations
```

### FORBIDDEN Actions:

- Replacing or removing existing LangChain ChatModels infrastructure
- Breaking existing LLM-001 API contracts or response formats
- Implementing framework-agnostic alternatives to LangChain
- Creating UI components or Gradio integration
- Adding document processing or RAG capabilities
- Implementing agent workflows or tool calling
- Adding authentication or user management
- Implementing vector embeddings or semantic search

## Success Criteria

- [ ] **Backward Compatibility**: All existing LLM-001 functionality works unchanged
- [ ] **Stateful Conversations**: Persistent conversation memory using LangChain infrastructure
- [ ] **Context Integration**: External systems can inject context into conversations
- [ ] **Unified API**: Single chat endpoint supports both stateless and stateful modes
- [ ] **Temporary Conversations**: Seamless stateless operation with automatic cleanup
- [ ] **State Performance**: Load/save conversation state in <500ms
- [ ] **LangChain Integration**: No performance degradation for existing LLM-001 features
- [ ] **Migration Support**: Existing conversations can upgrade to stateful format
- [ ] **>90% test coverage** for new state management functionality
- [ ] **Database migrations** complete successfully without data loss