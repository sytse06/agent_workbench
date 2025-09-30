# Git Workflow Guidelines

**Established**: 2025-09-30
**Branch Structure**: `main` (production) → `develop` (integration) → `feature/*` (development)

## Branch Strategy

### 🚀 `main` - Production Branch
- **Purpose**: Stable, production-ready code deployed to HuggingFace Spaces
- **Protection**: Direct pushes prohibited (except critical hotfixes)
- **Deployment**: Auto-deployed to production HF Spaces via GitHub Actions
- **Merge Sources**: `develop` (releases), hotfix branches (emergencies)

### 🔧 `develop` - Integration Branch
- **Purpose**: Integration branch for feature development
- **Stability**: Should be stable, but allows for integration testing
- **Merge Sources**: `feature/*` branches
- **Merge Target**: `main` for releases

### 🌟 `feature/*` - Development Branches
- **Naming**: `feature/[COMPONENT]-[TASK-ID]-[description]`
- **Examples**:
  - `feature/UI-004-chat-history-panel`
  - `feature/LLM-003-openrouter-integration`
  - `feature/PROD-005-docker-optimization`
- **Lifecycle**: Branch from `develop` → develop → merge back to `develop`

## Standard Development Workflow

### 1. Starting New Feature
```bash
# Switch to develop and pull latest
git checkout develop
git pull origin develop

# Create new feature branch
git checkout -b feature/COMPONENT-ID-description

# Work on your feature...
git add .
git commit -m "feat: implement feature description"
```

### 2. Completing Feature
```bash
# Ensure develop is up to date
git checkout develop
git pull origin develop

# Rebase feature on latest develop (optional but recommended)
git checkout feature/COMPONENT-ID-description
git rebase develop

# Merge feature to develop
git checkout develop
git merge feature/COMPONENT-ID-description

# Push to remote
git push origin develop

# Clean up feature branch
git branch -d feature/COMPONENT-ID-description
```

### 3. Release Process
```bash
# From develop, create release
git checkout develop
git pull origin develop

# Merge to main
git checkout main
git merge develop

# Tag release
git tag -a v1.x.x -m "Release v1.x.x: description"

# Push to production
git push origin main
git push origin --tags
```

## Hotfix Workflow (Emergency Production Fixes)

### When to Use Hotfixes
- **Critical production bugs** affecting HF Spaces
- **Security vulnerabilities** requiring immediate fixes
- **Deployment issues** blocking production functionality

### Hotfix Process
```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/description

# Fix the issue
git add .
git commit -m "hotfix: fix critical production issue"

# Apply to main
git checkout main
git merge hotfix/description

# Apply to develop
git checkout develop
git merge hotfix/description

# Push both branches
git push origin main
git push origin develop

# Clean up
git branch -d hotfix/description
```

## Commit Message Conventions

### Format
```
type(scope): description

[optional body]

[optional footer]
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **hotfix**: Emergency production fixes

### Examples
```bash
git commit -m "feat(ui): add chat history panel with export functionality"
git commit -m "fix(api): resolve SQLAlchemy connection pooling issue"
git commit -m "hotfix(deploy): fix requirements.txt generation in HF Spaces"
git commit -m "docs(workflow): add git workflow guidelines"
```

## Branch Protection Rules

### `main` Branch
- ✅ **Require pull request reviews**: 1 reviewer
- ✅ **Require status checks**: CI tests must pass
- ✅ **Require up-to-date branches**: Must be current with main
- ✅ **Include administrators**: Apply rules to admins
- ❌ **Allow force pushes**: Disabled for safety

### `develop` Branch
- ✅ **Require status checks**: CI tests must pass
- ❌ **Require pull request reviews**: Allow direct merges for speed
- ❌ **Allow force pushes**: Disabled for safety

## CI/CD Integration

### GitHub Actions Triggers
- **Push to `main`**: Deploy to production HF Spaces
- **Push to `develop`**: Run full test suite
- **Pull requests**: Run tests and quality checks

### Test Requirements
- **Unit tests**: Must pass (`pytest tests/unit/`)
- **Integration tests**: Must pass (`pytest tests/integration/`)
- **Code quality**: Linting (ruff), formatting (black), type checking (mypy)
- **Security**: Trivy vulnerability scanning

## Special Cases

### Emergency Hotfix (What We Just Did)
When a critical production issue requires immediate fixing:

1. **Work directly on `main`** (only for emergencies)
2. **Document thoroughly** (create hotfix documentation)
3. **Sync to `develop`** immediately after
4. **Resume normal workflow** for subsequent changes

### Large Architectural Changes
For major refactoring or architectural changes:

1. **Create `arch/` prefix branch** from `develop`
2. **Develop architecture** with multiple commits
3. **Review thoroughly** before merging to `develop`
4. **Consider feature flags** for gradual rollouts

## Tools and Commands

### Useful Git Aliases
```bash
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
git config --global alias.lg "log --oneline --decorate --all --graph"
```

### Branch Cleanup
```bash
# Delete merged local branches
git branch --merged develop | grep -v "develop\|main" | xargs -n 1 git branch -d

# Delete remote tracking branches that no longer exist
git remote prune origin
```

## Current Status

### Active Branches
- ✅ **`main`**: Production with LiteLLM OpenRouter hotfix
- ✅ **`develop`**: Synced with main, ready for new development
- 🔄 **Feature branches**: Various architectural and feature work in progress

### Recent Hotfix Summary
- **Issue**: HF Spaces deployment broken (SQLAlchemy, Gradio, API integration)
- **Solution**: LiteLLM + OpenRouter integration
- **Status**: ✅ Production deployed and working
- **Documentation**: See `docs/hotfix_litellm_hf.md`

---

**Next Development**: All new features should branch from `develop` and follow the standard workflow above.