# UI-005: Agent Workbench Design Implementation - Task List

**Status:** Ready for Implementation
**Created:** 2025-01-27
**Phase:** 4 (Visual Polish)
**Dependencies:** Phase 1-3 complete (routing, chat, settings, sidebar)
**CSS Foundation:** Normalized architecture complete (main.css, shared.css, fonts.css)

---

## Executive Summary

This document provides a comprehensive task list for implementing the Agent Workbench visual design. The design is analyzed from screenshots in `/design/screenshots/` and will be implemented as `agent-workbench-design.css` (separate file for safety, then optionally merged into `shared.css` after validation).

**Strategy:** Incremental implementation with component-by-component validation.

**Design References:**
- `/design/screenshots/Example_main_screen.png` - Main chat interface (idle state)
- `/design/screenshots/Example_expanded_sidebar_left.png` - Sidebar expanded
- `/design/screenshots/Example_settings_screen.png` - Settings modal
- `/design/screenshots/Example_login.png` - Login integration
- `UI-004-target-ux-ref.md` - Design specifications

**Icon Assets:**
All icons are located in `/design/icons/` directory:
- **Main Logo:**
  - `logo_72.png` - Central logo displayed above chat input when idle (72x72px)
- **Main Chat Page:**
  - `add_chat_icon_96.png` - New chat button (96x96px)
  - `view_sidebar_icon_96.png` - Sidebar toggle (96x96px)
  - `arrow_up_in_circle_icon_96.png` - Submit button idle/active state (96x96px)
  - `processing_icon_96.png` - Submit button processing state in textbox (96x96px)
  - `workspaces_icon_96.png` - Processing indicator in chat window (96x96px)
- **Settings Page:**
  - `settings_icon_96.png` - Open settings (96x96px)
  - `close_settings_icon.png` - Close settings modal (96x96px)

### Icon Mapping & Deployment Status

**Source Directory:** `/design/icons/` (design assets)
**Deployment Directory:** `src/agent_workbench/static/icons/` (served via /static/icons/)

| Required Filename | Purpose | Status | Notes |
|-------------------|---------|--------|-------|
| `logo_72.png` | Central logo | ✅ Deployed | Copied to static/icons/ |
| `add_chat_icon_96.png` | New chat button | ⚠️ Missing | Exists as `chat_add_icon_96.png` in design/icons/ |
| `view_sidebar_icon_96.png` | Sidebar toggle | ❌ Not deployed | Available in design/icons/ |
| `arrow_up_in_circle_icon_96.png` | Submit button | ❌ Not deployed | Available in design/icons/ |
| `processing_icon_96.png` | Submit processing state | ❌ Not deployed | Available in design/icons/ |
| `workspaces_icon_96.png` | Chat processing indicator | ❌ Not deployed | Available in design/icons/ |
| `settings_icon_96.png` | Open settings | ❌ Not deployed | Available in design/icons/ |
| `close_settings_icon_96.png` | Close settings modal | ❌ Not deployed | Available in design/icons/ |

**Current Workarounds:**
- Phase 4.2: Using inline SVG icons for sidebar toggle and new chat button
- Icons load without 404 errors but don't match design specifications

**Action Required (Task 4.1.6):**
```bash
# Copy icons from design/ to static/ directory
cp design/icons/chat_add_icon_96.png src/agent_workbench/static/icons/add_chat_icon_96.png
cp design/icons/view_sidebar_icon_96.png src/agent_workbench/static/icons/
cp design/icons/arrow_up_in_circle_icon_96.png src/agent_workbench/static/icons/
cp design/icons/processing_icon_96.png src/agent_workbench/static/icons/
cp design/icons/workspaces_icon_96.png src/agent_workbench/static/icons/
cp design/icons/settings_icon_96.png src/agent_workbench/static/icons/
cp design/icons/close_settings_icon_96.png src/agent_workbench/static/icons/
```

---

## Design Analysis from Screenshots

### Main Screen (Example_main_screen.png)

