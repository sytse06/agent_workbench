.PHONY: help install dev test clean

help:
	@echo "Agent Workbench - Practical Commands"
	@echo "===================================="
	@echo "install  - Install dependencies"  
	@echo "dev      - Setup development environment"
	@echo "test     - Run tests"
	@echo "clean    - Clean up"

install:
	uv sync --dev

dev:
	cp config/development.env .env
	@echo "✅ Development environment ready"
	@echo "Edit .env with your API keys"

test:
	uv run pytest tests/

clean:
	rm -rf .venv/ .pytest_cache/ htmlcov/ dist/ *.egg-info/
	find . -name __pycache__ -delete 2>/dev/null || true
