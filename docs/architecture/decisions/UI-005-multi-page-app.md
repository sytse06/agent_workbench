# UI-005: Multi-Page Gradio App with Native Routing

## Status

**Status**: Ready for Implementation
**Date**: October 27, 2025
**Decision Makers**: Human Architect
**Task ID**: UI-005-multi-page-app
**Phase**: 2.1 Foundation
**Dependencies**: UI-004 (PWA complete)
**Supersedes**: Previous UI-005 proposal (routing with sidebar)

---

## Context

### Current Problems

**1. Settings Page Broken in HF Spaces:**

- Settings mounted at `/settings` as separate Gradio app
- HF Spaces expects single app at root `/`
- Result: Settings inaccessible in production

**2. Model Controls in Chat Page:**

- Workbench: Provider/model selectors clutter chat interface
- SEO coach: Hidden entirely but code exists
- Should be in settings, not chat page

**3. Code Duplication:**

```
ui/
├── app.py                    # Workbench chat interface
├── seo_coach_app.py          # SEO coach chat interface (duplicate structure)
├── settings_page.py          # Separate mounted app
└── mode_factory.py           # Simple routing logic
```

**Same chat structure, different files = maintenance burden**

**4. Environment-Specific Mounting:**

```python
# Current: Complex conditional logic
if is_hf_spaces:
    app.mount("/", main_interface.app)
else:
    app.mount("/settings", settings_interface.app)
    app.mount("/app", main_interface.app)
```

### Root Causes

**1. Technical: Wrong Mounting Pattern**
- Using FastAPI mounting for multiple Gradio apps
- Should use Gradio's native `gr.Blocks.route()`

**2. Architectural: UI Duplication**
- Separate `create_workbench_app()` and `create_seo_coach_app()` functions
- Same component tree, different implementations
- Should use single builder with configuration-driven differences

**3. UX: Wrong Abstraction**
- Model controls in chat page (workbench only)
- Settings should be configuration hub
- Chat should be minimal (chatbox only)

### Target Solution

**Single `gr.Blocks()` app with:**
1. Native `gr.Blocks.route()` for multiple pages
2. Single component tree builder (`build_gradio_app()`)
3. Shared theme/CSS with mode-specific parameters
4. Configuration-driven visibility (not duplication)
5. Model controls moved to settings page

---

## Decision

### Use Gradio's Native Multi-Page Pattern + Shared Builder

