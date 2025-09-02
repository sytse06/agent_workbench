# Human-Steered AI Development Workflow

## Philosophy
- **Human navigates, AI pilots**
- **Architectural decisions are human-only**
- **Scope boundaries are sacred**
- **AI implements within constraints**

## Workflow Steps

### 1. Architectural Discussion (Human-Led)
```bash
scripts/scope/start-arch-discussion.sh TASK-ID-description
```
- Define what's in/out of scope
- Have architectural discussions (with yourself or AI advisor)
- Document decisions and rationale
- Set implementation boundaries

### 2. Start Bounded Implementation (AI-Assisted)
```bash
scripts/scope/start-bounded-implementation.sh TASK-ID
```
- Create implementation branch
- Generate AI prompt with strict boundaries
- AI implements within constraints only

### 3. Review Implementation (Human Oversight)
```bash
scripts/scope/review-implementation.sh TASK-ID
```
- Check scope compliance
- Verify boundaries were respected
- Detect any scope creep

## Quick Commands

### Git Workflow
```bash
make git-status                 # Show git overview
make arch TASK=CORE-002-name    # Start architecture phase
make feature TASK=CORE-002-name # Start implementation phase
```

### Environment Management
```bash
make dev                        # Development environment
make staging                    # Staging environment
make prod                       # Production environment
```

### Deployment
```bash
make deploy ENV=staging         # Deploy to staging
make deploy ENV=prod           # Deploy to production
```

## Key Principles

1. **No Architectural Surprises**: All architecture decisions documented and human-approved
2. **Scope Boundaries**: Clearly defined what's in/out for each task
3. **Implementation Constraints**: AI works within predefined boundaries
4. **Regular Reviews**: Human oversight at each step
5. **Iterative Planning**: Small, bounded iterations with clear objectives
