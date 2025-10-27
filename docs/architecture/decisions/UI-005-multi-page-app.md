# UI-005: Multi-Page Gradio App with Routes

## Status

**Status**: Ready for Implementation
**Date**: October 24, 2025
**Decision Makers**: Human Architect
**Task ID**: UI-005-multi-page-app
**Phase**: 2.1 Foundation
**Dependencies**: UI-004 (PWA complete)
**Supersedes**: Previous UI-005 (Ollama UX - deferred to UI-006)

## Context

### Current Problems

**Settings Page Broken in HF Spaces:**

- Settings mounted at `/settings` as separate Gradio app
- HF Spaces expects single app at root `/`
- Result: Settings inaccessible in production

**Complex Mounting Logic:**

```python
# Current: Environment-specific mounting
if is_hf_spaces:
    app.mount("/", main_interface.app)
else:
    app.mount("/settings", settings_interface.app)
    app.mount("/app", main_interface.app)
```

**Scattered UI Code:**

```
ui/
├── mode_factory.py           # Registry pattern
├── app.py                    # Workbench mode
├── seo_coach_app.py          # SEO coach mode (duplicate structure)
├── settings_page.py          # Separate mounted app
└── components/               # Scattered pieces
```

**Two Separate Apps Doing Same Thing:**

- `create_workbench_app()` - Chat interface for technical users
- `create_seo_coach_app()` - Chat interface for business users
- Same structure, different branding = code duplication

### Root Cause

Using **FastAPI mounting for multiple Gradio apps** instead of **Gradio's native routing**.

### Target Solution

**Single `gr.Blocks()` app with native `gr.Blocks.route()` for multiple pages.**

## Decision

### Use Gradio's Native Multi-Page Pattern

