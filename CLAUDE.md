# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Workbench is a **LangGraph-centered dual-mode AI development platform** built on 8 core domain objects with protocol-based database abstraction.

**Two Operational Modes:**
1. **Workbench Mode**: Technical interface for AI developers (English)
2. **SEO Coach Mode**: Dutch business-friendly SEO coaching interface

**Technology Stack:**
- FastAPI + Gradio (standardized mounting pattern)
- LangGraph StateGraph workflows
- SQLAlchemy (async) with SQLite backend
- HuggingFace Hub DB (for Spaces deployment)
- Protocol-based database abstraction

## Development Commands

### Environment Setup
```bash
# Install dependencies
make install  # or: uv sync

# Configure environment (choose one)
make dev      # Development environment
make staging  # Staging environment (develop branch)
make prod     # Production environment (main branch only)
```

### Running the Application
```bash
# Workbench mode (default)
make start-app

# SEO Coach mode
APP_MODE=seo_coach make start-app

# Debug modes (verbose logging)
make start-app-debug          # Debug logging
make start-app-verbose        # Maximum debug + API docs at /docs
```

### Testing
```bash
# Full test suite with coverage
make test

# Quick unit tests only (no backend required)
make test-unit-only

# Auto-start backend + run integration tests
make test-with-backend

# Pre-commit validation (quality + tests)
make pre-commit
```

### Code Quality
```bash
# Check code quality (black, ruff, mypy)
make quality

# Auto-fix formatting and linting issues
make quality-fix

# Individual tools
uv run black src/ tests/
uv run ruff check src/ tests/ --fix
uv run mypy src/
```

### Database Operations
```bash
# Run migrations
uv run alembic upgrade head

# Database analysis tools
make db-analyze                    # Show tables and row counts
make db-structure TABLE=table_name # Show table structure
make db-query TABLE=table_name     # Query table data
```

## Architecture: 8 Core Domain Objects

Phase 1 implements a **domain-driven architecture** with these core objects:

### 1. MESSAGE 💬
**Purpose:** Universal message format supporting agentic workflows

**Key Models:**
- `StandardMessage` (Pydantic): In-memory format with tool call support
- `MessageModel` (SQLAlchemy): Database persistence

**Features:**
- Multi-role: user, assistant, system, tool
- Tool calling: `tool_calls` and `tool_call_id` fields
- Extensible metadata

**Location:** `models/standard_messages.py`, `models/database.py`

### 2. CONVERSATION 💬📦
**Purpose:** Conversation lifecycle and persistence

**Key Models:**
- `ConversationResponse` (Pydantic): API response
- `ConversationModel` (SQLAlchemy): Database with cascade delete

**Service:** `ConversationService` (business logic layer)

**Location:** `models/consolidated_state.py`, `services/conversation_service.py`

### 3. STATE 🧠
**Purpose:** Dual-format state management (storage vs execution)

**Key Models:**
- `ConversationState` (Pydantic): Storage format - single source of truth
- `WorkbenchState` (TypedDict): LangGraph execution format
- `ValidatedWorkbenchState` (Pydantic): Validation wrapper

**Critical Pattern:**
```python
# Storage format (persisted)
ConversationState → WorkbenchState (via Bridge)
                    ↓
                LangGraph workflow execution
                    ↓
WorkbenchState → ConversationState (via Bridge)
```

**Location:** `models/standard_messages.py`, `models/consolidated_state.py`

### 4. WORKFLOW 🔄
**Purpose:** LangGraph StateGraph orchestration

**Implementations:**
- `SimpleChatWorkflow`: 2-node minimal workflow (testing/debugging)
- `ConsolidatedWorkbenchService`: Full multi-step workflow

**Primary Endpoint:** `POST /api/v1/chat/workflow`

**Location:** `services/simple_chat_workflow.py`, `services/consolidated_service.py`

### 5. CONTEXT 🌐
**Status:** ⚠️ Placeholder - needs Phase 2 implementation

**Current:** Basic structure in `WorkbenchState.context_data`

**Future:** Full context persistence, retrieval, and injection

**Location:** `services/context_service.py` (placeholder)