From [Gradio Multipage Apps Guide](https://www.gradio.app/guides/multipage-apps):

> `Blocks.route()` gives every logical "page" a URL (/, /settings, etc.) and a separate `<gradio-app>` instance. The user can bookmark or share a link to any page, exactly like a normal web page.

**Architecture Pattern:**

```
create_app()
    ↓
create_workbench_app() OR create_seo_app()
    ↓
build_gradio_app(config)  ← SINGLE BUILDER
    ↓
    ├─ Route: "/" (chat page)
    └─ Route: "/settings" (settings page)
```

**Benefits:**

1. **Native Gradio Feature** - Documented, supported, proven
2. **Real URLs** - Bookmarkable, shareable pages
3. **Shared Runtime** - Single queue, single backend
4. **Works Everywhere** - HF Spaces, local, Docker (no environment detection)
5. **Zero Duplication** - One builder, different configs
6. **Clean Chat Page** - Chatbox only, no model controls

---

## Architecture

### New Structure: 3 Files Total

```
ui/
├── mode_factory.py      # Mode registry + shared builder (~150 lines)
├── styles.py            # Shared CSS (~50 lines)
└── pages/
    ├── chat.py          # Chat page - minimal (~100 lines)
    └── settings.py      # Settings page - comprehensive (~200 lines)

static/
├── sw.js                # Service worker (existing, preserve)
└── icons/               # PWA icons (existing, preserve)
    ├── icon-*.png       # 9 sizes
    └── shortcut-*.png   # App shortcuts
```

**Total: ~500 lines** (vs 1000+ in current implementation)

---

## Implementation

### 1. Mode Factory - Shared Builder Pattern

**File:** `ui/mode_factory.py`

```python
"""
Mode Factory - Creates Gradio app based on APP_MODE environment variable.

Pattern:
    create_app() → create_workbench_app() OR create_seo_app()
                → build_gradio_app(config)

No code duplication - single builder, different configurations.
"""

import os
from typing import Dict, Any
import gradio as gr
from .pages import chat, settings
from .styles import SHARED_CSS


def create_app() -> gr.Blocks:
    """
    Entry point - creates Gradio app based on APP_MODE environment variable.

    Returns:
        gr.Blocks: Single Gradio Blocks instance with routes
    """
    mode = os.getenv("APP_MODE", "workbench")

    if mode == "workbench":
        return create_workbench_app()
    elif mode == "seo_coach":
        return create_seo_app()
    else:
        # Fallback to workbench
        return create_workbench_app()


def create_workbench_app() -> gr.Blocks:
    """
    Workbench mode configuration - technical users.

    Returns:
        gr.Blocks: Configured Gradio app for workbench mode
    """
    config = {
        "title": "Agent Workbench",
        "theme": gr.themes.Base(
            primary_hue="#3b82f6",  # Blue
            font="Roboto"
        ),

        # English labels
        "labels": {
            # Chat page
            "placeholder": "Type your message...",
            "send": "Send",

            # Settings page
            "models_tab": "🤖 Models",
            "appearance_tab": "🎨 Appearance",
            "context_tab": "📁 Project Info",
            "account_tab": "👤 Account",

            # Model settings
            "provider_label": "Provider",
            "model_label": "Model",
            "temperature_label": "Temperature",
            "max_tokens_label": "Max Tokens",

            # Context fields
            "context_name": "Project Name",
            "context_url": "Project URL",
            "context_description": "Description",

            # Locked model message (not shown in workbench)
            "model_locked": "Current Model",
            "model_locked_info": "Model selection available in this mode",
        },

        # Feature flags
        "allow_model_selection": True,   # Show model controls in settings
        "show_company_section": False,   # Hide business-specific fields

        # Default model config
        "available_providers": ["openai", "anthropic", "groq"],
        "default_provider": "openai",
        "available_models": ["gpt-4-turbo", "claude-3-5-sonnet", "llama-3-70b"],
        "default_model": "gpt-4-turbo",
    }

    return build_gradio_app(config)


def create_seo_app() -> gr.Blocks:
    """
    SEO coach mode configuration - business users.

    Returns:
        gr.Blocks: Configured Gradio app for SEO coach mode
    """
    config = {
        "title": "SEO Coach",
        "theme": gr.themes.Base(
            primary_hue="#10b981",  # Green
            font="Open Sans"
        ),

        # Dutch labels
        "labels": {
            # Chat page
            "placeholder": "Stel je vraag over SEO...",
            "send": "Verstuur",

            # Settings page
            "models_tab": "🤖 AI Model",
            "appearance_tab": "🎨 Weergave",
            "context_tab": "🏢 Bedrijfsinfo",
            "account_tab": "👤 Account",

            # Model settings
            "provider_label": "AI Provider",
            "model_label": "Model",
            "temperature_label": "Creativiteit",
            "max_tokens_label": "Max Tokens",

            # Context fields (business-oriented)
            "context_name": "Bedrijfsnaam",
            "context_url": "Website URL",
            "context_description": "Beschrijving",
            "business_type": "Type bedrijf",
            "location": "Locatie",

            # Locked model message
            "model_locked": "Huidig model",
            "model_locked_info": "SEO Coach gebruikt het beste model voor jou",
        },

        # Feature flags
        "allow_model_selection": False,  # Lock model in settings
        "show_company_section": True,    # Show business fields

        # Default model config (locked to best model)
        "available_providers": ["openai"],
        "default_provider": "openai",
        "available_models": ["gpt-4-turbo"],
        "default_model": "gpt-4-turbo",
    }

    return build_gradio_app(config)


def build_gradio_app(config: Dict[str, Any]) -> gr.Blocks:
    """
    Single Gradio app builder - shared by all modes.

    This function is called by create_workbench_app() and create_seo_app()
    with different configurations. It builds the SAME component tree for
    both modes - differences are controlled by config values.

    Args:
        config: Mode configuration dictionary

    Returns:
        gr.Blocks: Configured Gradio app with routes

    Critical Pattern:
        - ALL components must be defined (use visible= to hide)
        - Shared state defined at demo level, passed to render functions
        - Single queue() call happens in main.py, not here
    """

    with gr.Blocks(
        title=config["title"],
        theme=config["theme"],
        css=SHARED_CSS
    ) as demo:

        # Shared state - accessible across all routes
        # ⚠️ CRITICAL: Define state here, not in render functions
        user_state = gr.State(None)  # User session/auth data
        conversation_state = gr.State([])  # Current conversation messages

        # Route 1: Chat page (root)
        # Prefixed "app_" to avoid collision with gr.Chatbot internal name
        with demo.route("app_chat", "/"):
            chat.render(config, user_state, conversation_state)

        # Route 2: Settings page
        with demo.route("app_settings", "/settings"):
            settings.render(config, user_state)

    return demo
```

**⚠️ INCONSISTENCY ALERT - Model Lists:**

The `get_providers()` and `get_models()` functions are hardcoded in config.

**Question:** Should these be:
- **A)** Hardcoded in config (current approach)
- **B)** Loaded from `model_config_service.get_provider_choices_for_ui()` (existing service)
- **C)** Mix: Hardcoded for SEO coach, dynamic for workbench

**Recommendation:** Option B - use existing service for consistency with current behavior.

**TODO:** Import and use `model_config_service` instead of hardcoded lists.

---

### 2. Shared CSS

**File:** `ui/styles.py`

```python
"""
Shared CSS for all modes.

Mode-specific differences (colors, fonts) are handled via Gradio theme configuration,
NOT via CSS. This ensures both modes have identical styling with only theme variations.
"""

SHARED_CSS = """
/* Chat page styles */
.chatbot-container {
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Settings page styles */
.settings-section {
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    background: var(--background-fill-secondary);
}

.settings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

/* Input field consistency */
.input-row {
    display: flex;
    gap: 0.5rem;
    align-items: flex-end;
}

/* Button styling */
.settings-button {
    min-width: 40px;
    padding: 0.5rem;
}

/* Responsive layout */
@media (max-width: 768px) {
    .chatbot-container {
        height: 400px !important;
    }

    .input-row {
        flex-direction: column;
    }
}
```

**⚠️ UNCLEAR - CSS Variables:**

The CSS uses `var(--background-fill-secondary)` which is a Gradio theme variable.

**Question:** Are these guaranteed to be available in all Gradio themes?

**TODO:** Test with custom themes to ensure variables exist.

---

### 3. Chat Page - Minimal Interface

**File:** `ui/pages/chat.py`

