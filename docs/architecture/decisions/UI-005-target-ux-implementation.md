# UI-005: Target UX Implementation - Ollama-Inspired Interface

## Status

**Status**: Ready for Implementation
**Date**: October 23, 2025
**Decision Makers**: Human Architect
**Task ID**: UI-005-target-ux-implementation
**Phase**: 2.1 Extension
**Dependencies**: UI-004 (PWA + Settings page complete)
**Related**: `UI-004-target-ux-ref.md` (design specification)

## Context

The current implementation (UI-004) delivers a functional PWA with settings page, but uses default Gradio styling with a 4-tab settings layout. This doesn't match the target Ollama-inspired design documented in `UI-004-target-ux-ref.md`.

**Current State (Post UI-004)**:
- ✅ PWA manifest and service worker working
- ✅ Settings page accessible at `/settings`
- ✅ Main app at `/app` with explicit routing
- ❌ Default Gradio UI (not Ollama-style)
- ❌ 4-tab settings page (target is single-scroll)
- ❌ Model controls not integrated in chat input
- ❌ No dynamic logo/icon behavior
- ❌ Missing iOS-style toggle switches
- ❌ Ubuntu font not applied

**Target Design** (from `UI-004-target-ux-ref.md`):
- Minimal, centered chat interface with floating chatbox
- Dynamic logo that fades during processing
- Integrated controls in chat input (model selector, web search toggle)
- Left sidebar for chat history (slide-in)
- Single-scroll settings page with user profile at top
- iOS-style toggle switches
- Ubuntu font throughout
- Online/offline connectivity indicator

**Design References**:
- `/design/screenshots/Example_main_screen.png` - Ollama-style main interface
- `/design/screenshots/Example_settings_screen.png` - Single-scroll settings layout
- `/design/screenshots/Example_login.png` - Login integration in settings
- `/design/screenshots/Example_expanded_sidebar_left.png` - Chat history sidebar
- `/design/assets/fonts/` - Ubuntu font files

## Architecture Scope

### What's Included:

**Main Chat Interface (`/app`)**:
- Floating centered chatbox with dynamic logo behavior
- Integrated chat input bar with:
  - Model selector (inline, bottom-right)
  - Web search toggle (globe icon, left)
  - File upload drag-and-drop
  - Submit button (arrow, changes to processing icon)
- Left sidebar chat history (slide-in panel)
- Settings gear icon (top-right)
- Connectivity status indicator (cloud icon, top-right)
- Ubuntu font family
- Streaming response with agent status updates

**Settings Page (`/settings`)**:
- Single-scroll vertical layout (NOT tabs)
- User profile section at top (login status, manage account)
- Settings sections:
  - Account (theme toggle, language)
  - Models (provider, model, parameters)
  - Company (SEO coach mode only)
  - Advanced (debug mode, experimental features)
- iOS-style toggle switches
- Ubuntu font family
- Back button to main app

**Theming & Styling**:
- Gradio theme customization (320 variables)
- Custom CSS for iOS toggles and layout refinements
- Hybrid approach (theme + CSS) for 95% visual match
- Light/Dark/Auto theme support

### What's Explicitly Excluded:

- Agent execution logic (Phase 2.3+)
- Actual web search functionality (UI only)
- File processing (Phase 2.4 - UI stub only)
- Multi-language translations (selector only, no i18n)
- Custom theme editor (presets only)
- Offline agent execution
- Settings sync across devices
- Advanced model parameter tuning UI

## Architectural Decisions

### 0. Development Tooling: Chrome DevTools MCP Integration

**Purpose**: Accelerate design creation and CSS iteration using browser automation

**Chrome DevTools MCP** provides real-time browser inspection and manipulation, enabling rapid UI development:

**Key Capabilities**:
- **Live Page Inspection**: Take snapshots of rendered Gradio interface
- **CSS Injection**: Test CSS changes in real-time without reloading
- **Element Inspection**: Identify Gradio-generated selectors and structure
- **Screenshot Comparison**: Capture current state vs target designs
- **Network Analysis**: Debug asset loading (fonts, icons, CSS)
- **Responsive Testing**: Test breakpoints by resizing viewport

**Development Workflow**:

1. **Initial Inspection Phase**:
```python
# Start app locally
# Open in browser via Chrome DevTools MCP

# Take snapshot of current UI
mcp__chrome_devtools__take_snapshot(verbose=True)
# → Identifies all Gradio elements, classes, and structure

# Screenshot current state
mcp__chrome_devtools__take_screenshot()
# → Compare with target design screenshots
```

2. **CSS Iteration Phase**:
```python
# Test CSS changes live without restarting app
mcp__chrome_devtools__evaluate_script(
    function="""
    () => {
        const style = document.createElement('style');
        style.textContent = `
            .gradio-checkbox input[type="checkbox"] {
                appearance: none;
                width: 51px;
                height: 31px;
                background: #E9E9EA;
                border-radius: 16px;
            }
        `;
        document.head.appendChild(style);
    }
    """
)
# → See iOS toggle instantly without saving files
```

3. **Element Selection Phase**:
```python
# Find exact selectors for Gradio components
mcp__chrome_devtools__take_snapshot(verbose=True)
# → Returns UIDs for clicking, hovering, filling

# Test interactions
mcp__chrome_devtools__click(uid="button-123")
mcp__chrome_devtools__fill(uid="input-456", value="Test")
```

4. **Responsive Testing Phase**:
```python
# Test mobile breakpoint
mcp__chrome_devtools__resize_page(width=375, height=667)
mcp__chrome_devtools__take_screenshot()

# Test tablet breakpoint
mcp__chrome_devtools__resize_page(width=768, height=1024)
mcp__chrome_devtools__take_screenshot()

# Test desktop
mcp__chrome_devtools__resize_page(width=1440, height=900)
mcp__chrome_devtools__take_screenshot()
```

