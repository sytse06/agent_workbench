# LLM-001: LangChain Model Integration (Updated)

## Status
- **Status**: Ready for Implementation  
- **Date**: September 08, 2025
- **Decision Makers**: Human Architect
- **Task ID**: LLM-001-langchain-model-integration
- **Dependencies**: CORE-001 (FastAPI app), CORE-002 (conversation persistence)

## Context
Implement modern LangChain ChatModels integration with Pydantic validation for multiple LLM providers. Provides unified interface for chat completions with type-safe parameter handling, structured message management, and conversation persistence using current LangChain architecture patterns.

## Architecture Scope

### What's Included:
- **Modern LangChain Integration**: Dedicated provider packages (`langchain-openai`, `langchain-ollama`, `langchain-anthropic`)
- **Structured Message System**: Proper `SystemMessage`, `HumanMessage`, `AIMessage`, `ToolMessage` handling
- **Provider Abstraction Layer**: Unified interface across OpenRouter, Ollama, and direct providers
- **Type-Safe Configuration**: Pydantic models for all model parameters and conversation data
- **Message-Based Persistence**: Structured conversation storage with message roles and metadata
- **Streaming Support**: Async streaming with proper message chunking and assembly

### What's Explicitly Excluded:
- UI integration or Gradio components (UI-001)
- Agent workflows or tool calling (MCP-001, AGENT-001)  
- Document processing integration (DOC-001)
- Vector embeddings or semantic capabilities
- Complex conversation management beyond structured persistence

## Architectural Decisions

### 1. Modern LangChain Package Architecture
**Core Principle**: Use dedicated integration packages for better type safety and maintenance

```python
# Modern dedicated packages (✅ Current approach)
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama  
from langchain_anthropic import ChatAnthropic

# Legacy community package (❌ Deprecated)
# from langchain_community.chat_models import ChatOllama
```

**Rationale**: Dedicated packages provide better type safety, faster updates, and cleaner dependency management.

### 2. Structured Message System
**Message-First Architecture**: All conversations use LangChain's structured message types

```python
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage, 
    ToolMessage, BaseMessage
)

class ConversationManager:
    def __init__(self):
        self.messages: List[BaseMessage] = []
    
    async def add_user_message(self, content: str) -> None:
        self.messages.append(HumanMessage(content=content))
    
    async def invoke_model(self, model: BaseChatModel) -> AIMessage:
        response = await model.ainvoke(self.messages)
        self.messages.append(response)
        return response
```

**Database Schema Update**:
```sql
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) REFERENCES conversations(id),
    message_type VARCHAR(20) NOT NULL,  -- 'system', 'human', 'ai', 'tool'
    content TEXT NOT NULL,
    additional_kwargs JSON,  -- Tool calls, usage metadata, etc.
    response_metadata JSON,  -- Model-specific response data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Provider Configuration Strategy
**Updated Provider Support**:

```python
class ProviderConfig(BaseModel):
    provider_name: Literal["openai", "openrouter", "ollama", "anthropic"]
    model_name: str
    chat_model_class: Type[BaseChatModel]
    api_key_env_var: Optional[str] = None
    base_url: Optional[str] = None  # For OpenRouter custom endpoints
    default_params: Dict[str, Any] = Field(default_factory=dict)

