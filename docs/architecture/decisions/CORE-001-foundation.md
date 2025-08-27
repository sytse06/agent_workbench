# ADR: CORE-001 Foundation Architecture

## Status: In Progress
## Date: $(date +%Y-%m-%d)
## PRD Reference: CORE-001: Project Foundation

## Context
From PRD Development Phases Section - CORE-001: Project Foundation

**Architecture Scope**:
- UV-based dependency management with pyproject.toml
- Docker containerization with multi-stage builds
- FastAPI application structure with async support
- SQLite database with Alembic migration system

## Architectural Decisions

### 1. Dependency Management
**Decision**: UV with pyproject.toml (✅ Already implemented in clean setup)
**Rationale**: Fast, reliable, modern Python package management
**Implementation**: pyproject.toml configured with FastAPI, SQLAlchemy, Alembic

### 2. Application Structure
**Decision**: FastAPI with async/await support
**Rationale**: Type safety, performance, modern Python patterns
**Implementation**: src/agent_workbench/main.py as FastAPI entry point

### 3. Database Strategy
**Decision**: SQLite with Alembic migrations
**Rationale**: Simple deployment, version-controlled schema
**Implementation**: Alembic configured for async SQLite

### 4. Containerization
**Decision**: Docker with multi-stage builds using UV
**Rationale**: Environment consistency, optimized builds
**Implementation**: Multi-stage Dockerfile leveraging UV

## Implementation Boundaries for AI (FROM PRD)

### CREATE ONLY:
- `src/agent_workbench/__init__.py` - Package initialization
- `pyproject.toml` - UV dependency configuration (enhance existing)
- `Dockerfile` - Multi-stage container build
- `alembic.ini` - Database migration configuration (enhance existing)
- `src/agent_workbench/main.py` - FastAPI application entry point
- `alembic/env.py` - Alembic environment configuration

### MODIFY ONLY:
- Repository structure and configuration files
- Existing configuration files to complete foundation

### FORBIDDEN (per PRD):
- LLM integrations (reserved for LLM-001 task)
- UI components (reserved for UI-001 task)
- Complex business logic (premature for foundation)

## Success Criteria (from PRD requirements)
- [ ] FastAPI application starts: `uv run python -m agent_workbench`
- [ ] Database migrations work: `uv run alembic upgrade head`
- [ ] Docker builds successfully: `docker build .`
- [ ] Container runs: `docker run agent-workbench`
- [ ] Health check endpoint responds
- [ ] All tests pass: `make test`

## Next Steps
1. ✅ Architecture defined per PRD
2. Generate AI implementation prompt from PRD boundaries
3. AI implements foundation within exact PRD constraints
4. Human validates against PRD requirements
5. Merge to develop when complete

## Notes
This implements exactly what PRD specifies for CORE-001, with strict boundaries to prevent scope creep.
