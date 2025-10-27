# UI-005-chat-page: Minimal Chat Page with Conversation History Sidebar

**Status:** Draft
**Created:** 2025-01-27
**Dependencies:**
- UI-005-multi-page-app (routing foundation)
- UI-005-settings-page (model controls moved there)
- Existing conversation API endpoints
- Existing authentication system

---

## Overview

This document defines the chat page implementation with two key features:
1. **Minimal chat interface** - chatbox and input only (model controls moved to settings)
2. **Conversation history sidebar** - browser-style sidebar for loading previous conversations

**Rollout Strategy:**
- **Phase 1:** Workbench deployment only (feature flag enabled)
- **Phase 2:** SEO Coach deployment (experimental feature)

---

## Scope

### In Scope

1. **Minimal Chat Page UI**
   - Chatbox (gr.Chatbot)
   - Text input with send button
   - No model selector, no parameters (moved to settings)
   - Clean, focused chat experience

2. **Conversation History Sidebar**
   - Collapsible sidebar with conversation list
   - Card-based UI (title, timestamp, preview)
   - Click to load conversation into chatbox
   - Toggle button with animation
   - Click-away to collapse
   - Accessibility (ARIA attributes)

3. **Feature Flag Integration**
   - `SHOW_CONV_BROWSER` flag controls sidebar visibility
   - Enabled in workbench deployment
   - Disabled in seo_coach deployment (Phase 1)

4. **API Integration**
   - Use existing `/api/v1/conversations` endpoints
   - Use existing `/api/v1/conversations/{id}` endpoints
   - Use existing authentication (get_current_user)

### Out of Scope

- Settings page UI (covered in UI-005-settings-page)
- Routing implementation (covered in UI-005-multi-page-app)
- Full authentication system (covered in UI-007)
- New API endpoints (reuse existing)
- Conversation editing/deletion from sidebar (future enhancement)
- Search/filter in sidebar (future enhancement)

### Deferred to Future

- Pagination for long conversation lists
- Conversation tagging
- Conversation search
- Conversation rename from sidebar
- Multi-select for bulk operations

---

## Architecture Decisions

### Decision 1: Minimal Chat Page (Model Controls to Settings)

**Problem:** Current implementation has model selector, provider selector, and parameters cluttering the chat page.

**Solution:** Move all model controls to settings page, keep chat page minimal.

**Chat Page Contains:**
- Chatbox (gr.Chatbot) - displays conversation
- Text input (gr.Textbox) - user message entry
- Send button (gr.Button) - submit message
- Chat history sidebar (conditionally via feature flag)

**Rationale:**
- Clean, focused chat experience (like modern chat apps)
- Reduces cognitive load for users
- Settings are configuration, not conversation
- Matches target UX (Ollama-inspired minimal design)

### Decision 2: Sidebar Toggle Method - Hybrid Approach

**Problem:** Three possible toggle methods, each with tradeoffs:

| Method | How it works | Pros | Cons |
|--------|-------------|------|------|
| CSS Class Toggle | JavaScript adds/removes `gr-sidebar-collapsed` class | Fast, no state management, instant | Requires JS, not part of app state |
| Global Click-Away | One JS handler on root that collapses on outside click | Good UX, no manual close needed | Requires careful event handling |
| State + visible Flag | `gr.State` drives sidebar's `visible` attribute | Pure Python, testable, accessible | Re-render overhead, slight flicker |

**Solution:** Use hybrid approach combining all three:

1. **State as source of truth** - `gr.State(True)` for testability
2. **CSS class for instant feedback** - JS toggles class immediately
3. **Click-away for UX** - Global listener collapses on outside click

**Implementation Pattern:**

```python
# 1️⃣ State (source of truth)
sidebar_visible = gr.State(True)

# 2️⃣ Sidebar wrapped in Column with visible flag
with gr.Column(visible=sidebar_visible) as wrapper:
    with gr.Sidebar(position="left") as sb:
        # Conversation list UI
        conv_list_html = gr.HTML(elem_id="conv-sidebar")
        collapse_btn = gr.Button("Hide sidebar", variant="stop")

# 3️⃣ Pure Python toggle
collapse_btn.click(
    fn=lambda visible: not visible,
    inputs=sidebar_visible,
    outputs=sidebar_visible
)

# 4️⃣ CSS class toggle (instant feedback)
collapse_btn.click(
    fn=None,
    js="""
        const sb = document.querySelector('.gr-sidebar');
        const collapsed = sb.classList.toggle('gr-sidebar-collapsed');
        sb.setAttribute('aria-hidden', collapsed);
    """
)

# 5️⃣ Global click-away listener
demo.add_js("""
    document.querySelector('.gradio-app').addEventListener('click', function(e){
        const sb = document.querySelector('.gr-sidebar');
        if (!sb.contains(e.target)) {
            sb.classList.add('gr-sidebar-collapsed');
            sb.setAttribute('aria-hidden', 'true');
        }
    });
""")
```

