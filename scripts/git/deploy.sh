#!/bin/zsh
# Deploy specific branch to environment

if [[ -z "$1" ]]; then
    echo "Usage: $0 ENVIRONMENT [BRANCH]"
    echo "Environments: dev, staging, prod"
    echo "Example: $0 staging"
    echo "Example: $0 prod main"
    exit 1
fi

ENVIRONMENT="$1"
BRANCH="${2:-$(git branch --show-current)}"

case $ENVIRONMENT in
    "dev"|"development")
        echo "🛠️ Deploying $BRANCH to development environment..."
        git checkout "$BRANCH"
        cp config/development.env .env
        uv sync
        echo "✅ Development environment ready"
        echo "🚀 Run: uv run python -m agent_workbench"
        ;;
    "staging")
        echo "🧪 Deploying to staging environment..."
        if [[ "$BRANCH" != "develop" ]]; then
            echo "❌ Staging deploys from develop branch only"
            exit 1
        fi
        ./deploy/deploy-staging.sh
        ;;
    "prod"|"production")
        echo "🚀 Deploying to production environment..."
        if [[ "$BRANCH" != "main" ]]; then
            echo "❌ Production deploys from main branch only"
            exit 1
        fi
        read "confirm?Deploy to PRODUCTION? (y/N): "
        if [[ $confirm == [yY] ]]; then
            ./deploy/deploy-production.sh
        else
            echo "Production deployment cancelled"
        fi
        ;;
    *)
        echo "❌ Invalid environment: $ENVIRONMENT"
        echo "Valid environments: dev, staging, prod"
        exit 1
        ;;
esac
