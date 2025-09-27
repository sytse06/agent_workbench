# Product Requirements Document: Agent Workbench

## Project Overview

### Vision
Agent Workbench is a LangGraph-powered application providing robust workflow orchestration for AI development and specialized use cases. Built on production-proven state management patterns with dual-mode deployment supporting both technical AI development (workbench mode) and Dutch SEO coaching (seo_coach mode).

### Core Value Propositions
1. **Production-Proven State Management**: LangGraph workflows with TypedDict state models
2. **Dual Target Markets**: Technical users + Dutch small businesses through mode switching
3. **Workflow-First Architecture**: All interactions orchestrated through LangGraph state machines
4. **Universal LLM Support**: Provider-agnostic integration through LangChain foundation
5. **Rapid Deployment**: Single codebase deployed in multiple configurations

## Target Audiences

### Primary: Technical Users (Workbench Mode)
- AI developers and researchers working with workflow orchestration
- Teams needing robust state management for complex AI interactions
- Users requiring fine-grained control over multi-step AI processes

### Secondary: Dutch Small Businesses (SEO Coach Mode)
- Small business owners (1-50 employees) in Netherlands/EU
- Marketing agencies seeking white-label SEO coaching tools
- Businesses preparing for AI-optimized web presence

## System Architecture

### LangGraph-Centered Architecture

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Gradio UI     │───▶│   FastAPI Router     │───▶│   LangGraph Core    │
│ (Mode-Specific) │    │  (HTTP Interface)    │    │ (State Orchestra.)  │
└─────────────────┘    └──────────────────────┘    └─────────────────────┘
                                                             │
                        ┌─────────────────────────────────────┼─────────────────────────────────────┐
                        ▼                                     ▼                                     ▼
              ┌─────────────────┐                ┌─────────────────┐                ┌─────────────────┐
              │ Workflow Nodes  │                │ State Manager   │                │ LLM Services    │
              │                 │                │                 │                │                 │
              │ • load_conv     │                │ • TypedDict     │                │ • LangChain     │
              │ • process_msg   │                │ • Persistence   │                │ • Universal     │
              │ • generate_resp │                │ • Context Mgmt  │                │ • Streaming     │
              │ • save_state    │                │                 │                │                 │
              └─────────────────┘                └─────────────────┘                └─────────────────┘
```

### Key Architectural Decisions
- **LangGraph as Core**: All state management and workflow orchestration through LangGraph
- **FastAPI as HTTP Layer**: Lightweight HTTP interface for workflow execution
- **Gradio as UI Layer**: Mode-specific interfaces calling workflow endpoints
- **SQLite + LangGraph State**: Persistent storage bridged with workflow state
- **Mode-Based Deployment**: Single codebase, environment-controlled behavior

## Core Features

### 1. LangGraph Workflow System

**Production-Proven State Management**:
- TypedDict state models following GAIA agent patterns
- Conditional workflow routing based on user intent and context
- Error handling and retry logic within workflow nodes
- Real-time state persistence and recovery

**Workflow Node Architecture**:
```python
class WorkbenchState(TypedDict):
    # Core conversation
    conversation_id: UUID
    user_message: str
    assistant_response: Optional[str]
    
    # Workflow control
    workflow_mode: Literal["workbench", "seo_coach"]
    workflow_steps: List[str]
    execution_successful: bool
    
    # Context and state
    model_config: ModelConfig
    context_data: Dict[str, Any]
    conversation_history: List[StandardMessage]