5. **Font & Asset Verification**:
```python
# List network requests to verify assets loaded
mcp__chrome_devtools__list_network_requests(
    resourceTypes=["font", "image", "stylesheet"]
)
# → Check Ubuntu fonts loaded
# → Check icons loaded correctly

# Inspect specific request
mcp__chrome_devtools__get_network_request(reqid=123)
# → See response headers, status codes
```

**Integration Points**:

**CSS Development** (`static/assets/css/`):
- Test iOS toggle styles live
- Verify Ubuntu font rendering
- Debug responsive breakpoints
- Test theme variables
- Iterate on chat input bar layout

**Component Development** (`ui/components/`):
- Verify dynamic logo fade behavior
- Test sidebar slide animation
- Debug model selector positioning
- Check connectivity icon updates

**Theme Development** (`themes/`):
- Test Gradio theme variables live
- Verify color palette across themes
- Check contrast ratios
- Test auto theme with OS preference

**Benefits**:

1. **Rapid Iteration**: Test CSS without restarting app (saves 30-60s per iteration)
2. **Visual Debugging**: See exact Gradio-generated HTML/CSS structure
3. **Cross-Browser Testing**: Test in Chrome, then verify in other browsers
4. **Screenshot Comparison**: Capture and compare against target designs
5. **Responsive Verification**: Test all breakpoints quickly
6. **Asset Debugging**: Verify fonts, icons, CSS files load correctly

**Example Usage Pattern**:

```python
# 1. Start development session
# Terminal 1: APP_MODE=seo_coach make start-app-verbose
# Terminal 2: Open Chrome via MCP

# 2. Take baseline screenshot
mcp__chrome_devtools__navigate_page(url="http://localhost:8000/app")
mcp__chrome_devtools__take_screenshot(filePath="/tmp/current-app.png")

# 3. Compare with target
# Open /design/screenshots/Example_main_screen.png
# Identify differences (font, colors, layout, spacing)

# 4. Iterate on CSS
# Test changes via evaluate_script
# When satisfied, save to ollama-chat.css

# 5. Verify settings page
mcp__chrome_devtools__navigate_page(url="http://localhost:8000/settings")
mcp__chrome_devtools__take_snapshot(verbose=True)
# → Identify tab structure to remove

# 6. Test iOS toggles
# Find checkbox elements from snapshot
mcp__chrome_devtools__click(uid="checkbox-debug-mode")
mcp__chrome_devtools__take_screenshot()
# → Verify toggle animation works

# 7. Responsive testing
for width, height in [(375, 667), (768, 1024), (1440, 900)]:
    mcp__chrome_devtools__resize_page(width=width, height=height)
    mcp__chrome_devtools__take_screenshot(
        filePath=f"/tmp/app-{width}x{height}.png"
    )
```

**Time Savings Estimate**:
- **Without MCP**: 5-10 iterations/hour (restart app each time)
- **With MCP**: 20-30 iterations/hour (live CSS injection)
- **Development Speed**: 3-4x faster for CSS/styling work

**Tools Used**:
- `mcp__chrome_devtools__take_snapshot()` - Element inspection
- `mcp__chrome_devtools__take_screenshot()` - Visual comparison
- `mcp__chrome_devtools__evaluate_script()` - Live CSS injection
- `mcp__chrome_devtools__resize_page()` - Responsive testing
- `mcp__chrome_devtools__list_network_requests()` - Asset debugging
- `mcp__chrome_devtools__navigate_page()` - Page navigation

### 1. Main Interface Architecture: Ollama Pattern

**Design Philosophy**: Minimal, content-focused, floating chatbox

**Layout Structure**:
```
┌─────────────────────────────────────────────────────────┐
│  [☰] [+]                            [☁️] [⚙️]           │ ← Header
│                                                          │
│                      [Logo.png]                          │ ← Dynamic logo
│                                                          │
│                                                          │
│            ┌─────────────────────────────┐              │
│            │ User: Hello                 │              │
│            │ Assistant: Hi! How can I...│              │ ← Chat messages
│            │                             │              │
│            └─────────────────────────────┘              │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [🌐] Type a message...    [gpt-4] [↑]           │  │ ← Input bar
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Key Elements**:
- **Sidebar Toggle** (`view_sidebar_icon.png`): Top-left, opens chat history
- **New Chat** (`chat_add_icon.png`): Next to sidebar toggle
- **Dynamic Logo** (`logo.png`): Centered, fades during processing
- **Processing Icons**: `juggler_icon.png`, `planner_review_icon.png`, etc.
- **Connectivity Status** (`cloud_on_icon.png` / `cloud_off_icon.png`): Top-right
- **Settings Gear**: Top-right

**Dynamic Logo Behavior**:
```python
# Logo states:
# 1. IDLE: logo.png visible (centered, prominent)
# 2. PROCESSING: logo fades out, processing icon appears
#    - Use juggler_icon.png (animated) or planner_review_icon.png
# 3. STREAMING: Show agent status with icons:
#    - analyze_web_results_icon.png
#    - lightbulb_icon.png
#    - search_icon.png
# 4. NEW CHAT: Logo returns (user clicks chat_add_icon.png)
```

**Implementation Strategy**:
- Use Gradio `gr.Image()` for logo with `visible` parameter
- Toggle visibility via JavaScript during processing
- Agent status updates as separate message bubble (collapsible)
- Streaming response in new bubble below status

### 2. Chat Input Bar Architecture

**Integrated Controls** (single row, bottom of interface):

```
┌──────────────────────────────────────────────────────────┐
│ [🌐] Type your message here...        [gpt-4] [↑]       │
└──────────────────────────────────────────────────────────┘
     ↑                                      ↑      ↑
  Web toggle                           Model   Submit
