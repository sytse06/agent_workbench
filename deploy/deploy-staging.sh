#!/bin/zsh
# Deploy develop branch to staging environment

echo "🚀 Deploying to staging environment..."

# Ensure we're on develop branch
git checkout develop
git pull origin develop

# Copy staging configuration
cp config/staging.env .env

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Run tests
uv run pytest tests/ -v

echo "✅ Staging deployment complete"
echo "🌍 Access at: http://localhost:7860"
