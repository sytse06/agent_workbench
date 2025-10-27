Feature development plan for sidebar in chatpage which gives user access to earlier conversations via the ui. Below is a complete recipe: db, API endpoints, Gradio UI, feature‑flag workflow, and CI testing plan. First introduced as a separate experimental feature in workbench and later introduced in both deployment environments. Remember the code you see in this feature plan is boilerplate code. For real code do your checks and balances to integrate it into existing code.

-------------------
First phase: introduce “Earlier‑Conversations” in UI in workbench deployment first. 

> *You want a **browser‑style sidebar** (or modal) that lets the user click on any previous chat and load it into the same Gradio chat box.*  
> The conversations already exist in the DB – you just need a UI layer to fetch, list, and hydrate them.

Below is a **complete recipe**: database schema, API endpoints, Gradio UI, feature‑flag workflow, and CI testing plan.  Everything lives in the *same code base* and the UI component is turned on only in the Workbench image.

---

## 1.  Data Model

In the ConversationService you have the method to get conversation history with its api routes.

service = ConversationService()

# Get or create conversation
conv = service.get_or_create(conversation_id="550e8400-...")

# Add message
message_id = service.add_message(
    conv_id="550e8400-...",
    role="user",
    content="Hello, world!"
)

# Get conversation history
history = service.get_history(conversation_id="550e8400-...")
```

#### FastAPI Routes

```python
Location: api/routes/conversations.py

# Conversation endpoints
POST   /api/v1/conversations           - Create conversation
GET    /api/v1/conversations/{id}      - Get conversation
GET    /api/v1/conversations           - List conversations
PUT    /api/v1/conversations/{id}      - Update conversation
DELETE /api/v1/conversations/{id}      - Delete conversation

# Conversation state
GET    /api/v1/conversations/{id}/state - Get conversation state 

**We should check if it is indexed and use this for a fast lookup**

**We should also check if a chat conversation is automatically saved to db**

---

## 2.  Backend API (boilerplate code!)

> **Endpoints**  
> 1. `GET /api/conversations` – list the user’s chats (title, dates, preview).  
> 2. `GET /api/conversations/{id}` – fetch the full conversation.

```python
# app/routers/conversations.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.db import get_db  # asyncpg connection pool or SQLAlchemy async session
from app.auth import get_current_user  # returns User object

router = APIRouter(prefix="/api/conversations")

class ConvSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    preview: str  # first 100 chars of last message

class Message(BaseModel):
    role: str
    content: str

class Conversation(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message]

@router.get("/", response_model=List[ConvSummary])
async def list_conversations(user=Depends(get_current_user), db=Depends(get_db)):
    rows = await db.fetch_all(
        """
        SELECT id, title, created_at, updated_at,
               (messages->-1->>'content') AS preview
        FROM conversations
        WHERE user_id = $1
        ORDER BY updated_at DESC
        """,
        user.id,
    )
    return [
        ConvSummary(**{
            "id": r["id"],
            "title": r["title"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "preview": r["preview"][:100] or ""
        })
        for r in rows
    ]

@router.get("/{conv_id}", response_model=Conversation)
async def get_conversation(conv_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    row = await db.fetchrow(
        """
        SELECT id, title, created_at, updated_at,
               messages
        FROM conversations
        WHERE id = $1 AND user_id = $2
        """,
        conv_id, user.id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return Conversation(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        messages=[Message(**m) for m in row["messages"]]
    )
```

> **Security** – `get_current_user` is your authentication dependency (JWT cookie, session cookie, OAuth token).  It guarantees each user only sees his own conversations.

---

## 3.  Gradio UI – Sidebar that *Loads a Conversation*

### 3.1  UI Skeleton (same in all branches)

