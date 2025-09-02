#!/bin/zsh
# Start implementation with architectural boundaries

if [[ -z "$1" ]]; then
    echo "Usage: $0 TASK-ID"
    exit 1
fi

TASK_ID="$1"
ARCH_FILE="docs/architecture/decisions/$TASK_ID.md"

if [[ ! -f "$ARCH_FILE" ]]; then
    echo "❌ Architecture file not found: $ARCH_FILE"
    echo "Complete architecture phase first"
    exit 1
fi

echo "⚡ Starting bounded implementation for: $TASK_ID"

# Create implementation branch
git checkout develop
git checkout -b "feature/$TASK_ID"

# Create AI implementation prompt with boundaries
AI_PROMPT_FILE="docs/prompts/implementation/$TASK_ID-prompt.md"
mkdir -p "docs/prompts/implementation"

cat > "$AI_PROMPT_FILE" << PROMPT_EOF
# Implementation Prompt: $TASK_ID

## Context
Agent Workbench LLM chat application
Architecture decision: docs/architecture/decisions/$TASK_ID.md

## STRICT BOUNDARIES (DO NOT EXCEED)
$(grep -A 10 "What This Task Includes" "$ARCH_FILE")

$(grep -A 10 "What This Task Explicitly Excludes" "$ARCH_FILE")

## Implementation Requirements
$(grep -A 20 "Implementation Boundaries for AI" "$ARCH_FILE")

## IMPORTANT: DO NOT
- Add features not explicitly listed in scope
- Modify files not specified in boundaries
- Add dependencies not approved in architecture
- Change existing interfaces without explicit permission
- Implement "nice to have" features

PROMPT_EOF

echo "✅ Implementation branch created: feature/$TASK_ID"
echo "✅ AI prompt with boundaries created: $AI_PROMPT_FILE"
echo ""
echo "Next steps:"
echo "1. Use $AI_PROMPT_FILE with your AI tool"
echo "2. Review AI implementation against boundaries"
echo "3. Run: scripts/scope/review-implementation.sh $TASK_ID"