### 6. USER MODE 👤🎨
**Purpose:** Persona-based UI and workflow customization

**Current Modes:**
- `workbench`: Technical users, full model controls, debug tools
- `seo_coach`: Business users, Dutch language, business forms

**Pattern:**
```python
# ModeFactory creates mode-specific Gradio interfaces
factory = ModeFactory()
interface = factory.create_interface(mode="workbench")  # or "seo_coach"
```

**Location:** `ui/mode_factory.py`, `ui/app.py`, `ui/seo_coach_app.py`

### 7. AGENT/TOOL 🤖⚙️
**Status:** ❌ Config storage only - needs Phase 2 implementation

**Current:** `AgentConfigModel` for configuration storage

**Future:** Agent executor, tool registry, MCP integration

**Location:** `models/database.py`, `api/routes/agent_configs.py`

### 8. BRIDGE 🌉
**Purpose:** Convert between storage and execution formats

**Key Service:** `LangGraphStateBridge`

**Responsibilities:**
- `ConversationState` ↔ `WorkbenchState` conversion
- Context merging
- Message format translation
- Workflow state tracking

**Location:** `services/langgraph_bridge.py`

## Database Architecture: Protocol-Based Abstraction

**Design Pattern:** Protocol-based backend with environment auto-detection

```
Application Services
        ↓
AdaptiveDatabase (auto-selects backend)
        ↓
    ┌───┴───┐
    ↓       ↓
SQLiteBackend  HubBackend
    ↓           ↓
SQLAlchemy  HuggingFace Hub
```

### DatabaseBackend Protocol
**Location:** `database/protocol.py`

**Operations:**
- Conversation CRUD
- Message CRUD
- Business profile operations (SEO coach)
- Context operations

### Backends

**SQLiteBackend** (`database/backends/sqlite.py`)
- SQLAlchemy async models
- ThreadPoolExecutor bridge (async → sync Protocol)
- Used in: local development, Docker

**HubBackend** (`database/backends/hub.py`)
- HuggingFace Datasets wrapper
- Simple delegation pattern
- Used in: HuggingFace Spaces

**AdaptiveDatabase** (`database/adapter.py`)
- Environment detection: local/docker/hf_spaces
- Auto-selects appropriate backend
- Single API for all services

### Environment Detection
```python
# Automatic detection via environment variables
SPACE_ID → hf_spaces → HubBackend
/.dockerenv → docker → SQLiteBackend
default → local → SQLiteBackend
```

## Critical Production Pattern: Gradio + FastAPI Mounting

**⚠️ DO NOT MODIFY without explicit approval - this pattern is production-validated**

### The Standardized Pattern

```python
# Location: src/agent_workbench/main.py:74-141

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources and mount Gradio interface."""

    # 1. Initialize database FIRST
    db = await init_adaptive_database(mode=mode)
    app.adaptive_db = db

    # 2. Create Gradio interface
    gradio_interface = create_fastapi_mounted_gradio_interface()

    # 3. Apply queue and startup events
    gradio_interface.queue()
    gradio_interface.run_startup_events()

    # 4. Mount at root path using FastAPI's native mount
    app.mount("/", gradio_interface.app, name="gradio")

    yield

    # Cleanup
    await app.requests_client.aclose()

app = FastAPI(lifespan=lifespan)
```

### Why This Pattern Works

✅ **Lifecycle Order:**
1. Database initialized BEFORE interface creation
2. Interface created AFTER database ready
3. Mount happens BEFORE uvicorn accepts requests

✅ **Correct API Usage:**
- Uses `app.mount()` NOT `gr.mount_gradio_app()`
- Accesses `gradio_interface.app` (internal ASGI app)
- Mounts at root path "/" without redirect loops

✅ **Event System:**
- `queue()` enables async processing
- `run_startup_events()` initializes event handlers
- Both REQUIRED for responsive UI

### What Doesn't Work

❌ **Using gr.mount_gradio_app() at root:**
```python
# BROKEN - causes redirect loops
app = gr.mount_gradio_app(app, interface, path="/")
```

❌ **Mounting before database init:**
```python
# BROKEN - database not available
gradio_interface = create_interface()
app.mount("/", gradio_interface.app)
await init_database()
```

