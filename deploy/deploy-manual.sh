#!/bin/bash
# Manual HF Spaces Deployment Script
# This replicates the GitHub Actions workflow locally

set -e  # Exit on any error

echo "🚀 Manual HF Spaces Deployment"
echo "==============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to load HF_TOKEN from config files
load_hf_token() {
    # Try to load from .env first
    if [ -f ".env" ] && grep -q "HF_TOKEN=" ".env"; then
        export $(grep "HF_TOKEN=" .env | xargs)
        log_info "Loaded HF_TOKEN from .env"
        return 0
    fi

    # Try to load from config/production.env
    if [ -f "config/production.env" ] && grep -q "HF_TOKEN=" "config/production.env"; then
        export $(grep "HF_TOKEN=" config/production.env | xargs)
        log_info "Loaded HF_TOKEN from config/production.env"
        return 0
    fi

    return 1
}

# Check for HF_TOKEN
if [ -z "$HF_TOKEN" ]; then
    log_info "HF_TOKEN not in environment, checking config files..."
    if ! load_hf_token; then
        log_error "HF_TOKEN not found. Please set it in .env or config/production.env"
        exit 1
    fi
fi

# Set up HF authentication
export HUGGING_FACE_HUB_TOKEN="$HF_TOKEN"

# Verify authentication
log_info "Verifying HF authentication..."
# Try both old and new CLI commands
if huggingface-cli whoami > /dev/null 2>&1; then
    log_success "HF authentication verified"
elif hf auth whoami > /dev/null 2>&1; then
    log_success "HF authentication verified"
else
    log_error "HF authentication failed. Check your token."
    log_info "Trying to login with token..."
    # Attempt to login with token from environment
    if [ -n "$HF_TOKEN" ]; then
        if huggingface-cli login --token "$HF_TOKEN" > /dev/null 2>&1; then
            log_success "Successfully logged in with token"
        else
            log_error "Failed to login with token"
            exit 1
        fi
    else
        exit 1
    fi
fi

# Function to deploy a single Space
deploy_space() {
    local space_name="$1"
    local source_dir="$2"
    local space_type="$3"  # "workbench" or "seo-coach"

    log_info "Deploying $space_type Space: $space_name"
    log_info "Source directory: $source_dir"

    # Create temporary deployment directory
    local deploy_dir="hf-deploy-$space_type"

    if [ -d "$deploy_dir" ]; then
        log_warning "Removing existing deploy directory: $deploy_dir"
        rm -rf "$deploy_dir"
    fi

    mkdir "$deploy_dir"
    log_success "Created deployment directory: $deploy_dir"

    # Copy Space configuration files
    log_info "Copying Space configuration files..."
    cp -r "$source_dir"/* "$deploy_dir/"

    # Copy source code
    log_info "Copying application source code..."
    cp -r src/ "$deploy_dir/src/"
    cp pyproject.toml "$deploy_dir/"
    cp -r alembic/ "$deploy_dir/alembic/"
    cp alembic.ini "$deploy_dir/"

    # Copy config directory but exclude files with secrets
    log_info "Copying config files (excluding secret files)..."
    mkdir -p "$deploy_dir/config/"
    find config/ -name "*.env" -not -name "*production*" -not -name "*development*" -not -name "*staging*" -exec cp {} "$deploy_dir/config/" \; 2>/dev/null || true
    # Copy non-.env config files
    find config/ -not -name "*.env" -type f -exec cp {} "$deploy_dir/config/" \; 2>/dev/null || true

    # Generate requirements.txt from pyproject.toml
    log_info "Generating requirements.txt from pyproject.toml..."

    # Store current directory and navigate back to project root
    project_root="$(pwd)"
    cd "$project_root"

    # Use environment variables to pass values to Python
    DEPLOY_DIR="$deploy_dir" SPACE_TYPE="$space_type" uv run python -c "
import toml
import sys
import os

# Read pyproject.toml from project root
with open('pyproject.toml', 'r') as f:
    data = toml.load(f)

# Get variables from environment
deploy_dir = os.environ['DEPLOY_DIR']
space_type = os.environ['SPACE_TYPE']
requirements_path = os.path.join(deploy_dir, 'requirements.txt')

with open(requirements_path, 'w') as f:
    f.write('# Generated from pyproject.toml for HuggingFace Spaces\n')

    # Main dependencies
    for dep in data['project']['dependencies']:
        f.write(dep + '\n')

    # Add space-specific dependencies
    if space_type == 'seo-coach':
        f.write('firecrawl-py>=0.0.8\n')

print('✅ Generated requirements.txt')
"

    if [ $? -eq 0 ]; then
        log_success "Generated requirements.txt successfully"
    else
        log_error "Failed to generate requirements.txt"
        cd ..
        return 1
    fi

    # Navigate back to deployment directory
    cd "$deploy_dir"

    # Show what we're about to deploy
    log_info "Files in deployment directory:"
    ls -la
    echo ""

    # Create the Space if it doesn't exist
    log_info "Creating Space if it doesn't exist: $space_name"
    hf repo create "$space_name" --repo-type=space --space_sdk=gradio --exist-ok || {
        log_warning "Space creation returned an error (might already exist)"
    }

    # Remove .venv directory before deployment to reduce upload size
    if [ -d ".venv" ]; then
        log_info "Removing .venv directory to reduce upload size..."
        rm -rf .venv
    fi

    # Deploy to HF Space
    log_info "Uploading files to HF Space: $space_name"
    if hf upload "$space_name" . --repo-type=space; then
        log_success "Successfully deployed to $space_name"
        log_success "🌐 Space URL: https://huggingface.co/spaces/$space_name"
    else
        log_error "Failed to upload to $space_name"
        cd ..
        return 1
    fi

    cd ..
    log_success "Deployment of $space_type completed"
    return 0
}

# Deploy Workbench Space
echo ""
log_info "=== Deploying Workbench Space ==="
if deploy_space "sytse06/agent-workbench-technical" "deploy/hf-spaces/workbench" "workbench"; then
    log_success "Workbench Space deployment completed!"
else
    log_error "Workbench Space deployment failed!"
    exit 1
fi

# Deploy SEO Coach Space
echo ""
log_info "=== Deploying SEO Coach Space ==="
if deploy_space "sytse06/agent-workbench-seo-coach" "deploy/hf-spaces/seo-coach" "seo-coach"; then
    log_success "SEO Coach Space deployment completed!"
else
    log_error "SEO Coach Space deployment failed!"
    exit 1
fi

# Summary
echo ""
log_success "🎉 Manual deployment completed successfully!"
echo ""
echo "Your Spaces are now live:"
echo "🛠️  Workbench: https://huggingface.co/spaces/sytse06/agent-workbench-technical"
echo "🎯 SEO Coach: https://huggingface.co/spaces/sytse06/agent-workbench-seo-coach"
echo ""
echo "Next steps:"
echo "1. Test both Spaces in the browser"
echo "2. Check that PWA installation works on mobile"
echo "3. If everything works, debug GitHub Actions workflow"

# Cleanup temp directories
log_info "Cleaning up temporary directories..."
rm -rf hf-deploy-workbench hf-deploy-seo-coach 2>/dev/null || true
log_success "Cleanup completed"