From [Gradio Multipage Apps Guide](https://www.gradio.app/guides/multipage-apps):

> `Blocks.route()` gives every logical "page" a URL (/, /settings, etc.) and a separate `<gradio-app>` instance. The user can bookmark or share a link to any page, exactly like a normal web page.

**Benefits:**

1. **Native Gradio Feature** - Documented, supported, proven
2. **Real URLs** - Bookmarkable, shareable pages
3. **Shared Runtime** - Single queue, single backend
4. **Works Everywhere** - HF Spaces, local, Docker (no environment detection)
5. **Clean Code** - Modular pages, clear separation

## Architecture

### New Structure: KISS Principle

```
ui/
├── mode_factory.py      # Mode registry + create_app() (~80 lines)
└── pages/
    ├── chat.py          # Chat page (all modes)
    └── settings.py      # Settings page (all modes)
```

**Three files. That's it.**

### 1. Mode Factory - Simplified with Routes

```python
"""Mode Factory - Handles UI modes and future agent/tool configurations."""

import os
from typing import Dict, Any
import gradio as gr
from .pages import chat, settings

class ModeFactory:
    """Factory for creating mode-specific interfaces with agent/tool configs."""

    def __init__(self):
        # Current: Simple UI modes
        # Future: Agent configurations, tool sets, MCP servers
        self.mode_registry = {
            "workbench": {
                "title": "Agent Workbench",
                "theme_color": "#3b82f6",
                "show_model_selector": True,
                "show_advanced": True,
                # Future: Phase 2+ agent configs
                "agents": [],
                "tools": [],
                "mcp_servers": []
            },
            "seo_coach": {
                "title": "SEO Coach - Nederland",
                "theme_color": "#10b981",
                "show_model_selector": False,
                "show_advanced": False,
                "default_language": "nl",
                # Future: Phase 2+ agent configs
                "agents": [],
                "tools": [],
                "mcp_servers": []
            }
        }

        # Extension registry for Phase 2+
        self.extension_registry = {}

    def create_app(self) -> gr.Blocks:
        """Create Gradio app with routes based on mode."""
        mode = self._get_mode()
        config = self._get_mode_config(mode)

        with gr.Blocks(title=config["title"]) as demo:

            # Route 1: Chat (root)
            with demo.route("Chat", "/"):
                chat.render(mode=mode, config=config)

            # Route 2: Settings
            with demo.route("Settings", "/settings"):
                settings.render(mode=mode, config=config)

        return demo

    def _get_mode(self) -> str:
        """Get current mode from environment."""
        mode = os.getenv("APP_MODE", "workbench")
        if mode not in self.mode_registry and mode not in self.extension_registry:
            return "workbench"  # Fallback
        return mode

    def _get_mode_config(self, mode: str) -> Dict[str, Any]:
        """Get configuration for mode."""
        if mode in self.mode_registry:
            return self.mode_registry[mode]
        elif mode in self.extension_registry:
            return self.extension_registry[mode]
        else:
            return self.mode_registry["workbench"]

    # Phase 2+ Extension API
    def register_agent_mode(self, mode_name: str, config: Dict[str, Any]):
        """Register new agent mode with tools/MCP configuration."""
        self.extension_registry[mode_name] = config


# Singleton instance
_factory = ModeFactory()

def create_app() -> gr.Blocks:
    """Public API: Create Gradio app."""
    return _factory.create_app()

def register_agent_mode(mode_name: str, config: Dict[str, Any]):
    """Public API: Register new agent mode (Phase 2+)."""
    _factory.register_agent_mode(mode_name, config)
```

### 2. Chat Page - Unified for All Modes

```python
"""Chat page - works for workbench AND seo_coach."""

import gradio as gr
from typing import Dict, Any

def render(mode: str, config: Dict[str, Any]):
    """Render chat interface based on mode configuration.

    Args:
        mode: Current mode ("workbench" or "seo_coach")
        config: Mode configuration dict from mode_factory
    """

    # Header
    with gr.Row():
        gr.Markdown(f"# {config['title']}")
        settings_btn = gr.Button("⚙️ Settings", size="sm")
        settings_btn.click(
            fn=None,
            js="() => { window.location.href = '/settings'; }"
        )

    # Chat interface
    chatbot = gr.Chatbot(
        label="Conversation",
        height=600,
        show_copy_button=True
    )

    # Input area
    with gr.Row():
        msg = gr.Textbox(
            placeholder="Type your message...",
            scale=4,
            show_label=False
        )
        send = gr.Button("Send", scale=1, variant="primary")

    # Conditional: Model selector (workbench only)
    if config.get("show_model_selector", False):
        with gr.Row():
            provider = gr.Dropdown(
                choices=get_providers(),
                label="Provider",
                scale=1
            )
            model = gr.Dropdown(
                choices=get_models(),
                label="Model",
                scale=2
            )
            temperature = gr.Slider(
                minimum=0,
                maximum=2,
                value=0.7,
                label="Temperature",
                scale=1
            )

    # Future: Agent tools (Phase 2+)
    # if config.get("agents"):
    #     render_agent_selector(config["agents"])
    # if config.get("tools"):
    #     render_tool_palette(config["tools"])

    # Wire up events
    send.click(
        fn=handle_chat_message,
        inputs=[msg, chatbot, provider, model] if config.get("show_model_selector") else [msg, chatbot],
        outputs=[chatbot, msg]
    )

    msg.submit(
        fn=handle_chat_message,
        inputs=[msg, chatbot, provider, model] if config.get("show_model_selector") else [msg, chatbot],
        outputs=[chatbot, msg]
    )


async def handle_chat_message(message: str, history: list, provider=None, model=None):
    """Handle chat message submission."""
    # Implementation will use existing chat service
    pass


def get_providers():
    """Get available providers."""
    # Load from model_config_service
    pass


def get_models():
    """Get available models."""
    # Load from model_config_service
    pass
```

### 3. Settings Page - Unified for All Modes

```python
"""Settings page - works for workbench AND seo_coach."""

import gradio as gr
from typing import Dict, Any

def render(mode: str, config: Dict[str, Any]):
    """Render settings interface based on mode configuration.

    Args:
        mode: Current mode ("workbench" or "seo_coach")
        config: Mode configuration dict from mode_factory
    """

    # Header with back button
    with gr.Row():
        back_btn = gr.Button("← Back to Chat", size="sm")
        gr.Markdown("# ⚙️ Settings")

    back_btn.click(
        fn=None,
        js="() => { window.location.href = '/'; }"
    )

    # Account Section (all modes)
    with gr.Group():
        gr.Markdown("## 👤 Account")

        # User profile (if authenticated)
        user_id = gr.State()
        username_display = gr.Markdown("Not signed in")

        with gr.Row():
            signin_btn = gr.Button("Sign In", variant="primary")
            signout_btn = gr.Button("Sign Out", variant="secondary", visible=False)

    # Appearance Section (all modes)
    with gr.Group():
        gr.Markdown("## 🎨 Appearance")
        theme = gr.Radio(
            choices=["Light", "Dark", "Auto"],
            value="Auto",
            label="Theme"
        )

    # Model Settings (conditional - workbench only)
    if config.get("show_model_selector", False):
        with gr.Group():
            gr.Markdown("## 🤖 Models")
            provider = gr.Dropdown(
                choices=get_providers(),
                label="Provider"
            )
            model = gr.Dropdown(
                choices=get_models(),
                label="Model"
            )
            temperature = gr.Slider(
                minimum=0,
                maximum=2,
                value=0.7,
                step=0.1,
                label="Temperature"
            )
            max_tokens = gr.Slider(
                minimum=100,
                maximum=4000,
                value=2000,
                step=100,
                label="Max Tokens"
            )

    # Company Section (conditional - seo_coach only)
    if mode == "seo_coach":
        with gr.Group():
            gr.Markdown("## 🏢 Bedrijf")
            company_name = gr.Textbox(
                label="Bedrijfsnaam",
                placeholder="Bijv. Restaurant De Gouden Lepel"
            )
            business_type = gr.Dropdown(
                choices=["Restaurant", "Webshop", "Dienstverlener", "Anders"],
                label="Type bedrijf"
            )
            website = gr.Textbox(
                label="Website URL",
                placeholder="https://jouw-website.nl"
            )
            location = gr.Textbox(
                label="Locatie",
                placeholder="Amsterdam, Rotterdam, etc."
            )

    # Advanced Section (conditional - workbench only)
    if config.get("show_advanced", False):
        with gr.Group():
            gr.Markdown("## 🔧 Advanced")
            debug_mode = gr.Checkbox(
                label="Debug Mode",
                value=False
            )
            enable_mcp = gr.Checkbox(
                label="Enable MCP Tools",
                value=False
            )

    # Future: Agent/Tool Configuration (Phase 2+)
    # if config.get("mcp_servers"):
    #     render_mcp_server_config(config["mcp_servers"])
    # if config.get("tools"):
    #     render_tool_config(config["tools"])

    # Save Button
    with gr.Row():
        save_btn = gr.Button("Save Settings", variant="primary", scale=1)
        reset_btn = gr.Button("Reset to Defaults", variant="secondary", scale=1)

    # Wire up events
    save_btn.click(
        fn=save_settings,
        inputs=[theme, provider, model, temperature, max_tokens] if config.get("show_model_selector") else [theme],
        outputs=[],
        js="() => { window.location.href = '/?reload=1'; }"  # Redirect to chat with reload
    )

    reset_btn.click(
        fn=reset_settings,
        inputs=[user_id],
        outputs=[theme, provider, model, temperature, max_tokens] if config.get("show_model_selector") else [theme]
    )


async def save_settings(*args):
    """Save user settings to database."""
    # Implementation will use user_settings_service
    pass


async def reset_settings(user_id: str):
    """Reset settings to defaults."""
    # Implementation will use user_settings_service
    pass
```

### 4. Main.py - Simplified

```python
"""FastAPI app with single Gradio mount."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from ui.mode_factory import create_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources and mount Gradio interface."""

    # Initialize database
    db = await init_adaptive_database()
    app.adaptive_db = db

    # Create single Gradio app with routes
    gradio_app = create_app()
    gradio_app.queue()

    # Mount at root - works everywhere
    app.mount("/", gradio_app.app)

    yield

    # Cleanup
    await app.requests_client.aclose()

app = FastAPI(lifespan=lifespan)

# That's it. No environment detection. No conditional mounting.
```

## Implementation Plan

### Phase 1: Build Alongside Existing (No Breaking Changes)

Create new structure in parallel:

```
ui/
├── mode_factory.py          # Existing (will be replaced)
├── app.py                   # Existing (will be deleted)
├── seo_coach_app.py         # Existing (will be deleted)
├── settings_page.py         # Existing (will be deleted)
├── mode_factory_v2.py       # NEW - temporary name
└── pages/                   # NEW directory
    ├── chat.py              # NEW
    └── settings.py          # NEW
```

**Actions:**

1. Create `ui/pages/` directory
2. Create `ui/pages/chat.py` with unified chat interface
3. Create `ui/pages/settings.py` with unified settings interface
4. Create `ui/mode_factory_v2.py` with route-based factory

### Phase 2: Test New Structure

Create test entry point:

```python
# test_multipage_app.py
from ui.mode_factory_v2 import create_app

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()

    gradio_app = create_app()
    gradio_app.queue()
    app.mount("/", gradio_app.app)

    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port
```

**Test:**

```bash
# Terminal 1: Run old app
APP_MODE=workbench make start-app  # Port 8000

# Terminal 2: Run new app
uv run python test_multipage_app.py  # Port 8001

# Compare:
# Old: http://localhost:8000/app
# New: http://localhost:8001/

# Verify both modes work
APP_MODE=seo_coach uv run python test_multipage_app.py
```

### Phase 3: Validation Tests

**Test Matrix:**

| Environment | Mode      | Route / | Route /settings | Navigation | State |
| ----------- | --------- | ------- | --------------- | ---------- | ----- |
| Local       | workbench | ✅       | ✅               | ✅          | ✅     |
| Local       | seo_coach | ✅       | ✅               | ✅          | ✅     |
| Docker      | workbench | ✅       | ✅               | ✅          | ✅     |
| Docker      | seo_coach | ✅       | ✅               | ✅          | ✅     |
| HF Spaces   | workbench | ✅       | ✅               | ✅          | ✅     |
| HF Spaces   | seo_coach | ✅       | ✅               | ✅          | ✅     |

**Checklist:**

- [ ] Chat page loads at `/`
- [ ] Settings page loads at `/settings`
- [ ] Navigation Chat → Settings works
- [ ] Navigation Settings → Chat works
- [ ] Browser back button works
- [ ] Settings saved and loaded correctly
- [ ] Mode switching works (workbench ↔ seo_coach)
- [ ] Model selector shows in workbench, hidden in seo_coach
- [ ] Company section shows in seo_coach, hidden in workbench
- [ ] PWA manifest still works
- [ ] Service worker still works

### Phase 4: Cutover

Once all tests pass:

1. **Rename files:**
   
   ```bash
   # Backup old files
   git mv ui/mode_factory.py ui/mode_factory_old.py
   git mv ui/app.py ui/app_old.py
   git mv ui/seo_coach_app.py ui/seo_coach_app_old.py
   git mv ui/settings_page.py ui/settings_page_old.py
   
   # Activate new files
   git mv ui/mode_factory_v2.py ui/mode_factory.py
   ```

2. **Update main.py:**
   
   ```python
   # No changes needed! Already uses mode_factory.create_app()
   ```

3. **Test again:**
   
   ```bash
   make start-app  # Should use new structure
   ```

4. **Deploy to staging:**
   
   ```bash
   git checkout develop
   git merge feature/UI-005-multi-page-app
   # Test in staging HF Space
   ```

5. **Deploy to production:**
   
   ```bash
   git checkout main
   git merge develop
   # Test in production HF Spaces
   ```

6. **Delete old files:**
   
   ```bash
   git rm ui/mode_factory_old.py
   git rm ui/app_old.py
   git rm ui/seo_coach_app_old.py
   git rm ui/settings_page_old.py
   git commit -m "chore: remove old UI structure after successful migration"
   ```

## Migration Path

### Backwards Compatibility

**No breaking changes:**

- Database schema unchanged
- API endpoints unchanged
- Environment variables unchanged
- User settings preserved

**Seamless transition:**

- Users won't notice the change
- URLs remain the same
- Functionality identical

### Rollback Plan

If something breaks:

```bash
# Rollback to old structure
git mv ui/mode_factory.py ui/mode_factory_v2.py
git mv ui/mode_factory_old.py ui/mode_factory.py

# Restart app
make start-app
```

## Benefits

### Immediate Benefits

1. **Settings Work in HF Spaces** ✅
   
   - Native Gradio routing works everywhere
   - No environment detection needed

2. **Cleaner Code** ✅
   
   - 3 files instead of 5+
   - Single source of truth for each page
   - No code duplication between modes

3. **Better URLs** ✅
   
   - `/` - Chat page (bookmarkable)
   - `/settings` - Settings page (bookmarkable)
   - Real web pages, not mounted sub-apps

4. **Easier Testing** ✅
   
   - Each page can be tested independently
   - No complex mounting logic to test

5. **Simpler Deployment** ✅
   
   - Same code path for all environments
   - No conditional logic

### Future Benefits (Phase 2+)

1. **Agent Mode Registration** ✅
   
   ```python
   register_agent_mode("research_agent", {
       "title": "Research Assistant",
       "agents": ["deep_research", "citation_manager"],
       "tools": ["web_search", "pdf_reader", "arxiv_api"],
       "mcp_servers": ["browser", "filesystem", "academic_db"]
   })
   ```

2. **Tool-Specific UIs** ✅
   
   - Different tool palettes per mode
   - Conditional tool rendering based on config

3. **MCP Server Management** ✅
   
   - Per-mode MCP server configuration
   - Dynamic tool loading

## Success Criteria

### Must Pass All Tests

- [ ] **Local Development**: Both modes work on port 8000
- [ ] **Docker**: Both modes work in staging container
- [ ] **HF Spaces**: Both modes work in production
- [ ] **Navigation**: All routes and navigation work
- [ ] **Settings**: Save/load works, page accessible
- [ ] **PWA**: Installation and offline functionality work
- [ ] **No Regressions**: All existing features work

### Code Quality

- [ ] **3 UI files**: mode_factory.py, chat.py, settings.py
- [ ] **< 500 lines total**: UI code stays lean
- [ ] **No duplication**: Single implementation per page
- [ ] **Type hints**: All functions properly typed
- [ ] **Tests pass**: All existing tests pass

### Documentation

- [ ] **Updated CLAUDE.md**: New structure documented
- [ ] **Updated GRADIO_STANDARDIZATION**: Routes pattern added
- [ ] **Migration guide**: Clear steps for future changes

## Known Caveats

### 1. No Cross-Page Events

**Limitation**: Can't directly trigger updates on Chat page from Settings page

**Solution**: Reload page after saving settings

```python
save_btn.click(
    fn=save_settings,
    js="() => { window.location.href = '/?reload=1'; }"
)
```

**UX Impact**: Brief page reload - acceptable for settings save

### 2. Shared State Management

**Challenge**: User ID and session state need to persist across routes

**Solution**: Use gr.State() at demo level

```python
with gr.Blocks() as demo:
    user_id_state = gr.State()  # Shared across routes

    demo.load(fn=init_session, outputs=[user_id_state])
```

### 3. Browser Navigation

**Behavior**: Browser back/forward navigation triggers page re-render

**Impact**: Chat history reloaded from database
**Mitigation**: Fast database queries, minimal UX impact

## References

- **Gradio Multipage Guide**: https://www.gradio.app/guides/multipage-apps
- **Previous Standardization**: `docs/phase1/GRADIO_STANDARDIZATION_COMPLETE.md`
- **Current Structure**: `ui/mode_factory.py`, `ui/app.py`, `ui/seo_coach_app.py`
- **Route Pattern**: `gr.Blocks.route()` documentation

## Future Enhancements (Post UI-005)

**UI-005-target-ux-implementation: Ollama-Inspired Visual Design**

- Build on this foundation
- Apply beautiful UI to working routes
- Chrome DevTools MCP for rapid CSS iteration

**Phase 2: Agent Modes**

- Research agent mode
- Coding agent mode
- Custom agent configurations
- Tool palette per mode

**Phase 3: Advanced Features**

- Real-time collaboration
- Shared workspaces
- Multi-user chat rooms

---

**End of UI-005 Architecture Document**