```

**Components**:
1. **Web Search Toggle** (left):
   - Icon: 🌐 (globe icon from design)
   - Functionality: Toggle web search for current query
   - State: Checkable button (enabled/disabled)
   - UI-only in Phase 2.1 (actual search in Phase 2.5)

2. **Message Input** (center):
   - Gradio `gr.Textbox()`
   - Placeholder: "Type a message..."
   - File drag-and-drop support (show filename above input)
   - Multi-line support (expands on Enter)

3. **Model Selector** (right, inline):
   - Display: Model name only (e.g., "gpt-4", "claude-sonnet-4-5")
   - UI: Minimal dropdown (no label)
   - Loads from user settings
   - Updates settings on change

4. **Submit Button** (far right):
   - Icon: `arrow_up_in_circle_icon.png` (pale when empty, black when typed)
   - Processing: Changes to `processing_icon.png` during response
   - Disabled state: Greyed out after submit until response complete

**CSS Layout**:
```css
.chat-input-container {
    display: flex;
    align-items: center;
    gap: 12px;
    max-width: 800px;
    margin: 0 auto;
    padding: 16px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.web-toggle {
    flex: 0 0 auto;
}

.message-input {
    flex: 1;
}

.model-selector {
    flex: 0 0 auto;
    min-width: 120px;
}

.submit-button {
    flex: 0 0 auto;
}
```

### 3. Left Sidebar Chat History

**Trigger**: Sidebar icon (`view_sidebar_icon.png`) in top-left

**Panel Structure**:
```
┌───────────────────────┐
│ [+] New Chat         │ ← Prominent button
├───────────────────────┤
│ Today                │
│ • Chat about PWA     │
│ • SEO optimization   │
├───────────────────────┤
│ Yesterday            │
│ • Website redesign   │
│ • Content strategy   │
├───────────────────────┤
│ Last 7 days          │
│ • Technical docs     │
└───────────────────────┘
```

**Behavior**:
- **Closed state**: Only sidebar icon visible
- **Open state**: Panel slides in from left (300px width)
- **Toggle**: Click icon to open/close
- **New Chat**: Clears chatbox, shows logo, closes sidebar
- **Select conversation**: Loads messages, closes sidebar

**Implementation**:
```python
with gr.Column(visible=False, elem_id="chat-history-sidebar") as sidebar:
    new_chat_btn = gr.Button("➕ New Chat", variant="primary", size="lg")

    with gr.Column():
        gr.Markdown("### Today")
        # List conversations from today

        gr.Markdown("### Yesterday")
        # List conversations from yesterday

# Toggle sidebar visibility
sidebar_toggle.click(
    fn=lambda visible: not visible,
    inputs=[sidebar],
    outputs=[sidebar]
)
```

**CSS Animation**:
```css
#chat-history-sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    width: 300px;
    background: white;
    box-shadow: 2px 0 8px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
    transform: translateX(-100%);
}

#chat-history-sidebar.visible {
    transform: translateX(0);
}
```

### 4. Settings Page Architecture: Single-Scroll Layout

**Design Shift**: From 4-tab layout to single-scroll vertical layout

**Current Implementation (UI-004)**:
```python
with gr.Tabs():
    with gr.Tab("👤 Account"):
        # Account settings
    with gr.Tab("🤖 Models"):
        # Model settings
    with gr.Tab("🏢 Company"):
        # Company settings
    with gr.Tab("🔧 Advanced"):
        # Advanced settings
```

**Target Implementation (UI-005)**:
```python
with gr.Blocks() as settings:
    # Header with back button
    with gr.Row():
        back_btn = gr.Button("← Back to Chat")
        gr.Markdown("# ⚙️ Settings")

    # User Profile Section (top)
    with gr.Group(elem_classes=["setting-section", "user-profile"]):
        if user_id:
            gr.Markdown(f"## {username}")
            gr.Markdown(f"📧 {email}")
            upgrade_btn = gr.Button("Upgrade", variant="primary")
            manage_btn = gr.Button("Manage Account")
            signout_btn = gr.Button("Sign Out", variant="secondary")
        else:
            signin_btn = gr.Button("Sign In", variant="primary")

    # Account Settings
    with gr.Group(elem_classes=["setting-section"]):
        gr.Markdown("## 🎨 Appearance")
        theme_selector = gr.Radio(
            choices=["Light", "Dark", "Auto"],
            value="Auto",
            label="Theme"
        )

    # Models Settings
    with gr.Group(elem_classes=["setting-section"]):
        gr.Markdown("## 🤖 Models")
        provider_dropdown = gr.Dropdown(...)
        model_dropdown = gr.Dropdown(...)
        temperature_slider = gr.Slider(...)

    # Company Settings (SEO coach only)
    if mode == "seo_coach":
        with gr.Group(elem_classes=["setting-section"]):
            gr.Markdown("## 🏢 Company")
            company_name = gr.Textbox(...)

    # Advanced Settings
    with gr.Group(elem_classes=["setting-section"]):
        gr.Markdown("## 🔧 Advanced")
        debug_mode = gr.Checkbox(label="Debug Mode", ...)
```

**Key Changes**:
- Remove `gr.Tabs()` wrapper
- Convert tabs to `gr.Group()` sections
- Add user profile section at top
- Single scrollable page
- Each section has icon + heading
- Settings grouped logically

**Visual Layout** (matches `Example_settings_screen.png`):
```
┌────────────────────────────────┐
│ ← Back to Chat      Settings   │
├────────────────────────────────┤
│                                │
│  John Doe                      │  ← User profile
│  📧 john@example.com           │
│  [Upgrade] [Manage] [Sign Out] │
├────────────────────────────────┤
│  🎨 Appearance                 │  ← Account section
│  Theme: [Light] [Dark] [Auto]  │
├────────────────────────────────┤
│  🤖 Models                     │  ← Models section
│  Provider: [OpenRouter ▼]     │
│  Model: [claude-sonnet-4-5 ▼] │
│  Temperature: [━━━●━━━] 0.7   │
├────────────────────────────────┤
│  🔧 Advanced                   │  ← Advanced section
│  Debug Mode        [○────]     │  ← iOS toggle
│  Enable MCP        [●────]     │
├────────────────────────────────┤
│  [Reset to Defaults]           │
└────────────────────────────────┘
```

### 5. iOS-Style Toggle Switches

**Current**: Gradio default checkboxes (square boxes)
**Target**: iOS-style toggle switches (rounded sliders)

**Implementation Strategy**: Hybrid approach (Gradio theme + CSS override)

**Gradio Theme Variables** (44 checkbox variables):
```python
ios_toggle_theme = gr.themes.Soft(
    primary_hue="slate",
    font=["Ubuntu", "sans-serif"],
).set(
    checkbox_border_radius="12px",
    checkbox_background_color_selected="#34C759",  # iOS green
    checkbox_border_width="0px",
    checkbox_label_background_fill="transparent",
    checkbox_label_gap="12px",
)
```

**Custom CSS Override** (for iOS appearance):
```css
/* iOS-style toggle switch */
.gradio-checkbox input[type="checkbox"] {
    appearance: none;
    width: 51px;
    height: 31px;
    background: #E9E9EA;  /* iOS gray */
    border-radius: 16px;
    position: relative;
    cursor: pointer;
    transition: background 0.3s ease;
}