❌ **Forgetting startup events:**
```python
# BROKEN - buttons don't respond
gradio_interface.queue()
app.mount("/", gradio_interface.app)
# Missing: gradio_interface.run_startup_events()
```

### Testing the Pattern
```bash
# All 6 tests must pass before modifying Gradio code
uv run python test_gradio_unified.py
```

**Documentation:** `docs/phase1/GRADIO_STANDARDIZATION_COMPLETE.md`

## LangGraph Workflow Architecture

All chat interactions flow through LangGraph StateGraph workflows.

### Workflow State: WorkbenchState (TypedDict)

**Purpose:** LangGraph execution format (TypedDict required for StateGraph)

**Key Fields:**
```python
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
    conversation_history: List[StandardMessage]

    # Workflow orchestration
    workflow_mode: Literal["workbench", "seo_coach"]
    workflow_steps: List[str]
    execution_successful: bool

    # Mode-specific (SEO Coach)
    business_profile: Optional[Dict[str, Any]]
    coaching_phase: Optional[Literal["analysis", "recommendations", ...]]

    # Mode-specific (Workbench)
    debug_mode: Optional[bool]
    parameter_overrides: Optional[Dict[str, Any]]

    # Phase 2 extensions (agentic)
    mcp_tools_active: List[str]
    agent_state: Optional[Dict[str, Any]]
```

### Workflow Implementations

**SimpleChatWorkflow** (2-node minimal)
- Node 1: Process input (validation)
- Node 2: Generate response (LLM call)
- Used for: Testing, debugging

**ConsolidatedWorkbenchService** (full workflow)
- Multi-step StateGraph
- State persistence via Bridge
- Dual-mode routing (workbench/seo_coach)
- Used for: Production chat

### Complete Workflow Flow

```
1. User Input (Gradio UI)
2. POST /api/v1/chat/workflow
3. ConsolidatedWorkflowRequest (validation)
4. LangGraphStateBridge.load_into_langgraph_state()
   ├─ Load ConversationState from DB
   ├─ Convert to WorkbenchState
   └─ Inject user message
5. LangGraph StateGraph Execution
   ├─ Parse intent node
   ├─ Load context node
   ├─ Generate response node (LLM)
   └─ Format output node
6. LangGraphStateBridge.save_from_langgraph_state()
   ├─ Convert to ConversationState
   └─ Save to DB
7. ConsolidatedWorkflowResponse
8. Return to Gradio UI
```

## Human-Steered Development Workflow

This project uses a **human-steered architecture workflow** for feature development.

### Workflow Phases

**1. Architecture Phase (Human)**
```bash
make arch TASK=CORE-002-feature-name
```
Creates architecture document defining:
- Scope boundaries (included/excluded)
- Implementation boundaries (files to create/modify)
- Function signatures
- Success criteria

**2. Implementation Phase (AI)**
```bash
make feature TASK=CORE-002-feature-name
```
- Auto-merges architecture to develop
- Creates feature branch
- Generates implementation prompt
- AI implements within boundaries

**3. Validation Phase**
```bash
make validate TASK=CORE-002-feature-name
```
Comprehensive validation:
- Code quality (black, ruff, mypy)
- Test suite with coverage
- Scope compliance checks

**4. Completion Phase**
```bash
make complete TASK=CORE-002-feature-name
```
- Commits implementation
- Merges to develop
- Cleans up branches

### Quick Development Commands
```bash
make test-unit-only      # Fast iteration during development
make quality-fix         # Auto-fix formatting/linting
make test-with-backend   # Full integration testing
```

## API Endpoints

### PRIMARY: Full LangGraph Workflow
```
POST   /api/v1/chat/workflow         - Execute full workflow
POST   /api/v1/chat/workflow/stream  - Stream workflow execution
GET    /api/v1/chat/consolidated/state/{id} - Get conversation state
```

### UTILITY: Minimal Workflow (Testing)
```
POST   /api/v1/chat/simple           - Execute 2-node workflow
POST   /api/v1/chat/test-model       - Test model connectivity
GET    /api/v1/chat/providers        - List available providers
```

