.PHONY: help dev staging prod install test quality clean git-status deploy arch feature

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
	@echo "🌿 Git Workflow:"
	@echo "  make git-status   - Show git overview"
	@echo "  make arch TASK=CORE-002-name    - Start architecture"
	@echo "  make feature TASK=CORE-002-name - Start implementation"
	@echo ""
	@echo "🚀 Deployment:"
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
	@scripts/git/status.sh

arch:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make arch TASK=CORE-002-description"; \
		exit 1; \
	fi
	@scripts/git/start-architecture.sh $(TASK)

feature:
	@if [ -z "$(TASK)" ]; then \
		echo "Usage: make feature TASK=CORE-002"; \
		exit 1; \
	fi
	@scripts/git/start-feature.sh $(TASK)

# Deployment
deploy:
	@if [ -z "$(ENV)" ]; then \
		echo "Usage: make deploy ENV=staging|prod"; \
		exit 1; \
	fi
	@scripts/git/deploy.sh $(ENV)
