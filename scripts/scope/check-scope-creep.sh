#!/bin/zsh
# Check for scope creep in current branch

CURRENT_BRANCH=$(git branch --show-current)

if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "develop" ]]; then
    echo "❌ Run this from a feature branch"
    exit 1
fi

echo "🔍 Checking for scope creep in: $CURRENT_BRANCH"

# Extract task ID from branch name
TASK_ID=$(echo "$CURRENT_BRANCH" | sed 's/feature\///' | sed 's/arch\///')
ARCH_FILE="docs/architecture/decisions/$TASK_ID.md"

if [[ ! -f "$ARCH_FILE" ]]; then
    echo "❌ No architecture file found for: $TASK_ID"
    echo "This might indicate scope creep - implementing without proper planning"
    exit 1
fi

echo ""
echo "📊 Scope Analysis:"
echo "=================="

echo ""
echo "📁 Files modified:"
git diff --name-only develop

echo ""
echo "📈 Lines changed:"
git diff --stat develop | tail -1

echo ""
echo "🎯 Original scope (from architecture):"
grep -A 5 "What This Task Includes" "$ARCH_FILE" | grep -v "What This Task Includes"

echo ""
echo "❌ Excluded from scope:"
grep -A 5 "What This Task Explicitly Excludes" "$ARCH_FILE" | grep -v "What This Task Explicitly Excludes"