**CSS for Animation:**

```css
.gr-sidebar.gr-sidebar-collapsed {
    width: 0 !important;
    overflow: hidden;
    opacity: 0;
    transition: width 0.3s ease, opacity 0.3s ease;
}
.gr-sidebar {
    transition: width 0.3s ease, opacity 0.3s ease;
}
```

**Rationale:**
- State makes it testable (can assert on `sidebar_visible.value`)
- CSS toggle provides instant visual feedback
- Click-away improves UX (no manual close needed)
- ARIA attributes ensure accessibility
- Animation provides smooth transition

### Decision 3: Conversation List UI - Card-Based HTML

**Problem:** Need to display conversation list with title, timestamp, and preview.

**Solution:** Use `gr.HTML` with card-based UI populated via JavaScript fetch.

**Implementation:**

```python
def render_conv_sidebar(config: Dict[str, Any], user_state: gr.State) -> Tuple[gr.HTML, Callable]:
    """Render conversation history sidebar (feature-flagged)."""

    # Feature flag check
    if not config.get("show_conv_browser", False):
        return None, None

    # HTML container for cards
    sidebar_html = gr.HTML(elem_id="conv-sidebar", label="Recent Chats")

    # JavaScript to populate on load
    populate_js = """
    <script>
    (async () => {
        try {
            const res = await fetch('/api/v1/conversations', {
                credentials: 'include'  // send auth cookie
            });

            if (!res.ok) {
                console.error('Failed to fetch conversations');
                return;
            }

            const convs = await res.json();
            const container = document.getElementById('conv-sidebar');

            container.innerHTML = convs.map(c => `
                <div class="conv-card" data-id="${c.id}">
                    <strong>${c.title || 'Untitled'}</strong><br/>
                    <small>${new Date(c.updated_at).toLocaleString()}</small><br/>
                    <p>${(c.preview || '').substring(0, 100)}</p>
                </div>
            `).join('');

            // Click handler for cards
            document.querySelectorAll('.conv-card').forEach(el => {
                el.addEventListener('click', async () => {
                    const convId = el.dataset.id;

                    // Fetch full conversation
                    const conv = await fetch(`/api/v1/conversations/${convId}`, {
                        credentials: 'include'
                    }).then(r => r.json());

                    // Load into chatbot (trigger Gradio event)
                    window.dispatchEvent(new CustomEvent('load-conversation', {
                        detail: { messages: conv.messages }
                    }));
                });
            });
        } catch (err) {
            console.error('Error loading conversations:', err);
        }
    })();
    </script>
    """

    return sidebar_html, populate_js
```

**Card Styling:**

```css
#conv-sidebar .conv-card {
    border: 1px solid var(--border-color-primary, #e0e0e0);
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s;
    background: var(--background-fill-primary, #fff);
}

#conv-sidebar .conv-card:hover {
    background: var(--background-fill-secondary, #f5f5f5);
    border-color: var(--color-accent, #3b82f6);
}

#conv-sidebar .conv-card strong {
    font-size: 14px;
    font-weight: 600;
    color: var(--body-text-color, #000);
}

#conv-sidebar .conv-card small {
    font-size: 11px;
    color: var(--body-text-color-subdued, #666);
}

#conv-sidebar .conv-card p {
    font-size: 12px;
    color: var(--body-text-color-subdued, #666);
    margin-top: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
```

**Rationale:**
- `gr.HTML` is lightweight and highly stylable
- JavaScript fetch uses existing API endpoints
- Card-based UI is familiar (like email clients, chat apps)
- CSS variables ensure theme compatibility
- Click handler dispatches custom event for Gradio integration

### Decision 4: Feature Flag Strategy

**Problem:** Sidebar should only appear in workbench deployment initially.

**Solution:** Use `SHOW_CONV_BROWSER` environment variable flag.

**Configuration Pattern:**

```python
# mode_factory.py
def create_workbench_app() -> gr.Blocks:
    """Workbench mode - sidebar enabled."""
    config = {
        "title": "Agent Workbench",
        "theme": gr.themes.Base(primary_hue="#3b82f6"),
        "labels": {...},
        "show_conv_browser": os.getenv("SHOW_CONV_BROWSER", "true").lower() == "true",
        # ... other config
    }
    return build_gradio_app(config)

def create_seo_app() -> gr.Blocks:
    """SEO Coach mode - sidebar disabled initially."""
    config = {
        "title": "SEO Coach",
        "theme": gr.themes.Base(primary_hue="#10b981"),
        "labels": {...},
        "show_conv_browser": os.getenv("SHOW_CONV_BROWSER", "false").lower() == "true",
        # ... other config
    }
    return build_gradio_app(config)
```