```python
# mode_factory.py
import gradio as gr
from utils.flags import load_flags
from app.conversations import get_conversation, list_conversations
import asyncio
from typing import List, Optional

flags = load_flags()

def build_conversation_browser(user_id: int):
    """Return a hidden HTML div that will be replaced by a list of cards."""
    # 1️⃣ Get summary list from the backend
    async def fetch_list():
        return await list_conversations(user_id=user_id)

    # 2️⃣ Gradio element that will hold the cards
    conv_list = gr.HTML(elem_id="conv-list", label="Conversations")

    # 3️⃣ Event: when a card is clicked → load full conv
    def load_conv(conv_id: int):
        async def fetch_and_set():
            conv = await get_conversation(conv_id)
            # hydrate the chat state
            state.messages = conv.messages
            # optional: update title or other UI fields
        return gr.State(fetch_and_set)  # will trigger re‑render

    return conv_list, load_conv
```

### 3.2  Real‑world Gradio component

*We’ll use a **sidebar with “cards”** – `gr.HTML` that renders a list of clickable cards.  It’s lightweight, highly stylable with CSS.*

```python
# mode_factory.py – full app
import gradio as gr
from utils.flags import load_flags
from app.conversations import Conversation, list_conversations
import json, asyncio

flags = load_flags()

def render_conv_sidebar(user_id: int):
    # This function runs only if the flag is true
    if not flags.get("show_conv_browser"):
        return None, None

    # Fetch summaries on page load
    async def fetch_summaries():
        return await list_conversations(user_id=user_id)

    # Render an HTML div that will hold the cards
    sidebar = gr.HTML(elem_id="conv-sidebar", label="Recent Chats")
    # We'll fill it with JS after fetching
    # (see the JS snippet below)

    # Callback when user clicks a card
    def load_conv(conv_id: int):
        async def fetch_and_set():
            conv = await get_conversation(conv_id)
            # `chat_history` is the Gradio `State` that backs gr.Chatbot
            return conv.messages
        return gr.State(fetch_and_set)

    return sidebar, load_conv

def create_app():
    with gr.Blocks() as demo:
        # 1️⃣ Grab user_id from your auth session (cookie, JWT, etc.)
        user_id = get_current_user_id()  # you already have this from your FastAPI session

        # 2️⃣ Optional: load most recent conv automatically
        chat_state = gr.State([])

        # 3️⃣ Sidebar (only in Workbench)
        sidebar, load_conv_cb = render_conv_sidebar(user_id)
        if sidebar:
            sidebar.render()
            # Hook the click‑handler later

        # 4️⃣ Main chat area
        chatbot = gr.Chatbot(elem_id="chatbot")
        # … rest of your chat controls

        # 5️⃣ Connect the state to the chatbot
        chatbot.update(state=chat_state)

        # 6️⃣ JS that fills the sidebar with cards once summaries are fetched
        # We’ll use the `on_load` event that runs after the Blocks are rendered
        gr.HTML(
            value="""
            <script>
            // fetch list once the page is ready
            (async () => {
                const res = await fetch('/api/conversations', {
                    credentials: 'include'   // send auth cookie
                });
                const convs = await res.json();
                const container = document.getElementById('conv-sidebar');
                container.innerHTML = convs.map(c => `
                    <div class="conv-card" data-id="${c.id}">
                        <strong>${c.title}</strong><br/>
                        <small>${new Date(c.updated_at).toLocaleString()}</small><br/>
                        <p>${c.preview.replace(/\\n/g,'<br/>')}</p>
                    </div>
                `).join('');
                // click handler
                document.querySelectorAll('.conv-card').forEach(el=>{
                    el.addEventListener('click', async () => {
                        const convId = el.dataset.id;
                        // fetch full conversation and hydrate the chat
                        const conv = await fetch('/api/conversations/'+convId, {credentials:'include'}).then(r=>r.json());
                        const messages = conv.messages.map(m=>({role:m.role,content:m.content}));
                        // send to Gradio state
                        const state = await fetch('/queue?chat_history='+encodeURIComponent(JSON.stringify(messages)));
                        // the queue call will trigger re‑render
                    });
                });
            })();
            </script>
            """,
            elem_id="conv-script"
        )

    return demo
```

> **Explanation**  
> *The JavaScript part runs **once** when the page is first loaded.  It fetches the list, builds a set of “cards,” and attaches click listeners that load a full conversation into a hidden Gradio state (`chat_history`).  Gradio automatically re‑renders the chat box once the state changes.*  

