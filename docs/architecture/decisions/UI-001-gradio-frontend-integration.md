UI-001: Gradio Frontend Integration
Status

Status: Ready for Implementation
Date: September 02, 2025
Decision Makers: Human Architect
Task ID: UI-001-gradio-frontend-integration
Dependencies: CORE-001 (FastAPI), CORE-002 (API routes), LLM-001 (chat service)

Context
Implement Gradio interface that calls FastAPI endpoints for chat functionality. Provides user-friendly interface for model selection, parameter control, and chat interactions with real-time streaming support.
Architecture Scope
What's Included:

 Gradio interface calling FastAPI endpoints via HTTP
 Basic chat interface with message history and streaming
 Model selection dropdown with provider switching
 Essential parameter controls (temperature, max_tokens, etc.)
 Real-time streaming response handling
 Error handling and validation feedback in UI
 Conversation persistence and history loading

What's Explicitly Excluded:

MCP tool integration or selection UI (MCP-002)
Document upload interface or URL input (DOC-001)
Agent mode toggle and controls (AGENT-001)
Advanced parameter controls (expandable sections)
Authentication or user management UI
File management or document processing UI

Architectural Decisions
1. Gradio-FastAPI Architecture
Separation Strategy:

Gradio UI as lightweight client calling FastAPI HTTP endpoints
No direct business logic in Gradio components
Type-safe API communication using Pydantic models
WebSocket support for streaming chat responses

2. UI Layout Structure
Single-Tab Layout (Phase 1):
┌─────────────────────────────────────────────────┐
│                 Agent Workbench                 │
├─────────────────┬───────────────────────────────┤
│  Settings Panel │        Chat Interface         │
│                 │                               │
│ Model Selection │     Message History           │
│ Provider: [▼]   │  ┌─────────────────────────┐   │
│ Model: [▼]      │  │ User: Hello             │   │
│                 │  │ Assistant: Hi there!   │   │
│ Parameters      │  │                         │   │
│ Temperature: [] │  └─────────────────────────┘   │
│ Max Tokens: []  │                               │
│                 │     Message Input             │
│                 │  ┌─────────────────────────┐   │
│                 │  │ Type message...         │   │
│                 │  │                    Send │   │
│                 │  └─────────────────────────┘   │
└─────────────────┴───────────────────────────────┘
3. State Management
Gradio State Approach:

Use Gradio State for conversation_id and model config
Minimal client-side state - server holds conversation history
Real-time updates through Gradio's reactive system
Error state handling with user feedback

4. API Integration Pattern
HTTP Client Approach:

Use httpx for async HTTP calls to FastAPI endpoints
Proper error handling for network and API errors
Streaming support through Server-Sent Events (SSE)
Type validation on responses using Pydantic models

Implementation Boundaries for AI
Files to CREATE:
src/agent_workbench/ui/
├── __init__.py
├── app.py                   # Main Gradio application
├── components/
│   ├── __init__.py
│   ├── chat.py              # Chat interface components
│   ├── settings.py          # Model selection and parameters
│   └── common.py            # Shared UI utilities
└── client.py                # FastAPI HTTP client

src/agent_workbench/main.py  # MODIFY: Add Gradio mounting
Exact Function Signatures:
python# app.py
def create_gradio_app() -> gr.Blocks
async def launch_gradio(host: str = "0.0.0.0", port: int = 7860)

# components/chat.py  
async def send_message(message: str, conversation_id: str, model_config: dict) -> tuple[str, str]
async def stream_response(message: str, conversation_id: str, model_config: dict) -> AsyncGenerator[str, None]
def create_chat_interface() -> gr.Column

# components/settings.py
def create_model_selection() -> gr.Row
def create_parameter_controls() -> gr.Column  
async def get_available_models(provider: str) -> list[str]

# client.py
class FastAPIClient:
    async def chat_completion(self, request: ChatRequest) -> ChatResponse
    async def stream_chat(self, request: ChatRequest) -> AsyncGenerator[str, None]
    async def get_conversations(self) -> List[ConversationResponse]
Additional Dependencies:
tomlgradio = "^4.15.0"
httpx = "^0.25.0"           # For API client
websockets = "^12.0"        # For streaming support
FORBIDDEN Actions:

Adding MCP tool selection or integration
Creating document upload or URL input interfaces
Implementing agent mode toggle or controls
Adding authentication or user management UI
Creating file management or document processing interfaces
Adding vector search or semantic capabilities UI

Success Criteria:

 Chat interface works with real-time streaming
 Model selection updates available models correctly
 Parameter changes affect chat behavior appropriately
 Conversation history persists and loads correctly
 Error messages display clearly to users
 All UI interactions call correct FastAPI endpoints
 Responsive design works on desktop browsers