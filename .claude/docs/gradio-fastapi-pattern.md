# Critical Production Pattern: Gradio + FastAPI Mounting

**DO NOT MODIFY without explicit approval - this pattern is production-validated.**

## The Standardized Pattern

```python
# Location: src/agent_workbench/main.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database FIRST
    db = await init_adaptive_database(mode=mode)
    app.adaptive_db = db

    # 2. Create Gradio interface
    gradio_interface = create_fastapi_mounted_gradio_interface()

    # 3. Apply queue and startup events
    gradio_interface.queue()
    gradio_interface.run_startup_events()

    # 4. Mount at root path using FastAPI's native mount
    app.mount("/", gradio_interface.app, name="gradio")

    yield

    await app.requests_client.aclose()

app = FastAPI(lifespan=lifespan)
```

## Why This Pattern Works

1. Database initialized BEFORE interface creation
2. Interface created AFTER database ready
3. Mount happens BEFORE uvicorn accepts requests
4. Uses `app.mount()` NOT `gr.mount_gradio_app()`
5. Accesses `gradio_interface.app` (internal ASGI app)
6. `queue()` + `run_startup_events()` both REQUIRED

## What Doesn't Work

- `gr.mount_gradio_app(app, interface, path="/")` — causes redirect loops
- Mounting before database init — database not available
- Forgetting `run_startup_events()` — buttons don't respond

## Validation

```bash
uv run python test_gradio_unified.py  # All 6 tests must pass
```

**Full docs:** `docs/phase1/GRADIO_STANDARDIZATION_COMPLETE.md`