> **Why a sidebar?**  
> • No page refresh needed.  
> • Works in a single‑page app (SPA).  
> • You can still keep the same layout for SEO‑Coach; the component is hidden behind the flag.

---

## 3.  Feature‑Toggle & Branch Workflow

| Step | Branch / Flag | What is in the branch? | Merge strategy |
|------|---------------|------------------------|----------------|
| **Create feature branch** (`git checkout -b conv‑browser`) | *All new code* – DB migration, API, Gradio component, tests. | Merge later with `--no-ff`. |
| **Add flag** (`SHOW_CONV_BROWSER=true`) | Guard the UI code with `if flags["show_conv_browser"]`. | In Workbench build, set flag via env (`--flag=1`).  In SEO‑Coach build keep it off. |
| **Add DB migration** | Alembic / Flyway migration in `migrations/` folder. | Run in CI before merge. |
| **Add auth guard** | `Depends(get_current_user)` ensures each user only sees his own chats. | Unit test with fake user. |

**Tip:** If you prefer *pure branch isolation*, you can also create a separate micro‑service `conv‑browser`.  But for a single‑feature it’s usually overkill; the flag approach keeps infra minimal.

---

## 4.  Gradio Styling (optional)

```css
/* migrations/styles.css */
#conv-sidebar .conv-card {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 8px 12px;
    margin: 6px 0;
    cursor: pointer;
    transition: background 0.1s;
}
#conv-sidebar .conv-card:hover {
    background: #f5f5f5;
}
```

Add it to the app with

```python
demo.css = Path("migrations/styles.css").read_text()
```

---

## 5.  Testing & CI

| Test type | What you test | Tool |
|-----------|---------------|------|
| **Unit** | `list_conversations()` and `get_conversation()` against a mocked DB | `pytest`, `asyncio` |
| **End‑to‑End** | Open Workbench, click a conversation, chat appears | **Playwright** or **pyppeteer** |
| **Snapshot** | Screenshot of sidebar & chat after load | Playwright |
| **Security** | A user **cannot** load another user’s conv | Unit test by faking auth dependency |
| **Performance** | `/api/conversations` < 80 ms | `httpx` + `asyncio` |

**Sample Playwright test**

```yaml
- name: Conversation browser E2E
  run: |
    pip install playwright
    playwright install chromium
    python - <<'PY'
    import pyppeteer, asyncio, json
    async def run():
        browser = await pyppeteer.launch(headless=True)
        page = await browser.newPage()
        await page.goto('http://localhost:8000/chat')
        # Wait for sidebar to appear
        await page.waitForSelector('#conv-sidebar')
        # click the first card
        await page.click('#conv-sidebar .conv-card')
        # Wait for chat to be populated
        await page.waitForFunction("document.querySelector('#chatbot .gpt4o-response') !== null")
        await page.screenshot({'path':'conv-loaded.png'})
        await browser.close()
    asyncio.run(run())
    PY
```

If the screenshot changes, CI will fail → you spot UI regressions immediately.

---

## 6.  Quick‑Start Checklist

| ✅ | Item | Done? |
|----|------|-------|
| ✅ | **DB schema** (`conversations` table) | ✔️ |
| ✅ | **API** – list + get | ✔️ |
| ✅ | **Auth guard** – user isolation | ✔️ |
| ✅ | **Gradio sidebar** – HTML cards, click → state | ✔️ |
| ✅ | **Feature flag** (`SHOW_CONV_BROWSER`) | ✔️ |
| ✅ | **Separate branch** (`conv-browser`) | ✔️ |
| ✅ | **Unit & E2E tests** | ✔️ |
| ✅ | **WorkBench image** built with flag | ✔️ |

Once the feature passes all tests, just:

```bash
# Merge
git checkout main
git merge --no-ff conv-browser

# Enable flag in the Workbench build
export SHOW_CONV_BROWSER=true
docker build -t ghcr.io/meorg/workbench .
```

The SEO‑Coach image stays exactly the same – the sidebar never appears.

---

## 7.  Final Words

*You’re not restoring a single conversation; you’re giving the user **full historical access**.  The UI approach above lets them:

1. See a neatly‑formatted list (title, last updated, preview).  
2. Click to instantly load any past chat into the same chat box.  
3. Keep that browsing UI only in the Workbench (via flag).  

Feel free to tweak the list UI (pagination, search bar, tags, etc.) – the pattern stays the same.*  

Happy building! 🚀

--------------------
Second phase: introduce experimental featuer in seo coach app.

## 👀  “Earlier‑Conversations” UI – What It Means

> *You want a **browser‑style sidebar** (or modal) that lets the user click on any previous chat and load it into the same Gradio chat box.*  
> The conversations already exist in the DB – you just need a UI layer to fetch, list, and hydrate them.

Below is a **complete recipe**: database schema, API endpoints, Gradio UI, feature‑flag workflow, and CI testing plan.  Everything lives in the *same code base* and the UI component is turned on only in the Workbench image.

---

## 1.  Data Model

| Table | Columns | Notes |
|-------|---------|-------|
| `conversations` | `id PK`, `user_id FK`, `title`, `created_at`, `updated_at`, `messages JSONB` | Store all messages as JSONB; no separate `messages` table unless you need granular analytics. |
| `users` | `id PK`, `email`, … | Auth‑provider data. |

**Sample SQL**

```sql
CREATE TABLE conversations (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT REFERENCES users(id),
    title       TEXT NOT NULL DEFAULT 'Untitled',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    messages    JSONB NOT NULL        -- [{"role":"user","content":"Hi"},{"role":"assistant","content":"Hello"}]
);
```

**Index for fast look‑up**

```sql
CREATE INDEX ON conversations(user_id, created_at DESC);
```

---

## 2.  Backend API

> **Endpoints**  
> 1. `GET /api/conversations` – list the user’s chats (title, dates, preview).  
> 2. `GET /api/conversations/{id}` – fetch the full conversation.

```python
# app/routers/conversations.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.db import get_db  # asyncpg connection pool or SQLAlchemy async session
from app.auth import get_current_user  # returns User object

router = APIRouter(prefix="/api/conversations")

class ConvSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    preview: str  # first 100 chars of last message

class Message(BaseModel):
    role: str
    content: str

class Conversation(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message]

@router.get("/", response_model=List[ConvSummary])
async def list_conversations(user=Depends(get_current_user), db=Depends(get_db)):
    rows = await db.fetch_all(
        """
        SELECT id, title, created_at, updated_at,
               (messages->-1->>'content') AS preview
        FROM conversations
        WHERE user_id = $1
        ORDER BY updated_at DESC
        """,
        user.id,
    )
    return [
        ConvSummary(**{
            "id": r["id"],
            "title": r["title"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "preview": r["preview"][:100] or ""
        })
        for r in rows
    ]

@router.get("/{conv_id}", response_model=Conversation)
async def get_conversation(conv_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    row = await db.fetchrow(
        """
        SELECT id, title, created_at, updated_at,
               messages
        FROM conversations
        WHERE id = $1 AND user_id = $2
        """,
        conv_id, user.id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return Conversation(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        messages=[Message(**m) for m in row["messages"]]
    )
```

> **Security** – `get_current_user` is your authentication dependency (JWT cookie, session cookie, OAuth token).  It guarantees each user only sees his own conversations.

---

## 3.  Gradio UI – Sidebar that *Loads a Conversation*

### 3.1  UI Skeleton (same in all branches)

```python
# mode_factory.py
import gradio as gr
from utils.flags import load_flags
from app.conversations import get_conversation, list_conversations
import asyncio
from typing import List, Optional

flags = load_flags()

def build_conversation_browser(user_id: int):
    """Return a hidden HTML div that will be replaced by a list of cards."""
    # 1️⃣ Get summary list from the backend
    async def fetch_list():
        return await list_conversations(user_id=user_id)

    # 2️⃣ Gradio element that will hold the cards
    conv_list = gr.HTML(elem_id="conv-list", label="Conversations")

    # 3️⃣ Event: when a card is clicked → load full conv
    def load_conv(conv_id: int):
        async def fetch_and_set():
            conv = await get_conversation(conv_id)
            # hydrate the chat state
            state.messages = conv.messages
            # optional: update title or other UI fields
        return gr.State(fetch_and_set)  # will trigger re‑render

    return conv_list, load_conv
```