### CRUD Operations
```
# Conversations
POST   /api/v1/conversations
GET    /api/v1/conversations/{id}
GET    /api/v1/conversations
DELETE /api/v1/conversations/{id}

# Messages
POST   /api/v1/messages
GET    /api/v1/conversations/{id}/messages
DELETE /api/v1/messages/{id}

# Agent Configs (storage only in Phase 1)
POST   /api/v1/agent-configs
GET    /api/v1/agent-configs/{id}
```

### SEO Coach Specific
```
POST   /api/v1/chat/seo/business-profile
PUT    /api/v1/chat/seo/analysis/{id}
```

## Project Structure

```
src/agent_workbench/
├── models/
│   ├── standard_messages.py      - StandardMessage, ConversationState
│   ├── consolidated_state.py     - WorkbenchState, workflow models
│   ├── database.py               - SQLAlchemy models
│   ├── schemas.py                - Pydantic API schemas
│   └── business_models.py        - BusinessProfile, SEO models
│
├── database/
│   ├── protocol.py               - DatabaseBackend Protocol
│   ├── adapter.py                - AdaptiveDatabase
│   ├── detection.py              - Environment detection
│   └── backends/
│       ├── sqlite.py             - SQLiteBackend (async SQLAlchemy)
│       └── hub.py                - HubBackend (HF Datasets wrapper)
│
├── services/
│   ├── conversation_service.py   - Business logic
│   ├── state_manager.py          - State persistence
│   ├── langgraph_bridge.py       - State conversion (Bridge object)
│   ├── simple_chat_workflow.py   - 2-node minimal workflow
│   └── consolidated_service.py   - Full workflow service
│
├── api/routes/
│   ├── chat_workflow.py          - PRIMARY workflow endpoints
│   ├── simple_chat.py            - UTILITY testing endpoints
│   ├── conversations.py          - Conversation CRUD
│   ├── messages.py               - Message CRUD
│   ├── agent_configs.py          - Agent config CRUD
│   └── health.py                 - Health checks
│
├── ui/
│   ├── mode_factory.py           - Mode-based interface factory
│   ├── app.py                    - Workbench interface (technical)
│   └── seo_coach_app.py          - SEO Coach interface (Dutch)
│
└── main.py                       - FastAPI app + Gradio mounting
```

## Type Checking

This project enforces **strict typing** with mypy:

```toml
[tool.mypy]
disallow_untyped_defs = true      # All functions must have type hints
check_untyped_defs = true         # Check function bodies
disallow_incomplete_defs = true   # All parameters must be typed
```

**When writing new code:**
- All function signatures MUST include type hints
- Use `Optional[Type]` for nullable values
- Import types from `typing` module
- Use `TypedDict` for LangGraph state (not Pydantic)

## Common Development Patterns

### Adding a New LangGraph Workflow Node

```python
async def your_node(state: WorkbenchState) -> dict:
    """
    Process state and return updates.

    LangGraph merges returned dict into state.
    Don't need to return full state.
    """
    # Access state
    user_msg = state["user_message"]
    mode = state["workflow_mode"]

    # Process
    result = await process_something(user_msg, mode)

    # Return updates (will be merged)
    return {
        "assistant_response": result,
        "workflow_steps": state["workflow_steps"] + ["your_node"],
        "execution_successful": True
    }
```

### Working with the Bridge

```python
# Load for execution
lg_state = await bridge.load_into_langgraph_state(
    conversation_id=conv_id,
    user_message="Hello",
    workflow_mode="workbench"
)

# Execute workflow
final_state = await workflow.ainvoke(lg_state)

# Save after execution
await bridge.save_from_langgraph_state(final_state)
```

### Using AdaptiveDatabase

```python
# Initialize (auto-detects environment)
db = AdaptiveDatabase(mode="workbench")

# Use same API regardless of backend
conversation = db.get_conversation(conversation_id)
db.save_message(message_data)
messages = db.get_messages(conversation_id)
```

### Adding a New UI Mode

1. Create interface in `ui/your_mode_app.py`:
```python
def create_your_mode_app() -> gr.Blocks:
    with gr.Blocks(title="Your Mode") as app:
        # Build UI
        pass
    return app
```