```python
"""
Chat page - minimal chatbox interface.

NO model controls (moved to settings).
NO sidebar (separate feature - see docs/phase2/Feat-dev-plan-chat-history-in-sidebar-in-chatpage.md).

Identical structure for workbench and SEO coach modes - differences controlled by config labels.
"""

from typing import Dict, Any, List, Tuple
import gradio as gr


def render(
    config: Dict[str, Any],
    user_state: gr.State,
    conversation_state: gr.State
) -> None:
    """
    Render chat interface.

    Args:
        config: Mode configuration from mode_factory
        user_state: Shared user session state
        conversation_state: Shared conversation messages state

    Critical Pattern:
        - State passed from demo level, not created here
        - All event handlers must update conversation_state
        - NO model controls (in settings page)
    """

    # Header with settings button
    with gr.Row():
        gr.Markdown(f"# {config['title']}")
        settings_btn = gr.Button("⚙️", size="sm", elem_classes="settings-button")

    # Chatbox - loads from conversation_state
    chatbot = gr.Chatbot(
        value=conversation_state.value,
        label="",
        height=600,
        show_copy_button=True,
        elem_classes="chatbot-container"
    )

    # Input area
    with gr.Row(elem_classes="input-row"):
        msg = gr.Textbox(
            placeholder=config['labels']['placeholder'],
            scale=4,
            show_label=False,
            container=False
        )
        send = gr.Button(
            config['labels']['send'],
            scale=1,
            variant="primary"
        )

    # Event: Navigate to settings
    settings_btn.click(
        fn=None,
        js="() => { window.location.href = '/settings'; }"
    )

    # Event: Send message
    send.click(
        fn=handle_chat_message,
        inputs=[msg, chatbot, user_state],
        outputs=[chatbot, msg, conversation_state]
    )

    # Event: Submit message (Enter key)
    msg.submit(
        fn=handle_chat_message,
        inputs=[msg, chatbot, user_state],
        outputs=[chatbot, msg, conversation_state]
    )


async def handle_chat_message(
    message: str,
    history: List[Dict[str, str]],
    user_state: Dict[str, Any]
) -> Tuple[List[Dict[str, str]], str, List[Dict[str, str]]]:
    """
    Handle chat message submission.

    Args:
        message: User input text
        history: Current chat history
        user_state: User session data

    Returns:
        Tuple of (updated_history, cleared_input, updated_state)

    ⚠️ TODO: Implement real chat service integration
    """

    # TODO: Import and use ChatService
    # from services.llm_service import ChatService
    # from services.model_config_service import model_config_service
    #
    # # Get model config from user settings or defaults
    # model_config = user_state.get("model_config") or model_config_service.get_default_config()
    #
    # # Call chat service
    # chat_service = ChatService(model_config)
    # response = await chat_service.chat_completion(
    #     message=message,
    #     conversation_id=user_state.get("conversation_id")
    # )

    # Placeholder implementation
    new_history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": f"[Placeholder response to: {message}]"}
    ]

    return (
        new_history,      # Update chatbot display
        "",               # Clear input field
        new_history       # Update conversation_state
    )
```

**⚠️ CRITICAL - Missing Implementation:**

The `handle_chat_message` function is a stub. Real implementation needs:

1. **Import ChatService** - from `services.llm_service`
2. **Get model config** - from user settings or defaults
3. **Handle conversation persistence** - save to database
4. **Error handling** - network errors, rate limits, etc.

**Question:** Where should model config come from?
- **Option A:** User settings in database (requires settings save/load)
- **Option B:** Session state (lost on refresh)
- **Option C:** Environment defaults (current behavior)

**TODO:** Define settings persistence strategy before implementing.

---

### 4. Settings Page - Configuration Hub

**File:** `ui/pages/settings.py`