**Docker Environment:**

```dockerfile
# Workbench image
ENV APP_MODE=workbench
ENV SHOW_CONV_BROWSER=true

# SEO Coach image
ENV APP_MODE=seo_coach
ENV SHOW_CONV_BROWSER=false
```

**Render Logic:**

```python
def render_chat_page(config: Dict[str, Any], user_state: gr.State, conversation_state: gr.State):
    """Render chat page with optional sidebar."""

    # Sidebar (conditionally rendered)
    if config.get("show_conv_browser", False):
        sidebar_html, populate_js = render_conv_sidebar(config, user_state)
        sidebar_html.render()
        gr.HTML(populate_js)  # Inject population script

    # Main chat area (always rendered)
    with gr.Column():
        chatbot = gr.Chatbot(elem_id="chatbot", height=600)

        with gr.Row():
            msg = gr.Textbox(
                placeholder=config['labels']['input_placeholder'],
                show_label=False,
                container=False,
                scale=9
            )
            send = gr.Button(
                config['labels']['send_button'],
                variant="primary",
                scale=1
            )
```

**Rationale:**
- Environment variable allows runtime configuration
- Same codebase, different deployments
- Easy to toggle for testing
- No code changes needed to enable/disable
- Can be overridden per deployment

### Decision 5: API Integration (Reuse Existing)

**Problem:** Need to list and load conversations.

**Solution:** Use existing API endpoints - no new endpoints required.

**Existing Endpoints:**

```python
# Already implemented in api/routes/conversations.py

GET    /api/v1/conversations           # List user's conversations
GET    /api/v1/conversations/{id}      # Get conversation details
GET    /api/v1/conversations/{id}/messages  # Get conversation messages
```

**Expected Response Format:**

```json
// GET /api/v1/conversations
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Chat about Python",
    "created_at": "2025-01-27T10:00:00Z",
    "updated_at": "2025-01-27T10:15:00Z",
    "preview": "Can you help me with async/await?"
  }
]

// GET /api/v1/conversations/{id}
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Chat about Python",
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:15:00Z",
  "messages": [
    {"role": "user", "content": "Can you help me with async/await?"},
    {"role": "assistant", "content": "Sure! async/await is..."}
  ]
}
```

**Authentication:**

```python
# Existing authentication dependency
from api.dependencies import get_current_user

@router.get("/api/v1/conversations")
async def list_conversations(user=Depends(get_current_user)):
    """List user's conversations - already implements user isolation."""
    # Implementation already exists
    pass
```

**Rationale:**
- No new endpoints needed
- API already implements user isolation
- Authentication already handles security
- Response format already matches UI needs
- No backend changes required

### Decision 6: Conversation Loading Pattern

**Problem:** How to load a conversation from sidebar click into the chatbot.

**Solution:** Use custom JavaScript event + Gradio event handler.

**Implementation:**

```python
# In chat page render function
def render_chat_page(config, user_state, conversation_state):
    # ... chatbot setup ...

    # Hidden state for conversation loading
    load_conv_trigger = gr.State(None)

    # Event handler for loading conversation
    def load_conversation(conv_data: Optional[Dict]) -> List[Tuple[str, str]]:
        """Load conversation messages into chatbot."""
        if not conv_data:
            return []

        messages = conv_data.get("messages", [])

        # Convert to chatbot format (user, assistant pairs)
        chatbot_history = []
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                user_msg = messages[i]["content"]
                assistant_msg = messages[i + 1]["content"]
                chatbot_history.append((user_msg, assistant_msg))

        return chatbot_history

    # Wire custom event listener
    gr.HTML("""
    <script>
    window.addEventListener('load-conversation', async (e) => {
        const convId = e.detail.conversationId;

        // Fetch full conversation
        const res = await fetch(`/api/v1/conversations/${convId}`, {
            credentials: 'include'
        });
        const conv = await res.json();

        // Trigger Gradio state update
        gradio.State.set('load_conv_trigger', conv);
    });
    </script>
    """)

    # Connect state change to chatbot update
    load_conv_trigger.change(
        fn=load_conversation,
        inputs=[load_conv_trigger],
        outputs=[chatbot]
    )
```

**Rationale:**
- Custom event provides clean separation
- Gradio state bridges JavaScript to Python
- Existing conversation format works as-is
- No polling or websockets needed
- Testable (can trigger state directly in tests)

### Decision 7: Visual Enhancements (Deferred to Target UX)

**Problem:** Should visual polish (Ubuntu font, dynamic logo, connectivity status) be part of chat page implementation?