2. Register in `ui/mode_factory.py`:
```python
class ModeFactory:
    def __init__(self):
        self.mode_registry = {
            "workbench": create_workbench_app,
            "seo_coach": create_seo_coach_app,
            "your_mode": create_your_mode_app,  # Add here
        }
```

3. Add mode-specific state fields to `WorkbenchState`
4. Add tests in `tests/ui/test_your_mode.py`

## Phase 1 vs Phase 2

**Phase 1 (Current - COMPLETE):**
- ✅ 8 core domain objects
- ✅ Protocol-based database abstraction
- ✅ LangGraph StateGraph workflows
- ✅ Dual-mode UI (workbench + seo_coach)
- ✅ Standardized Gradio + FastAPI mounting
- ✅ HuggingFace Spaces deployment

**Phase 2 (Future - PLANNED):**
- ❌ Active agent execution framework
- ❌ MCP tool integration
- ❌ Multi-agent coordination
- ❌ Agent memory and learning
- ❌ Full context service implementation
- ❌ Dynamic tool selection

**Do NOT implement Phase 2 features unless explicitly requested.**

## Deployment

### Local Development
```bash
make dev
make start-app
# → http://localhost:8000/
```

### Docker
```bash
make docker-dev       # Development
make docker-staging   # Staging (mirrors production)
make docker-prod      # Production
```

### HuggingFace Spaces

**Auto-detection via SPACE_ID:**
- Detects Spaces environment
- Uses Hub DB backend automatically
- No local filesystem required

**Entry point:** `deploy/hf-spaces/workbench/app.py`

## Debugging

### Debug Mode
```bash
make start-app-debug    # Debug logging
make start-app-verbose  # Maximum verbosity + API docs
```

**When verbose:**
- API docs: http://localhost:8000/docs
- Request/response logging
- SQL query logging (SQLALCHEMY_ECHO=1)
- CORS debug headers

### Common Issues

**Gradio Interface Not Loading:**
- Run `uv run python test_gradio_unified.py` (all 6 tests must pass)
- Check APP_MODE environment variable
- Check logs for import errors

**Database Errors:**
- `make db-analyze` to check database state
- `uv run alembic upgrade head` to run migrations
- Verify DATABASE_URL in environment

**Type Errors:**
- `make quality` to see all type issues
- Add type hints to all function signatures
- Use `Optional[Type]` for nullable values

## Git Workflow

**Branches:**
- `main`: Production-ready code
- `develop`: Integration branch for staging
- `arch/TASK-NAME`: Architecture planning (human)
- `feature/TASK-NAME`: Implementation (AI)

**Branch Safety:**
- Production deploys only from `main`
- Staging deploys from `develop`
- Feature branches merge to `develop`

## Code Quality Standards

All code must pass:
- `black` (formatting)
- `ruff` (linting)
- `mypy` (type checking)
- `pytest` (test suite)

Run `make quality-fix` to auto-fix most issues before committing.

## Key Documentation References

**Phase 1 Implementation:**
- `docs/phase1/PHASE_1_IMPLEMENTATION.md` - **AUTHORITATIVE** source for Phase 1 architecture
- `docs/phase1/GRADIO_STANDARDIZATION_COMPLETE.md` - Gradio mounting pattern
- `docs/architecture/decisions/Phase 1 Realigned scope dependencies and completion.md` - Component dependencies

**Architecture Decisions:**
- `docs/architecture/decisions/` - Individual task architecture documents
- `docs/architecture/decisions/DECISION_TEMPLATE.md` - Template for new decisions

**Testing:**
- `test_gradio_unified.py` - Gradio mounting validation (6/6 must pass)

## Byterover MCP Integration

**Onboarding Workflow:**
1. Check handbook existence
2. Create/update handbook
3. Store/update modules

**Planning Workflow:**
1. Retrieve active plans
2. Save implementation plans
3. Retrieve knowledge for tasks
4. Update plan progress
5. Store knowledge after implementation

**Critical Rules:**
- Use `byterover-retrieve-knowledge` before each task
- Use `byterover-store-knowledge` after significant work
- Reference sources with "According to Byterover memory layer"