```

### 2. Dual-Mode Operation

**Workbench Mode** (Technical Users):
- Full workflow monitoring and control
- Model parameter tuning and provider switching
- State inspection and debugging capabilities
- Advanced context injection and manipulation

**SEO Coach Mode** (Business Users):
- Simplified Dutch interface with business context
- Automated SEO analysis workflow integration
- Progress tracking and coaching guidance
- Hidden technical complexity with guided interactions

### 3. Universal LLM Integration

**LangChain Foundation**:
- Proven provider abstraction through LangChain ChatModels
- OpenRouter, Ollama, OpenAI, Anthropic support
- Streaming response capabilities
- Retry logic and error handling

**Model Configuration Management**:
- Per-conversation model settings
- Mode-specific default configurations
- Dynamic parameter adjustment within workflows

### 4. State Management System

**LangGraph + Database Bridge**:
- TypedDict workflow state in memory
- SQLite persistence for conversation history
- Bidirectional state synchronization
- Context data injection from external sources

**Conversation Lifecycle**:
- Automatic state loading from database
- Workflow execution with state transitions  
- State persistence after completion
- Error recovery and rollback capabilities

## Technical Stack

### Core Technologies
- **Workflow Engine**: LangGraph for state management and orchestration
- **Backend API**: FastAPI with async/await support
- **Frontend UI**: Gradio with mode-specific interfaces
- **LLM Integration**: LangChain ChatModels for provider abstraction
- **Database**: SQLite with Alembic migrations
- **Package Management**: UV for fast dependency management

### State Management
- **LangGraph StateGraph**: Core workflow orchestration
- **TypedDict Models**: Type-safe state definitions
- **Database Bridge**: SQLite persistence with state synchronization
- **Context Integration**: External data injection capabilities

### Deployment Infrastructure
- **Containerization**: Docker with UV-based builds
- **Environment Control**: APP_MODE switching for deployment modes
- **Cloud Deployment**: HuggingFace Spaces (CPU tier)
- **Local Development**: Docker Compose with hot reloading

## Data Models

### LangGraph State Models
```python
class WorkbenchState(TypedDict):
    # Core workflow state
    conversation_id: UUID
    user_message: str
    assistant_response: Optional[str]
    
    # Configuration
    model_config: ModelConfig
    workflow_mode: Literal["workbench", "seo_coach"]
    
    # Execution tracking
    workflow_steps: List[str]
    current_operation: Optional[str]
    execution_successful: bool
    current_error: Optional[str]
    retry_count: int
    
    # Context and memory
    context_data: Dict[str, Any]
    active_contexts: List[str]
    conversation_history: List[StandardMessage]
    
    # Mode-specific extensions
    business_profile: Optional[Dict[str, Any]]
    seo_analysis: Optional[Dict[str, Any]]
    coaching_context: Optional[Dict[str, Any]]
```

### Database Models (Persistence Layer)
```python
class ConversationState(BaseModel):
    conversation_id: UUID
    messages: List[StandardMessage]
    model_config: ModelConfig
    context_data: Dict[str, Any]
    active_contexts: List[str]
    metadata: Dict[str, Any]
    updated_at: datetime

class BusinessProfile(BaseModel):
    business_id: UUID
    business_name: str
    website_url: str
    business_type: str
    target_market: str = "Nederland"
    seo_experience_level: str = "beginner"
```

## Development Phases

### Phase 1: LangGraph Foundation (Weeks 1-8)

#### CORE-001: Project Foundation (Week 1)
**Architecture Scope**:
- UV-based dependency management with pyproject.toml
- Docker containerization with APP_MODE support
- FastAPI application structure with async support
- SQLite database with Alembic migration system

**Implementation Boundaries**:
- CREATE: Basic project structure with mode switching capability
- ADD: Environment variable configuration for dual modes
- FORBIDDEN: LLM integrations, UI components, workflow logic

#### CORE-002: Database Models (Week 1-2)
**Architecture Scope**:
- SQLAlchemy models for conversations and state persistence
- Pydantic schemas for API contracts and validation
- Database schema supporting both workbench and SEO coach modes
- Alembic migrations for schema versioning

**Database Extensions**:
```sql
-- Core conversation tables
CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255),
    model_config JSON,
    workflow_mode VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP
);

