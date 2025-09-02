#!/bin/zsh
# Deploy main branch to production environment

echo "🚀 Deploying to production environment..."

# Ensure we're on main branch
git checkout main
git pull origin main

# Copy production configuration
cp config/production.env .env

# Install dependencies
uv sync --frozen

# Run database migrations
uv run alembic upgrade head

# Run full test suite
uv run pytest tests/ -v --cov=src/agent_workbench

echo "✅ Production deployment complete"
echo "🌍 Production ready"
