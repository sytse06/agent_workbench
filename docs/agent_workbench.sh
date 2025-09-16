#!/bin/zsh
# Agent Workbench - Streamlined Session Management
# Single codebase with environment-based deployment
# Usage: load_project agent_workbench

# ANSI color codes for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project Configuration - Single codebase
export PROJECT_NAME="agent_workbench"
export PROJECT_ROOT="$HOME/Documents/dev/projects/agent_workbench"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[Agent Workbench]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_section() {
    echo -e "\n${CYAN}=== $1 ===${NC}"
}

# Development environment (single codebase)
agent_dev() {
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        print_error "Project directory not found: $PROJECT_ROOT"
        print_info "Run 'git clone' or initialize the project first"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Setup environment for development
    export UV_PROJECT_ENVIRONMENT="development"
    export UV_PYTHON_PREFERENCE="managed"
    export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
    export PROJECT_ENV="dev"
    export APP_ENV="development"
    
    # Load development environment variables
    if [[ -f "config/development.env" ]]; then
        print_info "Loading development environment configuration..."
        set -a
        source config/development.env
        set +a
        print_status "Development environment variables loaded"
    elif [[ -f ".env" ]]; then
        # Fallback to .env if present
        set -a
        source .env
        set +a
        print_status "Environment variables loaded from .env"
    else
        print_warning "No environment configuration found"
        print_info "Copy config/development.env to .env or run: make dev"
    fi
    
    # Activate UV virtual environment
    if [[ -f ".venv/pyvenv.cfg" ]]; then
        export VIRTUAL_ENV="$(pwd)/.venv"
        export PATH="$VIRTUAL_ENV/bin:$PATH"
        unset PYTHON_HOME
        print_status "UV virtual environment activated"
    else
        print_warning "No UV virtual environment found. Run: uv sync"
    fi
    
    print_section "Agent Workbench Development Environment"
    echo
    print_info "Environment Status:"
    echo "📁 Directory: $(pwd)"
    
    local git_branch=$(git branch --show-current 2>/dev/null)
    echo "🌿 Git branch: ${git_branch:-'Not in git repo'}"
    
    local python_version=$(python3 --version 2>/dev/null)
    echo "🐍 Python: ${python_version:-'Python not found'}"
    
    if [[ -f ".venv/bin/python" ]]; then
        local venv_python=$(.venv/bin/python --version 2>/dev/null)
        echo "🔮 Virtual Env Python: ${venv_python:-'Version check failed'}"
    else
        echo "🔮 Virtual Env Python: No venv found"
    fi
    
    local uv_version=$(uv --version 2>/dev/null)
    echo "📦 UV: ${uv_version:-'UV not found'}"
    echo "🌍 Environment: ${APP_ENV:-development}"
    echo "🏷️  Project: $PROJECT_NAME"
    
    # Show current environment config
    if [[ -f ".env" ]]; then
        local env_type=$(grep "APP_ENV=" .env 2>/dev/null | cut -d'=' -f2)
        echo "⚙️  Active Config: ${env_type:-unknown}"
    fi
    
    echo
    echo -e "${CYAN}🚀 Quick Commands:${NC}"
    echo "  make dev                        - Configure dev environment"
    echo "  make staging                    - Configure staging environment"
    echo "  make prod                       - Configure production environment"
    echo "  make test                       - Run test suite"
    echo "  make quality-check              - Run code quality checks"
    echo "  make install                    - Install/sync dependencies"
    echo "  uv run python -m agent_workbench - Start application"
    echo "  uv run alembic upgrade head     - Apply database migrations"
    echo
    echo -e "${PURPLE}🌿 Human-Steered Workflow:${NC}"
    echo "  agent_arch TASK=CORE-001-name    - Start architecture phase"
    echo "  agent_feature TASK=CORE-001-name - Start implementation phase"
    echo "  agent_validate TASK=CORE-001-name - Comprehensive validation"
    echo "  agent_complete TASK=CORE-001-name - Complete & merge"
    echo "  agent_scope_check TASK=CORE-001   - Check scope compliance"
    echo
    echo -e "${YELLOW}🚀 Deployment:${NC}"
    echo "  make deploy ENV=staging         - Deploy to staging"
    echo "  make deploy ENV=prod           - Deploy to production"
    echo "  agent_staging                  - Switch to staging mode"
    echo "  agent_prod                     - Switch to production mode"
}