.gradio-checkbox input[type="checkbox"]:checked {
    background: #34C759;  /* iOS green */
}

.gradio-checkbox input[type="checkbox"]::before {
    content: '';
    position: absolute;
    width: 27px;
    height: 27px;
    border-radius: 50%;
    background: white;
    top: 2px;
    left: 2px;
    transition: transform 0.3s ease;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.gradio-checkbox input[type="checkbox"]:checked::before {
    transform: translateX(20px);
}
```

**Application**:
```python
# Apply to all checkboxes in settings and advanced sections
debug_mode_checkbox = gr.Checkbox(
    label="Debug Mode",
    value=False,
    info="Enable verbose logging",
    elem_classes=["ios-toggle"]
)
```

### 6. Typography: Ubuntu Font Family

**Font Files** (in `/design/assets/fonts/`):
- `Ubuntu-Regular.ttf`
- `Ubuntu-Bold.ttf`
- `Ubuntu-Italic.ttf`
- `Ubuntu-BoldItalic.ttf`

**CSS Font Loading**:
```css
/* File: static/assets/css/fonts.css */
@font-face {
    font-family: 'Ubuntu';
    src: url('/static/assets/fonts/Ubuntu-Regular.ttf') format('truetype');
    font-weight: 400;
    font-style: normal;
}

@font-face {
    font-family: 'Ubuntu';
    src: url('/static/assets/fonts/Ubuntu-Bold.ttf') format('truetype');
    font-weight: 700;
    font-style: normal;
}

@font-face {
    font-family: 'Ubuntu';
    src: url('/static/assets/fonts/Ubuntu-Italic.ttf') format('truetype');
    font-weight: 400;
    font-style: italic;
}

@font-face {
    font-family: 'Ubuntu';
    src: url('/static/assets/fonts/Ubuntu-BoldItalic.ttf') format('truetype');
    font-weight: 700;
    font-style: italic;
}
```

**Gradio Theme Integration**:
```python
ollama_theme = gr.themes.Soft(
    primary_hue="slate",
    font=["Ubuntu", "system-ui", "sans-serif"],  # Fallbacks
).set(
    body_text_font="Ubuntu",
    button_font="Ubuntu",
    input_font="Ubuntu",
)
```

**Import in All Interfaces**:
```python
custom_css = """
    @import url('/static/assets/css/fonts.css');

    body, input, button, select, textarea {
        font-family: 'Ubuntu', system-ui, sans-serif !important;
    }
"""

with gr.Blocks(theme=ollama_theme, css=custom_css) as interface:
    # Interface components
```

### 7. Connectivity Status Indicator

**Purpose**: Show online/offline status and airplane mode

**Location**: Top-right corner, left of settings gear icon

**States**:
1. **Online**: `cloud_on_icon.png` (cloud icon, normal color)
2. **Offline**: `cloud_off_icon.png` (cloud with slash, gray)

**Behavior**:
- Detects browser `navigator.onLine` status
- Shows offline when airplane mode enabled (settings)
- Disables cloud features when offline:
  - Model selector filtered to local models only
  - Web search toggle disabled
  - API key inputs grayed out in settings

**Implementation**:
```python
# Main app header
with gr.Row(elem_classes=["app-header"]):
    with gr.Column(scale=1):
        sidebar_toggle = gr.Button("☰", size="sm")
        new_chat_btn = gr.Button("➕", size="sm")

    with gr.Column(scale=10):
        pass  # Spacer

    with gr.Column(scale=1):
        connectivity_status = gr.Image(
            value="/static/icons/cloud_on_icon.png",
            elem_id="connectivity-status",
            height=24,
            width=24,
            interactive=False
        )
        settings_btn = gr.Button("⚙️", size="sm")

# JavaScript to detect online/offline
js_connectivity = """
function() {
    const updateStatus = () => {
        const isOnline = navigator.onLine;
        const icon = isOnline ?
            '/static/icons/cloud_on_icon.png' :
            '/static/icons/cloud_off_icon.png';
        document.getElementById('connectivity-status').src = icon;
    };

    window.addEventListener('online', updateStatus);
    window.addEventListener('offline', updateStatus);
    updateStatus();
}
"""

interface.load(fn=None, js=js_connectivity)
```

**Offline Feature Degradation**:
```python
def filter_models_by_connectivity(is_online: bool, all_models: List[str]) -> List[str]:
    """Filter models based on connectivity status."""
    if not is_online:
        # Show only local models (Ollama)
        return [m for m in all_models if m.startswith("ollama/")]
    return all_models

def update_ui_for_offline(is_online: bool):
    """Disable cloud features when offline."""
    return {
        web_search_toggle: gr.update(interactive=is_online),
        provider_dropdown: gr.update(
            choices=["Ollama"] if not is_online else all_providers
        ),
        upgrade_btn: gr.update(visible=is_online),
    }
```

### 8. Agent Transparency & Streaming

**Design Goal**: Show agent's "work" before final answer

**Two-Bubble Pattern**:
1. **Status Bubble** ("Thinking..."): Shows agent's plan/actions
2. **Answer Bubble**: Streams final response token-by-token

**Status Bubble Updates** (real-time):
```python
# Example status messages with icons
statuses = [
    "[Agent] 🔍 Searching the web for 'PWA best practices'...",
    "[Agent] 📚 Reading 3 articles...",
    "[Agent] ✨ Compiling the answer...",
]
```

**Implementation Pattern**:
```python
def stream_agent_response(query: str):
    """Stream agent response with status updates."""

    # Show initial status
    yield {
        status_bubble: gr.update(value="[Agent] 🤔 Thinking...", visible=True),
        answer_bubble: gr.update(value="", visible=False)
    }

    # Agent planning phase
    yield {
        status_bubble: gr.update(value="[Agent] 🔍 Searching the web..."),
    }

    # Begin streaming answer
    yield {
        status_bubble: gr.update(visible=True),  # Keep status visible
        answer_bubble: gr.update(visible=True)   # Show answer bubble
    }

    # Stream tokens
    for token in agent_stream(query):
        yield {
            answer_bubble: gr.update(value=token, visible=True)
        }

    # Complete
    yield {
        status_bubble: gr.update(visible=True),  # Make collapsible
        answer_bubble: gr.update(value=final_answer)
    }
```

**CSS Styling**:
```css
.status-bubble {
    background: #F5F5F7;  /* Light gray */
    border-left: 3px solid #007AFF;  /* Blue accent */
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 8px;
    font-size: 0.9rem;
    color: #6E6E73;
}

.answer-bubble {
    background: white;
    padding: 16px;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
```

### 9. Responsive Layouts

**Breakpoints**:
- **Desktop**: > 1024px (full sidebar, wide layout)
- **Tablet**: 768px - 1024px (collapsed sidebar, medium)
- **Mobile**: < 768px (collapsed sidebar, narrow)

**Main Chat Responsive Behavior**:
```css
/* Desktop: Full width sidebar */
@media (min-width: 1024px) {
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }

    #chat-history-sidebar {
        width: 300px;
    }
}