**Solution:** Implement functional foundation first, defer visual polish to separate phase.

**Visual Elements Deferred to UI-005-target-ux-implementation:**

1. **Ubuntu Font Integration** (UI-005-target-ux lines 620-684)
   - Font file loading (`@font-face` declarations)
   - Gradio theme font configuration
   - CSS font-family overrides

2. **Dynamic Logo Behavior** (UI-005-target-ux lines 299-317)
   - Logo fade during processing
   - Processing icon display
   - Agent status icons
   - Logo return on new chat

3. **Connectivity Status Indicator** (UI-005-target-ux lines 686-763)
   - Cloud on/off icon in header
   - Online/offline detection (navigator.onLine)
   - Feature degradation when offline
   - Airplane mode integration

4. **iOS-Style Visual Elements**
   - Processing state animations
   - Smooth transitions
   - Submit button icon changes
   - Status bubble styling

**Implementation in Chat Page (Functional Foundation):**
- Basic chatbox and input (no visual polish)
- Standard Gradio styling
- Functional sidebar toggle
- Working conversation loading

**Visual Polish Added Later:**
- Apply Ubuntu font (Phase 2)
- Add dynamic logo (Phase 2)
- Add connectivity indicator (Phase 2)
- Enhance animations (Phase 2)

**Rationale:**
- Ship functional foundation faster (reduces risk)
- Separate concerns (routing/functionality vs visual design)
- Allows testing core features before polish
- Visual refinements can iterate based on user feedback
- Easier rollback if issues found
- Follows "make it work, make it right, make it fast" principle

**Cross-Reference:**
- See `UI-005-target-ux-implementation.md` for complete visual specifications
- Ubuntu font: lines 620-684
- Dynamic logo: lines 267-317
- Connectivity status: lines 686-763
- Theme system: lines 916-993

---

## Implementation Plan

### Phase 1: Minimal Chat Page (No Sidebar)

**Goal:** Remove model controls from chat page, move to settings.

**Steps:**

1. **Update chat page render function** (`ui/pages/chat.py`)
   ```python
   def render(config: Dict[str, Any], user_state: gr.State, conversation_state: gr.State):
       """Render minimal chat page."""

       with gr.Column():
           # Chatbot
           chatbot = gr.Chatbot(
               elem_id="chatbot",
               height=600,
               show_label=False,
               container=True
           )

           # Input row
           with gr.Row():
               msg = gr.Textbox(
                   placeholder=config['labels']['input_placeholder'],
                   show_label=False,
                   container=False,
                   scale=9
               )
               send = gr.Button(
                   config['labels']['send_button'],
                   variant="primary",
                   scale=1
               )

           # Wire send button (reuse existing handle_chat_message)
           send.click(
               fn=handle_chat_message,
               inputs=[msg, chatbot, user_state, conversation_state],
               outputs=[chatbot, msg, conversation_state]
           )
   ```

2. **Remove model controls** (no provider/model dropdowns, no sliders)

3. **Update CSS** for minimal layout
   ```css
   #chatbot {
       border-radius: 12px;
       border: 1px solid var(--border-color-primary);
   }

   #chatbot .message {
       padding: 12px 16px;
   }
   ```

4. **Test with existing backend** (no changes needed)

**Success Criteria:**
- Chat page shows only chatbox and input
- Model selection works from settings page
- No visual clutter on chat page
- Existing chat functionality unchanged

### Phase 2: Sidebar UI Structure (No Loading Yet)

**Goal:** Add collapsible sidebar with static content.

**Steps:**

1. **Add sidebar to chat page**
   ```python
   # Feature flag check
   if config.get("show_conv_browser", False):
       with gr.Sidebar(position="left") as sb:
           gr.Markdown("## Recent Chats")
           conv_list_html = gr.HTML(elem_id="conv-sidebar")
           collapse_btn = gr.Button("Hide", variant="secondary")
   ```

2. **Add toggle logic** (hybrid approach)
   ```python
   # State
   sidebar_visible = gr.State(True)

   # Toggle button
   collapse_btn.click(
       fn=lambda v: not v,
       inputs=[sidebar_visible],
       outputs=[sidebar_visible]
   )

   # CSS toggle
   collapse_btn.click(
       fn=None,
       js="document.querySelector('.gr-sidebar').classList.toggle('gr-sidebar-collapsed');"
   )
   ```

3. **Add CSS for animation**

4. **Add click-away listener**

**Success Criteria:**
- Sidebar appears in workbench mode
- Sidebar hidden in seo_coach mode
- Toggle button works
- Click-away collapses sidebar
- Animation is smooth
- ARIA attributes set correctly

### Phase 3: Conversation List Population

**Goal:** Fetch and display conversation list.

**Steps:**

