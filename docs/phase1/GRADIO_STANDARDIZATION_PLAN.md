# Gradio UI Standardization Plan

## Problem
During debugging, the Gradio mounting code got broken for local dev. HF Spaces still works perfectly.

## Root Cause
- **HF Spaces**: Uses clean mounting code → Works ✅
- **Local Dev**: Mounting code was modified during debugging → Broken ❌

## Solution: Standardize on HF Spaces Pattern

### Core Principle
**"If it works in HF Spaces, use that exact code everywhere"**

### Standardized Pattern

```python
# 1. Environment Setup (via .env or os.environ)
APP_MODE=workbench  # or seo_coach
APP_ENV=development # or staging, production

# 2. Create Gradio Interface (ModeFactory)
from agent_workbench.ui.mode_factory import ModeFactory

factory = ModeFactory()
interface = factory.create_interface(mode=os.getenv("APP_MODE"))

# 3. Mount in FastAPI (NEVER modify this)
app = gr.mount_gradio_app(app, interface, path="/")

# 4. Run with uvicorn
uvicorn.run(app, host="0.0.0.0", port=PORT)
```

### Key Rules

1. **NEVER modify the mounting code in main.py**
   - It works in HF Spaces
   - Any changes break local dev
   - Keep it simple and stable

2. **Use ModeFactory everywhere**
   - Single source of truth for UI creation
   - Same code path for dev and production
   - Reduces duplication

3. **Environment vars for configuration**
   - APP_MODE: "workbench" or "seo_coach"
   - APP_ENV: "development", "staging", "production"
   - All other config via .env files

4. **Port differences are OK**
   - Dev: 8000
   - HF Spaces: 7860
   - Docker: 8000
   - This is expected and handled by uvicorn config

### Implementation Structure

```
agent_workbench/
├── ui/
│   ├── mode_factory.py          # SINGLE SOURCE: Creates all UIs
│   ├── app.py                   # Workbench mode implementation
│   └── seo_coach_app.py         # SEO coach mode implementation
│
├── main.py                      # FastAPI app + Gradio mounting (STABLE)
├── __main__.py                  # Dev entry point
│
└── deploy/
    └── hf-spaces/
        ├── workbench/app.py     # HF entry point (workbench)
        └── seo-coach/app.py     # HF entry point (seo_coach)
```

### Mounting Code (main.py) - MUST STAY STABLE

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan: mount Gradio ONCE at startup."""

    # 1. Initialize database
    init_adaptive_database()

    # 2. Create Gradio interface using ModeFactory
    from .ui.mode_factory import ModeFactory

    mode = os.getenv("APP_MODE", "workbench")
    factory = ModeFactory()
    gradio_interface = factory.create_interface(mode=mode)

    # 3. Mount Gradio (NEVER modify this)
    app = gr.mount_gradio_app(app, gradio_interface, path="/")

    yield

    # Cleanup
    # ...
```

### Development Entry Point (__main__.py) - CAN BE MODIFIED

```python
if __name__ == "__main__":
    # Dev-specific setup (logging, debug, etc.)
    setup_debug_logging()

    # Run with uvicorn (port 8000 for dev)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True if DEBUG else False
    )
```

### HF Spaces Entry Point (deploy/hf-spaces/*/app.py) - CAN BE MODIFIED

```python
if __name__ == "__main__":
    # HF-specific setup
    os.environ["APP_MODE"] = "workbench"  # or "seo_coach"

    # Run with uvicorn (port 7860 for HF)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860
    )
```

## Testing Strategy

### 1. Local Development Test
```bash
# Set environment
export APP_MODE=workbench

# Run
uv run python -m agent_workbench

# Verify
curl http://localhost:8000/
# Should show Gradio UI
```

### 2. HF Spaces Test
```bash
# Deploy to HF Spaces
git push

# Verify
# Visit https://huggingface.co/spaces/sytse06/agent-workbench
# UI should load and work
```

### 3. Mode Switching Test
```bash
# Test workbench mode
APP_MODE=workbench uv run python -m agent_workbench

# Test seo_coach mode
APP_MODE=seo_coach uv run python -m agent_workbench

# Both should work identically
```

## What Broke During Debugging

### Changes Made (that broke it)
1. ❌ Added `.queue()` before mounting
2. ❌ Changed mounting path from "/" to "/ui"
3. ❌ Added try/except around mounting
4. ❌ Added `SKIP_GRADIO_MOUNT` flag
5. ❌ Created dual-server approach

### Why These Broke It
- Gradio expects specific mounting pattern
- `.queue()` requires WebSocket setup
- Path changes break asset loading
- Try/except hides real errors
- Dual-server adds unnecessary complexity

## Restoration Plan

### Step 1: Revert to Clean Mounting Code
```python
# main.py - lifespan function
# Use EXACT code from last working HF Spaces commit
```

### Step 2: Test Locally
```bash
make start-app
# Should work immediately
```

### Step 3: Lock the Mounting Code
- Add comment: "DO NOT MODIFY - Working in HF Spaces"
- Any changes must be tested in HF Spaces first
- If HF Spaces breaks, local dev will too

### Step 4: Document the Pattern
- Update this doc
- Add to CLAUDE.md
- Create test script

## Future Changes

### How to Add Features WITHOUT Breaking

#### ✅ SAFE: Modify UI in mode_factory.py or app.py
```python
# ui/app.py
def create_workbench_app():
    # Add new buttons, change layout, etc.
    # This is SAFE - doesn't affect mounting
```

#### ✅ SAFE: Add new routes in FastAPI
```python
# api/routes/new_feature.py
@router.get("/new-endpoint")
# This is SAFE - doesn't affect Gradio
```

#### ✅ SAFE: Change environment variables
```python
# config/development.env
NEW_FEATURE=enabled
# This is SAFE - doesn't affect mounting
```

#### ❌ UNSAFE: Modify mounting code
```python
# main.py - lifespan
app = gr.mount_gradio_app(app, gradio_interface, path="/")
# DO NOT TOUCH THIS LINE
```

#### ❌ UNSAFE: Add middleware that affects /
```python
# main.py
@app.middleware("http")
async def intercept_root(request, call_next):
    # This can break Gradio routing
```

## Success Criteria

1. ✅ Local dev UI loads and works
2. ✅ HF Spaces UI loads and works
3. ✅ Both use same mounting code
4. ✅ Mode switching works (workbench ↔ seo_coach)
5. ✅ No special cases or workarounds needed

## Rollback Plan

If standardization breaks something:

1. **Revert main.py to last working commit**
   ```bash
   git log --oneline -- src/agent_workbench/main.py
   git checkout <commit-hash> -- src/agent_workbench/main.py
   ```

2. **Test HF Spaces first**
   - Deploy to staging HF Space
   - Verify UI works
   - Then deploy to local

3. **Document what broke**
   - Update this doc
   - Add to known issues
   - Create test case