-- LangGraph state bridge
CREATE TABLE conversation_states (
    conversation_id VARCHAR(36) PRIMARY KEY REFERENCES conversations(id),
    state_data JSON NOT NULL,
    context_data JSON,
    active_contexts JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SEO Coach specific
CREATE TABLE business_profiles (
    id VARCHAR(36) PRIMARY KEY,
    business_name VARCHAR(255),
    website_url VARCHAR(255) NOT NULL,
    business_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### LLM-002: LangGraph State Management (Week 2-4)
**Architecture Scope**:
- LangGraph StateGraph for workflow orchestration
- TypedDict state models for type-safe transitions
- Integration with database persistence layer
- Workflow nodes for core operations (load, process, generate, save)
- Conditional routing for dual-mode operation

**Core Workflow Implementation**:
```python
class WorkbenchLangGraphService:
    def _build_workflow(self) -> StateGraph:
        builder = StateGraph(WorkbenchState)
        
        # Core nodes
        builder.add_node("load_conversation", self._load_conversation_node)
        builder.add_node("process_message", self._process_message_node)
        builder.add_node("workbench_chat", self._workbench_chat_node)
        builder.add_node("seo_coaching", self._seo_coaching_node)
        builder.add_node("generate_response", self._generate_response_node)
        builder.add_node("save_state", self._save_state_node)
        
        # Conditional routing
        builder.add_conditional_edges(
            "process_message",
            self._route_by_mode,
            {"workbench": "workbench_chat", "seo_coach": "seo_coaching"}
        )
        
        return builder.compile()
```

#### UI-001: Dual-Mode Gradio Interface (Week 4-6)
**Architecture Scope**:
- Mode-specific Gradio interfaces (workbench vs seo_coach)
- Workflow API client for LangGraph endpoint communication
- Real-time workflow step monitoring
- Error handling and state recovery in UI

**Interface Implementations**:
- **Workbench Interface**: Technical controls, workflow monitoring, advanced parameters
- **SEO Coach Interface**: Simplified Dutch business interface, automated workflows

**UI Building Testing Strategy (PROD-001A)**:
Following the FastAPI ↔ Gradio ↔ Database triangle testing approach:

```
    FastAPI App
       /  \
      /    \
   Gradio  Database
     \    /
      \  /
    Tests
```

**Triangle Validation Framework**:
- **FastAPI Health**: `/health` endpoint responds successfully
- **Gradio Queue Fix**: UI mounting with `queue() + run_startup_events()` prevents unresponsiveness
- **Database Tables**: SQLAlchemy models (ConversationModel, MessageModel) exist and accessible

**UI Building Transparency Analysis**:
- **Complexity Score**: 10 components (above manageable threshold of 5)
- **Flow Mapping**: main.py → ModeFactory → mode-specific create_*_app()
- **Mode Factory**: Two-mode system (workbench/seo_coach) with clear boundaries
- **AST Analysis**: `python3 scripts/ui_building_analyzer.py` for debugging complex UI building issues

**Test Implementation**:
Essential tests added to `tests/ui/test_gradio_integration.py`:
1. `test_gradio_queue_fix_validation()` - Validates queue fix prevents UI unresponsiveness
2. `test_database_tables_exist()` - Prevents "burned hands" by validating DB schema

This testing strategy provides transparency into UI building complexity that may cause confusion during development, while ensuring the core FastAPI-Gradio-Database integration works reliably.

#### DEPLOY-001: Mode-Based Deployment (Week 7-8)
**Architecture Scope**:
- Docker deployment with APP_MODE environment control
- Environment-specific configurations
- HuggingFace Spaces deployment patterns
- Local development with hot reloading

**Deployment Configurations**:
```bash
# Workbench deployment
docker run -e APP_MODE=workbench agent-workbench

# SEO Coach deployment  
docker run -e APP_MODE=seo_coach agent-workbench
```

### Phase 2: Advanced Workflows & UI Enhancement (Weeks 9-16)

#### UI-002: Advanced Gradio UI Building (Week 9-10)
**Enhanced UI Components**:
- Advanced chat interfaces with streaming support
- Real-time workflow monitoring dashboards
- Interactive parameter tuning controls
- State inspection and debugging panels

**UI Building Strategy**:
Building on PROD-001A triangle testing foundation:
- **Mode Factory Expansion**: Support for custom mode registration and extension
- **Component Library**: Reusable Gradio components for both workbench and seo_coach modes
- **UI State Management**: Bidirectional sync between Gradio state and LangGraph workflows
- **Error Handling UI**: User-friendly error displays with recovery options

**Testing Approach**:
- Leverage existing triangle validation framework
- Extend `test_gradio_queue_fix_validation()` for advanced components
- AST analysis for component complexity monitoring
- UI integration tests for mode-specific interfaces

#### MCP-001: Tool Integration Workflows (Week 10-12)
- LangGraph nodes for MCP tool execution
- Firecrawl integration for SEO analysis workflows
- Tool result processing and context injection
- Multi-step workflow orchestration with tool calling

#### UI-003: Interactive Workflow Visualization (Week 13-14)
**Visual Workflow Components**:
- Real-time workflow step visualization in Gradio
- Interactive workflow debugging interfaces
- State transition monitoring dashboards
- Performance metrics visualization

**Advanced UI Features**:
- Workflow step-by-step execution controls
- State inspection with JSON viewers
- Interactive parameter adjustment during execution
- Visual workflow branching displays

#### AGENT-001: Advanced Agent Patterns (Week 15-16)
- Hierarchical agent workflows following GAIA patterns
- Multi-agent coordination through LangGraph
- Complex decision trees and workflow branching
- Agent state persistence and recovery

## Success Metrics

### Technical Metrics
- **Workflow Execution**: <3 seconds for simple chat, <10 seconds for complex workflows
- **State Persistence**: 100% state recovery after system restart
- **Error Recovery**: <2% permanent workflow failures
- **Mode Switching**: 100% successful deployment in both modes

### User Experience Metrics
- **Workbench Users**: >4.0/5.0 rating for workflow transparency and control
- **SEO Coach Users**: >90% task completion rate for business users
- **Response Quality**: Consistent output quality across all workflow paths

### Development Metrics
- **Workflow Maintainability**: Clear separation of concerns between nodes
- **State Management**: Type-safe state transitions with full error handling
- **Deployment Reliability**: >99% successful deployments across environments

## Environment Configuration

### Core Environment Variables
```bash
# Application Mode
APP_MODE=workbench|seo_coach

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/agent_workbench.db

# LLM Providers
OPENROUTER_API_KEY=your_key_here
OLLAMA_BASE_URL=http://localhost:11434

# Server Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
GRADIO_HOST=0.0.0.0  
GRADIO_PORT=7860

# LangGraph Configuration
LANGGRAPH_DEBUG=false
WORKFLOW_TIMEOUT_SECONDS=30
MAX_WORKFLOW_RETRIES=3
```

### Mode-Specific Settings
```bash
# Workbench Mode
DEFAULT_MODEL_CONFIG={"provider": "openrouter", "model": "qwen/qwq-32b-preview", "temperature": 0.7}
ENABLE_WORKFLOW_DEBUG=true
SHOW_ADVANCED_CONTROLS=true

# SEO Coach Mode
DUTCH_COACHING_MODEL={"provider": "openrouter", "model": "openai/gpt-4o-mini", "system_prompt": "Dutch SEO expert..."}
ENABLE_BUSINESS_CONTEXT=true
SIMPLIFIED_INTERFACE=true
```

## Future Roadmap

### Enhanced Workflow Capabilities
- Visual workflow builder for custom workflow creation
- Workflow templates for common AI development patterns
- Multi-modal workflow nodes (vision, audio, document processing)

### Advanced SEO Features
- Automated competitor analysis workflows
- SEO performance tracking and alerting
- Integration with Dutch marketing platforms

### Enterprise Features
- Multi-tenant workflow isolation
- Team collaboration on workflow development
- Enterprise deployment patterns (Kubernetes, cloud providers)

### Ecosystem Integration
- Workflow marketplace for sharing patterns
- Integration with popular AI development tools
- API ecosystem for third-party workflow extensions

---

This PRD establishes LangGraph as the foundational architecture for Agent Workbench, enabling both technical AI development workflows and specialized business applications through a single, robust platform. The dual-mode approach allows targeting different markets while maintaining shared infrastructure and proven workflow patterns.