1. **Add JavaScript fetch logic**
   ```javascript
   const res = await fetch('/api/v1/conversations', {
       credentials: 'include'
   });
   const convs = await res.json();
   ```

2. **Render cards**
   ```javascript
   container.innerHTML = convs.map(c => `
       <div class="conv-card" data-id="${c.id}">
           <strong>${c.title}</strong><br/>
           <small>${new Date(c.updated_at).toLocaleString()}</small><br/>
           <p>${c.preview}</p>
       </div>
   `).join('');
   ```

3. **Add card styling** (CSS from Decision 3)

4. **Test with mock data**

**Success Criteria:**
- Conversation list populates on page load
- Cards display title, timestamp, preview
- Empty state shows helpful message
- Error handling shows user-friendly message
- Loading state prevents multiple fetches

### Phase 4: Conversation Loading

**Goal:** Load conversation into chatbot on card click.

**Steps:**

1. **Add click handler to cards**
   ```javascript
   el.addEventListener('click', async () => {
       const convId = el.dataset.id;
       const conv = await fetch(`/api/v1/conversations/${convId}`, {
           credentials: 'include'
       }).then(r => r.json());

       window.dispatchEvent(new CustomEvent('load-conversation', {
           detail: { conversationId: convId }
       }));
   });
   ```

2. **Add custom event listener**

3. **Add conversation loading handler**

4. **Wire to chatbot state**

**Success Criteria:**
- Clicking card loads conversation
- Chatbot displays full conversation history
- Conversation state updates correctly
- Can continue conversation after loading
- Loading indicator shows during fetch

### Phase 5: Polish & Accessibility

**Goal:** Production-ready sidebar with full accessibility.

**Steps:**

1. **Add ARIA attributes**
   ```javascript
   sb.setAttribute('aria-hidden', collapsed);
   sb.setAttribute('aria-label', 'Conversation history');
   ```

2. **Add keyboard navigation**
   - Tab through conversation cards
   - Enter to load conversation
   - Escape to close sidebar

3. **Add loading states**
   - Skeleton cards while fetching
   - Spinner on conversation load

4. **Add error handling**
   - Network error toast
   - Empty state message
   - Retry button

5. **Add tests** (see Testing Strategy below)

**Success Criteria:**
- Screen reader announces sidebar state
- Keyboard navigation works
- Loading states prevent confusion
- Errors show helpful messages
- All tests pass

---

## Testing Strategy

### Unit Tests

```python
# tests/ui/test_chat_page.py

def test_chat_page_minimal_ui():
    """Test chat page renders without model controls."""
    config = {"show_conv_browser": False, "labels": {...}}
    user_state = gr.State(None)
    conversation_state = gr.State([])

    # Render should not raise
    render_chat_page(config, user_state, conversation_state)

    # Should contain chatbot and input
    # Should NOT contain model selector

def test_sidebar_feature_flag_off():
    """Test sidebar hidden when flag is false."""
    config = {"show_conv_browser": False}
    # Sidebar should not render

def test_sidebar_feature_flag_on():
    """Test sidebar visible when flag is true."""
    config = {"show_conv_browser": True}
    # Sidebar should render

def test_sidebar_toggle():
    """Test sidebar toggle changes state."""
    sidebar_visible = gr.State(True)
    # Click toggle button
    # Assert state is False

def test_load_conversation():
    """Test conversation loading formats messages correctly."""
    conv_data = {
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
    }
    result = load_conversation(conv_data)
    assert result == [("Hello", "Hi there")]
```

### Integration Tests

```python
# tests/integration/test_chat_sidebar.py

@pytest.mark.asyncio
async def test_conversation_list_api():
    """Test /api/v1/conversations returns user's conversations."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create test user and conversations
        # Fetch conversation list
        # Assert correct conversations returned

@pytest.mark.asyncio
async def test_conversation_load_api():
    """Test /api/v1/conversations/{id} returns conversation details."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create test conversation
        # Fetch conversation details
        # Assert messages returned correctly

@pytest.mark.asyncio
async def test_user_isolation():
    """Test user can only see their own conversations."""
    # Create two users with different conversations
    # User 1 should only see their conversations
    # User 2 should only see their conversations
```

### E2E Tests (Playwright)