# Provider registry with current packages
PROVIDER_REGISTRY = {
    "openai": ProviderConfig(
        provider_name="openai",
        chat_model_class=ChatOpenAI,
        api_key_env_var="OPENAI_API_KEY",
        model_name="gpt-4o-mini"
    ),
    "openrouter": ProviderConfig(
        provider_name="openrouter", 
        chat_model_class=ChatOpenAI,  # Uses OpenAI-compatible API
        base_url="https://openrouter.ai/api/v1",
        api_key_env_var="OPENROUTER_API_KEY",
        model_name="anthropic/claude-3.5-sonnet"
    ),
    "ollama": ProviderConfig(
        provider_name="ollama",
        chat_model_class=ChatOllama,
        base_url="http://localhost:11434",
        model_name="llama3.2"
    ),
    "anthropic": ProviderConfig(
        provider_name="anthropic",
        chat_model_class=ChatAnthropic,
        api_key_env_var="ANTHROPIC_API_KEY", 
        model_name="claude-3-5-sonnet-20241022"
    )
}
```

### 4. Enhanced Model Configuration
**Comprehensive Parameter Support**:

```python
class ModelConfig(BaseModel):
    provider: Literal["openai", "openrouter", "ollama", "anthropic"]
    model_name: str
    
    # Universal parameters (supported by most providers)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=1000, gt=0, le=100000)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    
    # LangChain-specific settings
    streaming: bool = True
    system_prompt: Optional[str] = None
    
    # Provider-specific parameters (validated per provider)
    extra_params: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('extra_params')
    @classmethod
    def validate_extra_params(cls, v, info):
        # Validate provider-specific parameters
        return v