# Enhanced agent_quality that integrates with Makefile
agent_quality() {
    print_info "Running comprehensive code quality checks..."
    if [[ -f "pyproject.toml" ]]; then
        make quality-check
    else
        print_error "No pyproject.toml found. Are you in the project directory?"
        print_info "Navigate to: $PROJECT_ROOT"
    fi
}

# Quick quality auto-fix
agent_fix() {
    print_info "Auto-fixing code quality issues..."
    if [[ -f "pyproject.toml" ]]; then
        make quality-fix
        print_status "Auto-fixes applied - review changes and re-validate"
    else
        print_error "No pyproject.toml found. Are you in the project directory?"
        print_info "Navigate to: $PROJECT_ROOT"
    fi
}

# Comprehensive validation function
agent_validate() {
    if [[ -z "$1" ]]; then
        print_error "Usage: agent_validate TASK-ID"
        print_info "Example: agent_validate CORE-002-database-models"
        return 1
    fi
    print_info "Running comprehensive validation for: $1"
    make validate TASK="$1"
}

# Scope compliance checker
agent_scope_check() {
    if [[ -z "$1" ]]; then
        print_error "Usage: agent_scope_check TASK-ID"
        print_info "Example: agent_scope_check CORE-002-database-models"
        return 1
    fi
    
    print_info "Checking scope compliance for: $1"
    if [[ -x "./scripts/scope/agent_scope_check.sh" ]]; then
        ./scripts/scope/agent_scope_check.sh "$1"
    else
        print_error "Scope check script not found: scripts/scope/agent_scope_check.sh"
        print_info "Ensure the script exists and is executable"
        return 1
    fi
}

# Pre-commit quality gate
agent_precommit() {
    print_info "Running pre-commit quality gate..."
    if [[ -f "pyproject.toml" ]]; then
        make pre-commit
    else
        print_error "No pyproject.toml found. Are you in the project directory?"
        print_info "Navigate to: $PROJECT_ROOT"
    fi
}

# Staging environment
agent_staging() {
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        print_error "Project directory not found: $PROJECT_ROOT"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Check if on correct branch for staging
    local current_branch=$(git branch --show-current 2>/dev/null)
    if [[ "$current_branch" != "develop" ]]; then
        print_warning "Staging typically deploys from 'develop' branch"
        print_info "Current branch: $current_branch"
        read "confirm?Continue anyway? (y/N): "
        if [[ $confirm != [yY] ]]; then
            print_info "Switch to develop: git checkout develop"
            return 1
        fi
    fi
    
    # Setup environment for staging
    export UV_PROJECT_ENVIRONMENT="staging"
    export UV_PYTHON_PREFERENCE="managed"
    export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
    export PROJECT_ENV="staging"
    export APP_ENV="staging"
    
    # Load staging environment variables
    if [[ -f "config/staging.env" ]]; then
        print_info "Loading staging environment configuration..."
        cp config/staging.env .env
        set -a
        source .env
        set +a
        print_status "Staging environment configured"
    else
        print_error "Staging configuration not found: config/staging.env"
        return 1
    fi
    
    # Activate UV virtual environment
    if [[ -f ".venv/pyvenv.cfg" ]]; then
        export VIRTUAL_ENV="$(pwd)/.venv"
        export PATH="$VIRTUAL_ENV/bin:$PATH"
        unset PYTHON_HOME
        print_status "UV virtual environment activated"
    else
        print_warning "No UV virtual environment found. Run: uv sync"
    fi
    
    print_section "Agent Workbench Staging Environment"
    echo
    print_info "Environment Status:"
    echo "📁 Directory: $(pwd)"
    echo "🌿 Git branch: $current_branch"
    echo "🌍 Environment: staging"
    echo "⚙️  Config: config/staging.env → .env"
    echo "🏷️  Project: $PROJECT_NAME"
    echo
    echo -e "${CYAN}🧪 Staging Commands:${NC}"
    echo "  uv run python -m agent_workbench - Start staging application"
    echo "  make test                       - Run tests before staging"
    echo "  make deploy ENV=staging         - Full staging deployment"
    echo "  agent_dev                      - Switch back to development"
}

