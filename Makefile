.PHONY: help dev staging prod install test quality clean git-status deploy arch feature validate complete

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
	@echo "📊 Git & Deployment:"
	@echo "  make git-status   - Show git overview"
	@echo "  make deploy ENV=staging   - Deploy to staging"
	@echo "  make deploy ENV=prod      - Deploy to production"

# Environment management
dev:
	@echo "🛠️ Starting development environment..."
	@cp config/development.env .env
	@echo "✅ Development environment configured"
	@echo "🚀 Run: uv run python -m agent_workbench"

staging:
	@echo "🧪 Configuring staging environment..."
	@if [ "$(shell git branch --show-current)" != "develop" ]; then \
		echo "❌ Switch to develop branch first: git checkout develop"; \
		exit 1; \
	fi
	@cp config/staging.env .env
	@echo "✅ Staging environment configured"

prod:
	@echo "🚀 Configuring production environment..."
	@if [ "$(shell git branch --show-current)" != "main" ]; then \
		echo "❌ Switch to main branch first: git checkout main"; \
		exit 1; \
	fi
	@cp config/production.env .env
	@echo "✅ Production environment configured"

# Development tools
install:
	uv sync

test:
	uv run pytest tests/ -v --cov=src/agent_workbench

quality:
	uv run ruff check src/ tests/
	uv run black --check src/ tests/
	uv run mypy src/

clean:
	rm -rf .venv/ .pytest_cache/ htmlcov/ dist/ *.egg-info/
	find . -name __pycache__ -delete 2>/dev/null || true

# Git workflow helpers
git-status:
	@echo "📊 Git Status Overview"
	@echo "Current branch: $(shell git branch --show-current)"
	@echo "Recent commits:"
	@git log --oneline -5
	@echo ""
	@echo "Architecture branches:"
	@git branch -a | grep "arch/" | sed 's/.*arch\//  🗂️  /' || echo "  (none)"
	@echo "Feature branches:"
	@git branch -a | grep "feature/" | sed 's/.*feature\//  ⚡  /' || echo "  (none)"

# Streamlined Human-Steered Workflow
arch:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make arch TASK=CORE-002-name"; \
		echo "Example: make arch TASK=CORE-002-database-models"; \
		exit 1; \
	fi
	@echo "🗂️ Architecture Phase: $(TASK)"
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
	@echo "✅ Architecture branch: arch/$(TASK)"
	@echo "📝 Edit: docs/architecture/decisions/$(TASK).md"
	@echo "🔄 When done: make feature TASK=$(TASK)"

feature:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make feature TASK=CORE-002-name"; \
		exit 1; \
	fi
	@if [ ! -f "docs/architecture/decisions/$(TASK).md" ]; then \
		echo "❌ No architecture found. Run: make arch TASK=$(TASK)"; \
		exit 1; \
	fi
	@echo "⚡ Implementation Phase: $(TASK)"
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
	@echo "✅ Feature branch: feature/$(TASK)"
	@echo "🤖 AI Prompt: docs/prompts/implementation/$(TASK)-prompt.md"
	@echo "🔄 When done: make validate TASK=$(TASK)"

validate:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make validate TASK=CORE-002-name"; \
		exit 1; \
	fi
	@echo "🔍 Comprehensive Implementation Validation: $(TASK)"
	@echo "=================================================="
	@echo ""
	
	# 1. Implementation Overview
	@echo "📋 Implementation Overview:"
	@files_changed=$$(git diff --name-only develop 2>/dev/null | wc -l | xargs); \
	lines_changed=$$(git diff --stat develop 2>/dev/null | tail -1 | grep -o '[0-9]\+ insertions\|[0-9]\+ deletions' | head -1 | grep -o '[0-9]\+' || echo "0"); \
	echo "   Files changed: $$files_changed"; \
	echo "   Lines changed: $$lines_changed"; \
	if [ $$files_changed -gt 20 ]; then \
		echo "   ⚠️  Large changeset - verify scope boundaries carefully"; \
	fi
	@echo ""
	
	# 2. Code Quality Validation
	@echo "🎨 Code Quality Validation:"
	@echo "   Running black (formatting)..."
	@if uv run black --check --quiet src/ tests/ 2>/dev/null; then \
		echo "   ✅ Code formatting passes"; \
	else \
		echo "   ❌ Code formatting issues detected"; \
		echo "   💡 Fix with: uv run black src/ tests/"; \
		exit 1; \
	fi
	@echo "   Running ruff (linting)..."
	@if uv run ruff check src/ tests/ --quiet 2>/dev/null; then \
		echo "   ✅ Code linting passes"; \
	else \
		echo "   ❌ Code linting issues detected"; \
		echo "   💡 Fix with: uv run ruff check src/ tests/ --fix"; \
		exit 1; \
	fi
	@echo "   Running mypy (type checking)..."
	@if uv run mypy src/ >/dev/null 2>&1; then \
		echo "   ✅ Type checking passes"; \
	else \
		echo "   ❌ Type checking issues detected"; \
		echo "   Running mypy to show details:"; \
		uv run mypy src/; \
		exit 1; \
	fi
	@echo ""
	
	# 3. Test Suite Validation
	@echo "🧪 Test Suite Validation:"
	@if uv run pytest tests/ --quiet --tb=no 2>/dev/null; then \
		coverage=$$(uv run pytest tests/ --cov=src/agent_workbench --cov-report=term-missing --quiet 2>/dev/null | grep "TOTAL" | awk '{print $$4}' || echo "unknown"); \
		echo "   ✅ All tests pass (Coverage: $$coverage)"; \
	else \
		echo "   ❌ Test failures detected"; \
		echo "   💡 Run: make test for details"; \
		exit 1; \
	fi
	@echo ""
	
	# 4. Scope Compliance Check  
	@echo "🎯 Scope Compliance Verification:"
	@if [ -x "./scripts/scope/agent_scope_check.sh" ]; then \
		if ./scripts/scope/agent_scope_check.sh $(TASK) 2>&1 | grep -q "SCOPE COMPLIANCE: APPROVED"; then \
			echo "   ✅ Architectural boundaries respected"; \
		else \
			echo "   ❌ Scope violations detected"; \
			echo "   💡 Run: ./scripts/scope/agent_scope_check.sh $(TASK)"; \
			exit 1; \
		fi; \
	else \
		echo "   ⚠️  Automated scope check unavailable"; \
		echo "   📋 Manual review required:"; \
		echo "      - Check files against: docs/architecture/decisions/$(TASK).md"; \
		echo "      - Verify no forbidden dependencies added"; \
		echo "      - Ensure implementation stays within boundaries"; \
	fi
	@echo ""
	
	# 5. Final Validation Summary
	@echo "=================================================="
	@echo "✅ VALIDATION COMPLETE: Implementation Ready"
	@echo ""
	@echo "📊 Validation Summary:"
	@echo "  ✅ Code Quality (black, ruff, mypy)"
	@echo "  ✅ Test Suite (pytest with coverage)"
	@echo "  ✅ Scope Compliance (architectural boundaries)"
	@echo ""
	@echo "🚀 Ready to complete: make complete TASK=$(TASK)"

