#!/bin/zsh
# Start feature branch for AI-assisted implementation

if [[ -z "$1" ]]; then
    echo "Usage: $0 TASK-ID"
    exit 1
fi

TASK_ID="$1"
ARCH_BRANCH="arch/$TASK_ID"
FEATURE_BRANCH="feature/$TASK_ID"

echo "⚡ Starting feature branch: $FEATURE_BRANCH"

# Check if architecture branch exists and is merged
if git branch -a | grep -q "$ARCH_BRANCH"; then
    if ! git merge-base --is-ancestor "$ARCH_BRANCH" develop; then
        echo "❌ Architecture branch $ARCH_BRANCH not merged to develop"
        echo "Merge architecture first: git checkout develop && git merge $ARCH_BRANCH"
        exit 1
    fi
else
    echo "⚠️ No architecture branch found for $TASK_ID"
    echo "Consider creating architecture first: scripts/git/start-architecture.sh $TASK_ID"
fi

# Switch to develop and update
git checkout develop
git pull origin develop 2>/dev/null || true

# Create feature branch
git checkout -b "$FEATURE_BRANCH"

echo "✅ Feature branch created: $FEATURE_BRANCH"
echo "🤖 This branch is for AI-assisted implementation within boundaries"
echo ""
echo "Next steps:"
echo "1. Use: scripts/scope/start-bounded-implementation.sh $TASK_ID"
echo "2. AI implements within architectural constraints"
echo "3. Review: scripts/scope/review-implementation.sh $TASK_ID"
echo "4. Approve: scripts/scope/approve-implementation.sh $TASK_ID"
