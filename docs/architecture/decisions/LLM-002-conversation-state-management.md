LLM-002: Conversation State Management
Status
Status: Ready for Implementation
Date: September 09, 2025
Decision Makers: Human Architect
Task ID: LLM-002-conversation-state-management
Dependencies: LLM-001 (chat foundation), CORE-002 (enhanced schema)
Context
Implement LangGraph-based conversation state management to transform the stateless chat service from LLM-001 into a context-aware, persistent conversation system. Provides the foundation for external context integration and advanced agent workflows while maintaining full backward compatibility with LLM-001.
Architecture Scope
What's Included:

LangGraph state management for persistent conversation context
Enhanced conversation lifecycle management
Context integration interface for external systems
Stateful conversation handling across sessions
Database schema extensions for state persistence
Migration path from LLM-001 stateless to stateful conversations
Advanced conversation management endpoints

What's Explicitly Excluded:

UI integration or Gradio components (UI-001)
Document processing logic or file handling (DOC-001)
MCP tool integration or agent workflows (MCP-001, AGENT-001)
Vector embeddings or semantic search capabilities
Authentication or user management
Direct LangChain ChatModel modifications (handled by LLM-001)

Architectural Decisions
1. LangGraph State Architecture
Core State Definition:
pythonfrom typing import TypedDict, Annotated, Sequence, Optional, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from datetime import datetime

class ConversationState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    model_config: ModelConfig  # From LLM-001
    context_data: Dict[str, Any]  # External context from DOC-001, etc.
    active_contexts: List[str]    # Context source identifiers
    metadata: Dict[str, Any]      # Conversation metadata
    updated_at: datetime
State Management Benefits:

Persistent conversation memory across sessions
Natural integration point for external context (documents, tools)
Foundation for future agent workflows
Eliminates "goldfish memory" problem of stateless LLMs

2. Database Schema Extension
Enhanced CORE-002 Schema:
sql-- Add to existing conversations table
ALTER TABLE conversations ADD COLUMN model_config JSON;