/* Tablet: Overlay sidebar */
@media (min-width: 768px) and (max-width: 1023px) {
    .chat-container {
        max-width: 600px;
        padding: 16px;
    }

    #chat-history-sidebar {
        width: 280px;
        z-index: 1000;
        background: white;
    }
}

/* Mobile: Full-screen overlay sidebar */
@media (max-width: 767px) {
    .chat-container {
        max-width: 100%;
        padding: 8px;
    }

    #chat-history-sidebar {
        width: 80%;
        z-index: 1000;
    }

    .chat-input-container {
        flex-direction: column;
        gap: 8px;
    }
}
```

**Settings Page Responsive**:
```css
/* Desktop: Centered, max-width */
@media (min-width: 768px) {
    .settings-page {
        max-width: 600px;
        margin: 0 auto;
        padding: 40px 20px;
    }
}

/* Mobile: Full width */
@media (max-width: 767px) {
    .settings-page {
        width: 100%;
        padding: 20px 16px;
    }

    .setting-section {
        padding: 16px;
    }
}
```

### 10. Theme System (Light/Dark/Auto)

**Theme Presets**:
- **Light**: Default Gradio light theme with customizations
- **Dark**: Gradio dark theme with customizations
- **Auto**: Respects OS/browser preference (`prefers-color-scheme`)

**Implementation**:
```python
def create_theme(mode: str = "auto"):
    """Create Gradio theme based on user preference."""

    base_theme = gr.themes.Soft(
        primary_hue="slate",
        font=["Ubuntu", "system-ui", "sans-serif"],
    )

    if mode == "light":
        return base_theme.set(
            body_background_fill="white",
            body_text_color="#1D1D1F",
            # ... light theme colors
        )

    elif mode == "dark":
        return base_theme.set(
            body_background_fill="#1D1D1F",
            body_text_color="#F5F5F7",
            # ... dark theme colors
        )

    else:  # auto
        # Use CSS media query
        return base_theme
```

**CSS Media Query for Auto Mode**:
```css
/* Auto theme: respect OS preference */
@media (prefers-color-scheme: dark) {
    :root {
        --body-bg: #1D1D1F;
        --body-text: #F5F5F7;
        --surface-bg: #2C2C2E;
        --border-color: #3A3A3C;
    }
}

@media (prefers-color-scheme: light) {
    :root {
        --body-bg: white;
        --body-text: #1D1D1F;
        --surface-bg: #F5F5F7;
        --border-color: #D1D1D6;
    }
}

body {
    background: var(--body-bg);
    color: var(--body-text);
}
```

**Theme Persistence**:
```python
# Load theme from user settings
async def load_user_theme(user_id: str) -> str:
    """Load user's theme preference."""
    settings = await user_settings_service.get_all_settings(user_id)
    return settings.get("account", {}).get("theme", "Auto")