```

### 5. Service Layer Architecture
**Updated Chat Service with Message Management**:

```python
class ChatService:
    def __init__(self, model_config: ModelConfig):
        self.config = model_config
        self.model = self._initialize_model()
        self.conversation_manager = ConversationManager()
    
    async def chat_completion(
        self, 
        message: str, 
        conversation_id: Optional[UUID] = None,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """Complete chat interaction with structured message handling"""
        
        # Load existing conversation or create new
        if conversation_id:
            await self.conversation_manager.load_conversation(conversation_id)
        
        # Add system prompt if provided
        if system_prompt and not self.conversation_manager.has_system_message():
            await self.conversation_manager.add_system_message(system_prompt)
        
        # Add user message
        await self.conversation_manager.add_user_message(message)
        
        # Get model response
        ai_message = await self.conversation_manager.invoke_model(self.model)
        
        # Persist conversation
        conversation_id = await self.conversation_manager.persist_conversation(conversation_id)
        
        return ChatResponse(
            reply=ai_message.content,
            conversation_id=conversation_id,
            message_id=ai_message.id,
            usage_metadata=ai_message.usage_metadata,
            response_metadata=ai_message.response_metadata
        )
    
    async def stream_completion(
        self, 
        message: str, 
        conversation_id: Optional[UUID] = None
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Stream chat completion with message chunk assembly"""
        
        # Similar setup as chat_completion
        if conversation_id:
            await self.conversation_manager.load_conversation(conversation_id)
        
        await self.conversation_manager.add_user_message(message)
        
        # Stream response
        chunks = []
        async for chunk in self.model.astream(self.conversation_manager.messages):
            chunks.append(chunk)
            yield ChatStreamChunk(
                content=chunk.content,
                conversation_id=conversation_id,
                is_final=False
            )
        
        # Assemble final message and persist
        final_message = sum(chunks, start=AIMessage(content=""))
        self.conversation_manager.messages.append(final_message)
        conversation_id = await self.conversation_manager.persist_conversation(conversation_id)
        
        # Send final chunk with metadata
        yield ChatStreamChunk(
            content="",
            conversation_id=conversation_id,
            is_final=True,
            usage_metadata=final_message.usage_metadata
        )
```

## Implementation Boundaries for AI

### Files to CREATE:
```
src/agent_workbench/services/
├── __init__.py
├── llm_service.py           # Main ChatService class
├── providers.py             # Provider registry and configurations  
├── conversation_manager.py  # Message-based conversation handling
└── model_factory.py         # Model instantiation with provider configs

src/agent_workbench/models/
├── llm_models.py           # Pydantic models for LLM configs
├── message_models.py       # Enhanced message persistence models
└── conversation_models.py  # Conversation and chat response models

src/agent_workbench/core/
├── exceptions.py           # LLM-specific exception classes
└── retry.py               # Retry logic utilities

src/agent_workbench/api/routes/
└── chat.py                # Updated chat endpoints with message support
```

### Exact Function Signatures:

```python
# llm_service.py
class ChatService:
    def __init__(self, model_config: ModelConfig) -> None
    async def chat_completion(self, message: str, conversation_id: Optional[UUID] = None, system_prompt: Optional[str] = None) -> ChatResponse
    async def stream_completion(self, message: str, conversation_id: Optional[UUID] = None) -> AsyncGenerator[ChatStreamChunk, None]
    async def get_available_models(self, provider: str) -> List[str]

# conversation_manager.py
class ConversationManager:
    def __init__(self) -> None
    async def add_system_message(self, content: str) -> None
    async def add_user_message(self, content: str) -> None
    async def invoke_model(self, model: BaseChatModel) -> AIMessage
    async def load_conversation(self, conversation_id: UUID) -> None
    async def persist_conversation(self, conversation_id: Optional[UUID] = None) -> UUID

# API endpoints (chat.py)
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest, service: ChatService = Depends(get_chat_service)) -> ChatResponse

@router.post("/chat/stream")
async def stream_chat(request: ChatRequest, service: ChatService = Depends(get_chat_service)) -> StreamingResponse
```

### Updated Dependencies:
```toml
# Core LangChain (current stable)
langchain = "^0.3.27"
langchain-core = "^0.3.27"

# Provider packages (dedicated, not community)
langchain-openai = "^0.3.32"      # OpenAI + OpenRouter
langchain-ollama = "^0.3.7"       # Ollama integration
langchain-anthropic = "^0.3.25"   # Anthropic Claude

# Supporting libraries
httpx = "^0.25.0"                  # HTTP client for retries
tenacity = "^8.2.0"                # Retry logic
```

### FORBIDDEN Actions:
- Using deprecated `langchain-community` chat models
- Creating simple string-based conversation storage  
- Implementing UI components or Gradio integration
- Adding agent workflows or tool calling capabilities
- Creating document processing or RAG features
- Using outdated package versions or legacy imports
- Bypassing structured message types for simple strings

## Database Migration Required

### Alembic Migration for Enhanced Messages:
```python
# alembic/versions/xxx_enhance_message_schema.py
def upgrade():
    # Add new columns for structured message data
    op.add_column('messages', sa.Column('message_type', sa.String(20), nullable=False, server_default='human'))
    op.add_column('messages', sa.Column('additional_kwargs', sa.JSON(), nullable=True))
    op.add_column('messages', sa.Column('response_metadata', sa.JSON(), nullable=True))
    
    # Migrate existing data: role -> message_type
    # 'user' -> 'human', 'assistant' -> 'ai', 'system' -> 'system'
    
    # Remove old role column after migration
    op.drop_column('messages', 'role')
```

## Success Criteria
- ✅ Chat completions work with all provider packages (OpenAI, OpenRouter, Ollama, Anthropic)
- ✅ Structured message system properly handles SystemMessage, HumanMessage, AIMessage
- ✅ Streaming responses work with proper chunk assembly and final message persistence
- ✅ All conversations stored with structured message data and metadata
- ✅ Parameter validation prevents invalid model calls across all providers
- ✅ Error handling with retries for API failures using modern LangChain patterns
- ✅ >90% test coverage including mock provider tests with realistic message flows
- ✅ Database migrations handle existing data transition to structured message format

## Testing Strategy
- **Unit Tests**: Mock all provider ChatModels with realistic message responses
- **Integration Tests**: Real API calls to each provider with structured message validation
- **Conversation Tests**: Full conversation flows with persistence and retrieval
- **Migration Tests**: Verify smooth transition from old role-based to new message-type schema

---

**Key Changes from Original ADR:**
1. **Updated to current LangChain versions** (0.3.x series, preparing for 1.0)
2. **Modern provider packages** instead of legacy community imports
3. **Structured message architecture** with proper SystemMessage/HumanMessage/AIMessage handling
4. **Enhanced database schema** supporting rich message metadata
5. **Proper conversation management** with message-based persistence
6. **Streaming with chunk assembly** following current LangChain patterns

This architecture provides a solid foundation for the dual-model system and future agent capabilities while maintaining type safety and modern LangChain best practices.