### 3.2  Real‑world Gradio component

*We’ll use a **sidebar with “cards”** – `gr.HTML` that renders a list of clickable cards.  It’s lightweight, highly stylable with CSS, and works in Gradio ≥ 4.11.*

```python
# mode_factory.py – full app
import gradio as gr
from utils.flags import load_flags
from app.conversations import Conversation, list_conversations
import json, asyncio

flags = load_flags()

def render_conv_sidebar(user_id: int):
    # This function runs only if the flag is true
    if not flags.get("show_conv_browser"):
        return None, None

    # Fetch summaries on page load
    async def fetch_summaries():
        return await list_conversations(user_id=user_id)

    # Render an HTML div that will hold the cards
    sidebar = gr.HTML(elem_id="conv-sidebar", label="Recent Chats")
    # We'll fill it with JS after fetching
    # (see the JS snippet below)

    # Callback when user clicks a card
    def load_conv(conv_id: int):
        async def fetch_and_set():
            conv = await get_conversation(conv_id)
            # `chat_history` is the Gradio `State` that backs gr.Chatbot
            return conv.messages
        return gr.State(fetch_and_set)

    return sidebar, load_conv

def create_app():
    with gr.Blocks() as demo:
        # 1️⃣ Grab user_id from your auth session (cookie, JWT, etc.)
        user_id = get_current_user_id()  # you already have this from your FastAPI session

        # 2️⃣ Optional: load most recent conv automatically
        chat_state = gr.State([])

        # 3️⃣ Sidebar (only in Workbench)
        sidebar, load_conv_cb = render_conv_sidebar(user_id)
        if sidebar:
            sidebar.render()
            # Hook the click‑handler later

        # 4️⃣ Main chat area
        chatbot = gr.Chatbot(elem_id="chatbot")
        # … rest of your chat controls

        # 5️⃣ Connect the state to the chatbot
        chatbot.update(state=chat_state)

        # 6️⃣ JS that fills the sidebar with cards once summaries are fetched
        # We’ll use the `on_load` event that runs after the Blocks are rendered
        gr.HTML(
            value="""
            <script>
            // fetch list once the page is ready
            (async () => {
                const res = await fetch('/api/conversations', {
                    credentials: 'include'   // send auth cookie
                });
                const convs = await res.json();
                const container = document.getElementById('conv-sidebar');
                container.innerHTML = convs.map(c => `
                    <div class="conv-card" data-id="${c.id}">
                        <strong>${c.title}</strong><br/>
                        <small>${new Date(c.updated_at).toLocaleString()}</small><br/>
                        <p>${c.preview.replace(/\\n/g,'<br/>')}</p>
                    </div>
                `).join('');
                // click handler
                document.querySelectorAll('.conv-card').forEach(el=>{
                    el.addEventListener('click', async () => {
                        const convId = el.dataset.id;
                        // fetch full conversation and hydrate the chat
                        const conv = await fetch('/api/conversations/'+convId, {credentials:'include'}).then(r=>r.json());
                        const messages = conv.messages.map(m=>({role:m.role,content:m.content}));
                        // send to Gradio state
                        const state = await fetch('/queue?chat_history='+encodeURIComponent(JSON.stringify(messages)));
                        // the queue call will trigger re‑render
                    });
                });
            })();
            </script>
            """,
            elem_id="conv-script"
        )

    return demo
```

> **Explanation**  
> *The JavaScript part runs **once** when the page is first loaded.  It fetches the list, builds a set of “cards,” and attaches click listeners that load a full conversation into a hidden Gradio state (`chat_history`).  Gradio automatically re‑renders the chat box once the state changes.*  

> **Why a sidebar?**  
> • No page refresh needed.  
> • Works in a single‑page app (SPA).  
> • You can still keep the same layout for SEO‑Coach; the component is hidden behind the flag.

---

## 3.  Feature‑Toggle & Branch Workflow

