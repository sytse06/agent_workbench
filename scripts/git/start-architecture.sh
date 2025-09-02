#!/bin/zsh
# Start architecture branch for human-led design

if [[ -z "$1" ]]; then
    echo "Usage: $0 TASK-ID-description"
    echo "Example: $0 CORE-002-llm-integration"
    exit 1
fi

TASK_ID="$1"
BRANCH="arch/$TASK_ID"

echo "🗂️ Starting architecture branch: $BRANCH"

# Switch to develop and update
git checkout develop
git pull origin develop 2>/dev/null || true

# Create architecture branch
git checkout -b "$BRANCH"

echo "✅ Architecture branch created: $BRANCH"
echo "📋 This branch is for human-led architectural decisions"
echo ""
echo "Next steps:"
echo "1. Use: scripts/scope/start-arch-discussion.sh $TASK_ID"
echo "2. Document architectural decisions"
echo "3. Commit architecture: git commit -m '[ARCH][$TASK_ID]: Architecture decisions'"
echo "4. Merge to develop when complete"
