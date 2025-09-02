#!/bin/zsh
# Start architectural discussion for a task

if [[ -z "$1" ]]; then
    echo "Usage: $0 TASK-ID-description"
    echo "Example: $0 CORE-002-llm-integration"
    exit 1
fi

TASK_ID="$1"
ARCH_DIR="docs/architecture/decisions"
ARCH_FILE="$ARCH_DIR/$TASK_ID.md"

echo "🗂️ Starting architectural discussion for: $TASK_ID"

# Create architecture decision document
mkdir -p "$ARCH_DIR"
cp docs/architecture/decisions/DECISION_TEMPLATE.md "$ARCH_FILE"

# Replace template placeholders
sed -i "" "s/\[TASK-ID\]/$TASK_ID/g" "$ARCH_FILE"
sed -i "" "s/\[Brief Title\]/Architecture Discussion/g" "$ARCH_FILE"

# Mark as scoping phase
sed -i "" "s/\[ \] SCOPING/\[x\] SCOPING/g" "$ARCH_FILE"

echo "✅ Architecture document created: $ARCH_FILE"
echo ""
echo "Next steps:"
echo "1. Define scope boundaries in the document"
echo "2. Have architectural discussion (with yourself or AI)"
echo "3. Make decisions and document rationale"
echo "4. Run: scripts/scope/finalize-arch-decision.sh $TASK_ID"