| Step | Branch / Flag | What is in the branch? | Merge strategy |
|------|---------------|------------------------|----------------|
| **Create feature branch** (`git checkout -b conv‑browser`) | *All new code* – DB migration, API, Gradio component, tests. | Merge later with `--no-ff`. |
| **Add flag** (`SHOW_CONV_BROWSER=true`) | Guard the UI code with `if flags["show_conv_browser"]`. | In Workbench build, set flag via env (`--flag=1`).  In SEO‑Coach build keep it off. |
| **Add DB migration** | Alembic / Flyway migration in `migrations/` folder. | Run in CI before merge. |
| **Add auth guard** | `Depends(get_current_user)` ensures each user only sees his own chats. | Unit test with fake user. |

**Tip:** If you prefer *pure branch isolation*, you can also create a separate micro‑service `conv‑browser`.  But for a single‑feature it’s usually overkill; the flag approach keeps infra minimal.

---

## 4.  Gradio Styling (optional)

```css
/* migrations/styles.css */
#conv-sidebar .conv-card {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 8px 12px;
    margin: 6px 0;
    cursor: pointer;
    transition: background 0.1s;
}
#conv-sidebar .conv-card:hover {
    background: #f5f5f5;
}
```

Add it to the app with

```python
demo.css = Path("migrations/styles.css").read_text()
```

---

## 5.  Testing & CI

| Test type | What you test | Tool |
|-----------|---------------|------|
| **Unit** | `list_conversations()` and `get_conversation()` against a mocked DB | `pytest`, `asyncio` |
| **End‑to‑End** | Open Workbench, click a conversation, chat appears | **Playwright** or **pyppeteer** |
| **Snapshot** | Screenshot of sidebar & chat after load | Playwright |
| **Security** | A user **cannot** load another user’s conv | Unit test by faking auth dependency |
| **Performance** | `/api/conversations` < 80 ms | `httpx` + `asyncio` |

**Sample Playwright test**

```yaml
- name: Conversation browser E2E
  run: |
    pip install playwright
    playwright install chromium
    python - <<'PY'
    import pyppeteer, asyncio, json
    async def run():
        browser = await pyppeteer.launch(headless=True)
        page = await browser.newPage()
        await page.goto('http://localhost:8000/chat')
        # Wait for sidebar to appear
        await page.waitForSelector('#conv-sidebar')
        # click the first card
        await page.click('#conv-sidebar .conv-card')
        # Wait for chat to be populated
        await page.waitForFunction("document.querySelector('#chatbot .gpt4o-response') !== null")
        await page.screenshot({'path':'conv-loaded.png'})
        await browser.close()
    asyncio.run(run())
    PY
```

If the screenshot changes, CI will fail → you spot UI regressions immediately.

---

## 6.  Quick‑Start Checklist

| ✅ | Item | Done? |
|----|------|-------|
| ✅ | **DB schema** (`conversations` table) | ✔️ |
| ✅ | **API** – list + get | ✔️ |
| ✅ | **Auth guard** – user isolation | ✔️ |
| ✅ | **Gradio sidebar** – HTML cards, click → state | ✔️ |
| ✅ | **Feature flag** (`SHOW_CONV_BROWSER`) | ✔️ |
| ✅ | **Separate branch** (`conv-browser`) | ✔️ |
| ✅ | **Unit & E2E tests** | ✔️ |
| ✅ | **WorkBench image** built with flag | ✔️ |

Once the feature passes all tests, just:

```bash
# Merge
git checkout main
git merge --no-ff conv-browser

# Enable flag in the Workbench build
export SHOW_CONV_BROWSER=true
docker build -t ghcr.io/meorg/workbench .
```

The SEO‑Coach image stays exactly the same – the sidebar never appears.

---

## 7.  Final Words

*You’re not restoring a single conversation; you’re giving the user **full historical access**.  The UI approach above lets them:

1. See a neatly‑formatted list (title, last updated, preview).  
2. Click to instantly load any past chat into the same chat box.  
3. Keep that browsing UI only in the Workbench (via flag).  

Feel free to tweak the list UI (pagination, search bar, tags, etc.) – the pattern stays the same.*  

Happy building! 🚀