```python
# tests/e2e/test_sidebar.py

async def test_sidebar_toggle_animation(page):
    """Test sidebar collapse animation."""
    await page.goto("http://localhost:8000/")

    # Wait for sidebar
    await page.wait_for_selector(".gr-sidebar")

    # Click toggle button
    await page.click("text=Hide sidebar")

    # Assert sidebar has collapsed class
    sidebar = await page.query_selector(".gr-sidebar")
    classes = await sidebar.get_attribute("class")
    assert "gr-sidebar-collapsed" in classes

    # Assert ARIA attribute
    aria_hidden = await sidebar.get_attribute("aria-hidden")
    assert aria_hidden == "true"

async def test_conversation_card_click(page):
    """Test clicking conversation card loads conversation."""
    await page.goto("http://localhost:8000/")

    # Wait for conversation list
    await page.wait_for_selector(".conv-card")

    # Click first card
    await page.click(".conv-card:first-child")

    # Wait for chatbot to update
    await page.wait_for_selector("#chatbot .message")

    # Assert conversation loaded
    messages = await page.query_selector_all("#chatbot .message")
    assert len(messages) > 0

async def test_click_away_collapses_sidebar(page):
    """Test clicking outside sidebar collapses it."""
    await page.goto("http://localhost:8000/")

    # Sidebar starts expanded
    sidebar = await page.query_selector(".gr-sidebar")
    classes = await sidebar.get_attribute("class")
    assert "gr-sidebar-collapsed" not in classes

    # Click outside sidebar
    await page.click("#chatbot")

    # Wait for animation
    await page.wait_for_timeout(500)

    # Assert sidebar collapsed
    classes = await sidebar.get_attribute("class")
    assert "gr-sidebar-collapsed" in classes
```

### Accessibility Tests

```python
# tests/accessibility/test_sidebar_a11y.py

async def test_sidebar_aria_attributes(page):
    """Test sidebar has correct ARIA attributes."""
    await page.goto("http://localhost:8000/")

    sidebar = await page.query_selector(".gr-sidebar")

    # Check aria-label
    label = await sidebar.get_attribute("aria-label")
    assert label is not None

    # Check aria-hidden when collapsed
    await page.click("text=Hide sidebar")
    aria_hidden = await sidebar.get_attribute("aria-hidden")
    assert aria_hidden == "true"

async def test_keyboard_navigation(page):
    """Test sidebar can be navigated with keyboard."""
    await page.goto("http://localhost:8000/")

    # Tab to first conversation card
    await page.keyboard.press("Tab")
    # ... (continue tabbing to sidebar)

    # Press Enter to load conversation
    await page.keyboard.press("Enter")

    # Assert conversation loaded
    messages = await page.query_selector_all("#chatbot .message")
    assert len(messages) > 0
```

---

## Success Criteria

### Minimal Chat Page

- ✅ Chat page renders without model controls
- ✅ Chatbox displays conversation history
- ✅ Text input accepts user messages
- ✅ Send button submits messages
- ✅ Model selection works from settings page
- ✅ No visual clutter on chat page
- ✅ Existing chat functionality unchanged

### Conversation History Sidebar

- ✅ Sidebar appears in workbench mode when flag enabled
- ✅ Sidebar hidden in seo_coach mode when flag disabled
- ✅ Conversation list fetches from API on page load
- ✅ Cards display title, timestamp, and preview
- ✅ Clicking card loads conversation into chatbot
- ✅ Toggle button collapses/expands sidebar
- ✅ Click-away collapses sidebar
- ✅ Animation is smooth (300ms transition)
- ✅ ARIA attributes set correctly
- ✅ Keyboard navigation works
- ✅ Loading states prevent confusion
- ✅ Error states show helpful messages
- ✅ Empty state shows helpful message
- ✅ User isolation enforced (can't see other users' conversations)

### Code Quality

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ All E2E tests pass
- ✅ All accessibility tests pass
- ✅ Code passes linting (ruff)
- ✅ Code passes formatting (black)
- ✅ Code passes type checking (mypy)
- ✅ Test coverage > 80%

---

## Known Issues & Open Questions

### Known Issues

1. **State Persistence Across Page Reloads**
   - Sidebar collapsed state not persisted
   - User has to re-collapse after refresh
   - **Resolution:** Defer to future enhancement (use localStorage)

2. **Conversation List Pagination**
   - No pagination for long conversation lists
   - Could cause performance issues with 100+ conversations
   - **Resolution:** Defer to future enhancement (implement pagination)

3. **Search/Filter in Sidebar**
   - No way to search conversations
   - Hard to find old conversations
   - **Resolution:** Defer to future enhancement (add search bar)

### Open Questions

1. **Should sidebar be on left or right?**
   - Left: Matches file explorers, feels more primary
   - Right: Matches chat apps (WhatsApp, Slack)
   - **Decision:** Left for workbench (developer tool), revisit for seo_coach

2. **Should conversation title be auto-generated?**
   - Current: First user message becomes title
   - Alternative: LLM-generated title from conversation
   - **Decision:** Use first message for now, add LLM title generation later

3. **Should sidebar show conversation count?**
   - E.g., "Recent Chats (23)"
   - **Decision:** Yes, add count in header

