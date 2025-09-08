LLM-001: LangChain Model Integration
Status

Status: Ready for Implementation
Date: September 02, 2025
Decision Makers: Human Architect
Task ID: LLM-001-langchain-model-integration
Dependencies: CORE-001 (FastAPI app), CORE-002 (conversation persistence)

Context
Implement LangChain ChatModels integration with Pydantic validation for multiple LLM providers. Provides unified interface for chat completions with type-safe parameter handling and conversation persistence.
Architecture Scope
What's Included:

 LangChain ChatModels wrapper with Pydantic validation
 Provider abstraction layer (OpenRouter, Ollama, direct providers)
 Model configuration system with parameter validation
 Basic chat completion functionality with streaming
 Integration with conversation persistence from CORE-002
 Error handling and retry logic for API calls

What's Explicitly Excluded:

UI integration or Gradio components (UI-001)
Agent workflows or tool calling (MCP-001, AGENT-001)
Document processing integration (DOC-001)
Complex conversation management beyond basic persistence
Vector embeddings or semantic capabilities

Architectural Decisions
1. LangChain Integration Architecture
Core Approach: Pydantic wrapper around LangChain ChatModels

Type-safe parameter validation before LangChain calls
Unified interface regardless of underlying provider
Streaming support through LangChain's async generators
Automatic conversation persistence after each interaction

2. Provider Support Strategy
Initial Providers:

OpenRouter: LangChain ChatOpenAI with custom base_url
Ollama: LangChain ChatOllama for local models
Direct Providers: OpenAI, Anthropic via LangChain ChatModels

Provider Configuration:
pythonclass ProviderConfig(BaseModel):
    provider_name: str
    chat_model_class: Type[BaseChatModel]  
    default_model: str
    api_key_env_var: Optional[str]
    base_url: Optional[str]
3. Model Parameter Management
Universal Parameters (supported by most providers):

temperature, max_tokens, top_p, frequency_penalty
streaming, system_prompt

Provider-Specific Parameters:

Stored in extra_params dict with validation
Passed through to LangChain model as kwargs

4. Chat Service Architecture
Service Layer Pattern:

ChatService class manages model instances and conversations
Async methods for chat completion with automatic persistence
Error handling with exponential backoff retry logic
Memory management for conversation context

Implementation Boundaries for AI
Files to CREATE:
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
Exact Function Signatures:
python# llm_service.py
class ChatService:
    def __init__(self, model_config: ModelConfig)
    async def chat_completion(self, message: str, conversation_id: Optional[UUID] = None) -> ChatResponse
    async def stream_completion(self, message: str, conversation_id: Optional[UUID] = None) -> AsyncGenerator[str, None]
    async def get_available_models(self, provider: str) -> List[str]

# chat_models.py  
class ModelConfig(BaseModel):
    provider: str
    model_name: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0, le=100000)
    streaming: bool = True
    system_prompt: Optional[str] = None

# API endpoints (chat.py)
@router.post("/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest, service: ChatService = Depends(get_chat_service))

@router.post("/chat/stream")  
async def stream_chat(request: ChatRequest, service: ChatService = Depends(get_chat_service))
Additional Dependencies:
tomllangchain = "^0.1.0"
langchain-community = "^0.3.25"
langchain-openai = "^0.0.8"
openai = "^1.6.0"           # For direct OpenAI integration
anthropic = "^0.8.0"        # For direct Anthropic integration
httpx = "^0.25.0"           # For HTTP retries
tenacity = "^8.2.0"         # For retry logic

FORBIDDEN Actions:
Creating UI components or Gradio integration
Implementing agent workflows or tool calling
Adding document processing or RAG capabilities
Creating complex conversation management beyond persistence
Adding authentication or user management
Implementing vector embeddings or semantic search

Success Criteria:
 Chat completions work with OpenRouter and Ollama
 Streaming responses work correctly
 All conversations automatically persisted to database
 Parameter validation prevents invalid model calls
 Error handling with retries for API failures
 >90% test coverage including mock provider tests