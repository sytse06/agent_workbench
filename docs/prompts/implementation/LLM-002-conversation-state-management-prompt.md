# Implementation Prompt: LLM-002-conversation-state-management

You are implementing **LLM-002-conversation-state-management** within strict architectural boundaries.

## Architecture Reference
# LLM-002: Conversation State Management

## Status

**Status**: Ready for Implementation  
**Date**: September 14, 2025  
**Decision Makers**: Human Architect  
**Task ID**: LLM-002-conversation-state-management  
**Dependencies**: LLM-001 (chat foundation), CORE-002 (database schema)

## Context

Transform the stateless chat service from LLM-001 into a context-aware, persistent conversation system using framework-agnostic state management. Provides robust conversation memory, external context integration, and foundation for advanced agent workflows while maintaining universal provider compatibility through OpenAI-standard interfaces.

## Architecture Scope

### What's Included:

- Framework-agnostic conversation state management with persistent memory across sessions
- OpenAI-compatible standard message format for universal provider support
- Universal provider registry supporting OpenAI, OpenRouter, vLLM, Ollama, and any OpenAI-compatible service
- Context integration interface for external systems (DOC-001, MCP-001) to inject data
- Enhanced conversation lifecycle management with state persistence
- Database schema extensions for state storage with efficient querying
- Migration path from LLM-001 stateless to stateful conversations
- Provider-agnostic LLM client using OpenAI-compatible endpoints

### What's Explicitly Excluded:

- UI integration or Gradio components (UI-001)
- Document processing logic or file handling (DOC-001)
- MCP tool integration or agent workflows (MCP-001, AGENT-001)
- Framework-specific implementations (LangChain, LiteLLM adapters)
- Vector embeddings or semantic search capabilities
- Authentication or user management
- Agent reasoning or decision-making logic

## Architectural Decisions

### 1. Framework-Agnostic State Architecture

**Core Philosophy**: State management is a data persistence problem, not a framework problem

```python
class ConversationState(BaseModel):
    conversation_id: UUID
    messages: List[StandardMessage]           # Full conversation history
    model_config: ModelConfig                # Provider and model settings
    context_data: Dict[str, Any]             # External context injection
    active_contexts: List[str]               # Context source tracking
    metadata: Dict[str, Any]                 # Conversation metadata
    updated_at: datetime
    
    # Future extensions (empty for now, ready for AGENT-001)
    agent_state: Optional[Dict[str, Any]] = None
    workflow_data: Optional[Dict[str, Any]] = None
```

### 2. OpenAI-Compatible Standard Message Format

**Universal Message Schema**:
```python
class StandardMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class ToolCall(BaseModel):
    id: str
    type: Literal["function"]
    function: ToolFunction

class ToolFunction(BaseModel):
    name: str
    arguments: str  # JSON string
```

### 3. Universal Provider Registry

**Provider Abstraction**:
```python
class ModelProvider(BaseModel):
    name: str
    base_url: str
    api_key_env_var: str
    models: List[str]
    supports_streaming: bool = True
    supports_tools: bool = False
    max_context_length: Optional[int] = None
    
class ModelConfig(BaseModel):
    provider: str                           # Provider identifier
    model: str                             # Model name
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0, le=100000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    system_prompt: Optional[str] = None
    streaming: bool = True
    extra_params: Dict[str, Any] = {}
```

### 4. Database Schema Extensions

**Enhanced Schema from CORE-002**:
```sql
-- Extend existing conversations table
ALTER TABLE conversations ADD COLUMN model_config JSON;
ALTER TABLE conversations ADD COLUMN context_sources JSON;
ALTER TABLE conversations ADD COLUMN last_activity TIMESTAMP;

-- New table for conversation state persistence
CREATE TABLE conversation_states (
    conversation_id VARCHAR(36) PRIMARY KEY REFERENCES conversations(id) ON DELETE CASCADE,
    state_data JSON NOT NULL,
    context_data JSON,
    active_contexts JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Indexes for performance
CREATE INDEX idx_conversation_states_updated ON conversation_states(updated_at);
CREATE INDEX idx_conversation_states_context ON conversation_states USING GIN (active_contexts);
CREATE INDEX idx_conversations_activity ON conversations(last_activity);
```

