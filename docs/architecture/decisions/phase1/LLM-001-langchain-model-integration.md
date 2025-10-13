# LLM-001: LangChain Model Integration

## Status

**Status**: Ready for Implementation  
**Date**: September 09, 2025  
**Decision Makers**: Human Architect  
**Task ID**: LLM-001-langchain-model-integration  
**Dependencies**: CORE-001 (FastAPI app), CORE-002 (conversation persistence)

## Context

Implement LangChain ChatModels integration with Pydantic validation for multiple LLM providers. Provides unified interface for chat completions with type-safe parameter handling and basic conversation persistence.

## Architecture Scope

### What's Included:

- LangChain ChatModels wrapper with Pydantic validation
- Provider abstraction layer (OpenRouter, Ollama, direct providers)
- Model configuration system with parameter validation
- Basic chat completion functionality with streaming
- Integration with conversation persistence from CORE-002
- Error handling and retry logic for API calls

### What's Explicitly Excluded:

- UI integration or Gradio components (UI-001)
- Agent workflows or tool calling (MCP-001, AGENT-001)
- Document processing integration (DOC-001)
- LangGraph state management (LLM-002)
- Complex conversation management beyond basic persistence
- Vector embeddings or semantic capabilities

## Architectural Decisions

### 1. LangChain Integration Architecture

**Core Approach**: Pydantic wrapper around LangChain ChatModels

- Type-safe parameter validation before LangChain calls
- Unified interface regardless of underlying provider
- Streaming support through LangChain's async generators
- Automatic conversation persistence after each interaction

### 2. Provider Support Strategy

**Initial Providers**:
- OpenRouter: LangChain ChatOpenAI with custom base_url
- Ollama: LangChain ChatOllama for local models
- Direct Providers: OpenAI, Anthropic via LangChain ChatModels

**Provider Configuration**:
```python
class ProviderConfig(BaseModel):
    provider_name: str
    chat_model_class: Type[BaseChatModel]  
    default_model: str
    api_key_env_var: Optional[str]
    base_url: Optional[str]
```

### 3. Model Parameter Management

**Universal Parameters** (supported by most providers):
- temperature, max_tokens, top_p, frequency_penalty
- streaming, system_prompt

**Provider-Specific Parameters**:
- Stored in extra_params dict with validation
- Passed through to LangChain model as kwargs

### 4. Chat Service Architecture

**Service Layer Pattern**:
- ChatService class manages model instances and conversations
- Async methods for chat completion with automatic persistence
- Error handling with exponential backoff retry logic
- Memory management for conversation context

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/services/
├── __init__.py
├── llm_service.py           # Main LLM service class
├── providers.py             # Provider configurations and registry
└── chat_models.py           # Pydantic wrapper models

src/agent_workbench/core/
├── exceptions.py            # LLM-specific exception classes
└── retry.py                 # Retry logic utilities

src/agent_workbench/api/routes/
└── chat.py                  # Chat completion endpoints
```

### Exact Function Signatures:

```python
# llm_service.py
class ChatService:
    def __init__(self, model_config: ModelConfig)
    async def chat_completion(self, message: str, conversation_id: Optional[UUID] = None) -> ChatResponse
    async def stream_completion(self, message: str, conversation_id: Optional[UUID] = None) -> AsyncGenerator[str, None]
    async def get_available_models(self, provider: str) -> List[str]

# conversation_service.py
class ConversationService:
    async def create_conversation(self, title: Optional[str] = None, model_config: Optional[ModelConfig] = None) -> UUID
    async def get_conversations(self, limit: int = 50) -> List[ConversationSummary]
    async def delete_conversation(self, conversation_id: UUID) -> bool
    async def get_conversation(self, conversation_id: UUID) -> ConversationResponse

# providers.py
class ModelRegistry:
    async def get_available_providers(self) -> List[str]
    async def get_provider_models(self, provider: str) -> List[ModelInfo]
    async def validate_model_config(self, config: ModelConfig) -> ValidationResult

# chat_models.py  
class ModelConfig(BaseModel):
    provider: str
    model_name: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0, le=100000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    system_prompt: Optional[str] = None
    streaming: bool = True
    extra_params: Dict[str, Any] = {}

class ModelInfo(BaseModel):
    name: str
    display_name: str
    context_length: int
    supports_streaming: bool
    supports_tools: bool

class ConversationSummary(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    message_count: int
    model_config: Optional[ModelConfig]

# API endpoints (chat.py)
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest, service: ChatService = Depends(get_chat_service))

@router.post("/chat/stream")  
async def stream_chat(request: ChatRequest, service: ChatService = Depends(get_chat_service))

# API endpoints (models.py)
@router.get("/models/providers", response_model=List[str])
async def get_providers()

@router.get("/models/{provider}", response_model=List[ModelInfo])
async def get_provider_models(provider: str)

# API endpoints (conversations.py)
@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations(limit: int = 50)

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: UUID)
```

### Additional Dependencies:

```toml
langchain = "^0.3.0"
langchain-community = "^0.3.0"
langchain-openai = "^0.2.0"
langchain-ollama = "^0.1.0"       # For Ollama integration
langchain-mistralai = "^0.1.0"    # For Mistral integration
openai = "^1.6.0"                 # For direct OpenAI integration
anthropic = "^0.8.0"              # For direct Anthropic integration
mistralai = "^1.0.0"              # For direct Mistral integration
ollama = "^0.3.0"                 # For direct Ollama integration
httpx = "^0.25.0"                 # For HTTP retries
tenacity = "^8.2.0"               # For retry logic
```

### FORBIDDEN Actions:

- Creating UI components or Gradio integration
- Implementing agent workflows or tool calling
- Adding document processing or RAG capabilities
- Creating LangGraph state management
- Adding authentication or user management
- Implementing vector embeddings or semantic search

## Success Criteria

- [ ] Chat completions work with OpenRouter and Ollama
- [ ] Streaming responses work correctly
- [ ] All conversations automatically persisted to database
- [ ] Parameter validation prevents invalid model calls
- [ ] Error handling with retries for API failures
- [ ] >90% test coverage including mock provider tests