# Production environment  
agent_prod() {
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        print_error "Project directory not found: $PROJECT_ROOT"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    
    # Check if on correct branch for production
    local current_branch=$(git branch --show-current 2>/dev/null)
    if [[ "$current_branch" != "main" ]]; then
        print_error "Production must deploy from 'main' branch only"
        print_info "Current branch: $current_branch"
        print_info "Switch to main: git checkout main"
        return 1
    fi
    
    # Production safety check
    print_warning "⚠️  PRODUCTION ENVIRONMENT ⚠️"
    read "confirm?Are you sure you want to configure production? (y/N): "
    if [[ $confirm != [yY] ]]; then
        print_info "Production configuration cancelled"
        return 1
    fi
    
    # Setup environment for production
    export UV_PROJECT_ENVIRONMENT="production"
    export UV_PYTHON_PREFERENCE="managed"
    export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
    export PROJECT_ENV="prod"
    export APP_ENV="production"
    
    # Load production environment variables
    if [[ -f "config/production.env" ]]; then
        print_info "Loading production environment configuration..."
        cp config/production.env .env
        set -a
        source .env
        set +a
        print_status "Production environment configured"
    else
        print_error "Production configuration not found: config/production.env"
        return 1
    fi
    
    # Activate UV virtual environment
    if [[ -f ".venv/pyvenv.cfg" ]]; then
        export VIRTUAL_ENV="$(pwd)/.venv"
        export PATH="$VIRTUAL_ENV/bin:$PATH"
        unset PYTHON_HOME
        print_status "UV virtual environment activated"
    else
        print_error "No UV virtual environment found. Run: uv sync"
        return 1
    fi
    
    print_section "Agent Workbench Production Environment"
    echo
    print_info "Environment Status:"
    echo "📁 Directory: $(pwd)"
    echo "🌿 Git branch: $current_branch"
    echo "🌍 Environment: production"
    echo "⚙️  Config: config/production.env → .env"
    echo "🏷️  Project: $PROJECT_NAME"
    echo
    print_warning "🚨 PRODUCTION ENVIRONMENT ACTIVE 🚨"
    echo
    echo -e "${CYAN}🚀 Production Commands:${NC}"
    echo "  uv run python -m agent_workbench - Start production application"
    echo "  make deploy ENV=prod            - Full production deployment"
    echo "  agent_dev                       - Switch back to development"
    echo "  agent_staging                   - Switch to staging"
}

# Comprehensive project status
agent_status() {
    print_section "Agent Workbench Project Status"
    
    local base_dir="$PROJECT_ROOT"
    echo "📁 Project Directory: $base_dir"
    
    # Check if base directory exists
    if [[ -d "$base_dir" ]]; then
        cd "$base_dir"
        local git_status=$(git branch --show-current 2>/dev/null)
        echo "🌿 Current Git Branch: ${git_status:-'Not in git repo'}"
        local last_commit=$(git log -1 --format='%h %s' 2>/dev/null)
        echo "🏷️  Last Commit: ${last_commit:-'No commits'}"
        
        # Show git workflow status
        echo
        echo "🌿 Git Workflow Status:"
        local arch_branches=$(git branch -a | grep "arch/" | wc -l | tr -d ' ')
        local feature_branches=$(git branch -a | grep "feature/" | wc -l | tr -d ' ')
        echo "   🏗️  Architecture branches: $arch_branches"
        echo "   ⚡ Feature branches: $feature_branches"
        
    else
        echo "❌ Project directory not found"
        print_info "Initialize project first or check PROJECT_ROOT path"
        return 1
    fi
    
    echo
    echo "⚙️  Environment Configurations:"
    for env in development staging production; do
        if [[ -f "config/${env}.env" ]]; then
            echo "   ✅ config/${env}.env"
        else
            echo "   ❌ config/${env}.env (missing)"
        fi
    done
    
    echo
    echo "🌍 Current Environment Setup:"
    if [[ -f ".env" ]]; then
        local env_type=$(grep "APP_ENV=" .env 2>/dev/null | cut -d'=' -f2)
        echo "   Active: ${env_type:-'unknown'}"
        local db_url=$(grep "DATABASE_URL=" .env 2>/dev/null | cut -d'=' -f2)
        if [[ -n "$db_url" ]]; then
            echo "   Database: ${db_url}"
        fi
    else
        echo "   ❌ No active environment (.env not found)"
        echo "   💡 Run: make dev, make staging, or make prod"
    fi
    
    echo
    echo "🔧 Development Setup:"
    
    # Check UV environment
    if [[ -f ".venv/pyvenv.cfg" ]]; then
        echo "   ✅ UV virtual environment"
        if [[ -f ".venv/bin/python" ]]; then
            local python_version=$(.venv/bin/python --version 2>/dev/null)
            echo "   🐍 Python: ${python_version:-'Version check failed'}"
        fi
    else
        echo "   ❌ No UV virtual environment (run: uv sync)"
    fi
    
    # Check pyproject.toml
    if [[ -f "pyproject.toml" ]]; then
        echo "   ✅ pyproject.toml found"
    else
        echo "   ❌ pyproject.toml not found"
    fi
    
    # Check alembic
    if [[ -f "alembic.ini" ]]; then
        echo "   ✅ Alembic configuration found"
    else
        echo "   ❌ Alembic not configured"
    fi
    
    # Check database
    if [[ -f "data/agent_workbench_dev.db" ]]; then
        echo "   ✅ Development database found"
    else
        echo "   ❌ No development database (run: uv run alembic upgrade head)"
    fi
    
    # Check human-steered workflow tools
    echo
    echo "🤖 Human-Steered Workflow Tools:"
    if [[ -x "./scripts/scope/agent_scope_check.sh" ]]; then
        echo "   ✅ Scope compliance checker"
    else
        echo "   ❌ Scope compliance checker (scripts/scope/agent_scope_check.sh)"
    fi
    
    if [[ -d "docs/architecture/decisions" ]]; then
        local adr_count=$(find docs/architecture/decisions -name "*.md" -type f | wc -l | tr -d ' ')
        echo "   ✅ Architecture decisions ($adr_count ADRs)"
    else
        echo "   ❌ Architecture decisions directory"
    fi
    
    echo
    echo "🔧 System Dependencies:"
    local uv_version=$(uv --version 2>/dev/null)
    echo "   📦 UV: ${uv_version:-'❌ Not installed'}"
    local python_version=$(python3 --version 2>/dev/null)
    echo "   🐍 System Python: ${python_version:-'❌ Not found'}"
    local git_version=$(git --version 2>/dev/null)
    echo "   🌐 Git: ${git_version:-'❌ Not installed'}"
    local docker_version=$(docker --version 2>/dev/null)
    echo "   🐳 Docker: ${docker_version:-'❌ Not installed (optional)'}"
    local ollama_version=$(ollama --version 2>/dev/null)
    echo "   🦙 Ollama: ${ollama_version:-'❌ Not installed (optional)'}"
    
    echo
    echo "🚀 Quick Actions:"
    echo "   agent_dev                       - Switch to development"
    echo "   agent_staging                   - Switch to staging"
    echo "   agent_prod                      - Switch to production"
    echo "   make git-status                 - Show detailed git status"
    echo "   make test                       - Run test suite"
    echo "   agent_quality                   - Run code quality checks"
}