# Apply on app load
interface.load(
    fn=load_user_theme,
    inputs=[user_id_state],
    outputs=[theme_state]
)
```

## Implementation Boundaries

### Files to CREATE:

```
src/agent_workbench/
├── ui/
│   ├── ollama_chat_interface.py        # New main chat UI (Ollama-style)
│   ├── ollama_settings_page.py         # New settings UI (single-scroll)
│   └── components/
│       ├── chat_input_bar.py           # Integrated input controls
│       ├── chat_history_sidebar.py     # Left sidebar panel
│       └── dynamic_logo.py             # Logo with fade behavior
├── static/
│   ├── assets/
│   │   ├── css/
│   │   │   ├── fonts.css               # Ubuntu font definitions
│   │   │   ├── ollama-chat.css         # Main chat styling
│   │   │   ├── ollama-settings.css     # Settings page styling
│   │   │   └── ios-toggles.css         # iOS-style toggle switches
│   │   └── fonts/
│   │       ├── Ubuntu-Regular.ttf
│   │       ├── Ubuntu-Bold.ttf
│   │       ├── Ubuntu-Italic.ttf
│   │       └── Ubuntu-BoldItalic.ttf
│   └── icons/
│       ├── view_sidebar_icon.png
│       ├── chat_add_icon.png
│       ├── arrow_up_in_circle_icon.png
│       ├── processing_icon.png
│       ├── cloud_on_icon.png
│       ├── cloud_off_icon.png
│       ├── juggler_icon.png
│       ├── planner_review_icon.png
│       ├── analyze_web_results_icon.png
│       ├── lightbulb_icon.png
│       └── search_icon.png
└── themes/
    ├── ollama_light.py                 # Light theme definition
    ├── ollama_dark.py                  # Dark theme definition
    └── ollama_auto.py                  # Auto theme with media queries
```

### Files to MODIFY:

```
src/agent_workbench/
├── ui/
│   ├── app.py                          # Use ollama_chat_interface
│   ├── seo_coach_app.py                # Use ollama_chat_interface + company
│   └── mode_factory.py                 # Register new interfaces
├── main.py                             # Mount static assets, update routes
└── services/
    └── user_settings_service.py        # Add theme loading helpers
```

### Exact Function Signatures:

```python
# CREATE: ui/ollama_chat_interface.py
def create_ollama_chat_interface(
    user_id: Optional[str] = None,
    mode: str = "workbench"
) -> gr.Blocks:
    """
    Create Ollama-inspired chat interface.

    Args:
        user_id: Current user UUID (loads model config)
        mode: App mode ("workbench" or "seo_coach")

    Returns:
        Gradio Blocks with floating chatbox, dynamic logo, integrated controls
    """

async def toggle_sidebar_visibility(current_visible: bool) -> Dict[str, Any]:
    """Toggle chat history sidebar."""

async def handle_new_chat(user_id: str) -> Dict[str, Any]:
    """Create new conversation and reset UI."""

async def update_connectivity_status() -> str:
    """Check online/offline status and return icon path."""

# CREATE: ui/ollama_settings_page.py
def create_ollama_settings_page(
    user_id: Optional[str] = None,
    mode: str = "workbench"
) -> gr.Blocks:
    """
    Create single-scroll settings page.

    Args:
        user_id: Current user UUID
        mode: App mode (controls Company section visibility)

    Returns:
        Gradio Blocks with vertical scroll layout, iOS toggles, Ubuntu font
    """

# CREATE: ui/components/chat_input_bar.py
def create_chat_input_bar(
    user_id: str,
    default_model: Optional[str] = None
) -> Tuple[gr.components]:
    """
    Create integrated chat input bar with web toggle, input, model selector, submit.

    Args:
        user_id: Current user UUID
        default_model: Default model from user settings

    Returns:
        Tuple of (web_toggle, message_input, model_selector, submit_btn)
    """

# CREATE: ui/components/chat_history_sidebar.py
def create_chat_history_sidebar(user_id: str) -> gr.Column:
    """
    Create slide-in chat history sidebar.

    Args:
        user_id: Current user UUID (loads conversation history)

    Returns:
        Gradio Column with conversation list, grouped by date
    """

async def load_conversation_history(user_id: str) -> List[Dict[str, Any]]:
    """Load user's conversation history, grouped by date."""

# CREATE: ui/components/dynamic_logo.py
def create_dynamic_logo() -> Tuple[gr.components]:
    """
    Create logo with dynamic visibility and processing state.

    Returns:
        Tuple of (logo_image, processing_icon, status_text)
    """

async def update_logo_state(
    processing: bool,
    status_message: Optional[str] = None
) -> Dict[str, Any]:
    """Update logo visibility and processing indicator."""

# CREATE: themes/ollama_light.py
def create_ollama_light_theme() -> gr.Theme:
    """Create Ollama-inspired light theme with Ubuntu font."""

# CREATE: themes/ollama_dark.py
def create_ollama_dark_theme() -> gr.Theme:
    """Create Ollama-inspired dark theme with Ubuntu font."""

# CREATE: themes/ollama_auto.py
def create_ollama_auto_theme() -> gr.Theme:
    """Create auto theme that respects OS preference."""

# MODIFY: ui/app.py
from ui.ollama_chat_interface import create_ollama_chat_interface

def create_fastapi_mounted_gradio_interface() -> gr.Blocks:
    """Create workbench interface with Ollama-style chat UI."""
    return create_ollama_chat_interface(user_id=get_current_user_id(), mode="workbench")

# MODIFY: ui/seo_coach_app.py
from ui.ollama_chat_interface import create_ollama_chat_interface

def create_seo_coach_app() -> gr.Blocks:
    """Create SEO Coach interface with Ollama-style chat UI."""
    return create_ollama_chat_interface(user_id=get_current_user_id(), mode="seo_coach")

# MODIFY: main.py
from fastapi.staticfiles import StaticFiles

# Add static mounts for assets
app.mount("/static/assets", StaticFiles(directory="static/assets"), name="assets")

@app.get("/settings")
async def settings_route(request: gr.Request):
    """Render Ollama-style settings page."""
    # Extract user_id from session
    # Return create_ollama_settings_page(user_id, mode)
```

### Additional Dependencies:

```toml
# pyproject.toml
[project.dependencies]
# No new dependencies required
# Uses existing: gradio, fastapi, sqlalchemy, aiosqlite
```

### FORBIDDEN Actions:

- Implementing actual web search functionality (Phase 2.5)
- Processing file uploads beyond UI stub (Phase 2.4)
- Adding agent execution logic (Phase 2.3+)
- Creating multi-language translations (Phase 3)
- Implementing offline LLM execution
- Adding custom theme editor beyond presets
- Creating settings import/export
- Implementing advanced model parameter tuning UI

## Testing Strategy

### UI Component Tests (Priority: HIGH)

```python
# tests/ui/test_ollama_chat_interface.py