```python
"""
Settings page - comprehensive configuration interface.

Contains:
    - Account/login
    - Model selection (workbench) or locked display (SEO coach)
    - Appearance settings
    - Context/business info

Critical Pattern:
    - ALL components always defined (use visible= to hide)
    - Avoids NameError when components referenced in event handlers
"""

from typing import Dict, Any, List, Optional
import gradio as gr


def render(
    config: Dict[str, Any],
    user_state: gr.State
) -> None:
    """
    Render settings interface.

    Args:
        config: Mode configuration from mode_factory
        user_state: Shared user session state

    Critical Pattern:
        - ALL components defined even if hidden (visible=False)
        - Prevents NameError in event handlers
        - Settings saved to user_state and database
    """

    # Header with back button
    with gr.Row(elem_classes="settings-header"):
        back_btn = gr.Button("← Back", size="sm")
        gr.Markdown("# ⚙️ Settings")

    with gr.Tabs():
        # Tab 1: Account
        with gr.Tab(config['labels']['account_tab']):
            render_account_tab(user_state)

        # Tab 2: Models
        with gr.Tab(config['labels']['models_tab']):
            model_components = render_models_tab(config)

        # Tab 3: Appearance
        with gr.Tab(config['labels']['appearance_tab']):
            appearance_components = render_appearance_tab(config)

        # Tab 4: Context/Business Info
        with gr.Tab(config['labels']['context_tab']):
            context_components = render_context_tab(config)

    # Save button (below tabs)
    with gr.Row():
        save_btn = gr.Button("💾 Save Settings", variant="primary", scale=2)
        reset_btn = gr.Button("↺ Reset to Defaults", variant="secondary", scale=1)

    # Event: Back to chat
    back_btn.click(
        fn=None,
        js="() => { window.location.href = '/'; }"
    )

    # Event: Save settings
    # All components guaranteed to exist (always defined)
    save_btn.click(
        fn=save_settings,
        inputs=[
            user_state,
            # Model components
            model_components["provider"],
            model_components["model"],
            model_components["temperature"],
            model_components["max_tokens"],
            # Appearance components
            appearance_components["theme"],
            # Context components
            context_components["name"],
            context_components["url"],
            context_components["description"],
            context_components["business_type"],
            context_components["location"],
        ],
        outputs=[user_state],
        # Reload page after save to apply settings
        js="() => { window.location.href = '/?reload=1'; }"
    )

    # Event: Reset settings
    reset_btn.click(
        fn=reset_settings,
        inputs=[user_state],
        outputs=[
            model_components["provider"],
            model_components["model"],
            model_components["temperature"],
            model_components["max_tokens"],
            appearance_components["theme"],
            context_components["name"],
            context_components["url"],
            context_components["description"],
        ]
    )


def render_account_tab(user_state: gr.State) -> None:
    """
    Render account/login tab.

    ⚠️ TODO: Implement real authentication
    """
    gr.Markdown("## Sign In")

    # Login form
    username = gr.Textbox(label="Username", placeholder="Enter username")
    password = gr.Textbox(label="Password", type="password", placeholder="Enter password")

    with gr.Row():
        signin_btn = gr.Button("🔓 Sign In", variant="primary", scale=1)
        signout_btn = gr.Button("🔒 Sign Out", variant="secondary", scale=1, visible=False)

    # Authentication status
    auth_status = gr.Markdown("Not signed in", elem_id="auth-status")

    # Events
    signin_btn.click(
        fn=handle_signin,
        inputs=[username, password, user_state],
        outputs=[user_state, auth_status, signin_btn, signout_btn]
    )

    signout_btn.click(
        fn=handle_signout,
        inputs=[user_state],
        outputs=[user_state, auth_status, signin_btn, signout_btn]
    )


def render_models_tab(config: Dict[str, Any]) -> Dict[str, gr.Component]:
    """
    Render models configuration tab.

    Critical Pattern:
        - ALL components always defined
        - Use visible= to hide/show based on config
        - Returns dict of components for event handler access

    Args:
        config: Mode configuration

    Returns:
        Dict of component references
    """
    gr.Markdown("## Model Configuration")

    # Get allow_model_selection flag
    allow_selection = config.get('allow_model_selection', False)

    # ⚠️ CRITICAL: Always define components, use visible= to hide
    provider = gr.Dropdown(
        choices=config.get('available_providers', []),
        value=config.get('default_provider', 'openai'),
        label=config['labels']['provider_label'],
        visible=allow_selection
    )

    model = gr.Dropdown(
        choices=config.get('available_models', []),
        value=config.get('default_model', 'gpt-4-turbo'),
        label=config['labels']['model_label'],
        visible=allow_selection
    )

    temperature = gr.Slider(
        minimum=0,
        maximum=2,
        value=0.7,
        step=0.1,
        label=config['labels']['temperature_label'],
        visible=allow_selection
    )

    max_tokens = gr.Slider(
        minimum=100,
        maximum=4000,
        value=2000,
        step=100,
        label=config['labels']['max_tokens_label'],
        visible=allow_selection
    )

    # Locked model message (shown when controls hidden)
    locked_msg = gr.Markdown(
        f"**{config['labels']['model_locked']}:** {config.get('default_model', 'gpt-4-turbo')}\n\n"
        f"_{config['labels']['model_locked_info']}_",
        visible=not allow_selection
    )

    return {
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "locked_msg": locked_msg
    }


def render_appearance_tab(config: Dict[str, Any]) -> Dict[str, gr.Component]:
    """
    Render appearance settings tab.

    Args:
        config: Mode configuration

    Returns:
        Dict of component references
    """
    gr.Markdown("## Theme")

    theme = gr.Radio(
        choices=["Light", "Dark", "Auto"],
        value="Auto",
        label="Color Theme",
        info="Auto mode follows your system settings"
    )

    return {"theme": theme}


def render_context_tab(config: Dict[str, Any]) -> Dict[str, gr.Component]:
    """
    Render context/business info tab.

    Critical Pattern:
        - Same fields for all modes
        - Different labels based on config
        - Business-specific fields use visible= flag

    Args:
        config: Mode configuration

    Returns:
        Dict of component references
    """
    gr.Markdown("## Context Information")

    # Universal fields (all modes)
    name = gr.Textbox(
        label=config['labels']['context_name'],
        placeholder=f"Enter {config['labels']['context_name'].lower()}"
    )

    url = gr.Textbox(
        label=config['labels']['context_url'],
        placeholder="https://example.com"
    )

    description = gr.Textbox(
        label=config['labels'].get('context_description', 'Description'),
        placeholder="Brief description",
        lines=3
    )

    # Business-specific fields (SEO coach only)
    # ⚠️ CRITICAL: Always define, use visible= to hide
    show_business = config.get('show_company_section', False)

    gr.Markdown("## Business Details", visible=show_business)

    business_type = gr.Dropdown(
        choices=["Restaurant", "Webshop", "Dienstverlener", "Anders"],
        label=config['labels'].get('business_type', 'Business Type'),
        visible=show_business
    )

    location = gr.Textbox(
        label=config['labels'].get('location', 'Location'),
        placeholder="City, Country",
        visible=show_business
    )

    return {
        "name": name,
        "url": url,
        "description": description,
        "business_type": business_type,
        "location": location
    }


# ============================================================================
# Event Handlers
# ============================================================================

async def handle_signin(
    username: str,
    password: str,
    user_state: Dict[str, Any]
) -> tuple:
    """
    Handle user sign in.

    ⚠️ TODO: Implement real authentication

    Returns:
        Tuple of (user_state, status_message, signin_visible, signout_visible)
    """
    # TODO: Implement real authentication
    # - Validate credentials against database
    # - Create session token
    # - Load user settings

    # Placeholder
    user_state = user_state or {}
    user_state["username"] = username
    user_state["authenticated"] = True

    return (
        user_state,
        f"✅ Signed in as {username}",
        gr.update(visible=False),  # Hide sign in button
        gr.update(visible=True)    # Show sign out button
    )


async def handle_signout(user_state: Dict[str, Any]) -> tuple:
    """
    Handle user sign out.

    Returns:
        Tuple of (user_state, status_message, signin_visible, signout_visible)
    """
    return (
        {},
        "Not signed in",
        gr.update(visible=True),   # Show sign in button
        gr.update(visible=False)   # Hide sign out button
    )


async def save_settings(
    user_state: Dict[str, Any],
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    theme: str,
    context_name: str,
    context_url: str,
    context_description: str,
    business_type: Optional[str],
    location: Optional[str]
) -> Dict[str, Any]:
    """
    Save user settings.

    Args:
        All settings values from UI components

    Returns:
        Updated user_state

    ⚠️ TODO: Implement real settings persistence
    """
    # TODO: Implement settings persistence
    # - Save to database (user_settings table)
    # - Update user_state
    # - Handle validation errors

    # Placeholder
    user_state = user_state or {}
    user_state.update({
        "model_config": {
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens
        },
        "appearance": {
            "theme": theme
        },
        "context": {
            "name": context_name,
            "url": context_url,
            "description": context_description,
            "business_type": business_type,
            "location": location
        }
    })

    return user_state


async def reset_settings(user_state: Dict[str, Any]) -> tuple:
    """
    Reset settings to defaults.

    Returns:
        Tuple of default values for all settings components

    ⚠️ TODO: Load defaults from model_config_service
    """
    # TODO: Load defaults from services
    # from services.model_config_service import model_config_service
    # defaults = model_config_service.get_default_config()

    return (
        "openai",      # provider
        "gpt-4-turbo", # model
        0.7,           # temperature
        2000,          # max_tokens
        "Auto",        # theme
        "",            # context_name
        "",            # context_url
        "",            # context_description
    )
```

