#!/bin/zsh
# Show git status overview for human-steered development

echo "📊 Agent Workbench Git Status"
echo "============================="

echo ""
echo "🌿 Current Branch: $(git branch --show-current)"
echo "🏷️ Last Commit: $(git log -1 --format='%h %s')"

echo ""
echo "🗂️ Architecture Branches (Human-Led):"
git branch -a | grep "arch/" | sed 's/.*arch\//  🗂️  /' || echo "  None"

echo ""
echo "⚡ Feature Branches (AI-Assisted):"
git branch -a | grep "feature/" | sed 's/.*feature\//  ⚡ /' || echo "  None"

echo ""
echo "🚀 Release Branches:"
git branch -a | grep "release/" | sed 's/.*release\//  🚀 /' || echo "  None"

echo ""
echo "🔥 Hotfix Branches:"
git branch -a | grep "hotfix/" | sed 's/.*hotfix\//  🔥 /' || echo "  None"

echo ""
echo "📈 Recent Activity:"
git log --oneline -5 | sed 's/^/  /'

echo ""
echo "🌍 Environment Status:"
if [[ -f ".env" ]]; then
    ENV_TYPE=$(grep "APP_ENV=" .env | cut -d'=' -f2)
    echo "  Current environment: $ENV_TYPE"
else
    echo "  No environment configured"
fi

echo ""
echo "🎯 Quick Actions:"
echo "  scripts/git/start-architecture.sh TASK-ID  # Start architecture"
echo "  scripts/git/start-feature.sh TASK-ID       # Start implementation"
echo "  scripts/git/deploy.sh staging              # Deploy to staging"
echo "  scripts/git/deploy.sh prod                 # Deploy to production"
