# CLAUDE.md

## Project Overview

Agent Workbench is a **LangGraph-centered dual-mode AI development platform** built on 8 core domain objects with protocol-based database abstraction.

- **Workbench Mode**: Technical interface for AI developers (English)
- **SEO Coach Mode**: Dutch business-friendly SEO coaching interface
- **Stack**: FastAPI + Gradio, LangGraph StateGraph, SQLAlchemy (async) + SQLite, HuggingFace Hub DB

## Commands

```bash
# Setup
make install          # Install deps (or: uv sync)
make dev              # Dev environment
make staging          # Staging environment
make prod             # Production environment

# Run
make start-app                # Workbench mode (default)
APP_MODE=seo_coach make start-app  # SEO Coach mode
make start-app-debug          # Debug logging
make start-app-verbose        # Max debug + API docs at /docs

# Test
make test                     # Full suite with coverage
make test-unit-only           # Quick unit tests (no backend)
make test-with-backend        # Auto-start backend + integration tests
make pre-commit               # Quality + tests

# Quality
make quality                  # Check (black, ruff, mypy)
make quality-fix              # Auto-fix formatting/linting

# Database
uv run alembic upgrade head   # Run migrations
make db-analyze               # Show tables and row counts
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
├── database/
│   ├── protocol.py               - DatabaseBackend Protocol
│   ├── adapter.py                - AdaptiveDatabase
│   ├── detection.py              - Environment detection
│   └── backends/
│       ├── sqlite.py             - SQLiteBackend
│       └── hub.py                - HubBackend (HF Spaces)
├── services/
│   ├── conversation_service.py   - Business logic
│   ├── state_manager.py          - State persistence
│   ├── langgraph_bridge.py       - State conversion (Bridge)
│   ├── simple_chat_workflow.py   - 2-node minimal workflow
│   └── consolidated_service.py   - Full workflow service
├── api/routes/
│   ├── chat_workflow.py          - PRIMARY workflow endpoints
│   ├── simple_chat.py            - Testing endpoints
│   ├── conversations.py          - Conversation CRUD
│   ├── messages.py               - Message CRUD
│   ├── agent_configs.py          - Agent config CRUD
│   └── health.py                 - Health checks
├── ui/
│   ├── mode_factory.py           - Mode-based interface factory
│   ├── app.py                    - Workbench interface
│   └── seo_coach_app.py          - SEO Coach interface (Dutch)
└── main.py                       - FastAPI app + Gradio mounting
```

## Conventions

- **Type hints required** on all function signatures (`disallow_untyped_defs = true`)
- Use `Optional[Type]` for nullable values, `TypedDict` for LangGraph state (not Pydantic)
- All code must pass: `black`, `ruff`, `mypy`, `pytest`
- **Do NOT implement Phase 2 features** (agent execution, MCP tools, multi-agent) unless explicitly requested

## Critical Pattern: Gradio + FastAPI Mounting

**DO NOT MODIFY** the mounting pattern in `main.py` without explicit approval. It is production-validated. See `.claude/docs/gradio-fastapi-pattern.md` for details.

Key rules: Database init BEFORE interface creation. Use `app.mount()` NOT `gr.mount_gradio_app()`. Both `queue()` and `run_startup_events()` are REQUIRED.

```bash
uv run python test_gradio_unified.py  # All 6 tests must pass before modifying Gradio code
```

## Git Workflow

- `main`: Production-ready
- `develop`: Integration/staging
- `arch/TASK-NAME`: Architecture planning (human)
- `feature/TASK-NAME`: Implementation (AI)
- Feature branches merge to `develop`

## Deployment

```bash
make start-app        # Local -> http://localhost:8000/
make docker-dev       # Docker dev
make docker-staging   # Docker staging
make docker-prod      # Docker production
```

HuggingFace Spaces: Auto-detected via `SPACE_ID`, uses Hub DB backend. Entry point: `deploy/hf-spaces/workbench/app.py`

## Detailed Reference (subdocs)

For deeper context, read these on-demand:

- `.claude/docs/domain-objects.md` — 8 core domain objects
- `.claude/docs/gradio-fastapi-pattern.md` — Critical Gradio+FastAPI mounting pattern
- `.claude/docs/workflow-architecture.md` — LangGraph workflow details + WorkbenchState
- `.claude/docs/database-architecture.md` — Protocol-based DB abstraction
- `.claude/docs/development-patterns.md` — Common patterns (nodes, bridge, modes, human-steered workflow)
- `.claude/docs/api-endpoints.md` — Full endpoint reference

## Key Documentation

- `docs/phase1/PHASE_1_IMPLEMENTATION.md` — **AUTHORITATIVE** Phase 1 architecture source
- `docs/phase1/GRADIO_STANDARDIZATION_COMPLETE.md` — Gradio mounting docs
- `docs/architecture/decisions/` — Architecture decision records

## Byterover MCP Integration

- Use `byterover-retrieve-knowledge` before each task
- Use `byterover-store-knowledge` after significant work
- Reference sources with "According to Byterover memory layer"