**⚠️ CRITICAL - Missing Implementations:**

1. **Authentication System:**
   - `handle_signin()` is a stub
   - No real credential validation
   - No session management
   - **Question:** Should UI-005 include auth, or defer to separate feature?

2. **Settings Persistence:**
   - `save_settings()` only updates `gr.State`
   - No database writes
   - Lost on page refresh
   - **Question:** Should settings be persisted to database or localStorage?

3. **Page Reload After Save:**
   - Using `js="() => { window.location.href = '/?reload=1'; }"`
   - Causes full page reload (not ideal UX)
   - **Alternative:** Could use Gradio event system to update state
   - **Question:** Is page reload acceptable, or should we use Gradio state updates?

**⚠️ INCONSISTENCY - Component Return Pattern:**

Settings tabs return `Dict[str, gr.Component]` but chat page doesn't. This is intentional (settings needs to wire up save button), but could be confusing.

**Recommendation:** Document this pattern clearly in code comments.

---

### 5. Main.py Integration

**File:** `src/agent_workbench/main.py` (modifications)

```python
# Existing imports...
from contextlib import asynccontextmanager
from fastapi import FastAPI
import os

# New import
from ui.mode_factory import create_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources and mount Gradio interface."""

    print("🔧 Initializing FastAPI lifespan services...")

    # 1. Initialize shared HTTP client
    app.requests_client = httpx.AsyncClient(timeout=30.0)

    # 2. Initialize database - use app.state (FastAPI best practice)
    mode = os.getenv("APP_MODE", "workbench")
    app.state.adaptive_db = await init_adaptive_database(mode=mode)

    # Provide session compatibility for existing code
    if hasattr(app.state.adaptive_db, "get_session"):
        app.get_session = app.state.adaptive_db.get_session
    else:
        app.get_session = lambda: None

    # 3. Create Gradio app (single instance with routes)
    gradio_app = create_app()

    # 4. Queue ONCE (not in create_app())
    gradio_app.queue()

    # 5. Run startup events (required for Gradio responsiveness)
    gradio_app.run_startup_events()

    # 6. Mount at root path
    app.mount("/", gradio_app.app, name="gradio")

    print("✅ Gradio interface mounted at root path")

    yield

    # Cleanup
    print("🔧 Shutting down FastAPI lifespan services...")
    await app.requests_client.aclose()


# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# API routes (existing, unchanged)
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat_workflow.router, prefix="/api/v1", tags=["chat"])
# ... other routers ...

# Static files (existing, unchanged)
app.mount("/static", StaticFiles(directory="src/agent_workbench/static"), name="static")

# PWA routes (existing, unchanged - lines 201-280)
# Dynamic manifest endpoint already exists
```

**⚠️ CRITICAL - Queue Call Location:**

The original proposal had `queue()` called in `create_app()`, which would cause duplicate calls. This is now fixed by:
1. Removing `queue()` from `mode_factory.py`
2. Calling it ONCE in `main.py` lifespan

**⚠️ UNCLEAR - Startup Events:**

The `gradio_app.run_startup_events()` call is critical for Gradio responsiveness but not well documented.

**Question:** Is this call still required with Gradio 4.x routing?

**TODO:** Test without this call to verify if still needed.

---

### 6. PWA Integration - Preserve Existing Assets

**No changes required** - existing PWA implementation already compatible.

**Existing files to preserve:**
```
static/
├── sw.js                           # Service worker (no changes)
└── icons/
    ├── icon-72.png                 # PWA icons (no changes)
    ├── icon-96.png
    ├── icon-128.png
    ├── icon-144.png
    ├── icon-152.png
    ├── icon-192.png
    ├── icon-384.png
    ├── icon-512.png
    ├── apple-touch-icon.png
    ├── shortcut-chat.png
    ├── shortcut-settings.png
    └── shortcut-history.png
```

**Existing dynamic manifest (main.py:201-280):**
- ✅ Already mode-aware (`APP_MODE` env var)
- ✅ Already generates correct shortcuts (`/` and `/settings`)
- ✅ Already adapts theme colors per mode

**Validation required:**
- [ ] Manifest shortcuts point to new routes
- [ ] Service worker caches new route structure
- [ ] PWA installation works in both modes
- [ ] Icons load correctly from `/static/icons/`

**✅ DECISION CONFIRMED - Root Route:**

Current manifest (lines 216-219) uses:
```python
start_url = "/" if is_hf_spaces else "/app"
settings_url = "/" if is_hf_spaces else "/settings"
```

After UI-005, routes are ALWAYS `/` and `/settings` (no environment detection).

**IMPLEMENTATION:** Update manifest logic to use root route:
```python
# After UI-005
start_url = "/"  # Chat page always at root
settings_url = "/settings"  # Settings page always at /settings
```