4. **Should sidebar have "New Chat" button?**
   - Convenient way to start fresh conversation
   - **Decision:** Yes, add button at top of sidebar

---

## Migration Path

### From Current Implementation

**Current State:**
- Chat page has model controls
- No conversation history UI
- Settings page doesn't exist yet

**Migration Steps:**

1. **Implement UI-005-multi-page-app** (routing foundation)
2. **Implement UI-005-settings-page** (move model controls)
3. **Implement Phase 1 of this document** (minimal chat page)
4. **Test thoroughly** (ensure chat still works)
5. **Implement Phase 2-4** (sidebar with conversation loading)
6. **Enable flag in workbench deployment**
7. **Monitor usage and feedback**
8. **Enable flag in seo_coach deployment** (Phase 2)

### Rollback Plan

If issues are found:

1. **Disable flag** (`SHOW_CONV_BROWSER=false`)
2. **Sidebar disappears, chat page still works**
3. **No database changes needed** (using existing API)
4. **No user data loss** (conversations still in DB)

---

## Future Enhancements

### Conversation Management

- Rename conversations
- Delete conversations
- Archive conversations
- Pin important conversations
- Tag conversations

### Search & Filter

- Full-text search in conversations
- Filter by date range
- Filter by tags
- Sort options (recent, alphabetical, etc.)

### Performance

- Pagination (load 20 at a time)
- Virtual scrolling for large lists
- Debounced search
- Lazy loading of conversation details

### Collaboration

- Share conversations (generate link)
- Export conversations (markdown, JSON, PDF)
- Conversation templates

### Analytics

- Conversation length tracking
- Token usage per conversation
- Most active conversations
- Conversation sentiment analysis

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-01-27 | Use hybrid toggle approach (state + CSS + click-away) | Best of all worlds: testable, instant feedback, good UX |
| 2025-01-27 | Use `gr.HTML` for conversation cards | Lightweight, highly stylable, no new components |
| 2025-01-27 | Feature flag for sidebar visibility | Phased rollout, easy to disable, no code changes |
| 2025-01-27 | Reuse existing API endpoints | No backend changes, user isolation already implemented |
| 2025-01-27 | Custom JavaScript event for loading | Clean separation, testable, no polling needed |
| 2025-01-27 | Sidebar on left side | Matches developer tools, feels primary |
| 2025-01-27 | Move model controls to settings | Cleaner chat experience, matches modern chat apps |

---

## References

- **UI-005-multi-page-app.md** - Routing foundation with mode factory pattern
- **UI-005-settings-page.md** - Settings implementation (model controls destination)
- **UI-005-target-ux-implementation.md** - Visual design specifications
- **Feat-dev-plan-chat-history-in-sidebar-in-chatpage.md** - Original feature brainstorm
- **Gradio Sidebar Documentation** - https://www.gradio.app/docs/sidebar
- **Gradio State Documentation** - https://www.gradio.app/docs/state
- **ARIA Best Practices** - https://www.w3.org/WAI/ARIA/apg/

---

## Appendix: Complete Example

### Full Chat Page Implementation