def test_ollama_chat_interface_renders():
    """Test Ollama-style chat interface renders correctly."""
    from ui.ollama_chat_interface import create_ollama_chat_interface

    interface = create_ollama_chat_interface(user_id="test-user", mode="workbench")

    assert isinstance(interface, gr.Blocks)
    # Verify CSS includes fonts.css
    # Verify Ubuntu theme applied

def test_chat_input_bar_components():
    """Test integrated input bar has all components."""
    from ui.components.chat_input_bar import create_chat_input_bar

    web_toggle, input_box, model_selector, submit_btn = create_chat_input_bar(
        user_id="test-user",
        default_model="gpt-4"
    )

    # Verify all components created
    assert web_toggle is not None
    assert input_box is not None
    assert model_selector is not None
    assert submit_btn is not None

def test_sidebar_toggle_visibility():
    """Test chat history sidebar toggles correctly."""
    from ui.components.chat_history_sidebar import create_chat_history_sidebar

    sidebar = create_chat_history_sidebar(user_id="test-user")

    # Initial state: hidden
    assert sidebar.visible == False

    # Toggle: visible
    # Note: Gradio visibility testing requires integration test

def test_dynamic_logo_states():
    """Test logo fades during processing."""
    from ui.components.dynamic_logo import create_dynamic_logo, update_logo_state

    logo, processing_icon, status = create_dynamic_logo()

    # Idle state
    result = await update_logo_state(processing=False)
    assert result[logo]["visible"] == True
    assert result[processing_icon]["visible"] == False

    # Processing state
    result = await update_logo_state(processing=True, status_message="Thinking...")
    assert result[logo]["visible"] == False
    assert result[processing_icon]["visible"] == True

def test_ollama_settings_single_scroll():
    """Test settings page uses single-scroll layout (not tabs)."""
    from ui.ollama_settings_page import create_ollama_settings_page

    settings = create_ollama_settings_page(user_id="test-user", mode="workbench")

    # Verify no gr.Tabs() in component tree
    # Verify gr.Group() sections exist
    # Manual verification required for visual layout
```

### CSS & Styling Tests (Priority: MEDIUM)

```python
# tests/ui/test_ios_toggles.py

def test_ios_toggle_css_applied():
    """Test iOS-style toggle CSS loads correctly."""
    import os

    css_path = "static/assets/css/ios-toggles.css"
    assert os.path.exists(css_path)

    with open(css_path) as f:
        content = f.read()
        assert "appearance: none" in content
        assert "#34C759" in content  # iOS green
        assert "transform: translateX(20px)" in content

def test_ubuntu_font_loading():
    """Test Ubuntu font files exist and CSS loads them."""
    import os

    font_dir = "static/assets/fonts/"
    required_fonts = [
        "Ubuntu-Regular.ttf",
        "Ubuntu-Bold.ttf",
        "Ubuntu-Italic.ttf",
        "Ubuntu-BoldItalic.ttf"
    ]

    for font in required_fonts:
        assert os.path.exists(os.path.join(font_dir, font))

    # Verify fonts.css references all fonts
    with open("static/assets/css/fonts.css") as f:
        content = f.read()
        for font in required_fonts:
            assert font in content

def test_ollama_theme_customization():
    """Test Gradio theme uses Ubuntu font and custom colors."""
    from themes.ollama_light import create_ollama_light_theme

    theme = create_ollama_light_theme()

    # Verify Ubuntu font in theme
    # Note: Gradio theme inspection limited
    # Manual verification via rendered interface required
```

### Responsive Layout Tests (Priority: MEDIUM)

```python
# tests/ui/test_responsive_layouts.py

def test_chat_container_responsive():
    """Test chat container adjusts to screen sizes."""
    # CSS media query verification

    with open("static/assets/css/ollama-chat.css") as f:
        content = f.read()
        assert "@media (min-width: 1024px)" in content
        assert "@media (max-width: 767px)" in content

def test_settings_page_responsive():
    """Test settings page adjusts to screen sizes."""

    with open("static/assets/css/ollama-settings.css") as f:
        content = f.read()
        assert "@media (min-width: 768px)" in content
        assert "max-width: 600px" in content  # Desktop centered

def test_sidebar_mobile_overlay():
    """Test sidebar becomes full-screen overlay on mobile."""

    with open("static/assets/css/ollama-chat.css") as f:
        content = f.read()
        assert "width: 80%" in content  # Mobile sidebar width
        assert "z-index: 1000" in content  # Overlay layer
```

### Integration Tests (Priority: HIGH)

```python
# tests/integration/test_settings_ui_migration.py

async def test_settings_migration_from_tabs_to_scroll(db, authenticated_user):
    """Test migrating from 4-tab to single-scroll settings."""
    from services.user_settings_service import UserSettingsService

    service = UserSettingsService(db)

    # Pre-populate settings (simulating UI-004 data)
    await service.save_model_settings(
        user_id=authenticated_user.id,
        provider="OpenRouter",
        model="claude-sonnet-4-5",
        temperature=0.7,
        max_tokens=2000
    )

    # Load settings in new UI
    from ui.ollama_settings_page import create_ollama_settings_page

    settings_page = create_ollama_settings_page(
        user_id=str(authenticated_user.id),
        mode="workbench"
    )

    # Verify settings loaded correctly
    # (Manual verification of Gradio component values)

async def test_chat_interface_loads_user_theme(db, authenticated_user):
    """Test chat interface applies user's theme preference."""
    from services.user_settings_service import UserSettingsService
    from ui.ollama_chat_interface import create_ollama_chat_interface

    service = UserSettingsService(db)

    # Set user theme to Dark
    await service.save_account_settings(
        user_id=authenticated_user.id,
        theme="Dark"
    )

    # Create interface
    interface = create_ollama_chat_interface(
        user_id=str(authenticated_user.id),
        mode="workbench"
    )

    # Verify dark theme applied
    # (Theme inspection limited in Gradio - manual verification)