**Rationale:**
- Simpler URLs (no /app prefix)
- Standard convention (root = main app)
- Easier PWA integration
- Consistent across all deployments
- Aligns with UI-005-chat-page.md and UI-005-target-ux-implementation.md

---

## Implementation Plan

### Phase 1: Build New Structure (No Breaking Changes)

**Parallel implementation** - old code continues to work.

```
ui/
├── mode_factory.py           # Existing (will be replaced)
├── app.py                    # Existing (keep for now)
├── seo_coach_app.py          # Existing (keep for now)
├── settings_page.py          # Existing (keep for now)
│
├── mode_factory_v2.py        # NEW - temporary name
├── styles.py                 # NEW
└── pages/                    # NEW directory
    ├── __init__.py           # NEW
    ├── chat.py               # NEW
    └── settings.py           # NEW
```

**Steps:**

1. Create `ui/pages/` directory
2. Create `ui/styles.py` with `SHARED_CSS`
3. Create `ui/pages/__init__.py`:
   ```python
   from . import chat, settings
   ```
4. Create `ui/pages/chat.py` (implementation above)
5. Create `ui/pages/settings.py` (implementation above)
6. Create `ui/mode_factory_v2.py` (implementation above)

**Validation:**
- [ ] All new files created
- [ ] No import errors
- [ ] Old code still works (not using new files yet)

---

### Phase 2: Test New Structure

Create test entry point to validate new structure in isolation.

**File:** `test_multipage_app.py` (project root)

```python
"""
Test entry point for UI-005 multipage app.

Run on different port (8001) to avoid conflicting with existing app (8000).

Usage:
    # Test workbench mode
    APP_MODE=workbench uvicorn test_multipage_app:app --port 8001

    # Test SEO coach mode
    APP_MODE=seo_coach uvicorn test_multipage_app:app --port 8001
"""

import os
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Set mode before importing (for testing)
if "APP_MODE" not in os.environ:
    os.environ["APP_MODE"] = "workbench"

# Import new mode factory
from src.agent_workbench.ui.mode_factory_v2 import create_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal lifespan for testing."""
    # Create Gradio app
    gradio_app = create_app()
    gradio_app.queue()

    # Mount
    app.mount("/", gradio_app.app)

    yield


# Create test app
app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    mode = os.getenv("APP_MODE", "workbench")
    print(f"🧪 Testing UI-005 multipage app in {mode} mode on port 8001")
    print(f"📍 Chat page: http://localhost:8001/")
    print(f"⚙️  Settings page: http://localhost:8001/settings")

    uvicorn.run(app, host="0.0.0.0", port=8001)
```

**Testing:**

```bash
# Terminal 1: Run old app (existing behavior)
APP_MODE=workbench make start-app
# → http://localhost:8000/

# Terminal 2: Run new app (UI-005)
APP_MODE=workbench uvicorn test_multipage_app:app --port 8001
# → http://localhost:8001/

# Compare:
# - Old: http://localhost:8000/app (or / in HF Spaces)
# - New: http://localhost:8001/

# Test both modes:
APP_MODE=seo_coach uvicorn test_multipage_app:app --port 8001
```

**Validation checklist:**
- [ ] Chat page loads at `http://localhost:8001/`
- [ ] Settings page loads at `http://localhost:8001/settings`
- [ ] Settings button navigates to `/settings`
- [ ] Back button navigates to `/`
- [ ] Both modes (workbench/seo_coach) work
- [ ] Chat input accepts messages
- [ ] Settings save button triggers (placeholder response OK)
- [ ] No console errors
- [ ] No import errors

---

### Phase 3: Validation Tests

**Test matrix:**

| Environment | Mode | Route / | Route /settings | Navigation | Model Controls | Business Fields |
|-------------|------|---------|-----------------|------------|----------------|-----------------|
| Local | workbench | ✅ | ✅ | ✅ | Visible | Hidden |
| Local | seo_coach | ✅ | ✅ | ✅ | Locked | Visible |
| Docker | workbench | ✅ | ✅ | ✅ | Visible | Hidden |
| Docker | seo_coach | ✅ | ✅ | ✅ | Locked | Visible |

**Manual testing checklist:**

**Chat Page:**
- [ ] Chatbox loads and displays correctly
- [ ] Input field accepts text
- [ ] Send button is clickable
- [ ] Settings button navigates to `/settings`
- [ ] NO model controls visible
- [ ] Placeholder messages appear in chatbot
- [ ] English labels (workbench) vs Dutch labels (SEO coach)

**Settings Page:**
- [ ] Back button navigates to `/`
- [ ] Account tab loads
- [ ] Models tab loads
- [ ] Appearance tab loads
- [ ] Context tab loads
- [ ] **Workbench:** Model dropdowns visible
- [ ] **Workbench:** Business fields hidden
- [ ] **SEO coach:** Model locked message visible
- [ ] **SEO coach:** Business fields visible
- [ ] Save button clickable (placeholder OK)
- [ ] Reset button clickable (placeholder OK)

**Navigation:**
- [ ] Browser back button works
- [ ] Browser forward button works
- [ ] Direct URL access works (`/`, `/settings`)
- [ ] Bookmarking works
- [ ] State preserved across navigation (if implemented)

**PWA (if testing in HF Spaces or with HTTPS):**
- [ ] Manifest loads at `/manifest.json`
- [ ] Icons load from `/static/icons/`
- [ ] Install prompt appears (desktop)
- [ ] App installs successfully
- [ ] Installed app launches to `/`
- [ ] Shortcuts work (New Chat, Settings)

---

### Phase 4: Cutover

**Prerequisites:**
- [ ] All Phase 3 tests pass
- [ ] No console errors in browser
- [ ] Code reviewed and approved
- [ ] Database migrations applied (if any)

**Steps:**