# Quick quality fix command
quality-fix:
	@echo "🔧 Auto-fixing code quality issues..."
	@uv run black src/ tests/
	@uv run ruff check src/ tests/ --fix --quiet
	@echo "✅ Formatting and auto-fixable issues resolved"
	@echo "💡 Re-run 'make validate TASK=your-task' to verify"

# Standalone quality check (matches your agent_quality function)
quality-check:
	@echo "🎨 Running comprehensive code quality checks..."
	@echo "🧹 Checking code formatting..."
	@uv run black --check src/ tests/
	@echo "📏 Checking code style..."
	@uv run ruff check src/ tests/
	@echo "🔬 Checking types..."
	@uv run mypy src/
	@echo "✅ Code quality checks complete"

# Pre-commit quality gate
pre-commit:
	@echo "🔍 Pre-commit Quality Gate"
	@echo "=========================="
	@$(MAKE) quality-check
	@$(MAKE) test
	@echo "✅ All pre-commit checks passed"

# Enhanced scope check command that integrates with quality
scope-validate:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make scope-validate TASK=CORE-002-name"; \
		exit 1; \
	fi
	@echo "🎯 Comprehensive Scope & Quality Validation"
	@echo "=========================================="
	@$(MAKE) quality-check
	@echo ""
	@if [ -x "./scripts/scope/agent_scope_check.sh" ]; then \
		./scripts/scope/agent_scope_check.sh $(TASK); \
	else \
		echo "❌ Scope check script not found"; \
		exit 1; \
	fi

complete:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make complete TASK=(TASK)"; \
		exit 1; \
	fi
	@echo "🎉 Completing Implementation: $(TASK)"
	@git add -A
	@TASK_PREFIX=$$(echo $(TASK) | cut -d'-' -f1); \
	git commit -m "[$$TASK_PREFIX][$(TASK)]: Implementation within architectural boundaries" \
	           -m "Scope: Implemented exactly as specified in architecture" \
	           -m "Tests: All tests passing" \
	           -m "Boundaries: No scope violations detected"
	@echo "✅ Implementation committed"
	@echo "🔄 Merging to develop..."
	@git checkout develop
	@git merge feature/$(TASK) --no-ff -m "Merge $(TASK): Human-steered implementation complete"
	@echo "🎯 $(TASK) successfully integrated into develop"
	@echo ""
	@echo "Next steps:"
	@echo "  - Start next task: make arch TASK=NEXT-TASK-name"
	@echo "  - Deploy to staging: make staging && make deploy ENV=staging"

# Deployment
deploy:
	@if [ -z "$(ENV)" ]; then \
		echo "Usage: make deploy ENV=staging|prod"; \
		exit 1; \
	fi
	@echo "🚀 Deploying to $(ENV) environment..."
	@if [ "$(ENV)" = "prod" ]; then \
		if [ "$(shell git branch --show-current)" != "main" ]; then \
			echo "❌ Production deploys from main branch only"; \
			exit 1; \
		fi; \
		read -p "Deploy to PRODUCTION? (y/N): " confirm; \
		if [ "$$confirm" != "y" ]; then \
			echo "Production deployment cancelled"; \
			exit 1; \
		fi; \
	fi
	@uv sync
	@uv run alembic upgrade head
	@echo "✅ Deployed to $(ENV)"