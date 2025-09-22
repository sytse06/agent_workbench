# Agent Workbench DevOps Guide

Complete reference for all development, deployment, and Docker operations in the Agent Workbench project.

## Table of Contents

- [Environment Management](#environment-management)
- [Human-Steered Development Workflow](#human-steered-development-workflow)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Deployment Operations](#deployment-operations)
- [Docker Extensions](#docker-extensions)
- [Database Operations](#database-operations)
- [Utility Commands](#utility-commands)

---

## Environment Management

### Core Environment Commands

These commands configure your local environment using the config/*.env files:

```bash
# Development environment (any branch)
make dev
# Copies config/development.env to .env
# Ready for: uv run python -m agent_workbench

# Staging environment (typically develop branch)
make staging
# Copies config/staging.env to .env
# Includes branch safety checks

# Production environment (main branch only)
make prod
# Copies config/production.env to .env
# Requires confirmation and main branch
```

### Environment File Structure

```
config/
├── development.env    # Local development with debug enabled
├── staging.env       # Pre-production testing environment
├── production.env    # Production configuration template
├── hf-spaces-workbench.env    # HuggingFace Spaces workbench config
└── hf-spaces-seo-coach.env    # HuggingFace Spaces SEO coach config
```

---

## Human-Steered Development Workflow

### Architecture Phase (Human-Led)

Start new architectural decisions:

```bash
# Create architecture branch and documentation template
make arch TASK=CORE-002-database-models
# Creates: arch/CORE-002-database-models branch
# Creates: docs/architecture/decisions/CORE-002-database-models.md
# Next: Edit the architecture document with human decisions
```

### Implementation Phase (AI-Led)

Convert architecture into implementation:

```bash
# Create feature branch with implementation constraints
make feature TASK=CORE-002-database-models
# Auto-merges arch branch to develop if needed
# Creates: feature/CORE-002-database-models branch
# Creates: docs/prompts/implementation/CORE-002-database-models-prompt.md
# Next: AI implements within architectural boundaries
```

### Validation Phase

Comprehensive implementation validation:

```bash
# Full validation suite
make validate TASK=CORE-002-database-models
# Runs: code quality (black, ruff, mypy)
# Runs: test suite with coverage
# Runs: scope compliance checks
# Verifies: architectural boundaries respected
```

### Completion Phase

Merge validated implementation:

```bash
# Complete implementation and merge to develop
make complete TASK=CORE-002-database-models
# Commits implementation with standardized message
# Merges feature branch to develop
# Optional: cleanup architecture branch
# Next: Deploy to staging or start next task
```

---

## Testing & Quality Assurance

### Basic Testing

```bash
# Install dependencies
make install

# Run full test suite
make test
# Equivalent: uv run pytest tests/ -v --cov=src/agent_workbench

# Code quality checks
make quality
# Runs: ruff check, black --check, mypy

# Auto-fix code quality issues
make quality-fix
# Runs: black (format), ruff --fix

# Pre-commit validation
make pre-commit
# Combines: quality-check + test
```

### Advanced Testing

```bash
# Clean environment testing
make clean
# Removes: .venv/, caches, artifacts

# Comprehensive quality check
make quality-check
# Detailed: formatting, linting, type checking
```

---

## Deployment Operations

### Staging Deployment

```bash
# Full staging deployment workflow
make staging-deploy
# Combines: staging environment + deployment + verification

# Individual staging operations
make staging              # Configure staging environment
make deploy ENV=staging   # Deploy to staging
make verify-staging      # Comprehensive staging verification
```

### Production Deployment

```bash
# Production deployment (main branch required)
make deploy ENV=prod
# Requires: main branch, confirmation
# Runs: dependency sync, database migrations
```

### Application Management

```bash
# Start application (requires .env)
make start-app
# Detects environment from .env file
# Runs: uv run python -m agent_workbench

# Git status with branch safety
make git-status
# Shows: current branch, recent commits
# Shows: architecture branches, feature branches
# Warns: if on main branch
```

---

## Docker Extensions

> **Philosophy**: Docker commands are orthogonal to core workflow.
> Use when you need containerized environments without disrupting existing development patterns.

### Environment-Based Docker

```bash
# Development container (mirrors make dev)
make docker-dev
# Uses: config/development.env
# Ports: 8000 (FastAPI), 7860 (Gradio)
# Mode: Interactive development

# Staging container (mirrors production)
make docker-staging
# Uses: config/staging.env
# Mirrors: production constraints
# Branch check: typically develop

# Production container
make docker-prod
# Uses: config/production.env
# Requires: main branch + confirmation
# Mode: Production environment
```

### Testing & Validation

```bash
# Clean isolated testing
make docker-test
# Fresh container + full test suite
# Equivalent: pytest + coverage in container

# Containerized validation
make docker-validate TASK=CORE-002-name
# Runs: tests + linting + type checking
# Orthogonal to: make validate

# Fresh environment
make docker-fresh
# Completely clean: no cache, new build
# Use when: debugging environment issues
```

### Database Operations

```bash
# Database migrations in container
make docker-migrate
# Runs: alembic upgrade head in container
# Stateless: no persistent volumes

# Fresh database in container
make docker-db-clean
# Removes existing DB + runs migrations
# Stateless: starts completely clean
```

### Utility Operations

```bash
# Interactive shell in container
make docker-shell
# Opens: /bin/bash in development container
# Use for: debugging, exploration

# Container logs
make docker-logs
# Shows: logs from running containers
# Checks: dev, staging, prod containers

# Cleanup Docker resources
make docker-cleanup
# Removes: all agent-workbench containers
# Removes: all agent-workbench images
# Runs: docker system prune
```

---

## Database Operations

### Alembic Migrations

The project uses Alembic for database schema management:

```bash
# Auto-generate migration from model changes
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# Show current migration status
uv run alembic current

# Show migration history
uv run alembic history
```

### Environment-Specific Databases

Each environment uses separate database files:

```
data/
├── agent_workbench_dev.db        # Development
├── agent_workbench_staging.db    # Staging
└── agent_workbench_prod.db       # Production
```

Database URLs are configured in respective config/*.env files.

---

## Utility Commands

### Development Utilities

```bash
# Show help with all commands
make help

# Clean all artifacts
make clean
# Removes: .venv/, caches, build artifacts

# Git status with enhanced information
make git-status
# Shows: branch status, recent commits, feature branches
```

### Advanced Quality Tools

```bash
# Enhanced quality commands
make quality-fix      # Auto-fix formatting and linting
make quality-check    # Comprehensive quality validation
make pre-commit       # Full pre-commit validation gate
```

### Staging Verification

```bash
# Comprehensive staging verification
make verify-staging
# Checks: environment, database, dependencies, tests
# Provides: manual testing checklist
# Ready for: production deployment
```

---

## Docker Architecture

### Image Strategy

- **Multi-stage builds**: Builder + Runtime stages
- **UV package manager**: Fast dependency installation
- **Stateless containers**: No persistent volumes (Phase 1)
- **Environment parity**: Staging mirrors production

### Port Configuration

- **8000**: FastAPI backend
- **7860**: Gradio frontend
- Both ports exposed in all Docker environments

### Environment Variables

Docker containers use the same config/*.env files as bare-metal environments:

- `--env-file config/development.env`
- `--env-file config/staging.env`
- `--env-file config/production.env`

Additional container-specific variables:
- `APP_ENV`: development|staging|production
- Environment-specific overrides

---

## Command Quick Reference

### Daily Development

```bash
make dev                    # Start development environment
make arch TASK=name         # Begin architecture phase
make feature TASK=name      # Begin implementation phase
make validate TASK=name     # Validate implementation
make complete TASK=name     # Complete and merge
```

### Testing & Quality

```bash
make test                   # Run test suite
make quality               # Code quality checks
make quality-fix           # Auto-fix quality issues
make docker-test           # Test in clean container
```

### Environment Management

```bash
make staging               # Configure staging
make staging-deploy        # Full staging deployment
make verify-staging        # Staging verification
make start-app            # Start application
```

### Docker Alternatives

```bash
make docker-dev            # Development in container
make docker-staging        # Staging container
make docker-fresh          # Completely fresh environment
make docker-cleanup        # Clean Docker resources
```

### Database Operations

```bash
make docker-migrate        # Migrations in container
make docker-db-clean       # Fresh database in container
uv run alembic upgrade head  # Direct migration
```

---

## Best Practices

### Branch Safety

- **Development**: Any branch (`make dev`)
- **Staging**: Typically develop branch (`make staging`)
- **Production**: Main branch only (`make prod`, `make docker-prod`)

### Environment Isolation

- Use `make docker-*` commands for isolated testing
- Use regular `make` commands for daily development
- Keep config/*.env files updated for all environments

### Human-Steered Workflow

1. **Human** defines architecture with `make arch`
2. **AI** implements within boundaries using `make feature`
3. **System** validates with `make validate`
4. **Human** reviews and completes with `make complete`

### Docker Strategy

- **Development**: Use `make docker-dev` for clean testing
- **Staging**: Use `make docker-staging` to mirror production
- **Production**: Use `make docker-prod` for production validation
- **Phase 1**: All containers are stateless (no persistent volumes)

This comprehensive DevOps guide ensures efficient development while maintaining the human-steered architectural philosophy of Agent Workbench.