1. **Rename files (atomic cutover):**

```bash
# Backup old files
git mv ui/mode_factory.py ui/mode_factory_old.py
git mv ui/app.py ui/app_old.py
git mv ui/seo_coach_app.py ui/seo_coach_app_old.py
git mv ui/settings_page.py ui/settings_page_old.py

# Activate new files
git mv ui/mode_factory_v2.py ui/mode_factory.py

# Commit
git add .
git commit -m "feat(ui): activate UI-005 multipage routing"
```

2. **Update main.py:**

No changes needed - `main.py` already imports `ui.mode_factory.create_app()`.

3. **Update manifest logic:**

```python
# main.py line 216-219
# Remove environment-specific path logic
start_url = "/"
settings_url = "/settings"
```

4. **Test again:**

```bash
make start-app
# → http://localhost:8000/

# Verify:
# - Chat at /
# - Settings at /settings
# - Both modes work
```

5. **Deploy to staging:**

```bash
git checkout develop
git merge feature/UI-005-multi-page-app --no-ff

# Push to trigger staging deployment
git push origin develop

# Monitor staging HF Space
```

6. **Deploy to production:**

```bash
git checkout main
git merge develop --no-ff

# Push to trigger production deployment
git push origin main

# Monitor production HF Spaces
```

7. **Delete old files (after validation):**

```bash
# After 1 week of stable operation
git rm ui/mode_factory_old.py
git rm ui/app_old.py
git rm ui/seo_coach_app_old.py
git rm ui/settings_page_old.py
git commit -m "chore: remove old UI structure after successful migration"
```

---

## Migration Path

### Backwards Compatibility

**No breaking changes:**

- ✅ Database schema unchanged
- ✅ API endpoints unchanged
- ✅ Environment variables unchanged (`APP_MODE`)
- ✅ User settings preserved (if persistence implemented)
- ✅ PWA assets unchanged
- ✅ Static files unchanged

**Seamless transition:**

- Users won't notice URL change (always `/` in HF Spaces)
- Functionality identical
- Performance unchanged (single queue, single mount)

### Rollback Plan

If issues detected in production:

```bash
# Rollback to old structure
git mv ui/mode_factory.py ui/mode_factory_v2.py
git mv ui/mode_factory_old.py ui/mode_factory.py

# Restart app
make start-app

# Or redeploy previous commit
git revert HEAD
git push origin main
```

**Rollback testing:**
- [ ] Old code still exists (not deleted yet)
- [ ] Rename commands tested
- [ ] Restart verified to work
- [ ] Database unchanged (no migration rollback needed)

---

## Benefits

### Immediate Benefits

1. **Settings Work in HF Spaces** ✅
   - Native Gradio routing works everywhere
   - No environment detection needed
   - `/settings` accessible in production

2. **Cleaner Code** ✅
   - 3 files (~500 lines) instead of 5+ files (1000+ lines)
   - Single source of truth: `build_gradio_app()`
   - No code duplication between modes

3. **Better URLs** ✅
   - `/` - Chat page (bookmarkable)
   - `/settings` - Settings page (bookmarkable)
   - Real web pages, not mounted sub-apps

4. **Model Controls in Right Place** ✅
   - Settings page (configuration hub)
   - Not cluttering chat interface
   - Available in workbench, locked in SEO coach

5. **Simpler Deployment** ✅
   - Same code path for all environments
   - No conditional logic in main.py
   - Easier to test and maintain

### Future Benefits (Phase 2+)

1. **Chat History Sidebar** ✅
   - Separate feature (see `docs/phase2/Feat-dev-plan-chat-history-in-sidebar-in-chatpage.md`)
   - Can be added to chat page without affecting structure
   - Feature flag in workbench first, then SEO coach

2. **Agent Mode Registration** ✅
   - Add new mode configs to `mode_factory.py`
   - Same `build_gradio_app()` builder
   - No new UI code needed

3. **Tool Palettes** ✅
   - Add to settings page as new tab
   - Configuration-driven tool selection
   - Per-mode tool availability

---

## Success Criteria

### Must Pass All Tests

- [ ] **Local Development**: Both modes work on port 8000
- [ ] **Docker**: Both modes work in staging container
- [ ] **HF Spaces**: Both modes work in production
- [ ] **Navigation**: All routes and browser navigation work
- [ ] **Settings**: Page accessible, save/load works (or stubbed)
- [ ] **Model Controls**: In settings, not chat
- [ ] **PWA**: Installation and manifest work
- [ ] **No Regressions**: All existing features work

### Code Quality

- [ ] **3 UI files**: mode_factory.py, chat.py, settings.py
- [ ] **~500 lines total**: UI code stays lean
- [ ] **No duplication**: Single `build_gradio_app()` implementation
- [ ] **Type hints**: All functions properly typed
- [ ] **No variable scoping errors**: All components always defined
- [ ] **Tests pass**: Existing tests still pass

### Documentation

- [ ] **Updated CLAUDE.md**: New structure documented
- [ ] **Updated GRADIO_STANDARDIZATION**: Routes pattern added
- [ ] **Migration guide**: This document serves as guide

---

## Known Issues & Open Questions

### ⚠️ CRITICAL - Missing Implementations

These must be addressed before or after UI-005:

1. **Chat Service Integration**
   - `handle_chat_message()` is a stub
   - Needs: `ChatService`, `model_config_service` imports
   - **Question:** Implement in UI-005 or separate ticket?
   - **Recommendation:** Separate ticket (UI-005 is structural change)

2. **Settings Persistence**
   - `save_settings()` only updates `gr.State`
   - No database writes
   - **Question:** Database or localStorage?
   - **Recommendation:** Database (consistent with existing patterns)

3. **Authentication System**
   - `handle_signin()` is a stub
   - No credential validation
   - **Question:** Implement in UI-005 or defer?
   - **Recommendation:** Defer to separate auth feature

