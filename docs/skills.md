# Gradio App Design Best Practices

**Purpose:** Reusable design patterns and best practices for building production-quality Gradio applications
**Source:** Lessons learned from Agent Workbench UI-005 implementation
**Audience:** Developers building custom Gradio UIs with Python

---

## Table of Contents

1. [The Three-Tier Customization Framework](#the-three-tier-customization-framework)
2. [State-Dependent UI Components](#state-dependent-ui-components)
3. [Aligning Components with Gradio's Nested Wrappers](#aligning-components-with-gradios-nested-wrappers)
4. [gr.HTML vs gr.Button for Icons](#grhtml-vs-grbutton-for-icons)
5. [CSS Architecture & Normalization](#css-architecture--normalization)
6. [Performance & Optimization](#performance--optimization)
7. [Security Best Practices](#security-best-practices)
8. [Function Design Best Practices](#function-design-best-practices)
9. [Testing Patterns](#testing-patterns)
10. [Clean Code Structure](#clean-code-structure)
11. [Common Anti-Patterns](#common-anti-patterns)
12. [Quick Reference](#quick-reference)
13. [SVG Icons for Web Apps](#svg-icons-for-web-apps)
14. [Claude Code Chrome DevTools Integration](#claude-code-chrome-devtools-integration)

---

## The Three-Tier Customization Framework

**Core Principle:** Choose the right abstraction level for your customization needs.

### Tier 1: Built-in Parameters ✅ Use First

**When to use:**
- Simple, documented changes
- Text labels, placeholders, visibility
- Basic component configuration

**Examples:**
```python
gr.ChatInterface(
    submit_btn="Send Message",  # Change button text
    show_submit=False,           # Hide button
    placeholder="Ask anything...", # Input placeholder
)
```

**Characteristics:**
- ✅ Minimal code (1 line)
- ✅ Highest stability (official API)
- ✅ Won't break on Gradio updates
- ✅ Best performance

**Decision:** If a built-in parameter exists, always use it.

---

### Tier 2: CSS Overrides ⚠️ Use for Visual Polish

**When to use:**
- Built-in params insufficient
- Pure visual changes (colors, spacing, borders)
- Component structure is fine

**Examples:**
```python
with gr.Blocks(css="""
    .my-button {
        background: #007AFF;
        border-radius: 8px;
        padding: 12px 24px;
    }

    .my-input {
        font-size: 16px;
        border: 2px solid #e0e0e0;
    }
""") as demo:
    btn = gr.Button("Click", elem_classes=["my-button"])
    inp = gr.Textbox(elem_classes=["my-input"])
```

**Best Practices:**
- ✅ Use custom `elem_classes` (not Gradio's internal classes)
- ✅ Use CSS variables for design tokens
- ✅ Keep selectors shallow (max 2-3 levels)
- ❌ Avoid deep chains like `.gradio-app > div > div > ...`
- ❌ Don't rely on Gradio's internal class names

**Characteristics:**
- ⚠️ Medium stability (can break if Gradio changes HTML)
- ⚠️ Requires testing after Gradio updates
- ✅ Good for visual polish
- ❌ Can't change component behavior

**Decision:** Use for colors, spacing, typography—not for dynamic behavior.

---

### Tier 3: gr.Blocks 🔧 Use for Full Control

**When to use:**
- Need custom behavior or state-dependent UI
- Icon swapping based on state
- Custom layouts not supported by high-level components
- Dynamic component updates

**Examples:**
```python
with gr.Blocks() as demo:
    # Full control over structure
    with gr.Row():
        inp = gr.Textbox()
        btn = gr.Button(
            icon="/icons/arrow.png",
            interactive=False  # Custom initial state
        )

    # Custom state management
    def update_btn(text):
        return gr.Button(
            icon="/icons/active.png" if text else "/icons/disabled.png",
            interactive=bool(text)
        )

    inp.change(fn=update_btn, inputs=[inp], outputs=[btn], queue=False)
```

**Characteristics:**
- ✅ Highest control
- ✅ Can implement any custom behavior
- ✅ Highest stability (you own the structure)
- ⚠️ More code to write
- ⚠️ Manual state management required

**Decision:** Use when you need state-dependent UI or custom behavior.

---

### Decision Framework

Ask these questions **in order**:

**Q1: Is there a built-in parameter?**
- Check Gradio docs for the component
- ✅ If YES → **Use Tier 1**
- ❌ If NO → Continue to Q2

**Q2: Is this purely visual (no behavior change)?**
- Only colors, spacing, borders, fonts?
- No state-dependent changes?
- ✅ If YES → **Use Tier 2** (CSS)
- ❌ If NO → Continue to Q3

**Q3: Need custom behavior or dynamic UI?**
- State-dependent changes?
- Icon swapping?
- Custom event handling?
- ✅ If YES → **Use Tier 3** (gr.Blocks)

---

## State-Dependent UI Components

**Pattern:** Components that change appearance/behavior based on application state

**Common Use Cases:**
- Submit button that activates when input has text
- Icons that change based on mode selection
- Processing indicators during API calls
- Show/hide advanced options

### Pattern: State-Dependent Button

**Complete Working Example:**

```python
import gradio as gr

def respond(message, chat_history):
    """Handle message submission."""
    if not message.strip():
        return chat_history, ""

    # Add messages
    chat_history.append({"role": "user", "content": message})
    response = call_api(message)
    chat_history.append({"role": "assistant", "content": response})

    return chat_history, ""  # (updated_chat, cleared_input)


def update_button_state(text):
    """Update button icon based on input state."""
    if text.strip():
        return gr.Button(
            icon="/icons/arrow_active.png",
            interactive=True
        )
    else:
        return gr.Button(
            icon="/icons/arrow_disabled.png",
            interactive=False
        )


with gr.Blocks() as demo:
    # ===== UI COMPONENTS =====
    chatbot = gr.Chatbot(type="messages")

    with gr.Row():
        textbox = gr.Textbox(placeholder="Type...", show_label=False)
        submit_btn = gr.Button(
            value="",
            icon="/icons/arrow_disabled.png",
            interactive=False,
            size="sm"
        )

    # ===== BINDINGS =====

    # Update button on every keystroke (instant)
    textbox.change(
        fn=update_button_state,
        inputs=[textbox],
        outputs=[submit_btn],
        queue=False  # KEY: instant UI update, no backend call
    )

    # Handle submit (both button and Enter key)
    submit_btn.click(fn=respond, inputs=[textbox, chatbot], outputs=[chatbot, textbox])
    textbox.submit(fn=respond, inputs=[textbox, chatbot], outputs=[chatbot, textbox])

demo.launch()
```

### Key Components Explained

**1. Dual Event Handlers** (Critical!)
```python
submit_btn.click(fn=respond, ...)  # Mouse click
textbox.submit(fn=respond, ...)    # Enter key
```
**Why:** Users expect both to work. Always wire both for input forms.

---

**2. `queue=False` for Instant Updates**
```python
textbox.change(fn=update_ui, ..., queue=False)
```
**Why:**
- ✅ Instant UI update (fires on every keystroke)
- ✅ No backend API call needed
- ✅ Feels responsive
- ❌ Don't use for operations that need backend (API calls, database queries)

---

**3. Return New Component Instance**
```python
def update_button(text):
    return gr.Button(icon="/new/icon.png", interactive=True)
```
**Why:**
- ✅ Gradio automatically replaces the old component
- ❌ Don't try to modify in place: `button.icon = "..."` won't work

---

**4. Generator Pattern for Processing States**
```python
def respond_with_processing(message, history):
    """Show processing state during long operations."""
    # Step 1: Show user message + processing icon
    history.append({"role": "user", "content": message})
    yield history, message, gr.Button(icon="/icons/processing.png")

    # Step 2: Call API (takes time)
    response = call_api(message)

    # Step 3: Show final result + reset
    history.append({"role": "assistant", "content": response})
    yield history, "", gr.Button(icon="/icons/arrow_disabled.png")
```

**When to use:**
- ✅ Operations > 1 second (API calls, database queries)
- ✅ Want to show intermediate states
- ✅ Streaming responses
- ❌ Instant operations (use simple returns)

---

## Aligning Components with Gradio's Nested Wrappers

**Problem:** Gradio wraps every component in multiple nested `div` layers (`.block`, `.html-container`, `.prose`, etc.) that shrink-wrap content by default, preventing edge-aligned layouts.

**Symptom:** When using `justify-content: flex-end` to right-align a component, it stops short of the container's edge despite removing padding and margins.

### The Root Cause

```
Parent Container (800px)
  └── gr.Row wrapper (shrink-wraps to content width!)
      └── gr.HTML wrapper (also shrinks!)
          └── Your icon (40px)
              Result: Icon aligned to right edge of wrapper, NOT parent
```

Even with `justify-content: flex-end`, the icon only aligns to its **immediate parent's edge**, not the ultimate container's edge. If intermediate wrappers shrink-wrap, there's a gap.

### The Solution: Cascading Width & Alignment

Force **every wrapper layer** to expand to 100% width and cascade the alignment down:

```css
/* 1. Make the group container expand to fill parent */
.agent-workbench-top-bar-right {
    display: flex;
    align-items: center;
    justify-content: flex-end;

    /* Force full width expansion */
    width: 100%;
    flex-grow: 1;
}

/* 2. Force all Gradio-generated wrappers to expand */
#settings-icon-container,
#settings-icon-container > .block,
#settings-icon-container > .block > .html-container {
    width: 100% !important;
    display: flex !important;
    justify-content: flex-end !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* 3. Ensure the icon itself has no right spacing */
.agent-workbench-top-bar-right .agent-workbench-icon-btn {
    margin-right: 0 !important;
    padding-right: 0 !important;
}
```

### Why This Works

**Cascading Full Width:**
- Each wrapper expands to match its parent's width (100%)
- `justify-content: flex-end` at each level pushes content rightward
- The icon reaches the absolute right edge of the top-level container

**Visual Flow:**
```
Parent Container (800px, padding: 20px → content: 760px)
  └── .top-bar-right (760px, flex-end) ← width: 100%
      └── #settings-icon-container (760px, flex-end) ← width: 100%
          └── .block (760px, flex-end) ← width: 100%
              └── Icon (40px, margin-right: 0)
                  Result: Icon at exactly 760px - 40px = 720px from left
                          = flush with right edge!
```

### Real-World Example: Top Bar Icon Alignment

**Context:** Aligning a settings icon with the right edge of a chat input bar, both inside a padded container.

**Python (Gradio):**
```python
with gr.Column(elem_classes=["agent-workbench-chat-container"]):
    # Top bar with left and right icon groups
    with gr.Row(elem_classes=["agent-workbench-top-bar"]):
        # Left group
        with gr.Row(elem_classes=["agent-workbench-top-bar-left"]):
            sidebar_toggle = gr.Button(icon="/icons/sidebar.svg")
            new_chat = gr.Button(icon="/icons/new-chat.svg")

        # Right group - needs edge alignment
        with gr.Row(elem_classes=["agent-workbench-top-bar-right"]):
            settings = gr.HTML(
                value='<div class="agent-workbench-icon-btn">...</div>',
                elem_id="settings-icon-container"
            )
```

**CSS (from above solution):**
```css
/* Container has padding that defines content boundaries */
.agent-workbench-chat-container {
    max-width: 800px;
    padding: var(--space-4xl) var(--space-xl);  /* 20px horizontal */
}

/* Top bar matches container width */
.agent-workbench-top-bar {
    width: 100%;
    display: flex;
    justify-content: space-between;
}

/* Left group aligns to left naturally */
.agent-workbench-top-bar-left {
    display: flex;
    justify-content: flex-start;
}

/* Right group: apply cascading solution */
.agent-workbench-top-bar-right {
    display: flex;
    justify-content: flex-end;
    width: 100%;
    flex-grow: 1;
}

/* Force all wrappers to expand (the key!) */
#settings-icon-container,
#settings-icon-container > .block,
#settings-icon-container > .block > .html-container {
    width: 100% !important;
    display: flex !important;
    justify-content: flex-end !important;
    padding: 0 !important;
    margin: 0 !important;
}
```

### When to Use This Pattern

✅ **Use when:**
- Aligning components to container edges (not just relative positioning)
- Working with `gr.Row`, `gr.Column` that contain custom HTML
- Need pixel-perfect alignment across responsive breakpoints
- Fighting Gradio's default shrink-wrap behavior

❌ **Don't use when:**
- Simple centering (use `justify-content: center` without width forcing)
- Left alignment (works naturally without intervention)
- You control the entire HTML structure (use simpler flexbox)

### Alternative: Negative Margin (Hacky)

If cascading width doesn't work due to other constraints:

```css
/* Push element right by compensating for gap */
.component-wrapper {
    margin-right: -8px;  /* Measure gap in DevTools first */
}
```

⚠️ **Warning:** Fragile, breaks on different screen sizes. Use only as last resort.

### Debugging Checklist

When edge alignment fails:

1. **Inspect wrapper hierarchy:** Use DevTools to identify all div layers
2. **Check computed width:** Each wrapper should show `width: 100%` or full pixel width
3. **Verify flexbox:** Each layer with `display: flex` needs explicit `width`
4. **Look for padding/margin:** Even 1px can cause misalignment
5. **Test responsive:** Check alignment at different viewport widths

**DevTools Tip:** Right-click element → Inspect → Styles tab → Filter for "width", "padding", "margin"

---

## gr.HTML vs gr.Button for Icons

**Principle:** Use `gr.Button` for interactive elements, `gr.HTML` for decoration only

### Decision Framework

**Use gr.Button when:**
- ✅ Element needs click handlers
- ✅ Needs accessibility (focus states, keyboard navigation, aria-label)
- ✅ Part of a form flow
- ✅ You have individual SVG/PNG icon files

**Use gr.HTML when:**
- ✅ Purely decorative (no interaction)
- ✅ Using SVG sprites (need `<use href="#symbol">` syntax)
- ✅ Complex custom markup that gr.Button can't handle
- ✅ Logos or branding elements

### Pattern: gr.Button with Icon

```python
# ✅ GOOD: Built-in accessibility and event handling
sidebar_toggle = gr.Button(
    value="",                                    # No text
    icon="/static/icons/sidebar.svg",           # External SVG file
    elem_classes=["agent-workbench-icon-btn"],
)

# Wire event - Gradio handles accessibility automatically
sidebar_toggle.click(fn=toggle_sidebar, inputs=[], outputs=[sidebar])
```

**Benefits:**
- ✅ Automatic aria-label from icon filename
- ✅ Built-in focus states and keyboard support
- ✅ Works with Gradio's event system
- ✅ Properly disabled when `interactive=False`

### Pattern: gr.HTML with SVG Sprite

```python
# Use when referencing SVG sprite symbols
_sidebar_toggle_btn = gr.HTML(
    value='<svg class="icon" aria-label="Toggle Sidebar"><use href="/static/icons/sprite.svg#sidebar"/></svg>',
    elem_classes=["agent-workbench-icon-btn"],
)
```

**Note:** When using gr.HTML for interactive elements, you lose:
- ❌ Gradio's built-in `.click()` handler (need custom JS)
- ❌ Automatic focus management
- ❌ Integration with `interactive` state

### Anti-Pattern: gr.HTML for Interactive Icons

```python
# ❌ BAD: Using gr.HTML when gr.Button would work
_submit_btn = gr.HTML(
    value=(
        '<div class="agent-workbench-icon-btn">'
        '<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 -960 960 960">'
        '<path d="M120-120v-720h720v720H120Z"/>'
        '</svg>'
        '</div>'
    ),
)
# Can't easily wire .click() event!

# ✅ GOOD: Use gr.Button
_submit_btn = gr.Button(
    value="",
    icon="/static/icons/submit.svg",
    elem_classes=["agent-workbench-icon-btn"],
)
_submit_btn.click(fn=handle_submit, ...)  # Easy!
```

### Combining: Sprite Icons with Click Handlers

If you want sprites AND click handlers, wrap gr.HTML in a gr.Button alternative:

```python
# Option 1: Use individual SVG files with gr.Button (recommended)
submit_btn = gr.Button(icon="/static/icons/submit.svg", ...)

# Option 2: Use sprite but accept limited Gradio integration
icon_display = gr.HTML('<svg class="icon"><use href="...#submit"/></svg>')
# Add custom JS for click handling via elem_id
```

**Recommendation:** For most icon buttons, use `gr.Button` with individual SVG files. Reserve sprites for decorative icons or when HTTP request optimization is critical.

---

## CSS Architecture & Normalization

**Problem:** Gradio's default styles can conflict with custom designs. Need a structured approach.

### Simplified CSS Architecture

**Pattern:** Two files with clear separation of concerns

```
static/assets/css/
├── tokens.css     # Design system (variables only, no selectors)
└── styles.css     # All component styles (imports tokens)
```

**Why Two Files:**
- ✅ Clear mental model: tokens vs styles
- ✅ Easy theme swapping (replace tokens.css)
- ✅ No confusion about where code belongs
- ❌ Avoid: 4+ files with unclear boundaries ("shared" vs "design"?)

**Example `tokens.css`:**
```css
/*
 * Design Tokens - ONLY variables, no selectors
 * Swap this file for different themes
 */
:root {
    /* Colors */
    --awb-bg: #ffffff;
    --awb-surface: #f8f8f8;
    --awb-text-primary: #1a1a1a;
    --awb-text-secondary: #666666;
    --awb-accent: #007AFF;
    --awb-border: #e0e0e0;

    /* Typography */
    --awb-font-heading: 'Ubuntu', sans-serif;
    --awb-font-body: 'Lora', serif;
    --awb-font-size-sm: 14px;
    --awb-font-size-base: 16px;

    /* Spacing */
    --awb-space-sm: 8px;
    --awb-space-md: 16px;
    --awb-space-lg: 24px;

    /* Borders & Shadows */
    --awb-radius-md: 8px;
    --awb-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
}

@media (prefers-color-scheme: dark) {
    :root {
        --awb-bg: #1a1a1a;
        --awb-surface: #2a2a2a;
        --awb-text-primary: #e0e0e0;
        --awb-border: #404040;
    }
}
```

**Example `styles.css`:**
```css
/*
 * Component Styles - All selectors go here
 */
@import url('tokens.css');

/* Base */
body {
    font-family: var(--awb-font-body);
    background: var(--awb-bg);
    color: var(--awb-text-primary);
}

/* Components */
.my-button {
    background: var(--awb-accent);
    padding: var(--awb-space-md);
    border-radius: var(--awb-radius-md);
}

.my-card {
    background: var(--awb-surface);
    box-shadow: var(--awb-shadow-sm);
}
```

### CSS Variables for Design Tokens

**Pattern:** Define design system as CSS custom properties

```css
:root {
    /* ===== COLORS ===== */
    --color-bg: #ffffff;
    --color-surface: #f8f8f8;
    --color-text-primary: #1a1a1a;
    --color-text-secondary: #666666;
    --color-border: #e0e0e0;
    --color-accent: #007AFF;

    /* ===== SPACING ===== */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;

    /* ===== TYPOGRAPHY ===== */
    --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-size-sm: 14px;
    --font-size-base: 16px;
    --font-size-lg: 18px;

    /* ===== BORDERS ===== */
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-full: 9999px;

    /* ===== SHADOWS ===== */
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.10);
    --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.12);

    /* ===== TRANSITIONS ===== */
    --transition-fast: 150ms ease;
    --transition-base: 250ms ease;
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
    :root {
        --color-bg: #1a1a1a;
        --color-surface: #2a2a2a;
        --color-text-primary: #e0e0e0;
        --color-text-secondary: #a0a0a0;
        --color-border: #404040;
    }
}
```

**Benefits:**
- ✅ Consistent design system
- ✅ Easy theme switching
- ✅ Single source of truth
- ✅ Maintainable at scale

### Using CSS Variables

```css
.my-button {
    background: var(--color-accent);
    padding: var(--space-md) var(--space-lg);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-fast);
}

.my-button:hover {
    box-shadow: var(--shadow-md);
}
```

---

### Loading External Fonts (Google Fonts, CDN)

**Problem:** Gradio's `css=""` parameter uses Constructable Stylesheets which **block `@import` rules for external URLs**

**Symptom:**
```python
# ❌ This won't work in gr.Blocks(css="...")
with gr.Blocks(css="""
    @import url('https://fonts.googleapis.com/css2?family=Roboto');
""") as demo:
    pass

# Console error: "@import rules are not allowed here"
```

**Why:** Gradio uses [Constructable Stylesheets](https://developer.mozilla.org/en-US/docs/Web/API/CSSStyleSheet/CSSStyleSheet) for CSS injection, which don't support external `@import` statements for security reasons.

---

**Solution: FastAPI Middleware Injection**

**Pattern:** Inject `<link>` tags directly into HTML `<head>` via middleware

```python
# main.py - Add this middleware BEFORE Gradio mount

@app.middleware("http")
async def inject_google_fonts(request, call_next):
    """Inject Google Fonts into HTML responses."""
    response = await call_next(request)

    # Only inject into HTML responses
    if (
        response.headers.get("content-type", "").startswith("text/html")
        and response.status_code == 200
    ):
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Build Google Fonts link
        google_fonts_url = (
            "https://fonts.googleapis.com/css2?"
            "family=Roboto:wght@300;400;500;700&"
            "display=swap"
        )

        fonts_html = f"""
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{google_fonts_url}" rel="stylesheet">
</head>""".encode("utf-8")

        # Inject before </head>
        modified_body = body.replace(b"</head>", fonts_html)

        # Return modified response (remove Content-Length to avoid mismatch)
        from fastapi.responses import Response

        headers = dict(response.headers)
        headers.pop("content-length", None)  # Will be recalculated

        return Response(
            content=modified_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )

    return response

# Mount Gradio AFTER middleware
app.mount("/", gradio_interface.app, name="gradio")
```

**Then use the fonts normally in CSS:**
```css
/* fonts.css or inline CSS */
:root {
    --font-family: 'Roboto', -apple-system, sans-serif;
}

body {
    font-family: var(--font-family);
}
```

---

**When to Use This Pattern:**
- ✅ Google Fonts or other CDN fonts
- ✅ External icon fonts (Font Awesome, Material Icons)
- ✅ Any external CSS that must be in `<head>`
- ❌ Local CSS files (use `@import url('/static/...')` instead)

**Benefits:**
- ✅ Bypasses Gradio's Constructable Stylesheets limitation
- ✅ Zero bundle size (fonts from CDN)
- ✅ Browser caching across sites
- ✅ Automatic WOFF2 optimization

**Drawbacks:**
- ⚠️ External dependency (requires internet)
- ⚠️ Privacy concerns (CDN tracking)
- ⚠️ GDPR compliance considerations

**Alternative:** For privacy-sensitive apps, download fonts and serve locally via `/static/fonts/`

---

## Performance & Optimization

**Principle:** Make UI responsive and efficient at scale

**Common Performance Issues:**
- Slow response times during API calls
- Unnecessary re-renders
- Large payload transfers
- Repeated expensive computations

### Caching Pure Functions

**Pattern:** Cache results of expensive computations that return the same output for the same input

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(param: str) -> dict:
    """
    Cache results for repeated calls.

    Use for:
    - Database lookups
    - Complex calculations
    - API calls with stable results
    """
    # Expensive operation
    result = heavy_processing(param)
    return result

# Use in Gradio
dropdown.change(
    fn=expensive_computation,
    inputs=[dropdown],
    outputs=[output]
)
```

**When to use:**
- ✅ Pure functions (same input → same output)
- ✅ Expensive operations (> 100ms)
- ✅ Frequently called with repeated inputs
- ❌ Functions with side effects
- ❌ Real-time data that must be fresh

---

### Async for I/O-Bound Operations

**Pattern:** Use async/await for operations that wait on external resources

```python
import asyncio
import httpx

async def fetch_data(query: str) -> dict:
    """
    Use async for API calls, database queries, file I/O.

    Allows other requests to be processed while waiting.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/{query}")
        return response.json()

async def process_multiple(queries: list) -> list:
    """Process multiple requests concurrently."""
    tasks = [fetch_data(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return results

# Wire async function (Gradio handles it automatically)
textbox.submit(fn=fetch_data, inputs=[textbox], outputs=[output])
```

**When to use:**
- ✅ External API calls
- ✅ Database queries
- ✅ File reading/writing
- ✅ Multiple concurrent operations
- ❌ CPU-intensive calculations (use multiprocessing instead)

---

### Minimize Payload Size

**Pattern:** Send only what the frontend needs

```python
# ❌ BAD: Sending raw PIL Image repeatedly
def process_image(img):
    processed = apply_filter(img)
    return processed  # Gradio serializes entire image each time

# ✅ GOOD: Base64 encode once, cache result
from functools import lru_cache
import base64
from io import BytesIO

@lru_cache(maxsize=32)
def get_thumbnail(image_path: str) -> str:
    """Cache base64-encoded thumbnails."""
    img = Image.open(image_path)
    img.thumbnail((200, 200))

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    b64 = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/jpeg;base64,{b64}"

# Use cached version
gallery.select(fn=get_thumbnail, inputs=[gallery], outputs=[preview])
```

**Best Practices:**
- ✅ Return only necessary fields from dictionaries
- ✅ Compress images before sending (JPEG quality 85)
- ✅ Use thumbnails for previews
- ✅ Paginate large lists
- ❌ Don't send entire objects when a subset will do

---

### Lazy Loading Components

**Pattern:** Load heavy components only when needed

```python
with gr.Blocks() as demo:
    # ===== ALWAYS VISIBLE =====
    textbox = gr.Textbox()
    submit_btn = gr.Button("Submit")

    # ===== LAZY LOADED =====
    with gr.Column(visible=False) as advanced_panel:
        # Heavy components loaded only when shown
        data_table = gr.DataFrame()
        visualization = gr.Plot()
        export_btn = gr.Button("Export")

    # Toggle visibility
    show_advanced = gr.Checkbox("Show Advanced")

    def toggle_panel(show: bool):
        return gr.Column(visible=show)

    show_advanced.change(
        fn=toggle_panel,
        inputs=[show_advanced],
        outputs=[advanced_panel],
        queue=False
    )
```

**When to use:**
- ✅ Optional advanced features
- ✅ Heavy visualizations
- ✅ Large data tables
- ✅ Debug panels

---

### Performance Checklist

- [ ] Cache pure functions with `@lru_cache`
- [ ] Use `async def` for I/O-bound operations
- [ ] Minimize JSON payload (< 100KB per response)
- [ ] Base64 encode images once, cache them
- [ ] Use `queue=False` for instant UI updates
- [ ] Lazy load heavy components (start with `visible=False`)
- [ ] Compress images (JPEG quality 85, thumbnails for previews)
- [ ] Profile slow functions (use `time.time()` or `cProfile`)

---

## Security Best Practices

**Principle:** Protect your app and users from malicious input and attacks

**Common Security Risks:**
- SQL injection
- Cross-site scripting (XSS)
- Denial of service (DoS)
- Unauthorized access
- Data leaks

### Input Validation

**Pattern:** Always validate and sanitize user input

```python
def safe_process(user_input: str) -> str:
    """Validate user input before processing."""

    # Length validation
    if len(user_input) > 2000:
        return "❌ Input too long (max 2000 characters)"

    if len(user_input.strip()) == 0:
        return "❌ Input cannot be empty"

    # Content validation
    if contains_sql_keywords(user_input):
        return "❌ Invalid characters detected"

    # Type validation
    try:
        validated = validate_and_escape(user_input)
    except ValueError as e:
        return f"❌ Invalid input: {e}"

    # Safe to process
    return process(validated)

def contains_sql_keywords(text: str) -> bool:
    """Check for SQL injection attempts."""
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'SELECT', '--', ';']
    upper_text = text.upper()
    return any(keyword in upper_text for keyword in dangerous)

def validate_and_escape(text: str) -> str:
    """Escape HTML to prevent XSS."""
    import html
    return html.escape(text)
```

**Validation Rules:**
- ✅ Check length limits
- ✅ Validate data types
- ✅ Escape HTML/JavaScript
- ✅ Whitelist allowed characters
- ✅ Reject SQL keywords
- ❌ Never trust user input directly

---

### Rate Limiting

**Pattern:** Prevent abuse by limiting request frequency

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
def expensive_operation(input: str) -> str:
    """
    Limit to 10 calls per minute per IP address.

    Protects against:
    - DoS attacks
    - Excessive API usage
    - Resource exhaustion
    """
    return process(input)

# Alternative: Simple in-memory rate limiting
from collections import defaultdict
from time import time

call_counts = defaultdict(list)

def rate_limited_process(input: str, user_ip: str) -> str:
    """Manual rate limiting implementation."""
    now = time()

    # Clean old entries (older than 60 seconds)
    call_counts[user_ip] = [
        t for t in call_counts[user_ip]
        if now - t < 60
    ]

    # Check limit
    if len(call_counts[user_ip]) >= 10:
        return "⚠️ Rate limit exceeded. Try again in a minute."

    # Record this call
    call_counts[user_ip].append(now)

    return process(input)
```

**Best Practices:**
- ✅ Limit by IP address
- ✅ Different limits for different endpoints
- ✅ Return clear error messages
- ✅ Log rate limit violations
- ❌ Don't make limits too strict (frustrates users)

---

### Authentication & Access Control

**Pattern:** Protect sensitive apps with login

```python
import gradio as gr

# Simple username/password auth
def authenticate(username: str, password: str) -> bool:
    """Validate credentials."""
    # Use environment variables or secure storage
    return username == "admin" and password == "secret123"

# Apply to entire app
with gr.Blocks() as demo:
    # ... your app ...
    pass

demo.launch(auth=authenticate)

# Alternative: More complex auth with sessions
def check_auth(request: gr.Request) -> bool:
    """Check if user is authenticated."""
    return request.session.get("authenticated", False)

with gr.Blocks() as demo:
    login_box = gr.Textbox(label="Password", type="password")
    login_btn = gr.Button("Login")
    protected_content = gr.Column(visible=False)

    def login(password: str):
        if password == "secret":
            return gr.Column(visible=True)
        return gr.Column(visible=False)

    login_btn.click(fn=login, inputs=[login_box], outputs=[protected_content])
```

**Security Levels:**
- 🔓 Public app: No auth needed
- 🔐 Internal tool: Simple password (`auth=function`)
- 🔒 Production app: OAuth, JWT, or external auth service

---

### Prevent XSS (Cross-Site Scripting)

**Pattern:** Escape user-generated content

```python
import html

def safe_display(user_content: str) -> str:
    """Display user content safely."""
    # Escape HTML tags
    escaped = html.escape(user_content)

    # Convert newlines to <br> safely
    formatted = escaped.replace('\n', '<br>')

    return formatted

# Use with gr.HTML
def render_comment(comment: str) -> str:
    safe_comment = safe_display(comment)
    return f'<div class="comment">{safe_comment}</div>'

comment_input = gr.Textbox()
comment_display = gr.HTML()

comment_input.submit(
    fn=render_comment,
    inputs=[comment_input],
    outputs=[comment_display]
)
```

**XSS Prevention Rules:**
- ✅ Escape all user content in HTML
- ✅ Use `html.escape()` for text
- ✅ Validate URLs before rendering links
- ❌ Never use `dangerouslySetInnerHTML` equivalent
- ❌ Don't trust user-provided HTML/JavaScript

---

### Security Checklist

**Before Deployment:**
- [ ] Validate all user inputs (length, type, content)
- [ ] Escape HTML in user-generated content
- [ ] Implement rate limiting (10-100 req/min)
- [ ] Add authentication for sensitive data
- [ ] Use HTTPS in production
- [ ] Set secure CORS policy
- [ ] Log security events (failed auth, rate limits)
- [ ] Keep dependencies updated (`pip list --outdated`)
- [ ] Don't expose stack traces to users
- [ ] Store secrets in environment variables, not code

**Production Security:**
```python
# ✅ GOOD: Environment variables
import os
API_KEY = os.getenv("API_KEY")

# ❌ BAD: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"  # Never do this!
```

---

## Function Design Best Practices

**Principle:** Write functions that are easy to use, debug, and maintain

### Type Hints for Better UI

**Pattern:** Use type hints to improve auto-generated interfaces

```python
def process(
    name: str,                    # → gr.Textbox
    age: int = 25,                # → gr.Number with default
    confirmed: bool = False,      # → gr.Checkbox
    category: str = "A",          # → gr.Textbox with default
) -> dict:
    """
    Type hints help Gradio:
    - Auto-generate appropriate input components
    - Validate types before calling function
    - Show better error messages
    """
    return {
        "name": name.title(),
        "age": age,
        "confirmed": confirmed,
        "category": category
    }

# Gradio automatically creates the right inputs
interface = gr.Interface(fn=process, inputs="auto", outputs="json")
```

**Supported Type Hints:**
```python
str          # → gr.Textbox
int          # → gr.Number
float        # → gr.Number
bool         # → gr.Checkbox
list         # → gr.Textbox (JSON)
dict         # → gr.Textbox (JSON)
PIL.Image    # → gr.Image
np.ndarray   # → gr.Image or gr.Audio
```

---

### Graceful Error Handling

**Pattern:** Never expose stack traces to users

```python
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_handler(input: str) -> str:
    """Handle errors gracefully with user-friendly messages."""
    try:
        # Validate input
        if not input:
            return "⚠️ Please enter some text"

        # Process
        result = process(input)
        return result

    except ValueError as e:
        # Expected errors: show to user
        return f"⚠️ Invalid input: {str(e)}"

    except ConnectionError:
        # Network issues: user-friendly message
        return "❌ Connection failed. Please check your internet and try again."

    except Exception as e:
        # Unexpected errors: log but don't expose
        logger.error(f"Unexpected error in safe_handler: {e}", exc_info=True)
        return "❌ Something went wrong. Our team has been notified."

# Use in Gradio
textbox.submit(fn=safe_handler, inputs=[textbox], outputs=[output])
```

**Error Handling Rules:**
- ✅ Catch specific exceptions first
- ✅ Return user-friendly messages
- ✅ Log unexpected errors with full traceback
- ✅ Notify team of critical errors
- ❌ Never show stack traces to users
- ❌ Don't use bare `except:` (too broad)

---

### Return Simple, Serializable Types

**Pattern:** Return JSON-compatible objects

```python
# ✅ GOOD: Simple, serializable
def get_user_data(user_id: int) -> dict:
    """Return plain dictionaries."""
    return {
        "id": user_id,
        "name": "Alice",
        "email": "alice@example.com",
        "created": "2024-01-15"  # String, not datetime
    }

# ❌ BAD: Complex objects
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email

def get_user_object(user_id: int) -> User:
    """Gradio can't serialize custom classes."""
    return User("Alice", "alice@example.com")  # Won't work!
```

**Serializable Types:**
- ✅ `str`, `int`, `float`, `bool`
- ✅ `list`, `dict`
- ✅ `None`
- ✅ PIL.Image (Gradio handles it)
- ✅ `np.ndarray` (for images/audio)
- ❌ Custom classes
- ❌ `datetime` objects (convert to string)
- ❌ File handles

---

### Function Design Checklist

- [ ] Add type hints to all parameters and return values
- [ ] Use descriptive parameter names
- [ ] Provide sensible defaults
- [ ] Add docstrings explaining what the function does
- [ ] Validate inputs at the start
- [ ] Handle errors gracefully (try/except)
- [ ] Return simple, JSON-serializable types
- [ ] Log errors for debugging
- [ ] Keep functions focused (single responsibility)

---

## Testing Patterns

**Principle:** Test your app to ensure it works reliably

**Why Test:**
- Catch bugs before users do
- Prevent regressions when making changes
- Document expected behavior
- Enable confident refactoring

### Unit Testing Functions

**Pattern:** Test backend logic independently of Gradio

```python
# test_functions.py
import pytest

def process_text(text: str) -> str:
    """Convert text to uppercase."""
    if not text:
        raise ValueError("Text cannot be empty")
    return text.upper()

# Unit tests
def test_process_text_success():
    """Test normal operation."""
    result = process_text("hello")
    assert result == "HELLO"

def test_process_text_empty():
    """Test error handling."""
    with pytest.raises(ValueError, match="cannot be empty"):
        process_text("")

def test_process_text_whitespace():
    """Test edge cases."""
    result = process_text("  hello  ")
    assert result == "  HELLO  "
```

**Run tests:**
```bash
pytest test_functions.py -v
```

---

### Integration Testing with gradio.testing

**Pattern:** Test end-to-end Gradio workflows

```python
# test_app.py
from gradio.testing import Client
import app  # Your file containing the demo

def test_chat_interface():
    """Test the full chat workflow."""
    client = Client(app.demo)

    # Submit a message
    result = client.predict("Hello", api_name="/chat")

    # Verify response
    assert isinstance(result, list)
    assert len(result) > 0
    assert "hello" in result[-1]["content"].lower()

def test_button_state_change():
    """Test state-dependent button."""
    client = Client(app.demo)

    # Initially disabled
    initial_state = client.view_api()
    # ... check button state ...

    # Type text
    result = client.predict("test input", api_name="/update")
    # ... verify button is now enabled ...
```

---

### Simple Smoke Tests

**Pattern:** Quick sanity checks without full test framework

```python
# smoke_test.py
"""Quick manual test of critical paths."""

def test_basic_functionality():
    """Test that core functions work."""
    from app import process_text, update_button_state

    # Test 1: Basic processing
    result = process_text("hello")
    assert result == "HELLO", "Text processing failed"

    # Test 2: State management
    button = update_button_state("test")
    assert button.interactive == True, "Button state failed"

    print("✅ All smoke tests passed")

if __name__ == "__main__":
    test_basic_functionality()
```

**Run:**
```bash
python smoke_test.py
```

---

### Testing Checklist

**Basic Testing (Minimum):**
- [ ] Test all backend functions with expected inputs
- [ ] Test error cases (empty input, invalid types)
- [ ] Test edge cases (very long input, special characters)
- [ ] Manual testing in browser before deployment

**Comprehensive Testing:**
- [ ] Unit tests for all functions (`pytest`)
- [ ] Integration tests with `gradio.testing.Client`
- [ ] Test state management and UI updates
- [ ] Test across different browsers
- [ ] Load testing for production apps
- [ ] Security testing (input validation, XSS)

**Example Test Command:**
```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run only fast tests
pytest tests/ -v -m "not slow"

# Run specific test
pytest tests/test_app.py::test_chat_interface -v
```

---

## Clean Code Structure

**Principle:** Separate UI definition from behavior wiring

### Pattern: Section-Based Organization

```python
with gr.Blocks() as demo:
    # ===== SECTION 1: UI COMPONENTS =====
    # Define all visual components first

    logo = gr.HTML(...)
    chatbot = gr.Chatbot(...)
    textbox = gr.Textbox(...)
    submit_btn = gr.Button(...)
    settings_btn = gr.Button(...)

    # ===== SECTION 2: BINDINGS =====
    # Wire behavior separately

    # Input state management
    textbox.change(fn=update_ui, inputs=[textbox], outputs=[submit_btn], queue=False)

    # Submit handlers
    submit_btn.click(fn=handle_submit, inputs=[textbox, chatbot], outputs=[chatbot, textbox])
    textbox.submit(fn=handle_submit, inputs=[textbox, chatbot], outputs=[chatbot, textbox])

    # Settings
    settings_btn.click(fn=open_settings, ...)
```

**Benefits:**
- ✅ Clear separation: structure vs behavior
- ✅ Easier to read and maintain
- ✅ Can comment/disable bindings without touching UI
- ✅ Matches React/Vue component patterns
- ✅ Easier debugging (know where to look)

### Function Organization

```python
# ===== STATE MANAGEMENT FUNCTIONS =====
def update_button_state(text):
    """Update button based on input."""
    return gr.Button(...)

def toggle_advanced(show):
    """Show/hide advanced options."""
    return gr.Column(visible=show)


# ===== EVENT HANDLERS =====
def handle_submit(message, history):
    """Handle form submission."""
    # ...
    return updated_history, ""

def handle_settings_click():
    """Open settings modal."""
    return gr.Column(visible=True)


# ===== UI DEFINITION =====
with gr.Blocks() as demo:
    # Components...
    # Bindings...
```

**Benefits:**
- ✅ Functions grouped by purpose
- ✅ Clear docstrings
- ✅ Easy to find and modify
- ✅ Testable in isolation

---

## Common Anti-Patterns

### ❌ Anti-Pattern 1: CSS-Based State Management

**Don't:**
```css
/* Bad: CSS can't access Gradio's component state */
.button:has(+ input:empty) {
    opacity: 0.5;
    pointer-events: none;
}
```

**Do:**
```python
# Good: Python has full state access
def update_button(text):
    return gr.Button(interactive=bool(text.strip()))

textbox.change(fn=update_button, inputs=[textbox], outputs=[btn], queue=False)
```

**Why:** CSS can't access Gradio's internal state. Use Python for state-dependent UI.

---

### ❌ Anti-Pattern 2: Forgetting Enter Key Handler

**Don't:**
```python
# Bad: Only handles button click
submit_btn.click(fn=respond, inputs=[textbox], outputs=[chatbot])
```

**Do:**
```python
# Good: Handles both button click and Enter key
submit_btn.click(fn=respond, inputs=[textbox], outputs=[chatbot])
textbox.submit(fn=respond, inputs=[textbox], outputs=[chatbot])
```

**Why:** Users expect Enter key to work. Always wire both.

---

### ❌ Anti-Pattern 3: Using Queue for Instant UI Updates

**Don't:**
```python
# Bad: Slow, unnecessary backend roundtrip
textbox.change(fn=update_ui, inputs=[textbox], outputs=[btn], queue=True)
```

**Do:**
```python
# Good: Instant, no API call
textbox.change(fn=update_ui, inputs=[textbox], outputs=[btn], queue=False)
```

**Why:** `queue=False` = instant client-side update. Use for pure UI changes.

---

### ❌ Anti-Pattern 4: Modifying Components In Place

**Don't:**
```python
# Bad: Doesn't work, Gradio needs new instance
def update_button(text):
    submit_btn.icon = "/new/icon.png"  # Won't work!
    return None
```

**Do:**
```python
# Good: Return new component instance
def update_button(text):
    return gr.Button(icon="/new/icon.png", interactive=True)
```

**Why:** Gradio's reactivity works by replacing components, not mutating them.

---

### ❌ Anti-Pattern 5: Deep CSS Selectors

**Don't:**
```css
/* Bad: Fragile, will break on Gradio updates */
div.gradio-container > div:nth-child(3) > label > span.gradio-button {
    background: blue;
}
```

**Do:**
```css
/* Good: Target your own classes */
.my-submit-btn {
    background: blue;
}
```

```python
btn = gr.Button(elem_classes=["my-submit-btn"])
```

**Why:** Gradio's internal structure can change. Use your own semantic classes.

---

### ❌ Anti-Pattern 6: Fighting the Abstraction

**Don't:**
```python
# Bad: Trying to force ChatInterface to do gr.Blocks work
gr.ChatInterface(
    submit_btn=complex_custom_button_with_state_management,
    css="...100 lines of fragile selectors..."
)
```

**Do:**
```python
# Good: Use the right tier for the job
with gr.Blocks():
    # Build custom layout with full control
    chatbot = gr.Chatbot(...)
    textbox = gr.Textbox(...)
    custom_btn = gr.Button(...)
    # Full state management...
```

**Why:** If you're fighting the framework, you're using the wrong tier.

---

## Quick Reference

### When to Use Each Tier

| Need | Tier 1 | Tier 2 | Tier 3 |
|------|--------|--------|--------|
| Change button text | ✅ | ✅ | ✅ |
| Hide/show component | ✅ | ✅ | ✅ |
| Change placeholder | ✅ | ✅ | ✅ |
| Change colors | ❌ | ✅ | ✅ |
| Adjust spacing | ❌ | ✅ | ✅ |
| Custom border radius | ❌ | ✅ | ✅ |
| Use custom icon | ❌ | ⚠️ | ✅ |
| State-dependent icon | ❌ | ❌ | ✅ |
| Dynamic behavior | ❌ | ❌ | ✅ |
| Custom layouts | ❌ | ❌ | ✅ |

---

### Common Patterns Cheat Sheet

**State-Dependent Button:**
```python
def update_btn(text):
    return gr.Button(icon=get_icon(text), interactive=bool(text))

textbox.change(fn=update_btn, inputs=[textbox], outputs=[btn], queue=False)
```

**Dual Event Handlers:**
```python
btn.click(fn=respond, inputs=[inp, chat], outputs=[chat, inp])
inp.submit(fn=respond, inputs=[inp, chat], outputs=[chat, inp])
```

**Processing State:**
```python
def respond(msg, history):
    history.append({"role": "user", "content": msg})
    yield history, msg, gr.Button(icon="/processing.png")  # Show processing

    response = call_api(msg)
    history.append({"role": "assistant", "content": response})
    yield history, "", gr.Button(icon="/idle.png")  # Reset
```

**Conditional Visibility:**
```python
def toggle(show):
    return gr.Column(visible=show)

checkbox.change(fn=toggle, inputs=[checkbox], outputs=[advanced_panel], queue=False)
```

---

### CSS Best Practices Checklist

- [ ] Use CSS variables for design tokens
- [ ] Organize: main.css → shared.css + fonts.css + design.css
- [ ] Target custom `elem_classes`, not Gradio internals
- [ ] Keep selectors shallow (max 2-3 levels)
- [ ] Support dark mode with `@media (prefers-color-scheme: dark)`
- [ ] Use semantic class names (`.submit-btn`, not `.btn1`)
- [ ] Test after Gradio updates (CSS can break)

---

### gr.Blocks Best Practices Checklist

- [ ] Separate UI components from bindings (two sections)
- [ ] Wire both `.click()` and `.submit()` for forms
- [ ] Use `queue=False` for instant UI updates
- [ ] Return new component instances (don't mutate)
- [ ] Use generators for long operations (>1s)
- [ ] Document why you chose Tier 3 over Tier 1/2
- [ ] Add docstrings to state management functions

---

## Real-World Example: Complete Chat Interface

Putting it all together:

```python
import gradio as gr

# ===== STATE MANAGEMENT =====
def update_submit_button(text):
    """Update submit button state based on input."""
    if text.strip():
        return gr.Button(icon="/icons/send_active.png", interactive=True)
    return gr.Button(icon="/icons/send_disabled.png", interactive=False)


# ===== EVENT HANDLERS =====
def handle_submit(message, history):
    """Handle message submission with processing state."""
    if not message.strip():
        return history, ""

    # Show user message + processing
    history.append({"role": "user", "content": message})
    yield history, message, gr.Button(icon="/icons/processing.png")

    # Call API
    response = call_api(message)

    # Show response + reset
    history.append({"role": "assistant", "content": response})
    yield history, "", gr.Button(icon="/icons/send_disabled.png", interactive=False)


# ===== UI DEFINITION =====
with gr.Blocks(
    css="""
        :root {
            --primary-color: #007AFF;
            --surface-color: #f8f8f8;
            --border-radius: 12px;
        }

        .chat-container {
            max-width: 800px;
            margin: 0 auto;
        }

        .submit-btn {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            padding: 0;
        }
    """,
    title="Chat App"
) as demo:

    # ===== UI COMPONENTS =====
    with gr.Column(elem_classes=["chat-container"]):
        chatbot = gr.Chatbot(
            type="messages",
            height=600,
            show_copy_button=True
        )

        with gr.Row():
            textbox = gr.Textbox(
                placeholder="Send a message...",
                show_label=False,
                scale=1
            )

            submit_btn = gr.Button(
                value="",
                icon="/icons/send_disabled.png",
                interactive=False,
                size="sm",
                elem_classes=["submit-btn"]
            )

    # ===== BINDINGS =====

    # Update button on input change
    textbox.change(
        fn=update_submit_button,
        inputs=[textbox],
        outputs=[submit_btn],
        queue=False
    )

    # Handle submit (button click)
    submit_btn.click(
        fn=handle_submit,
        inputs=[textbox, chatbot],
        outputs=[chatbot, textbox, submit_btn]
    )

    # Handle submit (Enter key)
    textbox.submit(
        fn=handle_submit,
        inputs=[textbox, chatbot],
        outputs=[chatbot, textbox, submit_btn]
    )

demo.launch()
```

---

## SVG Icons for Web Apps

**Principle:** Use SVG for scalable, theme-friendly icons that support dark/light modes

**Why SVG over PNG:**
- ✅ Infinitely scalable (no blur on retina displays)
- ✅ Tiny file size (< 2KB per icon)
- ✅ Easy theming via CSS (night mode support)
- ✅ Single HTTP request with sprites
- ✅ Accessible with ARIA attributes

**Target:** Small icon sets (< 20 icons) with minimal overhead but maximum quality

---

### 1. Create the Icons

| What | Why | Tool |
|------|-----|------|
| **Vector-first** | Keeps file size small, scales clean | Adobe Illustrator, Figma, Inkscape |
| **Keep the artwork simple** | Fewer nodes = faster rendering | – |
| **Export as "SVG" (not PDF)** | Raw XML → easier to edit | – |
| **Set a consistent viewport** | Same width/height for easier CSS | `viewBox="0 0 24 24"` (or whatever your design system uses) |

**Tip**: Export each icon once, then duplicate & tweak in code (e.g., color swaps).

---

### 2. Clean & Optimize

| Step | Command | Notes |
|------|---------|-------|
| **Validate XML** | `xmllint --noout icon.svg` | Catch malformed tags before shipping |
| **Optimize** | `svgo icon.svg -o icon.min.svg` | Removes comments, redundant attributes, converts to `path` only |
| **Keep `viewBox`** | `--enable=removeViewBox=false` (SVGO) | Essential for scaling |
| **Optional: Flatten gradients** | `--enable=cleanupIDs` | Reduces node count |
| **Manual review** | Open `icon.min.svg` in a text editor | Look for stray `id=` or `class=` that you'll never use |

**Result**: `< 2 KB` per icon on average, usually less.

**Example:**
```bash
# Install SVGO
npm install -g svgo

# Optimize single icon
svgo icon.svg -o icon.min.svg

# Batch optimize
svgo -f src/icons/ -o dist/icons/
```

---

### 3. Build an SVG Sprite (Optional but Recommended)

| Reason | How |
|--------|-----|
| **Single HTTP request** | Combine all 20 icons into `sprite.svg` |
| **Reusability** | `<use href="#icon-name">` in your markup |
| **Easy theming** | CSS on the `<use>` element |

**Tool:**
- **CLI**: `svg-sprite --symbol -o dist/sprite.svg src/icons/*.svg`
- **Webpack**: `svg-sprite-loader` (if you're using a bundler)

**If you prefer not to sprite**: keep each icon as an inline component – still fine for < 20.

**Example sprite.svg:**
```xml
<svg xmlns="http://www.w3.org/2000/svg" style="display:none;">
  <symbol id="gear" viewBox="0 0 24 24">
    <path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z"/>
  </symbol>
  <symbol id="close" viewBox="0 0 24 24">
    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
  </symbol>
</svg>
```

---

### 4. Embed Strategy

| Method | Use-case | Example |
|--------|----------|---------|
| **Inline `<svg>`** | Interactive icons (e.g., toggle button) | `<svg class="icon icon-gear" …>…</svg>` |
| **`<use>` from sprite** | Static icons in lists, menus | `<svg class="icon"><use href="#gear"></use></svg>` |
| **`<img src="…">`** | Fallback for very old browsers (IE 9-10) | `<img src="icons/gear.svg" alt="gear">` |
| **CSS `background-image`** | Decorative icons, badges | `.icon-gear { background:url(gear.svg) no-repeat; }` |

**Pick one** for each icon's role.
**Never mix**: e.g., use `<use>` only if you'll animate or change the fill via CSS.

**Gradio Example:**
```python
# Use inline SVG with gr.HTML
gear_icon = gr.HTML('''
    <svg class="icon icon-gear" viewBox="0 0 24 24" aria-label="Settings">
        <path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z"/>
    </svg>
''')

# Or use external SVG file
settings_btn = gr.Button(
    value="",
    icon="/static/icons/gear.svg",  # Will be served by FastAPI
    elem_classes=["icon-btn"]
)
```

---

### 5. Make Icons Theme-/Color-Responsive

**Pattern:** Use CSS variables for dark/light mode support

```html
<!-- 1️⃣ Icon definition (sprite) -->
<svg style="display:none;">
  <symbol id="gear" viewBox="0 0 24 24">
    <path d="M…"></path>
  </symbol>
</svg>

<!-- 2️⃣ Usage -->
<svg class="icon" aria-hidden="true">
  <use href="#gear"></use>
</svg>
```

```css
/* 3️⃣ Theming via CSS vars */
:root {
    --icon-fill: currentColor;
    --icon-stroke: none;
}

.icon use {
    fill: var(--icon-fill);
    stroke: var(--icon-stroke);
}

/* Dark mode */
.theme-dark,
@media (prefers-color-scheme: dark) {
    :root {
        --icon-fill: #ffffff;
    }
}

/* Light mode */
.theme-light,
@media (prefers-color-scheme: light) {
    :root {
        --icon-fill: #000000;
    }
}

/* Hover states */
.icon-btn:hover .icon use {
    fill: var(--color-accent);
}
```

**If you're not using a sprite**, put the `<path>` directly inside `<svg>` and style it the same way.

---

### 6. Accessibility Basics

| What | How |
|------|-----|
| **Decorative icon** | `aria-hidden="true"` |
| **Functional icon** | `role="img"`, `aria-label="…"` or `<title>` |
| **Keyboard focusable** | `tabindex="0"` if the icon triggers an action |
| **Description for complex icons** | `<desc>` or `aria-describedby` (rare for simple icons) |

**Examples:**

```html
<!-- Decorative (with adjacent text) -->
<button>
    <svg class="icon" aria-hidden="true">
        <use href="#close"></use>
    </svg>
    Close
</button>

<!-- Functional (icon only) -->
<button aria-label="Close dialog">
    <svg class="icon" role="img" focusable="false">
        <title>Close</title>
        <use href="#close"></use>
    </svg>
</button>

<!-- Interactive icon -->
<svg class="icon icon-close"
     aria-label="Close dialog"
     role="img"
     tabindex="0"
     onclick="closeDialog()">
    <use href="#close"></use>
</svg>
```

---

### 7. Performance & Caching

| Tip | Why |
|-----|-----|
| **Serve sprite with cache-headers** | `Cache-Control: public, max-age=31536000` |
| **Keep icons under 20 KB** | Quick parse, low DOM size |
| **Avoid `pointer-events="none"` unless intentional** | Might break click area |
| **Use `will-change: transform`** for animated icons | Gives browser a hint to optimize |

**FastAPI Static File Configuration:**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Serve SVG sprite with long cache
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

# Add cache headers in middleware (optional)
@app.middleware("http")
async def add_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.endswith(".svg"):
        response.headers["Cache-Control"] = "public, max-age=31536000"
    return response
```

---

### 8. Testing Checklist

| Test | Tool / Method |
|------|---------------|
| **Render in all target browsers** | Chrome, Firefox, Safari, Edge 18, IE 11 (if needed) |
| **Accessibility audit** | axe-core, Lighthouse "Accessibility" |
| **Performance audit** | Lighthouse "Performance", DevTools "Performance" |
| **Cross-origin** | Ensure all assets (fonts, data URIs) are same-origin or CORS-enabled |
| **Print** | Chrome "Print" preview – SVGs print fine, just double-check size |
| **Dark mode** | Toggle system theme and verify icon colors |
| **Screen readers** | VoiceOver (Mac), NVDA (Windows), JAWS |

---

### 9. Workflow Summary (Quick-Start)

1. **Design** → Export raw SVGs (`icon.svg`).
2. **Validate & Optimize** → `svgo icon.svg -o icon.min.svg`.
3. **Collect** → Place all `icon.min.svg` in `src/icons/`.
4. **Sprite** → `svg-sprite --symbol -o dist/sprite.svg src/icons/*.svg`.
5. **Add to page** → `<svg class="icon"><use href="#icon-name"></use></svg>`.
6. **Style** → CSS variables for theme.
7. **Accessibility** → `aria-label` / `role="img"`.
8. **Deploy** → Serve `sprite.svg` with long cache header.

---

### 10. Migration from PNG to SVG

**For Agent Workbench (current PNG icons → SVG):**

```bash
# Current PNG icons in:
# src/agent_workbench/static/icons/*.png

# 1. Design SVG versions (or convert simple ones)
# Use Figma/Illustrator or online converters for simple shapes

# 2. Optimize
svgo add_chat_icon.svg -o add_chat_icon_96.svg
svgo arrow_up_in_circle_icon.svg -o arrow_up_in_circle_icon_96.svg
# ... etc

# 3. Create sprite (optional)
svg-sprite --symbol -o static/icons/sprite.svg static/icons/*.svg

# 4. Update Python code
# From:
submit_btn = gr.Button(icon="/static/icons/arrow_up_in_circle_icon_96.png")

# To:
submit_btn = gr.Button(icon="/static/icons/arrow_up_in_circle_icon_96.svg")

# Or with sprite + HTML:
submit_btn = gr.HTML('''
    <button class="agent-workbench-submit-btn">
        <svg class="icon" aria-label="Submit">
            <use href="/static/icons/sprite.svg#arrow-up"></use>
        </svg>
    </button>
''')
```

**Benefits for Agent Workbench:**
- ✅ Single source for dark/light mode (no separate icon sets)
- ✅ Crisp on all screen densities
- ✅ Smaller file sizes (20 icons: ~40KB → ~20KB)
- ✅ CSS-controlled colors (matches theme automatically)

---

### Final Quick-Reference Table

| Category | Do It | Why |
|----------|-------|-----|
| **Design** | Keep icons 24×24, simple | Consistency |
| **Export** | SVG, not PNG | Vector |
| **Validate** | `xmllint` | Clean XML |
| **Optimize** | `SVGO` | Small file |
| **Sprite** | Optional | One request |
| **Embed** | Inline or `<use>` | Interactivity vs. static |
| **Theme** | CSS vars | Dark/Light mode |
| **ARIA** | `aria-label` or `aria-hidden` | Screen readers |
| **Cache** | 1-yr max-age | Faster load |
| **Test** | Lighthouse, axe | QA |

**With these steps, you'll have a razor-sharp icon set that's tiny, fast, theme-friendly, and accessible—all for less than a coffee's worth of effort!**

---

## Claude Code Chrome DevTools Integration

**Problem:** Claude Code's Chrome DevTools MCP provides an accessibility tree snapshot, but lacks access to the rich DOM information developers see in the Elements panel (CSS classes, computed styles, dimensions, etc.).

**Solution:** Inject custom JavaScript inspector functions via `evaluate_script` to bridge this gap.

### The Gap: A11y Tree vs Elements Panel

| Feature | MCP Snapshot | Elements Panel |
|---------|--------------|----------------|
| CSS Classes | ❌ | ✅ `agent-workbench-input-bar.svelte-1xp0cw7` |
| Computed Styles | ❌ | ✅ `padding: 12px`, `font: 14px` |
| Element IDs | ❌ | ✅ `#component-24` |
| DOM Hierarchy | Flat a11y tree | ✅ Full nested structure |
| Flexbox Info | ❌ | ✅ All flex containers |

### Injecting Inspector Functions

Run this once per page load to make inspector functions available:

```javascript
// Via mcp__chrome-devtools__evaluate_script
() => {
  // Comprehensive DOM Inspector Function
  window.inspectElement = (selector) => {
    const el = document.querySelector(selector);
    if (!el) return { error: `Element not found: ${selector}` };

    const styles = getComputedStyle(el);
    const rect = el.getBoundingClientRect();

    return {
      // Identity
      tagName: el.tagName,
      id: el.id || null,
      className: el.className || null,

      // Dimensions & Position
      dimensions: {
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        top: Math.round(rect.top),
        left: Math.round(rect.left)
      },

      // Box Model
      boxModel: {
        padding: styles.padding,
        margin: styles.margin,
        border: styles.border,
        boxSizing: styles.boxSizing
      },

      // Typography
      typography: {
        font: styles.font,
        fontSize: styles.fontSize,
        fontFamily: styles.fontFamily,
        fontWeight: styles.fontWeight,
        lineHeight: styles.lineHeight,
        color: styles.color,
        textAlign: styles.textAlign
      },

      // Background & Visual
      visual: {
        backgroundColor: styles.backgroundColor,
        backgroundImage: styles.backgroundImage !== 'none' ? styles.backgroundImage : null,
        borderRadius: styles.borderRadius,
        boxShadow: styles.boxShadow !== 'none' ? styles.boxShadow : null,
        opacity: styles.opacity
      },

      // Layout
      layout: {
        display: styles.display,
        position: styles.position,
        flexDirection: styles.flexDirection,
        justifyContent: styles.justifyContent,
        alignItems: styles.alignItems,
        gap: styles.gap,
        overflow: styles.overflow
      },

      // Hierarchy
      hierarchy: {
        parentTag: el.parentElement?.tagName || null,
        parentClass: el.parentElement?.className?.split(' ')[0] || null,
        childCount: el.children.length,
        childTags: [...el.children].slice(0, 5).map(c => c.tagName)
      },

      // Accessibility
      accessibility: {
        role: el.getAttribute('role') || null,
        ariaLabel: el.getAttribute('aria-label') || null,
        tabIndex: el.tabIndex
      }
    };
  };

  // List all elements matching a selector
  window.inspectAll = (selector) => {
    const elements = document.querySelectorAll(selector);
    return [...elements].map((el, i) => ({
      index: i,
      id: el.id || null,
      className: el.className?.split(' ').slice(0, 3).join(' ') || null,
      dimensions: `${el.offsetWidth}×${el.offsetHeight}`
    }));
  };

  // Find all flex containers (like Flexbox overlay)
  window.findFlexContainers = () => {
    const all = document.querySelectorAll('*');
    const flexContainers = [...all].filter(el => {
      const display = getComputedStyle(el).display;
      return display === 'flex' || display === 'inline-flex';
    });
    return flexContainers.slice(0, 20).map(el => ({
      tag: el.tagName,
      id: el.id || null,
      class: el.className?.split(' ').filter(c => !c.includes('svelte'))[0] || null,
      direction: getComputedStyle(el).flexDirection
    }));
  };

  return { status: 'Inspector functions loaded' };
}
```

### Using the Inspector Functions

**1. `inspectElement(selector)` - Full element details**

```javascript
// Via evaluate_script
() => inspectElement('.agent-workbench-input-bar')
```

Returns:
```json
{
  "tagName": "DIV",
  "id": "component-24",
  "className": "row agent-workbench-input-bar svelte-1xp0cw7",
  "dimensions": { "width": 760, "height": 94 },
  "boxModel": { "padding": "12px", "margin": "0px" },
  "typography": { "font": "14px / 21px Lora, Georgia" },
  "layout": { "display": "flex", "flexDirection": "row" }
}
```

**2. `inspectAll(selector)` - Quick survey of matching elements**

```javascript
() => inspectAll('button')
```

Returns:
```json
[
  { "index": 0, "id": "component-7", "className": "sm primary", "dimensions": "120×40" },
  { "index": 1, "id": "component-26", "className": "sm secondary", "dimensions": "32×32" }
]
```

**3. `findFlexContainers()` - Like DevTools Flexbox overlay**

```javascript
() => findFlexContainers()
```

Returns:
```json
[
  { "tag": "DIV", "id": null, "class": "gradio-container", "direction": "column" },
  { "tag": "DIV", "id": "component-24", "class": "row", "direction": "row" }
]
```

### Workflow: Human-Claude Collaboration

**Before (limited visibility):**
- Human: "Check the input bar styling"
- Claude: Takes screenshot, reads Python source, guesses at CSS

**After (shared visibility):**
- Human: "Check the input bar styling"
- Claude: Runs `inspectElement('.agent-workbench-input-bar')`
- Claude: Sees exact same info as human's Elements panel

**Best Practice:** Inject inspector functions at the start of UI debugging sessions. They persist until page refresh.

### Known Limitation: Screenshot Format Bug

When using `mcp__chrome-devtools__take_screenshot`, always specify `format: "jpeg"` to avoid API Error 400:

```
Error: "Image does not match the provided media type image/jpeg"
```

The MCP server declares images as JPEG but defaults to PNG format. Explicit JPEG format resolves the mismatch.

---

## Summary

**Key Takeaways:**

1. **Use the right tier:** Built-in params → CSS → gr.Blocks
2. **State-dependent UI needs gr.Blocks:** Don't fight with CSS
3. **`queue=False` for instant updates:** No backend needed for UI changes
4. **Always wire both click and submit:** Users expect Enter key to work
5. **Return new components:** Gradio reactivity works by replacement
6. **Organize code:** Separate UI from bindings
7. **Use CSS variables:** Design tokens for consistency
8. **Avoid deep selectors:** Target your own classes

**The Framework in One Sentence:**
> Choose the lowest tier that meets your needs, use CSS variables for design tokens, and use gr.Blocks + `queue=False` for state-dependent UI.

---

**Last Updated:** 2025-11-19
**Source Project:** Agent Workbench (UI-005)
**Contributions:** Team onboarding guide integration, SVG icon best practices, gr.HTML vs gr.Button decision framework, simplified CSS architecture
**License:** MIT