```python
# ui/pages/chat.py

import gradio as gr
from typing import Dict, Any, Optional, List, Tuple
import os

def render(config: Dict[str, Any], user_state: gr.State, conversation_state: gr.State):
    """
    Render minimal chat page with optional conversation history sidebar.

    Args:
        config: Mode-specific configuration (includes feature flags)
        user_state: Shared user authentication state
        conversation_state: Shared conversation state
    """

    # Sidebar toggle state (source of truth)
    sidebar_visible = gr.State(True)

    # Conversation loading trigger
    load_conv_trigger = gr.State(None)

    # Main layout
    with gr.Row():
        # Sidebar (conditionally rendered)
        if config.get("show_conv_browser", False):
            with gr.Column(visible=sidebar_visible, scale=2) as sidebar_wrapper:
                with gr.Sidebar(position="left", elem_id="conv-sidebar-container") as sb:
                    gr.Markdown("## Recent Chats")

                    # Conversation list container
                    conv_list_html = gr.HTML(elem_id="conv-sidebar")

                    # New chat button
                    new_chat_btn = gr.Button("+ New Chat", variant="primary", size="sm")

                    # Collapse button
                    collapse_btn = gr.Button("Hide", variant="secondary", size="sm")

            # Toggle logic (hybrid approach)
            collapse_btn.click(
                fn=lambda v: not v,
                inputs=[sidebar_visible],
                outputs=[sidebar_visible]
            )

            collapse_btn.click(
                fn=None,
                js="""
                    const sb = document.querySelector('.gr-sidebar');
                    const collapsed = sb.classList.toggle('gr-sidebar-collapsed');
                    sb.setAttribute('aria-hidden', collapsed);
                """
            )

        # Main chat area
        with gr.Column(scale=8):
            # Chatbot
            chatbot = gr.Chatbot(
                elem_id="chatbot",
                height=600,
                show_label=False,
                container=True,
                bubble_full_width=False
            )

            # Input row
            with gr.Row():
                msg = gr.Textbox(
                    placeholder=config['labels']['input_placeholder'],
                    show_label=False,
                    container=False,
                    scale=9
                )
                send = gr.Button(
                    config['labels']['send_button'],
                    variant="primary",
                    scale=1
                )

            # Wire send button (reuse existing handler)
            send.click(
                fn=handle_chat_message,
                inputs=[msg, chatbot, user_state, conversation_state],
                outputs=[chatbot, msg, conversation_state]
            )

    # JavaScript for sidebar population (if enabled)
    if config.get("show_conv_browser", False):
        gr.HTML("""
        <script>
        (async () => {
            try {
                const res = await fetch('/api/v1/conversations', {
                    credentials: 'include'
                });

                if (!res.ok) {
                    console.error('Failed to fetch conversations');
                    return;
                }

                const convs = await res.json();
                const container = document.getElementById('conv-sidebar');

                if (convs.length === 0) {
                    container.innerHTML = '<p style="color: #666; padding: 16px;">No conversations yet</p>';
                    return;
                }

                container.innerHTML = convs.map(c => `
                    <div class="conv-card" data-id="${c.id}">
                        <strong>${c.title || 'Untitled'}</strong><br/>
                        <small>${new Date(c.updated_at).toLocaleString()}</small><br/>
                        <p>${(c.preview || '').substring(0, 100)}</p>
                    </div>
                `).join('');

                // Click handler
                document.querySelectorAll('.conv-card').forEach(el => {
                    el.addEventListener('click', async () => {
                        const convId = el.dataset.id;

                        // Fetch full conversation
                        const conv = await fetch(`/api/v1/conversations/${convId}`, {
                            credentials: 'include'
                        }).then(r => r.json());

                        // Dispatch custom event
                        window.dispatchEvent(new CustomEvent('load-conversation', {
                            detail: { conversationId: convId, messages: conv.messages }
                        }));
                    });
                });
            } catch (err) {
                console.error('Error loading conversations:', err);
                document.getElementById('conv-sidebar').innerHTML =
                    '<p style="color: #f00; padding: 16px;">Error loading conversations</p>';
            }
        })();

        // Global click-away listener
        document.querySelector('.gradio-app').addEventListener('click', function(e) {
            const sb = document.querySelector('.gr-sidebar');
            if (sb && !sb.contains(e.target)) {
                sb.classList.add('gr-sidebar-collapsed');
                sb.setAttribute('aria-hidden', 'true');
            }
        });

        // Custom event listener for conversation loading
        window.addEventListener('load-conversation', async (e) => {
            const messages = e.detail.messages;
            // Trigger Gradio state update (implementation depends on your state structure)
            // This is a placeholder - actual implementation will vary
        });
        </script>
        """)

def handle_chat_message(
    message: str,
    history: List[Tuple[str, str]],
    user_state: Optional[Dict],
    conversation_state: Optional[Dict]
) -> Tuple[List[Tuple[str, str]], str, Dict]:
    """
    Handle chat message submission (reuse existing implementation).

    This function already exists - we're just reusing it.
    """
    # Implementation from existing code
    pass
```

### CSS Styling

```css
/* Sidebar collapse animation */
.gr-sidebar.gr-sidebar-collapsed {
    width: 0 !important;
    overflow: hidden;
    opacity: 0;
    transition: width 0.3s ease, opacity 0.3s ease;
}

.gr-sidebar {
    transition: width 0.3s ease, opacity 0.3s ease;
}

/* Conversation cards */
#conv-sidebar .conv-card {
    border: 1px solid var(--border-color-primary, #e0e0e0);
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s;
    background: var(--background-fill-primary, #fff);
}

#conv-sidebar .conv-card:hover {
    background: var(--background-fill-secondary, #f5f5f5);
    border-color: var(--color-accent, #3b82f6);
}

#conv-sidebar .conv-card strong {
    font-size: 14px;
    font-weight: 600;
    color: var(--body-text-color, #000);
}

#conv-sidebar .conv-card small {
    font-size: 11px;
    color: var(--body-text-color-subdued, #666);
}

#conv-sidebar .conv-card p {
    font-size: 12px;
    color: var(--body-text-color-subdued, #666);
    margin-top: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Chatbot styling */
#chatbot {
    border-radius: 12px;
    border: 1px solid var(--border-color-primary);
}

#chatbot .message {
    padding: 12px 16px;
}
```

---

**End of Document**