### ⚠️ INCONSISTENCIES

1. **Model Lists: Hardcoded vs Dynamic**
   - Currently: Hardcoded in config
   - Existing: `model_config_service.get_provider_choices_for_ui()`
   - **Resolution needed:** Use existing service or keep hardcoded?
   - **Recommendation:** Use existing service for consistency

2. **Page Reload After Settings Save**
   - Uses: `window.location.href = '/?reload=1'`
   - Impact: Full page reload (not ideal UX)
   - **Alternative:** Gradio state updates without reload
   - **Question:** Acceptable for MVP?
   - **Recommendation:** Ship with reload, optimize in follow-up

### ⚠️ UNCLEAR AREAS

1. **Shared State Scope**
   - Demo-level `gr.State()` shared across routes
   - **Question:** Does state persist across navigation?
   - **Answer needed:** Test browser back/forward behavior

2. **Gradio Startup Events**
   - `gradio_app.run_startup_events()` required?
   - **Question:** Still needed with Gradio 4.x routing?
   - **Action:** Test without this call

3. **CSS Theme Variables**
   - Uses: `var(--background-fill-secondary)`
   - **Question:** Guaranteed in all Gradio themes?
   - **Action:** Test with custom themes

### 🔍 TESTING GAPS

These need manual validation:

1. **Browser Navigation**
   - Back/forward button behavior
   - State preservation across navigation
   - Direct URL access

2. **PWA Installation**
   - Install prompt appearance
   - Icon loading
   - Shortcut functionality

3. **Variable Scoping**
   - All components accessible in event handlers
   - No `NameError` exceptions
   - Visible/hidden components work correctly

---

## Technical Pitfalls & Solutions

### 1. Variable Scope - NameError Prevention

**Problem:** Conditional component definition causes runtime errors.

**Solution:** Always define components, use `visible=` to hide.

```python
# GOOD: Always defined
provider = gr.Dropdown(
    choices=[...],
    visible=config.get("show_it", False)  # Hidden but exists
)

# BAD: Conditional definition
if config.get("show_it"):
    provider = gr.Dropdown(...)  # NameError if False!
```

### 2. Shared State Across Routes

**Problem:** `gr.State()` inside route is route-local.

**Solution:** Define state at demo level, pass to render functions.

```python
# GOOD: Demo-level state
with gr.Blocks() as demo:
    shared_state = gr.State()

    with demo.route("page1", "/"):
        render_page1(config, shared_state)

# BAD: Route-level state
with demo.route("page1", "/"):
    local_state = gr.State()  # Not shared!
```

### 3. Queue Called Twice

**Problem:** Duplicate `queue()` calls cause side effects.

**Solution:** Call once in main.py, not in create_app().

```python
# GOOD: Single queue in main.py
gradio_app = create_app()
gradio_app.queue()  # Once

# BAD: Queue in create_app()
def create_app():
    app = gr.Blocks()
    app.queue()  # First call
    return app

# main.py
gradio_app = create_app()
gradio_app.queue()  # Second call!
```

### 4. FastAPI State Assignment

**Problem:** Direct attribute assignment is fragile.

**Solution:** Use `app.state` namespace.

```python
# GOOD: Use app.state
app.state.adaptive_db = db

# BAD: Direct attribute
app.adaptive_db = db
```

### 5. Route Name Collisions

**Problem:** Route names may collide with Gradio internals.

**Solution:** Prefix route names with `app_`.

```python
# GOOD: Prefixed names
with demo.route("app_chat", "/"):
    ...

# BAD: Generic names (may collide)
with demo.route("Chat", "/"):  # Might collide with gr.Chatbot
    ...
```

---

## References

- **Gradio Multipage Guide**: https://www.gradio.app/guides/multipage-apps
- **Previous Standardization**: `docs/phase1/GRADIO_STANDARDIZATION_COMPLETE.md`
- **Current Structure**: `ui/mode_factory.py`, `ui/app.py`, `ui/seo_coach_app.py`
- **Route Pattern**: `gr.Blocks.route()` documentation
- **Chat History Feature**: `docs/phase2/Feat-dev-plan-chat-history-in-sidebar-in-chatpage.md`
- **PWA Implementation**: `src/agent_workbench/main.py` lines 201-280

---

## Future Enhancements (Post UI-005)

**Deferred to separate features:**

1. **Chat History Sidebar** (separate dev plan exists)
   - Browser-style conversation list
   - Click to load previous chats
   - Feature flag rollout (workbench first)

2. **Settings Persistence** (separate ticket)
   - Database backend for user settings
   - Load settings on login
   - Sync across devices

3. **Authentication System** (separate ticket)
   - Real credential validation
   - Session management
   - OAuth integration

4. **Ollama-Inspired UX** (UI-006)
   - Beautiful visual design
   - CSS iteration with Chrome DevTools MCP
   - Build on working multipage foundation

5. **Agent Modes** (Phase 2+)
   - Research agent mode
   - Coding agent mode
   - Custom agent configurations
   - Tool palette per mode

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-27 | Use native Gradio routing | Solves HF Spaces settings issue, cleaner architecture |
| 2025-10-27 | Single builder pattern | Eliminates code duplication between modes |
| 2025-10-27 | Move model controls to settings | Chat page should be minimal, settings is configuration hub |
| 2025-10-27 | Defer chat sidebar | Separate feature with existing dev plan |
| 2025-10-27 | Always-define component pattern | Prevents NameError in event handlers |
| 2025-10-27 | Demo-level shared state | Enables state sharing across routes |
| 2025-10-27 | Single queue() call in main.py | Prevents duplicate queue initialization |
| 2025-10-27 | Defer authentication | Out of scope for structural refactor |
| 2025-10-27 | Defer settings persistence | Can be added after routing foundation |

---

**End of UI-005 Architecture Document**
