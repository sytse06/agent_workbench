# Gradio Mounting Debug Session - 2025-10-06

## Problem Summary
Gradio UI loads but is not responsive (buttons don't work) when mounted in FastAPI locally. Works perfectly in HuggingFace Spaces.

## What Works ✅

1. **HuggingFace Spaces deployment** - Fully functional
   - UI loads correctly
   - Chat works
   - Database persistence works (Hub DB)

2. **AdaptiveDatabase** - Working correctly
   - Environment detection: ✅ (local/docker/hf_spaces)
   - SQLiteBackend: ✅ (tested successfully)
   - HubBackend: ✅ (working in HF Spaces)

3. **Standalone Gradio test** - Partially working
   - UI loads: ✅
   - Chat attempts to work: ✅
   - Error found: `ChatResponse` has `.message` not `.reply` (FIXED)

## What Doesn't Work ❌

1. **FastAPI-mounted Gradio** - UI loads but not responsive
   - Assets load (HTML/CSS/JS downloads)
   - UI renders
   - Event handlers don't fire (no button clicks work)
   - Even test button doesn't respond

## Root Cause Analysis

### Issue 1: Double-slash in asset URLs (FIXED)
```
http://127.0.0.1:8000//assets/nl-Dw1IiFHs.js
```
**Solution:** Mount at `/ui` instead of `/` to avoid path concatenation issue

### Issue 2: `.queue()` and FastAPI mounting
- `.queue()` requires WebSocket support
- `gr.mount_gradio_app()` doesn't properly handle WebSocket connections
- Attempted fix: Disable `.queue()` - DIDN'T HELP

### Issue 3: Event handlers not connecting
- Event handlers are properly wired in code: ✅
- Events fire in standalone mode: ✅
- Events DON'T fire when mounted in FastAPI: ❌
- Suggests: Gradio frontend JavaScript not connecting to backend

## Code Changes Made

1. ✅ Added `APP_MODE=workbench` to development.env and staging.env
2. ✅ Changed to use ModeFactory for proper UI creation
3. ✅ Fixed `ChatResponse.reply` → `ChatResponse.message`
4. ✅ Mounted Gradio at `/ui` instead of `/` (fixed double-slash)
5. ⚠️  Disabled `.queue()` (didn't help)
6. ⚠️  Created dual-server approach (not tested yet)

## Files Modified

- `config/development.env` - Added APP_MODE
- `config/staging.env` - Added APP_MODE
- `src/agent_workbench/main.py` - Changed to ModeFactory, mount at /ui
- `src/agent_workbench/ui/app.py` - Fixed ChatResponse.reply → .message
- `test_adaptive_db.py` - Created (passes all tests)
- `test_startup.py` - Created (passes all tests)
- `test_gradio_standalone.py` - Created (UI loads, chat tries to work)

## Next Steps for Debugging

### Option 1: Fix FastAPI mounting (preferred for single-server)
- [ ] Check Gradio version compatibility with `gr.mount_gradio_app()`
- [ ] Add explicit WebSocket route in FastAPI
- [ ] Check if Gradio needs specific middleware
- [ ] Review Gradio + FastAPI mounting examples from recent versions

### Option 2: Dual-server approach (works but adds complexity)
- [ ] Test `run_dual_server.py` fully
- [ ] Add reverse proxy configuration if needed
- [ ] Update deployment scripts for dual-server mode

### Option 3: Use Gradio's FastAPI integration differently
- [ ] Try creating FastAPI app INSIDE Gradio (app = gr.mount_gradio_app(None, ...))
- [ ] Use Gradio Blocks.queue().launch() with fastapi_app parameter
- [ ] Check if newer Gradio has better FastAPI integration

## Questions to Answer

1. **Why does it work in HF Spaces but not locally?**
   - Same mounting code
   - Same ModeFactory approach
   - Different: Environment (port 7860 vs 8000?)

2. **Why does standalone .launch() work but mounting doesn't?**
   - `.launch()` creates its own server
   - Mounting reuses FastAPI server
   - Suggests: Server configuration difference

3. **Is this a Gradio version issue?**
   - Check: `uv run pip show gradio`
   - Compare: HF Spaces Gradio version vs local

## Browser Console Errors Seen

```
InstallTrigger is verouderd en zal in de toekomst worden verwijderd.
Fout bij brontoewijzing: No sources are declared in this source map.
Bron-URL: http://127.0.0.1:8000//assets/nl-Dw1IiFHs.js (FIXED by mounting at /ui)
```

After fixing double-slash: UI loads but no errors, just not responsive.

## Terminal Output - FastAPI Startup

```
✅ Created workbench interface with event handlers
✅ Gradio interface mounted at /ui
✅ Root path redirects to /ui
```

All looks correct, but events don't fire.

## Documentation Created Today

- ✅ `docs/PHASE_1_IMPLEMENTATION.md` - Complete Phase 1 domain objects documentation
- ✅ Added User Mode as 8th domain object
- ✅ Documented workbench vs seo_coach modes

## Status

**Current State:**
- HF Spaces: ✅ Working perfectly
- Local development: ❌ UI loads but not responsive
- Database: ✅ Working (SQLite locally, Hub in Spaces)
- Architecture: ✅ Complete and documented

**Priority for Next Session:**
1. Debug why events don't fire when Gradio mounted in FastAPI locally
2. Test dual-server approach if mounting can't be fixed
3. Consider Gradio version or configuration issue
