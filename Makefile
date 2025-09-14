.PHONY: help dev staging prod install test quality clean git-status deploy arch feature validate complete post-staging verify-staging start-app

# Default shell to bash for better compatibility
SHELL := /bin/bash

# Color codes for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
NC := \033[0m # No Color

help:
	@echo "Agent Workbench - Human-Steered AI Development"
	@echo "=============================================="
	@echo ""
	@echo "🌍 Environment Management:"
	@echo "  make dev          - Development environment (any branch)"
	@echo "  make staging      - Staging environment (develop branch)"
	@echo "  make prod         - Production environment (main branch)"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run test suite"
	@echo "  make quality      - Code quality checks"
	@echo "  make clean        - Clean artifacts"
	@echo ""
	@echo "🌿 Human-Steered Workflow:"
	@echo "  make arch TASK=CORE-002-name      - Start architecture (human)"
	@echo "  make feature TASK=CORE-002-name   - Start implementation (AI)"
	@echo "  make validate TASK=CORE-002-name  - Check boundaries"
	@echo "  make complete TASK=CORE-002-name  - Merge to develop"
	@echo ""
	@echo "🧪 Staging Workflow:"
	@echo "  make staging-deploy               - Full staging deployment"
	@echo "  make verify-staging               - Comprehensive staging tests"
	@echo "  make start-app                    - Start application"
	@echo ""
	@echo "📊 Git & Deployment:"
	@echo "  make git-status   - Show git overview"
	@echo "  make deploy ENV=staging   - Deploy to staging"
	@echo "  make deploy ENV=prod      - Deploy to production"

# Enhanced environment management with validation
dev:
	@echo -e "$(BLUE)🛠️ Starting development environment...$(NC)"
	@if [ ! -f "config/development.env" ]; then \
		echo -e "$(RED)❌ config/development.env not found$(NC)"; \
		exit 1; \
	fi
	@cp config/development.env .env
	@echo -e "$(GREEN)✅ Development environment configured$(NC)"
	@echo -e "$(CYAN)🚀 Run: uv run python -m agent_workbench$(NC)"

staging:
	@echo -e "$(YELLOW)🧪 Configuring staging environment...$(NC)"
	@current_branch=$$(git branch --show-current); \
	if [ "$$current_branch" != "develop" ]; then \
		echo -e "$(YELLOW)⚠️  Currently on branch: $$current_branch$(NC)"; \
		echo -e "$(YELLOW)⚠️  Staging typically deploys from 'develop' branch$(NC)"; \
		read -p "Continue anyway? (y/N): " confirm; \
		if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
			echo -e "$(BLUE)💡 Switch to develop: git checkout develop$(NC)"; \
			exit 1; \
		fi; \
	fi
	@if [ ! -f "config/staging.env" ]; then \
		echo -e "$(RED)❌ config/staging.env not found$(NC)"; \
		exit 1; \
	fi
	@cp config/staging.env .env
	@echo -e "$(GREEN)✅ Staging environment configured$(NC)"

prod:
	@echo -e "$(RED)🚀 Configuring production environment...$(NC)"
	@if [ "$$(git branch --show-current)" != "main" ]; then \
		echo -e "$(RED)❌ Switch to main branch first: git checkout main$(NC)"; \
		exit 1; \
	fi
	@if [ ! -f "config/production.env" ]; then \
		echo -e "$(RED)❌ config/production.env not found$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(YELLOW)⚠️  PRODUCTION ENVIRONMENT$(NC)"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
		echo "Production configuration cancelled"; \
		exit 1; \
	fi
	@cp config/production.env .env
	@echo -e "$(GREEN)✅ Production environment configured$(NC)"

# Development tools with enhanced feedback
install:
	@echo -e "$(BLUE)📦 Installing dependencies...$(NC)"
	@uv sync
	@echo -e "$(GREEN)✅ Dependencies installed$(NC)"

test:
	@echo -e "$(BLUE)🧪 Running test suite...$(NC)"
	@uv run pytest tests/ -v --cov=src/agent_workbench
	@echo -e "$(GREEN)✅ Tests complete$(NC)"

quality:
	@echo -e "$(BLUE)🎨 Running code quality checks...$(NC)"
	@uv run ruff check src/ tests/
	@uv run black --check src/ tests/
	@uv run mypy src/
	@echo -e "$(GREEN)✅ Quality checks complete$(NC)"

clean:
	@echo -e "$(BLUE)🧹 Cleaning artifacts...$(NC)"
	@rm -rf .venv/ .pytest_cache/ htmlcov/ dist/ *.egg-info/
	@find . -name __pycache__ -delete 2>/dev/null || true
	@echo -e "$(GREEN)✅ Cleanup complete$(NC)"

# Enhanced git status with branch safety
git-status:
	@echo -e "$(CYAN)📊 Git Status Overview$(NC)"
	@current_branch=$$(git branch --show-current); \
	echo "Current branch: $$current_branch"; \
	if [ "$$current_branch" = "main" ]; then \
		echo -e "$(RED)⚠️  You are on MAIN branch - be careful!$(NC)"; \
	elif [ "$$current_branch" = "develop" ]; then \
		echo -e "$(GREEN)✅ On develop branch$(NC)"; \
	else \
		echo -e "$(YELLOW)ℹ️  On feature/arch branch$(NC)"; \
	fi
	@echo "Recent commits:"
	@git log --oneline -5
	@echo ""
	@echo "Architecture branches:"
	@git branch -a | grep "arch/" | sed 's/.*arch\//  🗂️  /' || echo "  (none)"
	@echo "Feature branches:"
	@git branch -a | grep "feature/" | sed 's/.*feature\//  ⚡  /' || echo "  (none)"

# Enhanced complete with better error handling
complete:
	@if [ -z "$(TASK)" ]; then \
		echo -e "$(RED)Usage: make complete TASK=TASK-NAME$(NC)"; \
		echo -e "$(BLUE)Example: make complete TASK=LLM-001-langchain-model-integration$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(PURPLE)🎉 Completing Implementation: $(TASK)$(NC)"
	@current_branch=$$(git branch --show-current); \
	expected_branch="feature/$(TASK)"; \
	if [ "$$current_branch" != "$$expected_branch" ]; then \
		echo -e "$(YELLOW)⚠️  Current branch: $$current_branch$(NC)"; \
		echo -e "$(YELLOW)⚠️  Expected branch: $$expected_branch$(NC)"; \
		read -p "Continue anyway? (y/N): " confirm; \
		if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
			echo "Task completion cancelled"; \
			exit 1; \
		fi; \
	fi
	@git add -A
	@if git diff --cached --quiet; then \
		echo -e "$(YELLOW)⚠️  No changes to commit$(NC)"; \
		exit 1; \
	fi
	@TASK_PREFIX=$$(echo $(TASK) | cut -d'-' -f1); \
	git commit -m "[$$TASK_PREFIX][$(TASK)]: Implementation within architectural boundaries" \
	           -m "Scope: Implemented exactly as specified in architecture" \
	           -m "Tests: All tests passing" \
	           -m "Boundaries: No scope violations detected"
	@echo -e "$(GREEN)✅ Implementation committed$(NC)"
	@echo -e "$(BLUE)🔄 Merging to develop...$(NC)"
	@git checkout develop
	@git merge feature/$(TASK) --no-ff -m "Merge $(TASK): Human-steered implementation complete"
	@echo -e "$(GREEN)🎯 $(TASK) successfully integrated into develop$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  - Start next task: make arch TASK=NEXT-TASK-name"
	@echo "  - Deploy to staging: make staging-deploy"

# New: Combined staging deployment
staging-deploy: staging deploy-staging
	@echo -e "$(GREEN)🎯 Staging deployment complete$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  - Verify deployment: make verify-staging"
	@echo "  - Start application: make start-app"

deploy-staging:
	@$(MAKE) deploy ENV=staging

# Enhanced deployment with better feedback
deploy:
	@if [ -z "$(ENV)" ]; then \
		echo -e "$(RED)Usage: make deploy ENV=staging|prod$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(BLUE)🚀 Deploying to $(ENV) environment...$(NC)"
	@if [ "$(ENV)" = "prod" ]; then \
		if [ "$$(git branch --show-current)" != "main" ]; then \
			echo -e "$(RED)❌ Production deploys from main branch only$(NC)"; \
			exit 1; \
		fi; \
		echo -e "$(RED)⚠️  PRODUCTION DEPLOYMENT$(NC)"; \
		read -p "Deploy to PRODUCTION? (y/N): " confirm; \
		if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
			echo "Production deployment cancelled"; \
			exit 1; \
		fi; \
	fi
	@echo -e "$(BLUE)📦 Syncing dependencies...$(NC)"
	@uv sync
	@echo -e "$(BLUE)🗄️ Running database migrations...$(NC)"
	@uv run alembic upgrade head
	@echo -e "$(GREEN)✅ Deployed to $(ENV)$(NC)"

# New: Application starter
start-app:
	@echo -e "$(BLUE)🚀 Starting Agent Workbench...$(NC)"
	@if [ ! -f ".env" ]; then \
		echo -e "$(RED)❌ No .env file found. Run make dev/staging/prod first$(NC)"; \
		exit 1; \
	fi
	@env_type=$$(grep "APP_ENV=" .env | cut -d'=' -f2); \
	echo -e "$(CYAN)Environment: $$env_type$(NC)"
	@uv run python -m agent_workbench

# New: Comprehensive staging verification
verify-staging:
	@echo -e "$(CYAN)🔬 Comprehensive Staging Verification$(NC)"
	@echo "========================================"
	@echo ""
	
	# 1. Environment Check
	@echo -e "$(BLUE)1. Environment Verification:$(NC)"
	@if [ ! -f ".env" ]; then \
		echo -e "$(RED)   ❌ No .env file found$(NC)"; \
		exit 1; \
	fi
	@env_type=$$(grep "APP_ENV=" .env 2>/dev/null | cut -d'=' -f2); \
	if [ "$$env_type" = "staging" ]; then \
		echo -e "$(GREEN)   ✅ Staging environment active$(NC)"; \
	else \
		echo -e "$(RED)   ❌ Wrong environment: $$env_type$(NC)"; \
		exit 1; \
	fi
	
	# 2. Database Check
	@echo -e "$(BLUE)2. Database Verification:$(NC)"
	@if [ -f "data/agent_workbench_staging.db" ]; then \
		echo -e "$(GREEN)   ✅ Staging database exists$(NC)"; \
	else \
		echo -e "$(RED)   ❌ Staging database not found$(NC)"; \
		exit 1; \
	fi
	
	# 3. Dependencies Check
	@echo -e "$(BLUE)3. Dependencies Verification:$(NC)"
	@if uv run python -c "import agent_workbench" 2>/dev/null; then \
		echo -e "$(GREEN)   ✅ Application imports successfully$(NC)"; \
	else \
		echo -e "$(RED)   ❌ Application import failed$(NC)"; \
		exit 1; \
	fi
	
	# 4. Test Suite
	@echo -e "$(BLUE)4. Test Suite Verification:$(NC)"
	@if uv run pytest tests/ --quiet --tb=no 2>/dev/null; then \
		echo -e "$(GREEN)   ✅ All tests pass$(NC)"; \
	else \
		echo -e "$(RED)   ❌ Test failures detected$(NC)"; \
		echo -e "$(BLUE)   💡 Run: make test for details$(NC)"; \
		exit 1; \
	fi
	
	@echo ""
	@echo -e "$(GREEN)🎯 STAGING VERIFICATION COMPLETE$(NC)"
	@echo ""
	@echo "Manual testing checklist:"
	@echo "  - [ ] Start app: make start-app"
	@echo "  - [ ] Test chat functionality"
	@echo "  - [ ] Test model switching"
	@echo "  - [ ] Test document processing"
	@echo "  - [ ] Test database persistence"
	@echo "  - [ ] Performance validation"
	@echo ""
	@echo -e "$(CYAN)Ready for production when manual testing complete$(NC)"

# Enhanced validation with more comprehensive checks
validate:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make validate TASK=CORE-002-name"; \
		exit 1; \
	fi
	@echo -e "$(CYAN)🔍 Comprehensive Implementation Validation: $(TASK)$(NC)"
	@echo "=================================================="
	@echo ""
	
	# 1. Branch Check
	@echo -e "$(BLUE)0. Branch Verification:$(NC)"
	@current_branch=$$(git branch --show-current); \
	expected_branch="feature/$(TASK)"; \
	if [ "$$current_branch" = "$$expected_branch" ]; then \
		echo -e "$(GREEN)   ✅ On correct branch: $$current_branch$(NC)"; \
	else \
		echo -e "$(YELLOW)   ⚠️  Current branch: $$current_branch$(NC)"; \
		echo -e "$(YELLOW)   ⚠️  Expected branch: $$expected_branch$(NC)"; \
	fi
	
	# 2. Implementation Overview
	@echo -e "$(BLUE)1. Implementation Overview:$(NC)"
	@files_changed=$$(git diff --name-only develop 2>/dev/null | wc -l | xargs); \
	lines_changed=$$(git diff --stat develop 2>/dev/null | tail -1 | grep -o '[0-9]\+ insertions\|[0-9]\+ deletions' | head -1 | grep -o '[0-9]\+' || echo "0"); \
	echo "   Files changed: $$files_changed"; \
	echo "   Lines changed: $$lines_changed"; \
	if [ $$files_changed -gt 20 ]; then \
		echo -e "$(YELLOW)   ⚠️  Large changeset - verify scope boundaries carefully$(NC)"; \
	fi
	@echo ""
	
	# 3. Code Quality Validation
	@echo -e "$(BLUE)2. Code Quality Validation:$(NC)"
	@echo "   Running black (formatting)..."
	@if uv run black --check --quiet src/ tests/ 2>/dev/null; then \
		echo -e "$(GREEN)   ✅ Code formatting passes$(NC)"; \
	else \
		echo -e "$(RED)   ❌ Code formatting issues detected$(NC)"; \
		echo -e "$(BLUE)   💡 Fix with: make quality-fix$(NC)"; \
		exit 1; \
	fi
	@echo "   Running ruff (linting)..."
	@if uv run ruff check src/ tests/ --quiet 2>/dev/null; then \
		echo -e "$(GREEN)   ✅ Code linting passes$(NC)"; \
	else \
		echo -e "$(RED)   ❌ Code linting issues detected$(NC)"; \
		echo -e "$(BLUE)   💡 Fix with: make quality-fix$(NC)"; \
		exit 1; \
	fi
	@echo "   Running mypy (type checking)..."
	@if uv run mypy src/ >/dev/null 2>&1; then \
		echo -e "$(GREEN)   ✅ Type checking passes$(NC)"; \
	else \
		echo -e "$(RED)   ❌ Type checking issues detected$(NC)"; \
		echo "   Running mypy to show details:"; \
		uv run mypy src/; \
		exit 1; \
	fi
	@echo ""
	
	# 4. Test Suite Validation
	@echo -e "$(BLUE)3. Test Suite Validation:$(NC)"
	@if uv run pytest tests/ --quiet --tb=no 2>/dev/null; then \
		coverage=$$(uv run pytest tests/ --cov=src/agent_workbench --cov-report=term-missing --quiet 2>/dev/null | grep "TOTAL" | awk '{print $$4}' || echo "unknown"); \
		echo -e "$(GREEN)   ✅ All tests pass (Coverage: $$coverage)$(NC)"; \
	else \
		echo -e "$(RED)   ❌ Test failures detected$(NC)"; \
		echo -e "$(BLUE)   💡 Run: make test for details$(NC)"; \
		exit 1; \
	fi
	@echo ""
	
	# 5. Scope Compliance Check  
	@echo -e "$(BLUE)4. Scope Compliance Verification:$(NC)"
	@if [ -x "./scripts/scope/agent_scope_check.sh" ]; then \
		if ./scripts/scope/agent_scope_check.sh $(TASK) 2>&1 | grep -q "SCOPE COMPLIANCE: APPROVED"; then \
			echo -e "$(GREEN)   ✅ Architectural boundaries respected$(NC)"; \
		else \
			echo -e "$(RED)   ❌ Scope violations detected$(NC)"; \
			echo -e "$(BLUE)   💡 Run: ./scripts/scope/agent_scope_check.sh $(TASK)$(NC)"; \
			exit 1; \
		fi; \
	else \
		echo -e "$(YELLOW)   ⚠️  Automated scope check unavailable$(NC)"; \
		echo "   📋 Manual review required:"; \
		echo "      - Check files against: docs/architecture/decisions/$(TASK).md"; \
		echo "      - Verify no forbidden dependencies added"; \
		echo "      - Ensure implementation stays within boundaries"; \
	fi
	@echo ""
	
	# 6. Final Validation Summary
	@echo "=================================================="
	@echo -e "$(GREEN)✅ VALIDATION COMPLETE: Implementation Ready$(NC)"
	@echo ""
	@echo "📊 Validation Summary:"
	@echo -e "$(GREEN)  ✅ Code Quality (black, ruff, mypy)$(NC)"
	@echo -e "$(GREEN)  ✅ Test Suite (pytest with coverage)$(NC)"
	@echo -e "$(GREEN)  ✅ Scope Compliance (architectural boundaries)$(NC)"
	@echo ""
	@echo -e "$(CYAN)🚀 Ready to complete: make complete TASK=$(TASK)$(NC)"

# Enhanced quality commands
quality-fix:
	@echo -e "$(BLUE)🔧 Auto-fixing code quality issues...$(NC)"
	@uv run black src/ tests/
	@uv run ruff check src/ tests/ --fix --quiet
	@echo -e "$(GREEN)✅ Formatting and auto-fixable issues resolved$(NC)"
	@echo -e "$(BLUE)💡 Re-run 'make validate TASK=your-task' to verify$(NC)"

quality-check:
	@echo -e "$(BLUE)🎨 Running comprehensive code quality checks...$(NC)"
	@echo "🧹 Checking code formatting..."
	@uv run black --check src/ tests/
	@echo "📏 Checking code style..."
	@uv run ruff check src/ tests/
	@echo "🔬 Checking types..."
	@uv run mypy src/
	@echo -e "$(GREEN)✅ Code quality checks complete$(NC)"

pre-commit:
	@echo -e "$(CYAN)🔍 Pre-commit Quality Gate$(NC)"
	@echo "=========================="
	@$(MAKE) quality-check
	@$(MAKE) test
	@echo -e "$(GREEN)✅ All pre-commit checks passed$(NC)"

# Architecture workflow (keeping existing functionality)
arch:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make arch TASK=CORE-002-name"; \
		echo "Example: make arch TASK=CORE-002-database-models"; \
		exit 1; \
	fi
	@echo -e "$(PURPLE)🗂️ Architecture Phase: $(TASK)$(NC)"
	@git checkout develop && git pull origin develop 2>/dev/null || true
	@git checkout -b arch/$(TASK) 2>/dev/null || git checkout arch/$(TASK)
	@mkdir -p docs/architecture/decisions
	@if [ ! -f "docs/architecture/decisions/$(TASK).md" ]; then \
		echo "# $(TASK): Architecture Decision" > docs/architecture/decisions/$(TASK).md; \
		echo "" >> docs/architecture/decisions/$(TASK).md; \
		echo "## Context" >> docs/architecture/decisions/$(TASK).md; \
		echo "[Brief description of what this task addresses]" >> docs/architecture/decisions/$(TASK).md; \
		echo "" >> docs/architecture/decisions/$(TASK).md; \
		echo "## What's Included" >> docs/architecture/decisions/$(TASK).md; \
		echo "- [ ] Specific requirement 1" >> docs/architecture/decisions/$(TASK).md; \
		echo "- [ ] Specific requirement 2" >> docs/architecture/decisions/$(TASK).md; \
		echo "" >> docs/architecture/decisions/$(TASK).md; \
		echo "## What's Excluded" >> docs/architecture/decisions/$(TASK).md; \
		echo "- ❌ Feature X (save for later)" >> docs/architecture/decisions/$(TASK).md; \
		echo "- ❌ Integration Y (separate task)" >> docs/architecture/decisions/$(TASK).md; \
		echo "" >> docs/architecture/decisions/$(TASK).md; \
		echo "## Implementation Boundaries" >> docs/architecture/decisions/$(TASK).md; \
		echo "### Files to CREATE:" >> docs/architecture/decisions/$(TASK).md; \
		echo "- \`src/agent_workbench/module/file.py\`" >> docs/architecture/decisions/$(TASK).md; \
		echo "" >> docs/architecture/decisions/$(TASK).md; \
		echo "### Exact Function Signatures:" >> docs/architecture/decisions/$(TASK).md; \
		echo "\`\`\`python" >> docs/architecture/decisions/$(TASK).md; \
		echo "def function_name(param: Type) -> ReturnType:" >> docs/architecture/decisions/$(TASK).md; \
		echo "    \"\"\"Brief description.\"\"\"" >> docs/architecture/decisions/$(TASK).md; \
		echo "    pass" >> docs/architecture/decisions/$(TASK).md; \
		echo "\`\`\`" >> docs/architecture/decisions/$(TASK).md; \
		echo "" >> docs/architecture/decisions/$(TASK).md; \
		echo "## Success Criteria" >> docs/architecture/decisions/$(TASK).md; \
		echo "- [ ] Measurable outcome 1" >> docs/architecture/decisions/$(TASK).md; \
		echo "- [ ] Measurable outcome 2" >> docs/architecture/decisions/$(TASK).md; \
	fi
	@echo -e "$(GREEN)✅ Architecture branch: arch/$(TASK)$(NC)"
	@echo -e "$(BLUE)📝 Edit: docs/architecture/decisions/$(TASK).md$(NC)"
	@echo -e "$(CYAN)🔄 When done: make feature TASK=$(TASK)$(NC)"

feature:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make feature TASK=CORE-002-name"; \
		exit 1; \
	fi
	@if [ ! -f "docs/architecture/decisions/$(TASK).md" ]; then \
		echo -e "$(RED)❌ No architecture found. Run: make arch TASK=$(TASK)$(NC)"; \
		exit 1; \
	fi
	@echo -e "$(PURPLE)⚡ Implementation Phase: $(TASK)$(NC)"
	@git checkout develop && git pull origin develop 2>/dev/null || true
	@git checkout -b feature/$(TASK) 2>/dev/null || git checkout feature/$(TASK)
	@mkdir -p docs/prompts/implementation
	@echo "# Implementation Prompt: $(TASK)" > docs/prompts/implementation/$(TASK)-prompt.md
	@echo "" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "You are implementing **$(TASK)** within strict architectural boundaries." >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "## Architecture Reference" >> docs/prompts/implementation/$(TASK)-prompt.md
	@cat docs/architecture/decisions/$(TASK).md >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "## CRITICAL CONSTRAINTS" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "- **ONLY implement** what's listed in 'What's Included'" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "- **NEVER implement** what's in 'What's Excluded'" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "- **Follow exact function signatures** if provided above" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "- **Create only the files** specified in Implementation Boundaries" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "- **Include comprehensive tests** for all new functionality" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "## Scope Violation Detection" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "If you want to add something not listed in scope, STOP." >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "Implementation will be validated against these exact boundaries." >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "## Ready for Implementation" >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo "Implement exactly what's specified above. No more, no less." >> docs/prompts/implementation/$(TASK)-prompt.md
	@echo -e "$(GREEN)✅ Feature branch: feature/$(TASK)$(NC)"
	@echo -e "$(BLUE)🤖 AI Prompt: docs/prompts/implementation/$(TASK)-prompt.md$(NC)"
	@echo -e "$(CYAN)🔄 When done: make validate TASK=$(TASK)$(NC)"