# Smart environment switcher
agent_shell() {
    local current_dir=$(pwd)
    
    # Check if we're in the agent workbench project
    if [[ "$current_dir" == *"agent_workbench"* ]]; then
        cd "$PROJECT_ROOT" 2>/dev/null || {
            print_error "Could not access project root: $PROJECT_ROOT"
            return 1
        }
        
        print_info "Agent Workbench Project Detected"
        echo
        echo "Select environment:"
        echo "1. 🛠️  Development - For active development work"
        echo "2. 🧪 Staging - For testing and integration"
        echo "3. 🚀 Production - For production deployment"
        echo "4. 📊 Status - Show project overview"
        echo "5. 🔧 Git Status - Show git workflow status"
        echo "6. 🎯 Quality Check - Run code quality validation"
        echo
        read "choice?Enter your choice (1-6): "
        case $choice in
            1) agent_dev ;;
            2) agent_staging ;;
            3) agent_prod ;;
            4) agent_status ;;
            5) make git-status ;;
            6) agent_quality ;;
            *) print_error "Invalid choice" ;;
        esac
    else
        print_info "Navigate to Agent Workbench project"
        echo
        echo "Available actions:"
        echo "1. 🛠️  Development environment"
        echo "2. 🧪 Staging environment"
        echo "3. 🚀 Production environment"
        echo "4. 📊 Project status"
        echo "5. 🎯 Quality check"
        echo
        read "choice?Enter your choice (1-5): "
        case $choice in
            1) agent_dev ;;
            2) agent_staging ;;
            3) agent_prod ;;
            4) agent_status ;;
            5) agent_quality ;;
            *) print_error "Invalid choice" ;;
        esac
    fi
}

# Streamlined project utilities
agent_sync() {
    print_info "Syncing UV dependencies..."
    if [[ -f "pyproject.toml" ]]; then
        uv sync
        print_status "Dependencies synced"
    else
        print_error "No pyproject.toml found. Are you in the project directory?"
        print_info "Navigate to: $PROJECT_ROOT"
    fi
}