### 5. Provider-Agnostic LLM Client

**Universal Client Implementation**:
```python
class UniversalLLMClient:
    """
    OpenAI-compatible client that works with any provider
    No framework dependencies, pure HTTP implementation
    """
    
    def __init__(self, provider_registry: ProviderRegistry):
        self.providers = provider_registry
        self.http_client = httpx.AsyncClient()
    
    async def chat_completion(
        self, 
        messages: List[StandardMessage], 
        config: ModelConfig
    ) -> ChatResponse:
        provider = await self.providers.get_provider(config.provider)
        request_data = self._build_chat_request(messages, config)
        response = await self.http_client.post(
            f"{provider.base_url}/chat/completions",
            json=request_data,
            headers=self._build_headers(provider)
        )
        return self._parse_chat_response(response.json())
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/models/
├── messages.py              # StandardMessage, ToolCall definitions
├── providers.py             # ModelProvider, ModelConfig definitions
├── conversation_state.py    # ConversationState and database models
└── responses.py             # ChatResponse, streaming response models

src/agent_workbench/services/
├── state_manager.py         # Core state persistence and lifecycle
├── provider_registry.py     # Provider management and validation
├── conversation_service.py  # Context-aware conversation logic
└── context_service.py       # External context integration

src/agent_workbench/core/
├── universal_client.py      # OpenAI-compatible LLM client
└── message_builder.py       # Context-aware message construction

src/agent_workbench/config/
└── providers.py             # Default provider configurations

src/agent_workbench/api/routes/
├── conversations.py         # Enhanced conversation management
├── context.py              # Context integration endpoints
└── providers.py            # Provider information endpoints
```

### Files to MODIFY:

```
src/agent_workbench/services/llm_service.py  # Integration with state management
src/agent_workbench/api/routes/chat.py       # Add stateful chat endpoints
```

### Exact Function Signatures:

```python
# models/conversation_state.py
class ConversationState(BaseModel):
    conversation_id: UUID
    messages: List[StandardMessage]
    model_config: ModelConfig
    context_data: Dict[str, Any]
    active_contexts: List[str]
    metadata: Dict[str, Any]
    updated_at: datetime
    agent_state: Optional[Dict[str, Any]] = None
    workflow_data: Optional[Dict[str, Any]] = None

class ConversationStateDB(Base):
    __tablename__ = "conversation_states"
    conversation_id = Column(UUID, ForeignKey("conversations.id"), primary_key=True)
    state_data = Column(JSON, nullable=False)
    context_data = Column(JSON)
    active_contexts = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)
    version = Column(Integer, default=1)

# services/state_manager.py
class StateManager:
    async def load_conversation_state(self, conversation_id: UUID) -> ConversationState
    async def save_conversation_state(self, state: ConversationState) -> None
    async def create_conversation(self, model_config: ModelConfig, title: Optional[str] = None) -> UUID
    async def delete_conversation(self, conversation_id: UUID) -> bool
    async def list_conversations(self, limit: int = 50, offset: int = 0) -> List[ConversationSummary]
    async def migrate_conversation_to_stateful(self, conversation_id: UUID) -> ConversationState

# services/conversation_service.py
class ConversationService:
    async def chat_with_context(self, conversation_id: UUID, message: str) -> ChatResponse
    async def stream_chat_with_context(self, conversation_id: UUID, message: str) -> AsyncGenerator[str, None]
    async def get_conversation_summary(self, conversation_id: UUID) -> ConversationSummary
    async def update_conversation_config(self, conversation_id: UUID, config: ModelConfig) -> None

# services/context_service.py
class ContextService:
    async def update_conversation_context(self, conversation_id: UUID, context_data: Dict[str, Any], sources: List[str]) -> None
    async def clear_conversation_context(self, conversation_id: UUID, source: Optional[str] = None) -> None
    async def get_active_contexts(self, conversation_id: UUID) -> List[str]
    async def get_context_data(self, conversation_id: UUID) -> Dict[str, Any]

# services/provider_registry.py
class ProviderRegistry:
    async def get_available_providers(self) -> List[ModelProvider]
    async def get_provider_models(self, provider_name: str) -> List[str]
    async def validate_model_config(self, config: ModelConfig) -> ValidationResult
    async def get_provider(self, provider_name: str) -> ModelProvider
    async def register_custom_provider(self, provider: ModelProvider) -> None

# core/universal_client.py
class UniversalLLMClient:
    async def chat_completion(self, messages: List[StandardMessage], config: ModelConfig) -> ChatResponse
    async def stream_completion(self, messages: List[StandardMessage], config: ModelConfig) -> AsyncGenerator[str, None]
    async def validate_connection(self, provider: str) -> bool

# models/messages.py
class StandardMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    content: str
    conversation_id: UUID
    message_count: int
    model_used: str
    metadata: Optional[Dict[str, Any]] = None

class ConversationSummary(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    model_config: Optional[ModelConfig]
    active_contexts: List[str]

# API endpoints (conversations.py)
@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(limit: int = 50, offset: int = 0)

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest)

@router.get("/conversations/{conversation_id}/state", response_model=ConversationStateResponse)
async def get_conversation_state(conversation_id: UUID)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: UUID)

# API endpoints (context.py)
@router.put("/conversations/{conversation_id}/context")
async def update_conversation_context(conversation_id: UUID, request: ContextUpdateRequest)

@router.delete("/conversations/{conversation_id}/context")
async def clear_conversation_context(conversation_id: UUID, source: Optional[str] = None)

@router.get("/conversations/{conversation_id}/context")
async def get_conversation_context(conversation_id: UUID)

# Enhanced chat endpoints (MODIFY chat.py)
@router.post("/chat/stateful", response_model=ChatResponse)
async def chat_completion_stateful(request: StatefulChatRequest)

@router.post("/chat/stateful/stream")
async def stream_chat_stateful(request: StatefulChatRequest)

# Provider endpoints (providers.py)
@router.get("/providers", response_model=List[ModelProvider])
async def get_providers()

@router.get("/providers/{provider_name}/models", response_model=List[str])
async def get_provider_models(provider_name: str)

@router.post("/providers/{provider_name}/validate")
async def validate_provider_config(provider_name: str, config: ModelConfig)
```