**Visual Characteristics:**
- **Background:** Very light gray (#f5f5f5 or #f8f8f8)
- **Layout:** Centered, floating, minimal
- **Logo:** Large Agent Workbench logo (logo_72.png), center-top, prominent when idle
- **Whitespace:** Generous padding, breathing room
- **Window:** macOS-style with traffic lights (red/yellow/green dots)

**Top Navigation (Top-Left):**
- Sidebar toggle icon (`view_sidebar_icon_96.png`)
- New chat icon (`add_chat_icon_96.png` - red circle with plus)
- Both appear to be ~32px icons with subtle hover states

**Chat Input Bar (Bottom-Center):**
- Width: ~600-800px, centered
- Background: White with subtle shadow
- Border-radius: 12px
- Height: ~48px
- Components (left to right):
  1. Globe icon (web search toggle) - Blue (#007AFF)
  2. Text input "Send a message" - Light gray placeholder
  3. Model selector "gpt-oss:20b" - Dropdown with chevron
  4. Submit button - Circular (32px), gray when disabled

**Typography:**
- Font family: Clean, modern (likely Ubuntu per spec)
- Input text: ~15px
- Model selector: ~13px

### Sidebar Expanded (Example_expanded_sidebar_left.png)

**Sidebar Characteristics:**
- Width: ~280px
- Background: White
- Border-right: 1px solid light gray
- Shadow: Subtle right shadow
- Position: Fixed left, slides in/out
- Z-index: High (above main content)

**Sidebar Header:**
- "New Chat" button - Red circle icon + text
- Padding: 16px

**Conversation List:**
- Each item: Single line, truncated with "..."
- Text color: Dark gray (#333)
- Hover: Light gray background
- Active: Slightly darker background
- Font-size: 14px
- Padding: 8px 16px
- No visible dividers (clean list)

**Date Grouping:**
- "This week" header visible in screenshot
- Headers appear to be subtle (gray, small font)

### Settings Screen (Example_settings_screen.png)

**Settings Modal:**
- Width: ~600px
- Background: White
- Border-radius: 12px (rounded corners)
- Shadow: Strong shadow (0 8px 32px rgba(0,0,0,0.12))
- Position: Centered overlay
- Padding: 24px

**Header:**
- "Settings" title - Left-aligned, ~18px bold
- X close button - Top-right corner (32px clickable area)
- macOS traffic lights (red/yellow/green) top-left

**User Profile Section:**
- Username "sytse" - Bold, ~16px
- Email "sytse@schaaaf.nl" - Gray, ~14px
- Three buttons: "Upgrade" (dark), "Manage" (outline), "Sign out" (outline)
- Avatar icon - Right side (robot icon, ~48px)

**Settings Sections:**
- Each section has icon + title + description
- Toggles: iOS-style (rounded, animated)
- Sliders: Custom styled with value labels
- Spacing: 20px between sections
- Dividers: Subtle gray lines (1px, #e0e0e0)

**Toggle Switch Design:**
- Width: 44px
- Height: 24px
- Border-radius: 12px (pill shape)
- Off state: Light gray background
- On state: Blue background (#007AFF)
- Knob: White circle, 20px, smooth transition

---

## CSS Architecture Decision

**Create:** `static/assets/css/agent-workbench-design.css` (~400 lines)

**Import Pattern:**
```css
/* main.css */
@import url('fonts.css');
@import url('shared.css');
@import url('agent-workbench-design.css');  /* NEW - Agent Workbench visual layer */
```

**Why Separate File:**
- ✅ Safe to test without breaking existing UI
- ✅ Easy to enable/disable with feature flag
- ✅ Clear separation: functional (shared.css) vs visual (agent-workbench-design.css)
- ✅ Can merge into shared.css later once validated

**Alternative (if preferred):**
- Merge directly into `shared.css` (increases from 148 → ~550 lines)

---

## Gradio Component Architecture Decision

### gr.ChatInterface vs gr.Chatbot

**Decision:** Use `gr.ChatInterface` instead of `gr.Chatbot` for the main chat page.

**Rationale:**

**gr.ChatInterface** provides:
- ✅ **Integrated submit button in textbox** - Matches Agent Workbench design (arrow_up_in_circle_icon_96.png inside input)
- ✅ **Built-in message handling** - Automatic user/assistant message flow
- ✅ **Streaming support** - Native support for streaming responses with typing indicators
- ✅ **State management** - Built-in conversation history management
- ✅ **Better UX pattern** - Single-line input with integrated controls (like ChatGPT, Agent Workbench, Claude)

**gr.Chatbot** provides:
- ❌ **Separate input component** - Requires separate gr.Textbox + gr.Button (less integrated)
- ❌ **Manual wiring** - Need to manually wire submit button to input field
- ❌ **Additional complexity** - More code to achieve same UX

**Implementation Pattern:**
```python
# ui/pages/chat.py (NEW PATTERN with gr.ChatInterface)

with gr.Blocks() as chat_page:
    chatinterface = gr.ChatInterface(
        fn=chat_handler,
        chatbot=gr.Chatbot(elem_classes=["agent-workbench-messages"]),
        textbox=gr.Textbox(
            placeholder="Send a message",
            elem_classes=["agent-workbench-message-input"],
            show_label=False,
            submit_btn=gr.Button(
                icon="/design/icons/arrow_up_in_circle_icon_96.png",
                elem_classes=["agent-workbench-submit-btn"]
            )
        ),
        elem_classes=["agent-workbench-chat-interface"],
        # Additional controls can be added with additional_inputs
        additional_inputs=[
            gr.Checkbox(label="Web Search", elem_classes=["agent-workbench-web-search"]),
            gr.Dropdown(label="Model", elem_classes=["agent-workbench-model-selector"])
        ]
    )
```

**Benefits for Agent Workbench Design:**
1. Submit button naturally sits inside textbox (design requirement)
2. Processing states handled automatically (gray → black → processing_icon_96.png)
3. Message streaming built-in (typing indicators, cursor animation)
4. Cleaner component tree (less nested HTML)
5. Better accessibility (proper ARIA labels, keyboard navigation)

**Migration Note:**
Existing `gr.Chatbot` implementations should be refactored to `gr.ChatInterface` during Phase 4.11 integration.

---

## Gradio Customization Strategy: The Three-Tier Framework

**Source:** Gradio expert consultation (2025-01-27)
**Purpose:** Practical decision framework for UI customization within Gradio's constraints

### The Three Tiers

When customizing Gradio components, choose the right abstraction level:

#### **Tier 1: Built-in Parameters** ✅ Use First
**When:** You need simple, documented changes
**Examples:** Text labels, hiding components, basic configs
**Effort:** Minimal (1 parameter change)
**Stability:** Highest (official API, won't break on updates)

```python
# Good fit for Tier 1
gr.ChatInterface(
    submit_btn="Send Message",  # Just change text
    show_submit=False,          # Just hide button
    placeholder="Type here...",  # Simple text change
)
```

**Use for:**
- Changing button/label text
- Showing/hiding components
- Setting placeholders
- Basic value initialization

---

#### **Tier 2: CSS Overrides** ⚠️ Use for Visual Tweaks
**When:** Built-in params insufficient, but component structure is fine
**Examples:** Colors, spacing, borders, fonts
**Effort:** Low to Medium (write CSS, test selectors)
**Stability:** Medium (can break if Gradio changes class names)

```python
# Good fit for Tier 2
gr.ChatInterface(
    fn=handler,
    css="""
    .agent-workbench-submit-btn {
        background: black;
        border-radius: 50%;
        padding: 8px;
    }
    """,
    textbox=gr.Textbox(elem_classes=["agent-workbench-input"])
)
```

**Use for:**
- Color changes
- Spacing/padding adjustments
- Border styling
- Font sizes
- Simple hover effects

**Avoid:**
- Deep selector chains (`.gradio-app > div > div > ...`)
- Relying on Gradio's internal class names
- Trying to change component behavior

---

#### **Tier 3: gr.Blocks** 🔧 Use for Full Control
**When:** Need custom behavior, layout, or state-dependent UI
**Examples:** Custom icons, dynamic states, complex layouts
**Effort:** High (manual wiring, state management, more code)
**Stability:** Highest (you control the structure)

```python
# Good fit for Tier 3
with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages")

    with gr.Row(elem_classes=["input-bar"]):
        textbox = gr.Textbox(show_label=False)

        # FULL control over button
        submit_btn = gr.Button(
            value="",
            icon="/static/icons/arrow.png",  # Custom icon
            elem_classes=["custom-btn"],
            interactive=False  # Start disabled
        )

    # Manual state management
    def update_button(text):
        if text.strip():
            return gr.Button(
                icon="/static/icons/arrow_active.png",
                interactive=True
            )
        return gr.Button(
            icon="/static/icons/arrow_disabled.png",
            interactive=False
        )

    textbox.change(fn=update_button, inputs=[textbox], outputs=[submit_btn])
    submit_btn.click(fn=handler, inputs=[textbox, chatbot], outputs=[chatbot, textbox])
```

**Use for:**
- Custom icons
- State-dependent UI (disabled → active → processing)
- Icon swapping based on conditions
- Custom click behavior
- Complex layouts
- Multi-component interactions

---

### Decision Framework

For any customization need, ask these questions in order:

**Q1: Is there a built-in parameter for this?**
- Check Gradio docs for the component
- Look for simple props (text, show/hide, placeholder, etc.)
- ✅ If YES → **Use Tier 1** (built-in parameter)
- ❌ If NO → Continue to Q2

**Q2: Is this purely visual (no behavior change)?**
- Only changing colors, spacing, borders, fonts?
- No state-dependent changes needed?
- No icon swapping or dynamic content?
- ✅ If YES → **Use Tier 2** (CSS)
- ❌ If NO → Continue to Q3

**Q3: Do you need custom behavior or dynamic UI?**
- State-dependent changes (disabled/active states)?
- Custom icons or icon swapping?
- Custom click handlers or event logic?
- Different layout than Gradio provides?
- ✅ If YES → **Use Tier 3** (gr.Blocks)

---

### Quick Reference Matrix

| Customization Need | Tier 1 | Tier 2 | Tier 3 |
|-------------------|--------|--------|--------|
| Change button text | ✅ | ✅ | ✅ |
| Hide/show component | ✅ | ✅ | ✅ |
| Change placeholder | ✅ | ✅ | ✅ |
| Change colors | ❌ | ✅ | ✅ |
| Adjust spacing/padding | ❌ | ✅ | ✅ |
| Custom border radius | ❌ | ✅ | ✅ |
| Use custom icon | ❌ | ⚠️ | ✅ |
| State-dependent icon | ❌ | ❌ | ✅ |
| Disabled → active states | ❌ | ❌ | ✅ |
| Custom click behavior | ❌ | ❌ | ✅ |
| Complex layouts | ❌ | ❌ | ✅ |

**Legend:**
- ✅ **Supported** - Good fit for this tier
- ⚠️ **Possible but fragile** - Can work but may break
- ❌ **Not supported** - Wrong tier for this need

---

### Practical Examples

#### **Example 1: Submit Button with State-Dependent Icon**

**Requirement:**
- Custom arrow icon
- Gray when disabled (no text in input)
- Black when active (text present)
- Animated when processing

**Analysis:**
- ❌ Tier 1: No built-in param for icon swapping
- ❌ Tier 2: CSS can't reliably detect Gradio's text state
- ✅ **Tier 3 required** - Need state management + icon swapping

**Implementation:** See Tier 3 code example above

---

#### **Example 2: Change Submit Button Color**

**Requirement:**
- Just make the button blue instead of default

**Analysis:**
- ❌ Tier 1: No color parameter in ChatInterface
- ✅ **Tier 2 sufficient** - Pure visual change

**Implementation:**
```python
gr.ChatInterface(
    fn=handler,
    css=".submit-btn { background: #007AFF !important; }",
    textbox=gr.Textbox(elem_classes=["my-input"])
)
```

---

#### **Example 3: Change Placeholder Text**

**Requirement:**
- Change "Type a message..." to "Ask me anything..."

**Analysis:**
- ✅ **Tier 1 sufficient** - Built-in parameter exists

**Implementation:**
```python
gr.ChatInterface(
    fn=handler,
    placeholder="Ask me anything..."
)
```

---

### Common Pitfalls to Avoid

**❌ Fighting the abstraction:**
```python
# Bad: Trying to force ChatInterface to do Blocks-level work
gr.ChatInterface(
    submit_btn=complex_custom_button_with_states,  # Won't work
    css="...fragile deep selectors..."
)
```

**✅ Using the right tool:**
```python
# Good: Recognize when to drop to gr.Blocks
with gr.Blocks():
    # Build with full control
    ...
```

**❌ CSS overreach:**
```css
/* Bad: Trying to do stateful logic with CSS */
.gradio-send button::after {
    content: url('/icon.png');  /* Fragile, state-blind */
}
```

**✅ State management in Python:**
```python
# Good: Manage state properly with gr.Blocks
def update_icon(text):
    return gr.Button(icon=get_appropriate_icon(text))
```

**❌ Deep CSS selectors:**
```css
/* Bad: Fragile, will break on Gradio updates */
div.gradio-container > div:nth-child(3) > label > span {
    /* Relies on Gradio's internal structure */
}
```

**✅ Semantic classes:**
```css
/* Good: Target your own classes */
.agent-workbench-input {
    /* Stable, under your control */
}
```

---

### Guidelines for Agent Workbench

**When implementing UI-005 phases:**

1. **Always start with Tier 1** - Check Gradio docs first
2. **Use Tier 2 for visual polish** - Colors, spacing, borders
3. **Only use Tier 3 when necessary** - Custom behavior, state-dependent UI
4. **Don't fight Gradio** - If it feels hard, you're probably using wrong tier
5. **Document tier choice** - Note why you chose Tier 2 vs Tier 3

**Signals you need Tier 3:**
- "I wish I could swap this icon when..."
- "The button should do X when Y happens..."
- "I need different icons for different states..."
- "I want to position components differently..."

**Signals Tier 2 is enough:**
- "I just want it blue instead of gray..."
- "I need more padding..."
- "I want rounded corners..."

**Signals Tier 1 is enough:**
- "I just want to change the label..."
- "I just want to hide this..."
- "I just want different placeholder text..."

---

## Tier 3 Implementation Patterns: Reusable Code Templates

**Source:** Gradio expert patterns (2025-01-27)
**Purpose:** Production-tested patterns for common Tier 3 use cases

### Pattern 1: State-Dependent Button (Icon Swapping)

**Use case:** Button icon/state changes based on input (disabled → active → processing)

**Example:** Submit button with arrow icon that activates when user types

#### **Complete Implementation**

```python
import gradio as gr

def respond(message, chat_history):
    """
    Handle message submission.

    Returns:
        tuple: (updated_chat_history, cleared_input)
    """
    if not message.strip():
        return chat_history, ""

    # Add user message
    chat_history.append({"role": "user", "content": message})

    # Call API
    response = call_workflow_api(message)

    # Add assistant message
    chat_history.append({"role": "assistant", "content": response})

    return chat_history, ""  # Update chat, clear input


def update_button_state(text):
    """
    Update button icon and interactive state based on input.

    Args:
        text: Current textbox content

    Returns:
        gr.Button: Updated button with new icon/state
    """
    if text.strip():
        # Has text → active state
        return gr.Button(
            icon="/static/icons/arrow_active.png",
            interactive=True
        )
    else:
        # Empty → disabled state
        return gr.Button(
            icon="/static/icons/arrow_disabled.png",
            interactive=False
        )


with gr.Blocks(css="""
    .custom-submit-btn {
        min-width: 32px !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 50% !important;
        padding: 0 !important;
    }

    .custom-submit-btn img {
        width: 20px;
        height: 20px;
    }
""") as demo:

    # ===== UI COMPONENTS =====
    chatbot = gr.Chatbot(type="messages")

    with gr.Row():
        textbox = gr.Textbox(
            placeholder="Type a message...",
            show_label=False,
            scale=1  # Takes remaining space
        )

        submit_btn = gr.Button(
            value="",
            icon="/static/icons/arrow_disabled.png",  # Start disabled
            interactive=False,
            size="sm",
            elem_classes=["custom-submit-btn"]
        )

    # ===== BINDINGS =====

    # Update button on every keystroke (instant, no backend queue)
    textbox.change(
        fn=update_button_state,
        inputs=[textbox],
        outputs=[submit_btn],
        queue=False  # KEY: instant UI update
    )

    # Handle submit (button click)
    submit_btn.click(
        fn=respond,
        inputs=[textbox, chatbot],
        outputs=[chatbot, textbox]
    )

    # Handle submit (Enter key)
    textbox.submit(
        fn=respond,
        inputs=[textbox, chatbot],
        outputs=[chatbot, textbox]
    )

demo.launch()
```

#### **Key Components Explained**

**1. Dual Event Handlers (Critical!)**
```python
submit_btn.click(fn=respond, ...)  # Mouse click
textbox.submit(fn=respond, ...)    # Enter key
```
✅ **Always wire BOTH** - users expect both to work

**2. Dynamic State with `.change()` + `queue=False`**
```python
textbox.change(
    fn=update_button_state,
    inputs=[textbox],
    outputs=[submit_btn],
    queue=False  # Instant update, no API call
)
```
✅ **`queue=False`** = instant UI update (fires on every keystroke)
✅ No backend roundtrip needed for UI-only changes

**3. Return Updated Component**
```python
def update_button_state(text):
    return gr.Button(
        icon="/new/icon.png",
        interactive=True  # Enable/disable
    )
```
✅ Return **new component instance** with updated properties
✅ Gradio automatically replaces the old button

**4. Tuple Returns for Multiple Outputs**
```python
def respond(message, chat_history):
    # ...process...
    return chat_history, ""  # (updated_chat, cleared_input)
```
✅ Order matches `outputs=[chatbot, textbox]`
✅ `""` clears the textbox after submit

---

### Pattern 2: Processing State (with Generator)

**Use case:** Show processing indicator during async operations

```python
def respond_with_processing(message, chat_history):
    """
    Handle message with processing state feedback.

    Uses generator (yield) to show intermediate states.
    """
    if not message.strip():
        return chat_history, ""

    # Step 1: Show user message + processing indicator
    chat_history.append({"role": "user", "content": message})
    yield chat_history, message, gr.Button(icon="/static/icons/processing.png")

    # Step 2: Call API (this takes time)
    response = call_workflow_api(message)

    # Step 3: Show final result + reset button
    chat_history.append({"role": "assistant", "content": response})
    yield chat_history, "", gr.Button(icon="/static/icons/arrow_disabled.png")


# Binding with 3 outputs (chat, textbox, button)
submit_btn.click(
    fn=respond_with_processing,
    inputs=[textbox, chatbot],
    outputs=[chatbot, textbox, submit_btn]  # 3 outputs!
)
```

**When to use generators:**
- ✅ Long-running operations (API calls > 1s)
- ✅ Want to show intermediate states
- ✅ Streaming responses
- ❌ Simple, instant operations (use regular functions)

---

### Pattern 3: Conditional Visibility

**Use case:** Show/hide components based on state

```python
def toggle_advanced_options(show_advanced):
    """Toggle visibility of advanced settings."""
    if show_advanced:
        return gr.Column(visible=True)
    else:
        return gr.Column(visible=False)


with gr.Blocks() as demo:
    show_advanced = gr.Checkbox(label="Show Advanced Options")

    advanced_options = gr.Column(visible=False)
    with advanced_options:
        temperature = gr.Slider(...)
        max_tokens = gr.Slider(...)

    # Toggle visibility
    show_advanced.change(
        fn=toggle_advanced_options,
        inputs=[show_advanced],
        outputs=[advanced_options],
        queue=False  # Instant toggle
    )
```

---

### Pattern 4: Clean Code Structure

**Best practice:** Separate UI definition from behavior wiring

```python
with gr.Blocks() as demo:
    # ===== SECTION 1: UI COMPONENTS =====
    # Define all components first
    chatbot = gr.Chatbot(...)
    textbox = gr.Textbox(...)
    submit_btn = gr.Button(...)
    settings_btn = gr.Button(...)

    # ===== SECTION 2: BINDINGS =====
    # Wire behavior separately
    textbox.change(fn=update_ui, ...)
    submit_btn.click(fn=handle_submit, ...)
    settings_btn.click(fn=open_settings, ...)
```

**Benefits:**
- ✅ Clear separation of structure vs behavior
- ✅ Easier to read and maintain
- ✅ Can comment/disable bindings without touching UI
- ✅ Matches React/Vue component patterns

---

### Common Patterns Summary

| Pattern | Use Case | Key Feature | When to Use |
|---------|----------|-------------|-------------|
| **State-Dependent Button** | Icon/state changes on input | `.change()` + `queue=False` | Button depends on input state |
| **Processing State** | Show loading/processing | Generator (yield) | Long operations (>1s) |
| **Conditional Visibility** | Show/hide components | `visible=True/False` | Dynamic UI layouts |
| **Dual Event Handlers** | Click + Enter | Both `.click()` and `.submit()` | All input forms |

---

### Anti-Patterns to Avoid

**❌ Don't: Try to manage state with CSS**
```css
/* Bad: CSS can't access Gradio state */
.button:has(+ input:empty) { display: none; }
```

**✅ Do: Manage state with Python**
```python
# Good: Python has full state access
textbox.change(fn=update_button, ...)
```

---

**❌ Don't: Forget Enter key handler**
```python
# Bad: Only handles button click
submit_btn.click(fn=respond, ...)
```

**✅ Do: Wire both click and submit**
```python
# Good: Handles both button and Enter
submit_btn.click(fn=respond, ...)
textbox.submit(fn=respond, ...)  # Enter key
```

---

**❌ Don't: Use queue for instant UI updates**
```python
# Bad: Slow, unnecessary backend roundtrip
textbox.change(fn=update_ui, ..., queue=True)
```

**✅ Do: Use queue=False for instant feedback**
```python
# Good: Instant, no API call needed
textbox.change(fn=update_ui, ..., queue=False)
```

---

**❌ Don't: Modify components in place**
```python
# Bad: Doesn't work, Gradio needs new instance
def update_button(text):
    submit_btn.icon = "/new/icon.png"  # Won't work!
    return None
```

**✅ Do: Return new component instance**
```python
# Good: Return updated component
def update_button(text):
    return gr.Button(icon="/new/icon.png")
```

---

### Quick Reference: When to Use Each Pattern

**State-Dependent Button:**
- Submit button that activates when input has text ✅
- Icon that changes based on mode selection ✅
- Button that shows different states (idle/active/processing) ✅

**Generator Pattern:**
- API calls that take >1 second ✅
- Streaming responses ✅
- Multi-step operations with feedback ✅

**Conditional Visibility:**
- Advanced options toggle ✅
- Different UIs for different modes ✅
- Progressive disclosure ✅

**Simple Function Return:**
- Instant operations (<100ms) ✅
- Pure UI state changes ✅
- Form submissions ✅

---

## Implementation Tasks

### Phase 4.1: Foundation & Variables (Week 1, Day 1-2)

**Goal:** Set up CSS file structure and design system variables

#### Task 4.1.1: Create File Structure
- [ ] Create `static/assets/css/agent-workbench-design.css`
- [ ] Add header comment with design attribution
- [ ] Import in `main.css`: `@import url('agent-workbench-design.css');`
- [ ] Update `sw.js` to cache `agent-workbench-design.css`
- [ ] Test file loads correctly (check DevTools Network tab)

**File:** `static/assets/css/agent-workbench-design.css` (initial structure)
```css
/*
 * Agent Workbench Design Layer
 *
 * Visual design implementation based on:
 * - /design/screenshots/Example_main_screen.png
 * - /design/screenshots/Example_expanded_sidebar_left.png
 * - /design/screenshots/Example_settings_screen.png
 *
 * This file contains Agent Workbench-specific visual styling.
 * Functional styles remain in shared.css.
 */

/* ===== DESIGN TOKENS ===== */
/* Add CSS variables here */

/* ===== LAYOUT ===== */
/* Centered floating chat layout */

/* ===== COMPONENTS ===== */
/* Individual UI components */
```

#### Task 4.1.2: Define CSS Variables (Design Tokens)
- [ ] Extract colors from screenshots (use color picker)
- [ ] Define spacing scale (4px, 8px, 12px, 16px, 20px, 24px)
- [ ] Define typography scale
- [ ] Define shadow styles
- [ ] Define border-radius values
- [ ] Define transition timings

**Code:**
```css
:root {
    /* ===== COLORS ===== */

    /* Backgrounds */
    --awb-bg: #f8f8f8;
    --awb-surface: #ffffff;
    --awb-sidebar-bg: #ffffff;

    /* Text */
    --awb-text-primary: #333333;
    --awb-text-secondary: #666666;
    --awb-text-tertiary: #999999;
    --awb-placeholder: #bbbbbb;

    /* Borders */
    --awb-border: #e0e0e0;
    --awb-border-light: #f0f0f0;

    /* Accent colors */
    --awb-blue: #007AFF;
    --awb-red: #FF3B30;
    --awb-green: #34C759;
    --awb-gray: #8E8E93;

    /* Button states */
    --awb-btn-disabled: #e0e0e0;
    --awb-btn-hover: #f5f5f5;
    --awb-btn-active: #000000;

    /* ===== SPACING ===== */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 12px;
    --space-lg: 16px;
    --space-xl: 20px;
    --space-2xl: 24px;
    --space-3xl: 32px;
    --space-4xl: 40px;

    /* ===== TYPOGRAPHY ===== */
    --font-size-xs: 12px;
    --font-size-sm: 13px;
    --font-size-base: 15px;
    --font-size-lg: 16px;
    --font-size-xl: 18px;

    /* ===== SHADOWS ===== */
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.10);
    --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.12);

    /* ===== BORDERS ===== */
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 9999px;

    /* ===== TRANSITIONS ===== */
    --transition-fast: 150ms ease;
    --transition-base: 250ms ease;
    --transition-slow: 350ms ease;
}
```

#### Task 4.1.3: Dark Mode Variables
- [ ] Analyze dark mode requirements from UI-004-target-ux-ref.md
- [ ] Define dark mode color palette
- [ ] Create `@media (prefers-color-scheme: dark)` block
- [ ] Test auto-detection with OS settings
- [ ] Create manual override classes (`.light-mode`, `.dark-mode`)

**Code:**
```css
@media (prefers-color-scheme: dark) {
    :root {
        /* Dark mode colors */
        --awb-bg: #1a1a1a;
        --awb-surface: #2a2a2a;
        --awb-sidebar-bg: #242424;

        --awb-text-primary: #e0e0e0;
        --awb-text-secondary: #a0a0a0;
        --awb-text-tertiary: #707070;
        --awb-placeholder: #505050;

        --awb-border: #404040;
        --awb-border-light: #333333;

        /* Accent colors stay same or adjust slightly */
    }
}

/* Manual theme overrides */
body.light-mode {
    /* Force light theme */
}

body.dark-mode {
    /* Force dark theme */
}
```

**Validation:**
- [ ] Open DevTools → Elements → Computed styles
- [ ] Verify CSS variables are defined
- [ ] Toggle dark mode in OS → verify variables update
- [ ] Screenshot comparison with design

**Estimated Time:** 2-3 hours

---

### Phase 4.2: Main Layout (Week 1, Day 2-3)

**Goal:** Implement centered floating chat layout

#### Task 4.2.1: Page Background
- [ ] Set body background to `--awb-bg`
- [ ] Remove default Gradio background
- [ ] Test background covers full viewport

**Code:**
```css
body {
    background: var(--awb-bg);
    font-family: var(--font-family); /* From fonts.css */
}

/* Override Gradio default */
.gradio-container {
    background: transparent !important;
}
```

#### Task 4.2.2: Centered Chat Container
- [ ] Create `.agent-workbench-chat-container` class
- [ ] Center horizontally with max-width
- [ ] Add vertical padding for breathing room
- [ ] Test on desktop (1920px), tablet (768px), mobile (375px)

**Code:**
```css
.agent-workbench-chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: var(--space-4xl) var(--space-xl);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    gap: var(--space-2xl);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .agent-workbench-chat-container {
        padding: var(--space-2xl) var(--space-lg);
    }
}

@media (max-width: 480px) {
    .agent-workbench-chat-container {
        padding: var(--space-xl) var(--space-md);
    }
}
```

#### Task 4.2.3: Main Logo (Idle State)
- [ ] Style `.agent-workbench-logo` container
- [ ] Center logo horizontally
- [ ] Add vertical padding
- [ ] Prepare for fade animation (next phase)

**Code:**
```css
.agent-workbench-logo {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: var(--space-4xl) 0;
    opacity: 1;
    transition: opacity var(--transition-base);
}

.agent-workbench-logo img {
    width: 72px;
    height: 72px;
    /* Logo from design: logo_72.png */
}

/* Hidden state (for processing) - implemented in Phase 4.3 */
.agent-workbench-logo.hidden {
    opacity: 0;
    pointer-events: none;
}
```

**Validation:**
- [ ] Logo appears centered
- [ ] Layout responsive on mobile
- [ ] Background color matches design
- [ ] No horizontal scroll on any viewport size

**Estimated Time:** 2-3 hours

---

### Phase 4.3: Chat Input Bar (Week 1, Day 3-4)

**Goal:** Implement bottom-centered input bar with integrated controls

#### Task 4.3.1: Input Bar Container
- [ ] Create `.agent-workbench-input-bar` class
- [ ] Position sticky at bottom
- [ ] White background with shadow
- [ ] Rounded corners (12px)
- [ ] Flexbox layout for children

**Code:**
```css
.agent-workbench-input-bar {
    position: sticky;
    bottom: var(--space-xl);
    width: 100%;
    max-width: 800px;
    margin: 0 auto;

    background: var(--awb-surface);
    border: 1px solid var(--awb-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);

    padding: var(--space-md);
    display: flex;
    align-items: center;
    gap: var(--space-md);

    transition: box-shadow var(--transition-fast);
}

.agent-workbench-input-bar:focus-within {
    box-shadow: var(--shadow-lg);
    border-color: var(--awb-blue);
}

@media (max-width: 768px) {
    .agent-workbench-input-bar {
        bottom: var(--space-md);
        border-radius: var(--radius-md);
    }
}
```

#### Task 4.3.2: Web Search Toggle (Globe Icon)
- [ ] Style globe icon button
- [ ] Blue color when active
- [ ] Gray when inactive
- [ ] Smooth transition
- [ ] Touch-friendly size (44x44px min for mobile)

**Code:**
```css
.agent-workbench-web-search {
    width: 32px;
    height: 32px;
    min-width: 32px; /* Prevent shrinking */

    display: flex;
    align-items: center;
    justify-content: center;

    border: none;
    background: transparent;
    border-radius: var(--radius-sm);

    color: var(--awb-gray);
    cursor: pointer;

    transition: all var(--transition-fast);
}

.agent-workbench-web-search:hover {
    background: var(--awb-btn-hover);
}

.agent-workbench-web-search.active {
    color: var(--awb-blue);
    background: rgba(0, 122, 255, 0.1);
}

/* Icon size */
.agent-workbench-web-search svg,
.agent-workbench-web-search img {
    width: 20px;
    height: 20px;
}

/* Mobile touch target */
@media (max-width: 768px) {
    .agent-workbench-web-search {
        width: 44px;
        height: 44px;
    }
}
```

#### Task 4.3.3: Message Input Field
- [ ] Style text input
- [ ] Flexible width (flex: 1)
- [ ] No border (borderless design)
- [ ] Placeholder styling
- [ ] Focus state

**Code:**
```css
.agent-workbench-message-input {
    flex: 1;

    border: none;
    background: transparent;
    outline: none;

    font-size: var(--font-size-base);
    color: var(--awb-text-primary);
    font-family: var(--font-family);

    padding: var(--space-sm) 0;
}

.agent-workbench-message-input::placeholder {
    color: var(--awb-placeholder);
}

/* Remove autofill background */
.agent-workbench-message-input:-webkit-autofill {
    -webkit-box-shadow: 0 0 0 1000px var(--awb-surface) inset;
    -webkit-text-fill-color: var(--awb-text-primary);
}
```

#### Task 4.3.4: Model Selector Dropdown
- [ ] Style model dropdown
- [ ] Small font (13px)
- [ ] Chevron indicator
- [ ] Hover state
- [ ] Click state

**Code:**
```css
.agent-workbench-model-selector {
    display: flex;
    align-items: center;
    gap: var(--space-xs);

    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-sm);

    font-size: var(--font-size-sm);
    color: var(--awb-text-secondary);

    background: transparent;
    border: none;
    cursor: pointer;

    transition: background var(--transition-fast);
}

.agent-workbench-model-selector:hover {
    background: var(--awb-btn-hover);
}

/* Chevron icon */
.agent-workbench-model-selector::after {
    content: '▼';
    font-size: 10px;
    margin-left: var(--space-xs);
}
```

#### Task 4.3.5: Submit Button (Three States)
- [ ] Create circular button
- [ ] State 1: Pale gray (disabled, no text entered) - Uses `arrow_up_in_circle_icon_96.png`
- [ ] State 2: Black (active, message typed) - Uses `arrow_up_in_circle_icon_96.png`
- [ ] State 3: Processing (in textbox) - Uses `processing_icon_96.png` with animation
- [ ] Smooth transitions between states

**Note:** When using `gr.ChatInterface`, the submit button is automatically integrated into the textbox (Agent Workbench-style). Icon can be specified via the `submit_btn` parameter:

```python
submit_btn=gr.Button(
    icon="/design/icons/arrow_up_in_circle_icon_96.png",
    elem_classes=["agent-workbench-submit-btn"]
)
```

**CSS Code:**
```css
.agent-workbench-submit-btn {
    width: 32px;
    height: 32px;
    min-width: 32px;

    border-radius: var(--radius-full);
    border: none;

    display: flex;
    align-items: center;
    justify-content: center;

    cursor: pointer;
    transition: all var(--transition-base);

    /* Default: Disabled state (no message) */
    background: var(--awb-btn-disabled);
    color: var(--awb-text-tertiary);
}

/* State 2: Active (message entered) */
.agent-workbench-submit-btn.active {
    background: var(--awb-btn-active);
    color: white;
    cursor: pointer;
}

.agent-workbench-submit-btn.active:hover {
    transform: scale(1.05);
    box-shadow: var(--shadow-sm);
}

/* State 3: Processing (show processing_icon_96.png) */
.agent-workbench-submit-btn.processing {
    background: transparent; /* No background, just animated icon */
    animation: pulse 1.5s ease-in-out infinite;
    cursor: not-allowed;
}

.agent-workbench-submit-btn.processing::after {
    content: '';
    width: 20px;
    height: 20px;
    background: url('/design/icons/processing_icon_96.png') center/contain no-repeat;
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.6;
    }
}

/* Icon inside button */
.agent-workbench-submit-btn img {
    width: 20px;
    height: 20px;
}

/* Mobile touch target */
@media (max-width: 768px) {
    .agent-workbench-submit-btn {
        width: 44px;
        height: 44px;
    }

    .agent-workbench-submit-btn img {
        width: 24px;
        height: 24px;
    }
}
```

**Validation:**
- [ ] Input bar appears at bottom, centered
- [ ] White background with subtle shadow
- [ ] Globe icon toggles blue on click
- [ ] Text input expands to fill space
- [ ] Model selector shows current model
- [ ] Submit button gray by default
- [ ] Submit button turns black when typing
- [ ] All components align properly

**Estimated Time:** 4-5 hours

---

### Phase 4.4: Top Navigation (Week 1, Day 4-5)

**Goal:** Implement top navigation bar with sidebar toggle and settings icon

#### Task 4.4.1: Navigation Bar Container
- [ ] Create `.agent-workbench-top-nav` class
- [ ] Fixed positioning at top
- [ ] Full width with max-width constraint
- [ ] Flexbox for left/right alignment
- [ ] Subtle bottom border

**Code:**
```css
.agent-workbench-top-nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 900;

    background: var(--awb-surface);
    border-bottom: 1px solid var(--awb-border-light);

    padding: var(--space-md) var(--space-xl);
}

.agent-workbench-top-nav-inner {
    max-width: 1400px;
    margin: 0 auto;

    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Add top padding to body to account for fixed nav */
body {
    padding-top: 56px; /* Height of nav bar */
}

@media (max-width: 768px) {
    .agent-workbench-top-nav {
        padding: var(--space-sm) var(--space-md);
    }

    body {
        padding-top: 48px;
    }
}
```

#### Task 4.4.2: Left Controls (Sidebar Toggle + New Chat)
- [ ] Style sidebar toggle button (`view_sidebar_icon_96.png`)
- [ ] Style new chat button (`add_chat_icon_96.png`)
- [ ] Flexbox layout with gap
- [ ] Icon buttons with hover states

**Python (Gradio component setup):**
```python
# ui/pages/chat.py
sidebar_toggle = gr.Button(
    icon="/design/icons/view_sidebar_icon_96.png",
    elem_classes=["agent-workbench-nav-btn", "agent-workbench-sidebar-toggle"]
)

new_chat_btn = gr.Button(
    icon="/design/icons/add_chat_icon_96.png",
    elem_classes=["agent-workbench-nav-btn", "agent-workbench-new-chat-btn"]
)
```

**CSS Code:**
```css
.agent-workbench-nav-left {
    display: flex;
    align-items: center;
    gap: var(--space-md);
}

.agent-workbench-nav-btn {
    width: 32px;
    height: 32px;

    display: flex;
    align-items: center;
    justify-content: center;

    border: none;
    background: transparent;
    border-radius: var(--radius-sm);

    color: var(--awb-text-secondary);
    cursor: pointer;

    transition: all var(--transition-fast);
}

.agent-workbench-nav-btn:hover {
    background: var(--awb-btn-hover);
    color: var(--awb-text-primary);
}

.agent-workbench-nav-btn img {
    width: 20px;
    height: 20px;
}

/* New chat button - icon already has red circle built-in (add_chat_icon_96.png) */
.agent-workbench-new-chat-btn {
    /* No additional styling needed - icon handles visual */
}

/* Mobile touch targets */
@media (max-width: 768px) {
    .agent-workbench-nav-btn {
        width: 44px;
        height: 44px;
    }

    .agent-workbench-nav-btn img {
        width: 24px;
        height: 24px;
    }
}
```

#### Task 4.4.3: Right Controls (Cloud Status + Settings)
- [ ] Style settings icon button (`settings_icon_96.png`)
- [ ] Style cloud connectivity icon
- [ ] Online state (cloud icon)
- [ ] Offline state (cloud with slash)

**Python (Gradio component setup):**
```python
# ui/pages/chat.py
settings_btn = gr.Button(
    icon="/design/icons/settings_icon_96.png",
    elem_classes=["agent-workbench-nav-btn", "agent-workbench-settings-btn"]
)
```

**CSS Code:**
```css
.agent-workbench-nav-right {
    display: flex;
    align-items: center;
    gap: var(--space-md);
}

/* Cloud connectivity indicator */
.agent-workbench-cloud-status {
    width: 32px;
    height: 32px;

    display: flex;
    align-items: center;
    justify-content: center;

    color: var(--awb-text-tertiary);
}

.agent-workbench-cloud-status.online {
    color: var(--awb-blue);
}

.agent-workbench-cloud-status.offline {
    color: var(--awb-red);
}

/* Settings button - uses same .agent-workbench-nav-btn styles */
.agent-workbench-settings-btn {
    /* Inherits from .agent-workbench-nav-btn */
}
```

**Validation:**
- [ ] Navigation bar fixed at top
- [ ] Sidebar toggle on left
- [ ] New chat button with red indicator
- [ ] Settings icon on right
- [ ] Cloud status shows online/offline
- [ ] All hover states work
- [ ] Body content not hidden under nav

**Estimated Time:** 3-4 hours

---

### Phase 4.5: Sidebar Styling (Week 2, Day 1-2)

**Goal:** Style conversation history sidebar to match design

#### Task 4.5.1: Sidebar Container
- [ ] Style `.agent-workbench-sidebar` container
- [ ] Fixed position, left side
- [ ] Slide-in animation
- [ ] Right border and shadow
- [ ] Z-index above main content

**Code:**
```css
.agent-workbench-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;

    width: 280px;

    background: var(--awb-sidebar-bg);
    border-right: 1px solid var(--awb-border);
    box-shadow: 2px 0 12px rgba(0, 0, 0, 0.08);

    z-index: 950;

    /* Slide in/out animation */
    transform: translateX(-100%);
    transition: transform var(--transition-base);

    overflow-y: auto;
}

.agent-workbench-sidebar.open {
    transform: translateX(0);
}

/* Backdrop (click-away) */
.agent-workbench-sidebar-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    background: rgba(0, 0, 0, 0.2);
    z-index: 940;

    opacity: 0;
    pointer-events: none;
    transition: opacity var(--transition-base);
}

.agent-workbench-sidebar-backdrop.visible {
    opacity: 1;
    pointer-events: auto;
}

@media (max-width: 768px) {
    .agent-workbench-sidebar {
        width: 85%;
        max-width: 320px;
    }
}
```

#### Task 4.5.2: Sidebar Header (New Chat Button)
- [ ] Style header section
- [ ] New chat button with red icon
- [ ] Padding and border

**Code:**
```css
.agent-workbench-sidebar-header {
    padding: var(--space-lg);
    border-bottom: 1px solid var(--awb-border-light);
}

.agent-workbench-sidebar-new-chat {
    width: 100%;

    display: flex;
    align-items: center;
    gap: var(--space-md);

    padding: var(--space-md);
    border-radius: var(--radius-md);
    border: 1px solid var(--awb-border);
    background: transparent;

    font-size: var(--font-size-base);
    color: var(--awb-text-primary);
    cursor: pointer;

    transition: all var(--transition-fast);
}

.agent-workbench-sidebar-new-chat:hover {
    background: var(--awb-btn-hover);
}

.agent-workbench-sidebar-new-chat .icon {
    width: 20px;
    height: 20px;
    color: var(--awb-red);
}
```

#### Task 4.5.3: Conversation List Items
- [ ] Style individual conversation items
- [ ] Truncate long titles with ellipsis
- [ ] Hover and active states
- [ ] Date group headers

**Code:**
```css
.agent-workbench-conversation-list {
    padding: var(--space-sm) 0;
}

/* Date group header */
.agent-workbench-conversation-group {
    padding: var(--space-md) var(--space-lg);
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: var(--awb-text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Individual conversation item */
.agent-workbench-conversation-item {
    padding: var(--space-md) var(--space-lg);

    font-size: var(--font-size-sm);
    color: var(--awb-text-primary);

    cursor: pointer;
    transition: background var(--transition-fast);

    /* Truncate with ellipsis */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.agent-workbench-conversation-item:hover {
    background: var(--awb-btn-hover);
}

.agent-workbench-conversation-item.active {
    background: rgba(0, 122, 255, 0.1);
    color: var(--awb-blue);
    font-weight: 500;
}
```

**Validation:**
- [ ] Sidebar slides in from left
- [ ] New chat button at top
- [ ] Conversation list displays correctly
- [ ] Items truncate with "..." when too long
- [ ] Hover states work
- [ ] Click-away closes sidebar
- [ ] Backdrop appears when open

**Estimated Time:** 3-4 hours

---

### Phase 4.6: Settings Modal (Week 2, Day 2-3)

**Goal:** Style settings page as centered modal dialog

#### Task 4.6.1: Modal Overlay & Container
- [ ] Create overlay backdrop
- [ ] Center modal dialog
- [ ] Rounded corners with shadow
- [ ] macOS-style window chrome

**Code:**
```css
/* Modal overlay */
.agent-workbench-settings-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(4px);

    display: flex;
    align-items: center;
    justify-content: center;

    z-index: 1000;
    padding: var(--space-2xl);
}

/* Modal dialog */
.agent-workbench-settings-modal {
    width: 100%;
    max-width: 600px;
    max-height: 80vh;

    background: var(--awb-surface);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-lg);

    overflow: hidden;
    display: flex;
    flex-direction: column;
}

@media (max-width: 768px) {
    .agent-workbench-settings-overlay {
        padding: 0;
    }

    .agent-workbench-settings-modal {
        max-width: 100%;
        max-height: 100vh;
        border-radius: 0;
    }
}
```

#### Task 4.6.2: Settings Header
- [ ] Title on left
- [ ] Close button with `close_settings_icon.png` on right
- [ ] macOS traffic lights
- [ ] Bottom border

**Python (Gradio component setup):**
```python
# ui/pages/settings.py
close_btn = gr.Button(
    icon="/design/icons/close_settings_icon.png",
    elem_classes=["agent-workbench-close-btn"]
)
```

**CSS Code:**
```css
.agent-workbench-settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: var(--space-2xl);
    border-bottom: 1px solid var(--awb-border-light);
}

/* macOS traffic lights */
.agent-workbench-traffic-lights {
    display: flex;
    gap: var(--space-sm);
}

.agent-workbench-traffic-light {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

.agent-workbench-traffic-light.red { background: #FF5F57; }
.agent-workbench-traffic-light.yellow { background: #FFBD2E; }
.agent-workbench-traffic-light.green { background: #28CA42; }

/* Title */
.agent-workbench-settings-title {
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: var(--awb-text-primary);
}

/* Close button */
.agent-workbench-close-btn {
    width: 32px;
    height: 32px;

    display: flex;
    align-items: center;
    justify-content: center;

    border: none;
    background: transparent;
    border-radius: var(--radius-sm);

    color: var(--awb-text-tertiary);
    cursor: pointer;

    transition: all var(--transition-fast);
}

.agent-workbench-close-btn:hover {
    background: var(--awb-btn-hover);
    color: var(--awb-text-primary);
}

.agent-workbench-close-btn img {
    width: 16px;
    height: 16px;
}
```

#### Task 4.6.3: User Profile Section
- [ ] Style user info (username + email)
- [ ] Three buttons (Upgrade, Manage, Sign out)
- [ ] Avatar on right
- [ ] Divider below

**Code:**
```css
.agent-workbench-user-profile {
    display: flex;
    justify-content: space-between;
    align-items: center;

    padding: var(--space-2xl);
    border-bottom: 1px solid var(--awb-border-light);
}

.agent-workbench-user-info {
    flex: 1;
}

.agent-workbench-username {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--awb-text-primary);
    margin-bottom: var(--space-xs);
}

.agent-workbench-user-email {
    font-size: var(--font-size-sm);
    color: var(--awb-text-secondary);
    margin-bottom: var(--space-lg);
}

/* Action buttons */
.agent-workbench-user-actions {
    display: flex;
    gap: var(--space-sm);
}

.agent-workbench-user-btn {
    padding: var(--space-sm) var(--space-lg);
    border-radius: var(--radius-sm);

    font-size: var(--font-size-sm);
    font-weight: 500;

    cursor: pointer;
    transition: all var(--transition-fast);
}

.agent-workbench-user-btn.primary {
    background: var(--awb-text-primary);
    color: white;
    border: none;
}

.agent-workbench-user-btn.secondary {
    background: transparent;
    color: var(--awb-text-primary);
    border: 1px solid var(--awb-border);
}

.agent-workbench-user-btn:hover {
    opacity: 0.8;
}

/* Avatar */
.agent-workbench-user-avatar {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    background: var(--awb-btn-hover);

    display: flex;
    align-items: center;
    justify-content: center;
}
```

#### Task 4.6.4: Settings Content (Scrollable)
- [ ] Scrollable content area
- [ ] Section spacing
- [ ] Icon + title + description layout

**Code:**
```css
.agent-workbench-settings-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-2xl);
}

/* Individual setting section */
.agent-workbench-setting {
    display: flex;
    align-items: flex-start;
    gap: var(--space-lg);

    padding: var(--space-xl) 0;
    border-bottom: 1px solid var(--awb-border-light);
}

.agent-workbench-setting:last-child {
    border-bottom: none;
}

/* Icon */
.agent-workbench-setting-icon {
    width: 24px;
    height: 24px;
    color: var(--awb-text-secondary);
    flex-shrink: 0;
}

/* Content */
.agent-workbench-setting-content {
    flex: 1;
}

.agent-workbench-setting-title {
    font-size: var(--font-size-base);
    font-weight: 500;
    color: var(--awb-text-primary);
    margin-bottom: var(--space-xs);
}

.agent-workbench-setting-description {
    font-size: var(--font-size-sm);
    color: var(--awb-text-secondary);
    line-height: 1.5;
}

/* Control (toggle, slider, etc.) */
.agent-workbench-setting-control {
    margin-top: var(--space-md);
}
```

#### Task 4.6.5: iOS-Style Toggle Switches
- [ ] Create custom toggle switch
- [ ] Pill shape (44x24px)
- [ ] Animated knob
- [ ] Off state (gray) → On state (blue)

**Code:**
```css
.agent-workbench-toggle {
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
}

/* Hide default checkbox */
.agent-workbench-toggle input {
    opacity: 0;
    width: 0;
    height: 0;
}

/* Toggle track */
.agent-workbench-toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    background: var(--awb-gray);
    border-radius: 12px;

    transition: all var(--transition-base);
}

/* Toggle knob */
.agent-workbench-toggle-slider::before {
    position: absolute;
    content: "";
    height: 20px;
    width: 20px;
    left: 2px;
    bottom: 2px;

    background: white;
    border-radius: 50%;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);

    transition: all var(--transition-base);
}

/* Checked state */
.agent-workbench-toggle input:checked + .agent-workbench-toggle-slider {
    background: var(--awb-blue);
}

.agent-workbench-toggle input:checked + .agent-workbench-toggle-slider::before {
    transform: translateX(20px);
}

/* Focus state */
.agent-workbench-toggle input:focus + .agent-workbench-toggle-slider {
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
}
```

#### Task 4.6.6: Custom Slider
- [ ] Style range slider
- [ ] Value labels
- [ ] Track and thumb styling

**Code:**
```css
.agent-workbench-slider-container {
    width: 100%;
}

.agent-workbench-slider {
    width: 100%;
    height: 4px;
    border-radius: 2px;
    background: var(--awb-border);
    outline: none;

    -webkit-appearance: none;
    appearance: none;
}

/* Track */
.agent-workbench-slider::-webkit-slider-track {
    width: 100%;
    height: 4px;
    background: var(--awb-border);
    border-radius: 2px;
}

.agent-workbench-slider::-moz-range-track {
    width: 100%;
    height: 4px;
    background: var(--awb-border);
    border-radius: 2px;
}

/* Thumb */
.agent-workbench-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    background: var(--awb-blue);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.agent-workbench-slider::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: var(--awb-blue);
    border-radius: 50%;
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Value labels */
.agent-workbench-slider-labels {
    display: flex;
    justify-content: space-between;
    margin-top: var(--space-sm);
    font-size: var(--font-size-xs);
    color: var(--awb-text-tertiary);
}
```

**Validation:**
- [ ] Settings modal appears centered
- [ ] Close button (X) works
- [ ] User profile section displays correctly
- [ ] iOS toggles animate smoothly
- [ ] Sliders work and show values
- [ ] Content scrolls if too long
- [ ] Mobile responsive

**Estimated Time:** 5-6 hours

---

### Phase 4.7: Message Bubbles & Agent Status (Week 2, Day 3-4)

**Goal:** Style chat messages and agent thinking indicators

#### Task 4.7.1: Message Container
- [ ] Style message wrapper
- [ ] Vertical spacing between messages
- [ ] Max-width for readability

**Code:**
```css
.agent-workbench-messages {
    display: flex;
    flex-direction: column;
    gap: var(--space-lg);
    padding: var(--space-2xl) 0;
}

.agent-workbench-message {
    max-width: 85%;
    animation: fadeIn var(--transition-base);
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

#### Task 4.7.2: User Messages
- [ ] Style user message bubbles
- [ ] Align right
- [ ] Blue background
- [ ] White text

**Code:**
```css
.agent-workbench-message.user {
    align-self: flex-end;
}

.agent-workbench-message-bubble.user {
    background: var(--awb-blue);
    color: white;

    padding: var(--space-md) var(--space-lg);
    border-radius: var(--radius-lg);
    border-bottom-right-radius: var(--space-xs);

    font-size: var(--font-size-base);
    line-height: 1.5;
    word-wrap: break-word;
}
```

#### Task 4.7.3: Assistant Messages
- [ ] Style assistant bubbles
- [ ] Align left
- [ ] Light gray background
- [ ] Dark text

**Code:**
```css
.agent-workbench-message.assistant {
    align-self: flex-start;
}

.agent-workbench-message-bubble.assistant {
    background: var(--awb-surface);
    color: var(--awb-text-primary);
    border: 1px solid var(--awb-border);

    padding: var(--space-md) var(--space-lg);
    border-radius: var(--radius-lg);
    border-bottom-left-radius: var(--space-xs);

    font-size: var(--font-size-base);
    line-height: 1.5;
    word-wrap: break-word;
}
```

#### Task 4.7.4: Agent Status Bubble ("Thinking...")
- [ ] Style status indicator
- [ ] Yellow/amber background
- [ ] Processing icon (`workspaces_icon_96.png`) on left
- [ ] Animated

**Code:**
```css
.agent-workbench-agent-status {
    display: flex;
    align-items: center;
    gap: var(--space-md);

    padding: var(--space-md) var(--space-lg);
    border-radius: var(--radius-lg);

    background: #FFF3CD;
    border: 1px solid #FFD700;
    color: #856404;

    font-size: var(--font-size-sm);
    font-weight: 500;

    animation: slideIn var(--transition-base);
}

.agent-workbench-agent-status .icon {
    width: 20px;
    height: 20px;
    /* Use workspaces_icon_96.png for processing state */
    background: url('/design/icons/workspaces_icon_96.png') center/contain no-repeat;
    animation: spin 2s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-16px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Processing state (default - uses workspaces_icon_96.png) */
.agent-workbench-agent-status.processing .icon {
    background: url('/design/icons/workspaces_icon_96.png') center/contain no-repeat;
}
```

#### Task 4.7.5: Streaming Response Animation
- [ ] Cursor blink animation
- [ ] Typing indicator

**Code:**
```css
.agent-workbench-typing-indicator {
    display: inline-block;
    width: 4px;
    height: 16px;
    background: var(--awb-text-primary);
    animation: blink 1s step-end infinite;
    margin-left: 2px;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}
```

**Validation:**
- [ ] Messages display correctly
- [ ] User messages align right (blue)
- [ ] Assistant messages align left (white)
- [ ] Agent status shows with icon
- [ ] Animations smooth
- [ ] Text wraps properly

**Estimated Time:** 3-4 hours

---

### Phase 4.8: Responsive Design (Week 2, Day 4-5)

**Goal:** Ensure all components work on mobile, tablet, desktop

#### Task 4.8.1: Mobile Breakpoints
- [ ] Test on 375px (iPhone SE)
- [ ] Test on 390px (iPhone 12/13)
- [ ] Test on 428px (iPhone Pro Max)
- [ ] Adjust spacing for small screens

**Code:**
```css
/* Mobile portrait (< 480px) */
@media (max-width: 480px) {
    .agent-workbench-chat-container {
        padding: var(--space-xl) var(--space-sm);
    }

    .agent-workbench-input-bar {
        padding: var(--space-sm);
        gap: var(--space-sm);
    }

    .agent-workbench-message {
        max-width: 95%;
    }

    .agent-workbench-logo img {
        width: 48px;
        height: 48px;
    }
}
```

#### Task 4.8.2: Tablet Layout
- [ ] Test on iPad (768px)
- [ ] Test on iPad Pro (1024px)
- [ ] Adjust for landscape orientation

**Code:**
```css
/* Tablet (768px - 1024px) */
@media (min-width: 768px) and (max-width: 1024px) {
    .agent-workbench-chat-container {
        max-width: 700px;
    }

    .agent-workbench-sidebar {
        width: 320px;
    }
}
```

#### Task 4.8.3: Touch Targets
- [ ] Verify all interactive elements ≥ 44x44px on mobile
- [ ] Test tap/click on actual devices
- [ ] Add touch-action CSS where needed

**Code:**
```css
/* Ensure minimum touch target size on mobile */
@media (max-width: 768px) {
    .agent-workbench-nav-btn,
    .agent-workbench-web-search,
    .agent-workbench-submit-btn {
        min-width: 44px;
        min-height: 44px;
    }
}
```

#### Task 4.8.4: Landscape Orientation
- [ ] Handle landscape mode on phones
- [ ] Adjust heights and padding

**Code:**
```css
/* Mobile landscape */
@media (max-height: 600px) and (orientation: landscape) {
    .agent-workbench-logo {
        padding: var(--space-xl) 0;
    }

    .agent-workbench-logo img {
        width: 40px;
        height: 40px;
    }

    .agent-workbench-input-bar {
        bottom: var(--space-sm);
    }
}
```

**Validation:**
- [ ] Test on real devices (iOS, Android)
- [ ] Test with Chrome DevTools device emulation
- [ ] Verify touch targets ≥ 44px
- [ ] No horizontal scroll on any viewport
- [ ] Text remains readable at all sizes

**Estimated Time:** 3-4 hours

---

### Phase 4.9: Dark Mode (Week 3, Day 1)

**Goal:** Implement complete dark mode support

#### Task 4.9.1: Test Auto-Detection
- [ ] Verify `prefers-color-scheme` media query works
- [ ] Test on macOS (System Preferences → Appearance)
- [ ] Test on iOS (Settings → Display → Dark Mode)
- [ ] Ensure variables update correctly

#### Task 4.9.2: Manual Theme Toggle
- [ ] Implement JavaScript theme switcher
- [ ] Add classes to body: `.light-mode`, `.dark-mode`
- [ ] Persist choice to localStorage
- [ ] Wire to settings page theme selector

**JavaScript (add to Gradio custom JS):**
```javascript
function setTheme(theme) {
    document.body.classList.remove('light-mode', 'dark-mode');

    if (theme === 'light') {
        document.body.classList.add('light-mode');
    } else if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    }
    // 'auto' = no class, use media query

    localStorage.setItem('theme', theme);
}

// Load theme on page load
const savedTheme = localStorage.getItem('theme') || 'auto';
if (savedTheme !== 'auto') {
    setTheme(savedTheme);
}
```

#### Task 4.9.3: Dark Mode Refinements
- [ ] Test all components in dark mode
- [ ] Adjust contrast ratios for accessibility
- [ ] Fix any hard-coded colors
- [ ] Test shadows (may need adjustment)

**Validation:**
- [ ] Auto dark mode works (detects OS setting)
- [ ] Manual toggle works (Light/Dark/Auto)
- [ ] Theme persists after page reload
- [ ] All components readable in dark mode
- [ ] WCAG AA contrast ratio met (4.5:1 for text)

**Estimated Time:** 3-4 hours

---

### Phase 4.10: Polish & Animation (Week 3, Day 2-3)

**Goal:** Add subtle animations and micro-interactions

#### Task 4.10.1: Logo Fade Animation
- [ ] Implement fade-out during processing
- [ ] Show processing icon (juggler or spinner)
- [ ] Fade logo back in on idle

**Code:**
```css
/* Already defined in Phase 4.2.3, now wire with JS */

.agent-workbench-logo.processing {
    opacity: 0;
}

.agent-workbench-processing-icon {
    display: none;
    animation: bounce 1s ease-in-out infinite;
}

.agent-workbench-logo.processing + .agent-workbench-processing-icon {
    display: flex;
}

@keyframes bounce {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-8px);
    }
}
```

**JavaScript:**
```javascript
// On message send
document.querySelector('.agent-workbench-logo').classList.add('processing');

// On response complete
document.querySelector('.agent-workbench-logo').classList.remove('processing');
```

#### Task 4.10.2: Toast Notifications
- [ ] Create toast notification component
- [ ] Slide up from bottom
- [ ] Auto-dismiss after 3 seconds

**Code:**
```css
.agent-workbench-toast {
    position: fixed;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);

    padding: var(--space-md) var(--space-xl);
    border-radius: var(--radius-md);

    background: #323232;
    color: white;
    font-size: var(--font-size-sm);
    box-shadow: var(--shadow-lg);

    z-index: 2000;

    opacity: 0;
    transition: all var(--transition-base);
}

.agent-workbench-toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}
```

#### Task 4.10.3: Button Hover Effects
- [ ] Add scale transform on hover
- [ ] Add subtle shadow on hover
- [ ] Smooth transitions

**Code:**
```css
/* Enhance existing button hover states */
.agent-workbench-nav-btn:hover,
.agent-workbench-submit-btn.active:hover {
    transform: scale(1.05);
}

.agent-workbench-nav-btn:active,
.agent-workbench-submit-btn:active {
    transform: scale(0.95);
}
```

#### Task 4.10.4: Loading States
- [ ] Skeleton screens for loading content
- [ ] Shimmer animation

**Code:**
```css
.agent-workbench-skeleton {
    background: linear-gradient(
        90deg,
        var(--awb-border) 0%,
        var(--awb-btn-hover) 50%,
        var(--awb-border) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm);
}

@keyframes shimmer {
    0% {
        background-position: -200% 0;
    }
    100% {
        background-position: 200% 0;
    }
}
```

**Validation:**
- [ ] Logo fades during processing
- [ ] Toasts appear/disappear smoothly
- [ ] Buttons feel responsive
- [ ] Loading states show progress
- [ ] All animations 60fps (no jank)

**Estimated Time:** 4-5 hours

---

### Phase 4.11: Integration & Testing (Week 3, Day 4-5)

**Goal:** Wire CSS to actual Gradio components and test thoroughly

#### Task 4.11.1: Apply Classes to Gradio Components
- [ ] Update `chat.py` to use `gr.ChatInterface` with custom styling
- [ ] Update `settings.py` to add `elem_classes`
- [ ] Update `sidebar.py` to add `elem_classes`

**Complete gr.ChatInterface Example:**
```python
# ui/pages/chat.py

import gradio as gr
from typing import List, Tuple

def chat_handler(message: str, history: List[Tuple[str, str]], web_search: bool, model: str) -> str:
    """Handle chat messages with streaming support."""
    # Your chat logic here
    return "Response from model"

def create_chat_page() -> gr.Blocks:
    with gr.Blocks(elem_classes=["agent-workbench-chat-container"]) as chat_page:

        # Top navigation bar
        with gr.Row(elem_classes=["agent-workbench-top-nav"]):
            with gr.Row(elem_classes=["agent-workbench-nav-left"]):
                sidebar_toggle = gr.Button(
                    icon="/design/icons/view_sidebar_icon_96.png",
                    elem_classes=["agent-workbench-nav-btn", "agent-workbench-sidebar-toggle"]
                )
                new_chat_btn = gr.Button(
                    icon="/design/icons/add_chat_icon_96.png",
                    elem_classes=["agent-workbench-nav-btn", "agent-workbench-new-chat-btn"]
                )

            with gr.Row(elem_classes=["agent-workbench-nav-right"]):
                cloud_status = gr.HTML(
                    "<div class='agent-workbench-cloud-status online'>☁</div>"
                )
                settings_btn = gr.Button(
                    icon="/design/icons/settings_icon_96.png",
                    elem_classes=["agent-workbench-nav-btn", "agent-workbench-settings-btn"]
                )

        # Main logo (shows when idle)
        gr.Image(
            value="/design/icons/logo_72.png",
            elem_classes=["agent-workbench-logo"],
            show_label=False
        )

        # Chat interface with integrated controls
        chat_interface = gr.ChatInterface(
            fn=chat_handler,
            chatbot=gr.Chatbot(
                elem_classes=["agent-workbench-messages"],
                show_label=False,
                height=600
            ),
            textbox=gr.Textbox(
                placeholder="Send a message",
                elem_classes=["agent-workbench-message-input"],
                show_label=False,
                container=False,
                submit_btn=gr.Button(
                    icon="/design/icons/arrow_up_in_circle_icon_96.png",
                    elem_classes=["agent-workbench-submit-btn"]
                )
            ),
            additional_inputs=[
                gr.Checkbox(
                    label="Web Search",
                    value=False,
                    elem_classes=["agent-workbench-web-search"],
                    container=False
                ),
                gr.Dropdown(
                    label="Model",
                    choices=["gpt-4", "claude-3", "llama-2"],
                    value="gpt-4",
                    elem_classes=["agent-workbench-model-selector"],
                    container=False
                )
            ],
            elem_classes=["agent-workbench-chat-interface"]
        )

        # Wire button events
        sidebar_toggle.click(
            fn=lambda: gr.update(visible=True),
            outputs=[]  # Update sidebar visibility
        )

        new_chat_btn.click(
            fn=lambda: [],
            outputs=[chat_interface.chatbot]  # Clear chat
        )

        settings_btn.click(
            fn=lambda: gr.update(visible=True),
            outputs=[]  # Show settings modal
        )

    return chat_page
```

**Settings Page Example:**
```python
# ui/pages/settings.py

def create_settings_modal() -> gr.Blocks:
    with gr.Blocks(visible=False, elem_classes=["agent-workbench-settings-overlay"]) as settings:
        with gr.Column(elem_classes=["agent-workbench-settings-modal"]):
            # Header
            with gr.Row(elem_classes=["agent-workbench-settings-header"]):
                with gr.Row(elem_classes=["agent-workbench-traffic-lights"]):
                    gr.HTML("<div class='agent-workbench-traffic-light red'></div>")
                    gr.HTML("<div class='agent-workbench-traffic-light yellow'></div>")
                    gr.HTML("<div class='agent-workbench-traffic-light green'></div>")

                gr.Markdown("# Settings", elem_classes=["agent-workbench-settings-title"])

                close_btn = gr.Button(
                    icon="/design/icons/close_settings_icon.png",
                    elem_classes=["agent-workbench-close-btn"]
                )

            # User profile section
            with gr.Row(elem_classes=["agent-workbench-user-profile"]):
                with gr.Column(elem_classes=["agent-workbench-user-info"]):
                    gr.Markdown("**sytse**", elem_classes=["agent-workbench-username"])
                    gr.Markdown("sytse@schaaaf.nl", elem_classes=["agent-workbench-user-email"])

                    with gr.Row(elem_classes=["agent-workbench-user-actions"]):
                        gr.Button("Upgrade", elem_classes=["agent-workbench-user-btn", "primary"])
                        gr.Button("Manage", elem_classes=["agent-workbench-user-btn", "secondary"])
                        gr.Button("Sign out", elem_classes=["agent-workbench-user-btn", "secondary"])

            # Settings content
            with gr.Column(elem_classes=["agent-workbench-settings-content"]):
                # Theme setting
                with gr.Row(elem_classes=["agent-workbench-setting"]):
                    gr.HTML("<span class='agent-workbench-setting-icon'>🌓</span>")
                    with gr.Column(elem_classes=["agent-workbench-setting-content"]):
                        gr.Markdown("**Theme**", elem_classes=["agent-workbench-setting-title"])
                        gr.Markdown("Choose light, dark, or auto", elem_classes=["agent-workbench-setting-description"])

                        theme_toggle = gr.Radio(
                            choices=["Light", "Dark", "Auto"],
                            value="Auto",
                            elem_classes=["agent-workbench-toggle"]
                        )

            # Wire close button
            close_btn.click(
                fn=lambda: gr.update(visible=False),
                outputs=[settings]
            )

    return settings
```

#### Task 4.11.2: Cross-Browser Testing
- [ ] Test on Chrome (latest)
- [ ] Test on Firefox (latest)
- [ ] Test on Safari (macOS, iOS)
- [ ] Test on Edge (latest)

#### Task 4.11.3: Accessibility Testing
- [ ] Run Lighthouse audit (target: 90+)
- [ ] Test keyboard navigation (Tab, Enter, Esc)
- [ ] Test screen reader (VoiceOver on macOS)
- [ ] Verify ARIA labels
- [ ] Check color contrast ratios

#### Task 4.11.4: Performance Testing
- [ ] Measure First Contentful Paint (FCP)
- [ ] Measure Largest Contentful Paint (LCP)
- [ ] Measure Cumulative Layout Shift (CLS)
- [ ] Optimize if metrics below threshold

#### Task 4.11.5: Visual Regression Testing
- [ ] Take screenshots of all components
- [ ] Compare with design mockups
- [ ] Note differences and iterate
- [ ] Aim for >90% visual match

**Testing Checklist:**
- [ ] Desktop Chrome - Light mode
- [ ] Desktop Chrome - Dark mode
- [ ] Desktop Firefox - Light mode
- [ ] Desktop Safari - Light mode
- [ ] Mobile Safari (iOS) - Light mode
- [ ] Mobile Chrome (Android) - Light mode
- [ ] Tablet iPad - Light mode
- [ ] Lighthouse score >90
- [ ] Keyboard navigation works
- [ ] No console errors

**Estimated Time:** 6-8 hours

---

## Summary & Timeline

### Total Estimated Time: ~50-60 hours (3 weeks)

**Week 1:**
- Phase 4.1: Foundation & Variables (2-3 hours)
- Phase 4.2: Main Layout (2-3 hours)
- Phase 4.3: Chat Input Bar (4-5 hours)
- Phase 4.4: Top Navigation (3-4 hours)

**Week 2:**
- Phase 4.5: Sidebar Styling (3-4 hours)
- Phase 4.6: Settings Modal (5-6 hours)
- Phase 4.7: Message Bubbles (3-4 hours)
- Phase 4.8: Responsive Design (3-4 hours)

**Week 3:**
- Phase 4.9: Dark Mode (3-4 hours)
- Phase 4.10: Polish & Animation (4-5 hours)
- Phase 4.11: Integration & Testing (6-8 hours)

---

## Success Criteria

### Must Have (P0):
- [ ] All components match design screenshots (>90% visual match)
- [ ] Ubuntu font loads without flash (FOUT)
- [ ] Dark mode works (auto + manual toggle)
- [ ] Responsive on mobile (320px+)
- [ ] Lighthouse score >90
- [ ] Zero console errors
- [ ] All hover/active states work

### Should Have (P1):
- [ ] Smooth animations (60fps)
- [ ] Toast notifications
- [ ] Logo fade during processing
- [ ] Keyboard navigation
- [ ] Touch targets ≥44px on mobile

### Nice to Have (P2):
- [ ] Skeleton loading screens
- [ ] Advanced micro-interactions
- [ ] Scroll animations
- [ ] Haptic feedback (mobile)

---

## Rollback Plan

If Agent Workbench design causes issues:

**Option 1: Feature Flag**
```python
# ui/mode_factory_v2.py
enable_agent_workbench_design = os.getenv("ENABLE_AGENT_WORKBENCH_DESIGN", "false") == "true"

if enable_agent_workbench_design:
    css = """
        @import url('/static/assets/css/main.css');
        @import url('/static/assets/css/agent-workbench-design.css');
    """
else:
    css = "@import url('/static/assets/css/main.css');"
```

**Option 2: Disable CSS Import**
```python
# Remove from main.css
# @import url('agent-workbench-design.css');
```

**Option 3: Revert to Previous Version**
```bash
git checkout main -- static/assets/css/agent-workbench-design.css
# Or delete file entirely
rm static/assets/css/agent-workbench-design.css
```

---

## JavaScript Pattern Discovery - Phase 4.2

### Issue 1: Logo/Chatbot Visibility Toggle

**Critical Discovery:** Gradio 5.x strips `<script>` tags from `gr.HTML` components for security reasons.

#### The Problem

During Phase 4.2 implementation, we discovered that JavaScript embedded in `gr.HTML` components does not execute:

```python
# ❌ WRONG - This JavaScript will NOT execute
gr.HTML(
    value='''
    <div class="agent-workbench-logo">
        <img src="/static/icons/logo_72.png">
        <script>
            // This script is stripped by Gradio for security
            console.log("This will never run");
        </script>
    </div>
    '''
)
```

**Evidence:** Chrome DevTools inspection showed `hasToggleScript: false` in the component properties, confirming JavaScript was stripped.

#### The Solution

Use Gradio's `.load()` event with the `js=` parameter instead of embedding `<script>` tags:

```python
# ✅ CORRECT - Use .load() event with js= parameter
with gr.Blocks() as demo:
    # Define your components
    logo = gr.HTML(
        value='<div class="agent-workbench-logo"><img src="/static/icons/logo_72.png"></div>',
        elem_classes=["agent-workbench-logo-container"]
    )

    chatbot = gr.Chatbot(elem_classes=["agent-workbench-messages"])

    # Add JavaScript via load event (MUST be inside with demo: context)
    demo.load(
        fn=None,
        js="""
        function() {
            // Your JavaScript code here
            console.log("This WILL execute on page load");

            const logo = document.querySelector('.agent-workbench-logo');
            const chatbot = document.querySelector('.agent-workbench-messages');

            // Example: Toggle visibility based on message count
            if (chatbot.children.length === 0) {
                logo.style.display = 'flex';
                chatbot.style.display = 'none';
            }
        }
        """
    )
```

#### Implementation Example - Logo/Chatbot Visibility Toggle

**File:** `src/agent_workbench/ui/mode_factory_v2.py:206-257`

```python
with gr.Blocks() as demo:
    # ... component definitions ...

    # Phase 4.2: Logo/chatbot visibility toggle on page load
    demo.load(
        fn=None,
        js="""
        function() {
            // Wait for Gradio to fully render
            setTimeout(() => {
                const chatbot = document.querySelector('.agent-workbench-messages');
                const logo = document.querySelector('.agent-workbench-logo');

                if (!chatbot || !logo) return;

                // Check if chatbot has real messages
                const messageElements = chatbot.querySelectorAll('[data-testid*="message"], .message, [role="user"], [role="assistant"]');
                const hasMessages = messageElements.length > 0;

                if (hasMessages) {
                    // Has messages: Hide logo, show chatbot
                    logo.style.display = 'none';
                    chatbot.style.display = 'block';
                } else {
                    // No messages: Show logo, hide chatbot
                    logo.style.display = 'flex';
                    chatbot.style.display = 'none';
                }

                // Watch for changes to chatbot (new messages)
                const observer = new MutationObserver(() => {
                    const msgs = chatbot.querySelectorAll('[data-testid*="message"]');
                    if (msgs.length > 0) {
                        logo.style.display = 'none';
                        chatbot.style.display = 'block';
                    }
                });

                observer.observe(chatbot, {
                    childList: true,
                    subtree: true,
                    characterData: true
                });
            }, 500);
        }
        """
    )
```

#### Key Requirements

1. **Context Requirement:** The `.load()` call MUST be inside the `with demo:` context block
2. **Timing:** Use `setTimeout()` to ensure DOM is fully rendered before accessing elements
3. **Error Handling:** Check for element existence before manipulating (`if (!element) return;`)
4. **MutationObserver:** Use for dynamic UI updates that need to watch for DOM changes

#### Common Pitfalls

❌ **Calling .load() outside context:**
```python
demo = gr.Blocks()
# ... define components ...
demo.load(...)  # ❌ May cause NameError or not execute
```

✅ **Calling .load() inside context:**
```python
with gr.Blocks() as demo:
    # ... define components ...
    demo.load(...)  # ✅ Correct
```

---

### Issue 2: Sidebar Conversation History Not Loading (gr.ChatInterface)

**Status:** 🔴 ACTIVE ISSUE - Under Investigation

#### The Problem

After switching from `gr.Chatbot` to `gr.ChatInterface` (Phase 4.2), the sidebar conversation history list stopped loading on page load. The `populate_list` function is not being called.

**Evidence:**
- No "populate_list" logs appear in server output on page load
- Sidebar is visible but empty (no conversation list items)
- The `@demo.load()` decorator (lines 193-204 in mode_factory_v2.py) appears to not be executing

#### Current Implementation

**File:** `src/agent_workbench/ui/mode_factory_v2.py:189-204`

```python
# Auto-load conversation history into Dataset list from BrowserState
# on page load (only for guest users - auth users use database)
if conversations_list_storage and conv_list:

    @demo.load(
        inputs=[user_state, conversations_list_storage], outputs=[conv_list]
    )
    def load_conversations_from_browser(user_state_val, stored_conversations):
        """
        Load conversation history from BrowserState (localStorage).

        For guest users only - authenticated users use database.
        """
        from .pages.chat import populate_list

        return populate_list(user_state_val, stored_conversations or [])
```

#### Suspected Root Cause

**Hypothesis:** The change from `gr.Chatbot` to `gr.ChatInterface` may affect:
1. **BrowserState initialization timing** - `gr.ChatInterface` might initialize components in a different order
2. **Component return values** - `chat.render()` returns `conversations_list_storage` and `conv_list`, but these might not be properly initialized when `gr.ChatInterface` is used
3. **Multiple demo.load() conflicts** - Having both:
   - A `@demo.load()` decorator (sidebar loading, lines 193-204)
   - A direct `demo.load()` call (logo toggle, lines 206-257)

   ...might cause the first one to be skipped or overridden

#### Investigation Steps Needed

1. **Add debug logging** to confirm whether `load_conversations_from_browser` is called:
   ```python
   def load_conversations_from_browser(user_state_val, stored_conversations):
       print("[DEBUG] load_conversations_from_browser CALLED!")
       print(f"  user_state: {user_state_val}")
       print(f"  stored_conversations: {len(stored_conversations or [])}")
       # ... rest of function
   ```

2. **Check if `conv_list` is None** after `chat.render()` returns:
   ```python
   conversations_list_storage, conv_list = chat.render(...)
   print(f"[DEBUG] After chat.render():")
   print(f"  conversations_list_storage: {conversations_list_storage}")
   print(f"  conv_list: {conv_list}")
   ```

3. **Test decorator pattern vs direct call** - Try changing from decorator to direct call:
   ```python
   # Instead of @demo.load() decorator
   demo.load(
       fn=load_conversations_from_browser,
       inputs=[user_state, conversations_list_storage],
       outputs=[conv_list]
   )
   ```

4. **Check gr.ChatInterface component hierarchy** - `gr.ChatInterface` wraps a `gr.Chatbot` internally, which might change how BrowserState interacts with the chatbot value initialization:
   ```python
   # In chat.py line 84-95
   chat_interface = gr.ChatInterface(
       fn=handle_chat_interface_message,
       chatbot=gr.Chatbot(
           value=(conversation_state.value if conversation_state.value else []),  # <-- This line
           # ...
       )
   )
   ```

#### Potential Fixes

**Option 1: Use direct demo.load() call instead of decorator**
```python
if conversations_list_storage and conv_list:
    def load_conversations_from_browser(user_state_val, stored_conversations):
        from .pages.chat import populate_list
        return populate_list(user_state_val, stored_conversations or [])

    # Direct call instead of decorator
    demo.load(
        fn=load_conversations_from_browser,
        inputs=[user_state, conversations_list_storage],
        outputs=[conv_list]
    )
```

**Option 2: Combine both load events into single call**
```python
demo.load(
    fn=load_conversations_from_browser,
    inputs=[user_state, conversations_list_storage],
    outputs=[conv_list],
    js="""
    function() {
        // Logo toggle JavaScript here
        setTimeout(() => {
            // ... logo/chatbot visibility logic ...
        }, 500);
    }
    """
)
```

**Option 3: Initialize BrowserState earlier**
```python
# Move BrowserState creation BEFORE gr.ChatInterface
conversations_list_storage = gr.BrowserState(
    default_value=[],
    storage_key="agent_workbench_conversations_list",
)

# Then create chat_interface with explicit value
chat_interface = gr.ChatInterface(
    chatbot=gr.Chatbot(
        value=[],  # Explicit empty value instead of conversation_state.value
        # ...
    )
)
```

#### Related Files
- `src/agent_workbench/ui/mode_factory_v2.py:189-257` - Load event definitions
- `src/agent_workbench/ui/pages/chat.py:39-44, 84-95` - BrowserState and ChatInterface setup
- `src/agent_workbench/ui/pages/chat.py:149-225` - `populate_list()` function

#### Status Tracking
- [ ] Add debug logging to confirm function execution
- [ ] Test decorator vs direct call pattern
- [ ] Test single combined load event
- [ ] Test BrowserState initialization order
- [ ] Verify gr.ChatInterface doesn't interfere with BrowserState

**Next Steps:** Add debug logging and test each potential fix systematically.

---

### When to Use .load() Event with js= Parameter

Use `demo.load()` with `js=` parameter for:
- ✅ Client-side DOM manipulation on page load
- ✅ Dynamic button state changes
- ✅ Visibility toggles based on UI state
- ✅ Event listeners for user interactions
- ✅ Third-party library initialization
- ✅ Custom animations and transitions

Do NOT use for:
- ❌ Server-side data processing (use Python functions instead)
- ❌ API calls (use Gradio's event handlers with Python backend)
- ❌ State management across sessions (use Gradio State)

### Browser Compatibility

This pattern works in all modern browsers:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**MutationObserver support:** All modern browsers (IE11+ with polyfill)

---

## Post-Implementation

**After Phase 4 Complete:**
1. Get user feedback (internal testing)
2. Iterate based on feedback
3. Consider merging `agent-workbench-design.css` into `shared.css` (if stable)
4. Update documentation with implementation notes
5. Create video walkthrough of design features

**Potential Enhancements (Phase 5):**
- Animated transitions between pages
- Custom scrollbars
- Advanced theme customization
- User-uploaded avatars
- Custom font size controls

---

**End of Document**