-- New table for LangGraph state persistence
CREATE TABLE conversation_states (
    conversation_id VARCHAR(36) PRIMARY KEY REFERENCES conversations(id),
    state_data JSON NOT NULL,
    context_sources JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for performance
CREATE INDEX idx_conversation_states_updated ON conversation_states(updated_at);
CREATE INDEX idx_conversation_states_context ON conversation_states USING GIN (context_sources);
3. State Persistence Strategy
Automatic State Management:

State automatically saved after each chat interaction
Lazy loading of conversation state on first access
State compression for long conversations
Context source tracking for external integrations

Migration from LLM-001:

Existing conversations automatically upgraded to stateful
Backward compatibility maintained for LLM-001 endpoints
Gradual migration path without breaking changes

4. Context Integration Architecture
External Context Flow:
python# External systems (DOC-001) update conversation state
def update_conversation_context(
    conversation_id: UUID,
    context_data: Dict[str, Any],
    context_sources: List[str]
):
    state = load_conversation_state(conversation_id)
    state["context_data"].update(context_data)
    state["active_contexts"].extend(context_sources)
    save_conversation_state(conversation_id, state)

# LLM service reads context from state naturally
def build_context_aware_messages(state: ConversationState, message: str) -> List[BaseMessage]:
    messages = list(state["messages"])
    
    if state.get("context_data"):
        context_prompt = create_context_prompt(state["context_data"])
        messages.insert(-1, context_prompt)  # Insert before latest user message
    
    messages.append(HumanMessage(content=message))
    return messages
5. LangGraph Workflow Integration
Simple Chat Workflow:
pythonfrom langgraph.graph import StateGraph, END

def create_chat_workflow() -> StateGraph:
    workflow = StateGraph(ConversationState)
    
    workflow.add_node("load_context", load_conversation_context)
    workflow.add_node("chat_completion", chat_completion_node)
    workflow.add_node("save_state", save_conversation_state_node)
    
    workflow.add_edge("load_context", "chat_completion")
    workflow.add_edge("chat_completion", "save_state")
    workflow.add_edge("save_state", END)
    
    workflow.set_entry_point("load_context")
    return workflow.compile()
Implementation Boundaries for AI
Files to CREATE:
src/agent_workbench/services/
├── state_manager.py         # LangGraph state persistence
├── conversation_manager.py  # Enhanced conversation lifecycle
└── context_service.py       # Context integration interface

src/agent_workbench/core/
├── chat_state.py           # LangGraph state definitions
└── workflow.py             # Basic chat workflow

src/agent_workbench/api/routes/
├── conversations.py        # Enhanced conversation management
└── context.py             # Context integration endpoints

src/agent_workbench/models/
└── conversation_state.py  # Database model for state persistence
Files to MODIFY:
src/agent_workbench/services/llm_service.py  # Add state management integration
src/agent_workbench/api/routes/chat.py       # Add stateful endpoints
Exact Function Signatures:
python# state_manager.py
class StateManager:
    async def load_conversation_state(self, conversation_id: UUID) -> ConversationState
    async def save_conversation_state(self, conversation_id: UUID, state: ConversationState) -> None
    async def create_default_state(self, conversation_id: UUID, model_config: ModelConfig) -> ConversationState
    async def migrate_conversation_to_state(self, conversation_id: UUID) -> ConversationState

# conversation_manager.py
class ConversationManager:
    async def create_conversation(self, title: Optional[str] = None, model_config: Optional[ModelConfig] = None) -> UUID
    async def get_conversations(self, limit: int = 50) -> List[ConversationSummary]
    async def delete_conversation(self, conversation_id: UUID) -> bool
    async def update_conversation_config(self, conversation_id: UUID, config: ModelConfig) -> None
    async def get_conversation_state(self, conversation_id: UUID) -> ConversationState

# context_service.py
class ContextService:
    async def update_conversation_context(self, conversation_id: UUID, context_data: Dict[str, Any], sources: List[str]) -> None
    async def clear_conversation_context(self, conversation_id: UUID, source: Optional[str] = None) -> None
    async def get_active_contexts(self, conversation_id: UUID) -> List[str]

# Enhanced LLM service (MODIFY llm_service.py)
class ChatService:
    # Add state management methods
    async def chat_completion_stateful(self, message: str, conversation_id: UUID) -> Tuple[ChatResponse, ConversationState]
    async def stream_completion_stateful(self, message: str, conversation_id: UUID) -> AsyncGenerator[str, None]

# API endpoints
@router.get("/conversations", response_model=List[ConversationSummary])
async def get_conversations()

@router.post("/conversations", response_model=ConversationResponse)  
async def create_conversation(request: CreateConversationRequest)

@router.get("/conversations/{conversation_id}/state", response_model=ConversationStateResponse)
async def get_conversation_state(conversation_id: UUID)

@router.put("/conversations/{conversation_id}/context")
async def update_conversation_context(conversation_id: UUID, request: ContextUpdateRequest)

# Enhanced chat endpoints (MODIFY chat.py)
@router.post("/chat/stateful", response_model=ChatResponse)
async def chat_completion_stateful(request: ChatRequest)

@router.post("/chat/stateful/stream")
async def stream_chat_stateful(request: ChatRequest)
Additional Dependencies:
tomllanggraph = "^0.2.28"      # LangGraph state management
sqlalchemy = "^2.0.0"      # Enhanced database models
alembic = "^1.12.0"        # Database migrations
FORBIDDEN Actions:

Creating UI components or Gradio integration
Implementing document processing or file handling logic
Adding MCP tool calling or agent decision-making
Modifying core LangChain ChatModel functionality from LLM-001
Adding authentication or user management
Implementing vector embeddings or semantic search

Integration Points
1. LLM-001 Integration
Backward Compatibility:

All LLM-001 endpoints continue to work unchanged
Stateless endpoints automatically create minimal state
Gradual migration path from stateless to stateful

Enhanced Functionality:
python# LLM-001 stateless endpoint still works
POST /chat  # Creates temporary state, discards after response

# LLM-002 adds stateful endpoints
POST /chat/stateful  # Uses persistent conversation state
POST /chat/stateful/stream  # Stateful streaming
2. UI-001 Integration
Enhanced Conversation Management:
python# Provides additional endpoints for UI-001:
GET /conversations                    # List conversations with state info
POST /conversations                   # Create with model config
GET /conversations/{id}/state         # Get full conversation state
PUT /conversations/{id}/context       # Update context (for future use)
3. DOC-001 Integration Preparation
Context Integration Interface:
python# DOC-001 can update conversation context via:
PUT /conversations/{id}/context
{
  "context_data": {"documents": [...], "summaries": [...]},
  "sources": ["doc1.pdf", "web_page_1"]
}

# Context flows naturally through state to chat completion
4. AGENT-001 Foundation
State Extension Ready:
python# Future agent state extends conversation state
class AgentState(ConversationState):
    active_tools: List[str]
    tool_results: Dict[str, Any]
    agent_reasoning: Optional[str]
    
# Same state management infrastructure supports agent workflows
Migration Strategy
Phase 1: Infrastructure Setup

Deploy database schema changes
Implement state management infrastructure
Add stateful endpoints alongside existing ones

Phase 2: Gradual Migration

UI-001 can optionally use stateful endpoints
Existing conversations automatically upgrade on first stateful access
Performance monitoring and optimization

Phase 3: Context Integration

DOC-001 integrates via context update endpoints
Full context-aware conversations
Advanced conversation management features

Success Criteria
Core State Management:

 LangGraph state persistence working correctly
 All conversation state automatically saved/loaded
 Context integration interface functional
 Migration from LLM-001 conversations seamless

Integration Requirements:

 Backward compatibility with LLM-001 maintained
 Enhanced conversation management endpoints working
 Context update endpoints ready for DOC-001 integration
 State performance acceptable (<500ms for state operations)

Database & Migration:

 Database schema migrations successful
 Existing conversations migrate to stateful without data loss
 State compression working for long conversations
 Context source tracking accurate

Foundation for Future:

 State structure extensible for agent workflows
 Context integration tested with mock external data
 Performance benchmarks established for state operations
 >90% test coverage for state management functionality

Implementation Philosophy
LLM-002 transforms the stateless chat foundation from LLM-001 into a context-aware, persistent conversation system. The key architectural principle is state as the communication channel between components:
Memory Persistence: Conversations maintain full context across sessions, solving the "goldfish memory" problem of traditional stateless LLMs
Context Flow: External systems integrate by updating conversation state rather than complex injection APIs
Future Foundation: The LangGraph state architecture provides the foundation for agent workflows while maintaining the simplicity of the chat interface
Seamless Evolution: Existing LLM-001 functionality remains unchanged, with stateful capabilities added as enhancements rather than replacements
This approach creates a robust, scalable foundation for advanced AI workbench capabilities while preserving the reliability and simplicity established in LLM-001.