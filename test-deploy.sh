#!/bin/bash
# Test HF deployment locally

echo "Testing HF CLI and token..."

# Function to load HF_TOKEN from config files
load_hf_token() {
    # Try to load from .env first
    if [ -f ".env" ] && grep -q "HF_TOKEN=" ".env"; then
        export $(grep "HF_TOKEN=" .env | xargs)
        echo "📁 Loaded HF_TOKEN from .env"
        return 0
    fi

    # Try to load from config/production.env
    if [ -f "config/production.env" ] && grep -q "HF_TOKEN=" "config/production.env"; then
        export $(grep "HF_TOKEN=" config/production.env | xargs)
        echo "📁 Loaded HF_TOKEN from config/production.env"
        return 0
    fi

    # Try to load from config/development.env
    if [ -f "config/development.env" ] && grep -q "HF_TOKEN=" "config/development.env"; then
        export $(grep "HF_TOKEN=" config/development.env | xargs)
        echo "📁 Loaded HF_TOKEN from config/development.env"
        return 0
    fi

    return 1
}

# Try to load HF_TOKEN from config files if not already set
if [ -z "$HF_TOKEN" ]; then
    echo "🔍 HF_TOKEN not in environment, checking config files..."

    if ! load_hf_token; then
        echo "❌ HF_TOKEN not found in environment or config files"
        echo ""
        echo "💡 Options to fix this:"
        echo "   1. Set environment variable: HF_TOKEN=your_token ./test-deploy.sh"
        echo "   2. Add HF_TOKEN=your_token to .env"
        echo "   3. Add HF_TOKEN=your_token to config/production.env"
        exit 1
    fi
else
    echo "✅ Using HF_TOKEN from environment variable"
fi

# Test token
echo "🔍 Testing token authentication..."

# Set the token as environment variable for huggingface-cli
export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"

# Test authentication (use newer command)
hf auth whoami

if [ $? -eq 0 ]; then
    echo "✅ Token authentication successful"
else
    echo "❌ Token authentication failed"
    echo "💡 Make sure your HF_TOKEN is valid and has the right permissions"
    exit 1
fi

echo "🚀 Creating test space..."

# Try to create a test space (HUGGING_FACE_HUB_TOKEN is already exported)
# Use newer command and specify SDK type for Space
hf repo create sytse06/test-agent-workbench --repo-type=space --space_sdk=gradio --exist-ok

if [ $? -eq 0 ]; then
    echo "✅ Test space creation successful"
else
    echo "❌ Test space creation failed"
    exit 1
fi

echo "✅ All tests passed!"