async def test_connectivity_status_updates(db, authenticated_user):
    """Test connectivity indicator updates based on network status."""
    from ui.ollama_chat_interface import create_ollama_chat_interface

    interface = create_ollama_chat_interface(
        user_id=str(authenticated_user.id),
        mode="workbench"
    )

    # Verify connectivity status component exists
    # JavaScript detection tested via browser automation (Selenium)
```

### Manual Testing Checklist

**Main Chat Interface:**
- [ ] Logo visible in idle state (centered, prominent)
- [ ] Logo fades during processing, processing icon appears
- [ ] Status bubble shows agent actions with icons
- [ ] Answer streams token-by-token in separate bubble
- [ ] Chat input bar has all components (web toggle, input, model, submit)
- [ ] Model selector inline bottom-right, shows model name only
- [ ] Submit button changes to processing icon during response
- [ ] Sidebar toggle opens/closes chat history from left
- [ ] New chat button clears chatbox, shows logo
- [ ] Connectivity icon shows cloud/cloud-off based on network
- [ ] Settings gear navigates to /settings
- [ ] Ubuntu font applied throughout

**Settings Page:**
- [ ] Single-scroll layout (not tabs)
- [ ] User profile section at top (name, email, buttons)
- [ ] Account section with theme radio buttons
- [ ] Models section with dropdowns and sliders
- [ ] Company section visible in SEO coach mode only
- [ ] Advanced section with iOS-style toggles
- [ ] Toggles animate smoothly (slide left/right)
- [ ] Back button returns to /app
- [ ] Ubuntu font applied throughout
- [ ] Responsive on mobile (full width, scrollable)

**Theming:**
- [ ] Light theme: white background, dark text
- [ ] Dark theme: dark background, light text
- [ ] Auto theme: follows OS preference
- [ ] Theme persists across page refreshes
- [ ] iOS green color (#34C759) on toggles

**Responsive:**
- [ ] Desktop (>1024px): Centered chatbox, 300px sidebar
- [ ] Tablet (768-1024px): Overlay sidebar, medium chatbox
- [ ] Mobile (<768px): Full-screen sidebar, narrow chatbox
- [ ] Settings page centered on desktop, full width on mobile

### Test Coverage Goals

- **UI Components**: 70% (Gradio rendering limits automated testing)
- **CSS & Styling**: 60% (visual verification required)
- **Integration**: 80% (critical for data flow)
- **Responsive**: 50% (browser automation for accurate testing)

**Overall UI-005 Target: 65% coverage**

## Success Criteria

- [ ] **Ollama-Style Main Interface**: Floating chatbox, centered logo, integrated input bar
- [ ] **Dynamic Logo**: Fades during processing, returns on new chat
- [ ] **Chat Input Bar**: Web toggle, input, model selector, submit (all inline)
- [ ] **Left Sidebar**: Slides in from left, shows conversation history
- [ ] **Single-Scroll Settings**: Vertical layout (not tabs), user profile at top
- [ ] **iOS-Style Toggles**: Animated switches (not checkboxes) in settings
- [ ] **Ubuntu Font**: Applied throughout interface (main + settings)
- [ ] **Connectivity Status**: Cloud icon shows online/offline state
- [ ] **Agent Transparency**: Status bubble shows actions, answer streams separately
- [ ] **Theme System**: Light/Dark/Auto themes working with Ubuntu font
- [ ] **Responsive**: Works on desktop, tablet, mobile (320px+)
- [ ] **Settings Migration**: Existing settings from UI-004 load correctly
- [ ] **65%+ test coverage** for UI-005 components
- [ ] **Manual checklist 100% complete**
- [ ] **Visual match**: 95% similarity to design screenshots
- [ ] **Navigation**: All routes work (/app, /settings, sidebar, back buttons)

## Migration Notes

### From UI-004 to UI-005

**Existing Users**:
1. **Settings Data**: Preserved (uses same database schema)
2. **UI Change**: From 4-tab to single-scroll layout
3. **Theme**: Auto-applied based on existing preference
4. **No Data Loss**: All settings carry over seamlessly

**Code Changes**:
- Replace `ui/app.py` and `ui/seo_coach_app.py` imports
- Replace `ui/settings_page.py` with `ui/ollama_settings_page.py`
- Add static asset mounts in `main.py`
- Copy font files to `static/assets/fonts/`
- Copy icon files to `static/icons/`
- Create CSS files in `static/assets/css/`

**Deployment**:
- No database migrations required (uses existing schema)
- Add font and icon files to repo
- Update static file serving in FastAPI
- Test on ngrok before production deploy

**Backwards Compatibility**:
- Settings data format unchanged
- API endpoints unchanged
- Database schema unchanged
- Conversation history unchanged

## Future Enhancements (Phase 3+)

**Not Implemented in UI-005:**
- File upload visual enhancements (Phase 2.4)
- Actual web search integration (Phase 2.5)
- Agent execution with tool calling (Phase 2.3+)
- Collapsible status bubble after completion
- Share target visual refinements
- Multi-language UI translations
- Custom theme editor
- Advanced model parameter controls
- Keyboard shortcuts
- Accessibility enhancements (ARIA labels, screen reader)

## References

- **Design Spec**: `UI-004-target-ux-ref.md` (authoritative UX document)
- **Design Assets**: `/design/screenshots/` (Example_main_screen, Example_settings_screen)
- **Font Assets**: `/design/assets/fonts/` (Ubuntu font family)
- **Icon Assets**: `/design/icons/` (all UI icons referenced)
- **Previous Implementation**: `UI-004-pwa-app-user-settings.md` (database schema)
- **Gradio Themes**: https://www.gradio.app/guides/theming-guide
- **Ollama Reference**: https://ollama.com (design inspiration)
- **iOS Design Guidelines**: https://developer.apple.com/design/human-interface-guidelines/toggles