### Additional Dependencies:

```toml
# Core functionality (minimal, stable)
fastapi = "^0.104.0"
pydantic = "^2.5.0"
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
httpx = "^0.25.0"          # For OpenAI-compatible HTTP requests
asyncio = "^3.9.0"         # Async support
uuid = "^1.30.0"           # UUID generation
python-dotenv = "^1.0.0"   # Environment configuration

# Database and persistence
aiosqlite = "^0.19.0"      # Async SQLite support
asyncpg = "^0.29.0"        # PostgreSQL async support (optional)

# Optional enhancements
tenacity = "^8.2.0"        # Retry logic for HTTP requests
structlog = "^23.2.0"      # Structured logging
```

### FORBIDDEN Actions:

- Adding LangChain, LangGraph, or LiteLLM dependencies
- Creating UI components or Gradio integration
- Implementing document processing or file handling logic
- Adding MCP tool calling or agent decision-making
- Implementing vector embeddings or semantic search
- Adding authentication or user management
- Creating framework-specific adapters or wrappers

## Success Criteria

- [ ] Conversation state persistence working correctly across sessions
- [ ] Context integration interface functional for external systems
- [ ] Migration from LLM-001 conversations seamless with no data loss
- [ ] Universal provider support for OpenAI, OpenRouter, vLLM, Ollama
- [ ] OpenAI-compatible message format works across all providers
- [ ] State operations complete in <500ms for good user experience
- [ ] Backward compatibility with LLM-001 maintained completely
- [ ] >90% test coverage for state management functionality
## CRITICAL CONSTRAINTS
- **ONLY implement** what's listed in 'What's Included'
- **NEVER implement** what's in 'What's Excluded'
- **Follow exact function signatures** if provided above
- **Create only the files** specified in Implementation Boundaries
- **Include comprehensive tests** for all new functionality

## Scope Violation Detection
If you want to add something not listed in scope, STOP.
Implementation will be validated against these exact boundaries.

## Ready for Implementation
Implement exactly what's specified above. No more, no less.
