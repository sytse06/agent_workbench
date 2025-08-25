# Agent Workbench PRD

## Vision
Agent Workbench: Robust, type-safe interaction with multiple LLM providers through unified interface.

## Core Features
1. **FastAPI Backend** - Async HTTP API
2. **Gradio Frontend** - Lightweight UI  
3. **LangChain Integration** - Universal LLM support
4. **SQLite + Alembic** - Database with migrations
5. **Pydantic** - Type safety throughout

## Development Tasks

### CORE-001: Foundation
- UV dependency management with pyproject.toml
- FastAPI application structure  
- SQLite database with Alembic
- Basic project setup

### LLM-001: Model Integration  
- LangChain ChatModels wrapper
- Provider abstraction (OpenAI, Anthropic, etc.)
- Basic chat functionality

### UI-001: Gradio Interface
- Chat interface
- Model selection
- Parameter controls

This PRD drives the human-steered development process.