agent_clean() {
    print_info "Cleaning project artifacts..."
    rm -rf .venv/ .pytest_cache/ htmlcov/ dist/ *.egg-info/
    find . -type d -name __pycache__ -delete 2>/dev/null
    find . -type f -name "*.pyc" -delete 2>/dev/null
    print_status "Project cleaned"
}

agent_test() {
    print_info "Running tests..."
    if [[ -f "pyproject.toml" ]]; then
        uv run pytest tests/ -v --cov=src/agent_workbench
    else
        print_error "No pyproject.toml found. Are you in the project directory?"
    fi
}

agent_migrate() {
    print_info "Running database migrations..."
    if [[ -f "alembic.ini" ]]; then
        uv run alembic upgrade head
        print_status "Database migrations complete"
    else
        print_error "No alembic.ini found. Are you in the project directory?"
    fi
}

agent_reset_db() {
    local current_env="${APP_ENV:-development}"
    print_warning "This will delete your $current_env database and recreate it. Are you sure? (y/N)"
    read "confirm?"
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        rm -f data/agent_workbench_${current_env}.db
        if [[ -f "alembic.ini" ]]; then
            uv run alembic upgrade head
            print_status "Database reset complete for $current_env environment"
        else
            print_error "No alembic.ini found for migration"
        fi
    else
        print_info "Database reset cancelled"
    fi
}

# Git workflow shortcuts
agent_git_status() {
    print_info "Running comprehensive git status..."
    if [[ -f "scripts/git/status.sh" ]]; then
        ./scripts/git/status.sh
    else
        make git-status
    fi
}

# Human-Steered Workflow functions
agent_arch() {
    if [[ -z "$1" ]]; then
        print_error "Usage: agent_arch TASK-ID-description"
        print_info "Example: agent_arch CORE-001-model-system"
        return 1
    fi
    make arch TASK="$1"
}

agent_feature() {
    if [[ -z "$1" ]]; then
        print_error "Usage: agent_feature TASK-ID"
        print_info "Example: agent_feature CORE-001-model-system"
        return 1
    fi
    make feature TASK="$1"
}

agent_complete() {
    if [[ -z "$1" ]]; then
        print_error "Usage: agent_complete TASK-ID"
        print_info "Example: agent_complete CORE-001-model-system"
        return 1
    fi
    make complete TASK="$1"
}

# Create aliases for backwards compatibility and convenience
alias agent="agent_shell"
alias posh_agent="agent_shell"
alias awb="agent_shell"

print_status "Agent Workbench streamlined session management loaded! 🚀"
print_info "Project: $PROJECT_ROOT"
print_info "Single codebase with environment-based deployment"

# Available commands info
echo -e "\n${CYAN}🌍 Environment Management:${NC}"
echo "  agent_dev        - Development environment"
echo "  agent_staging    - Staging environment" 
echo "  agent_prod       - Production environment"
echo "  agent_status     - Show project status"
echo "  agent_shell      - Smart environment switcher (aliases: agent, awb)"

echo -e "\n${PURPLE}🔧 Development Tools:${NC}"
echo "  agent_sync       - Sync UV dependencies"
echo "  agent_clean      - Clean project artifacts"
echo "  agent_test       - Run test suite"
echo "  agent_quality    - Run code quality checks"
echo "  agent_fix        - Auto-fix code quality issues"
echo "  agent_precommit  - Pre-commit quality gate"
echo "  agent_migrate    - Run database migrations"
echo "  agent_reset_db   - Reset database (with confirmation)"

echo -e "\n${YELLOW}🌿 Human-Steered Workflow:${NC}"
echo "  agent_arch TASK          - Start architecture phase"
echo "  agent_feature TASK       - Start implementation phase"
echo "  agent_validate TASK      - Comprehensive validation (quality + scope + tests)"
echo "  agent_complete TASK      - Complete & merge to develop"
echo "  agent_scope_check TASK   - Check scope compliance only"
echo "  agent_git_status         - Comprehensive git status"

echo -e "\n${GREEN}🚀 Quick Start:${NC}"
echo "  agent            - Interactive environment switcher"
echo "  agent_dev        - Jump to development"
echo "  make dev         - Configure development environment"

# Check project setup status
if [[ ! -d "$PROJECT_ROOT" ]]; then
    print_warning "Project directory not found: $PROJECT_ROOT"
    echo "💡 Create the project directory and initialize with git"
elif [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    print_warning "Project not fully initialized"
    echo "💡 Navigate to project and initialize: cd $PROJECT_ROOT && uv init"
fi