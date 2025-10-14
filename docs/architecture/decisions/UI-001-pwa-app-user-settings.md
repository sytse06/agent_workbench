# UI-001: PWA App with User Settings

## Status

**Status**: Ready for Implementation
**Date**: October 13, 2025
**Decision Makers**: Human Architect
**Task ID**: UI-001-pwa-app-user-settings
**Phase**: 2.1
**Dependencies**: CORE-001 (User Authentication & Settings from Phase 2.0)

## Context

Transform Agent Workbench from a web application into a Progressive Web App (PWA) with native app-like capabilities and a dedicated settings management system. This addresses the need for:

1. **Native App Experience**: Users expect installable apps with offline support, not just web pages
2. **Settings Management**: Current model/provider configuration is buried in chat UI, causing UX friction
3. **Mobile-First Design**: PWA enables "Add to Home Screen" for mobile and desktop access
4. **Share Integration**: Allow users to share content from other apps directly into Agent Workbench

**Design Standard**: Follow Ollama app interface pattern
- Clean, minimal centered chat interface
- Model selector integrated subtly in chat input (bottom-right)
- Separate settings page (not cluttering main chat UI)
- Native app-like behavior and responsiveness

This phase builds on Phase 2.0's authentication system, requiring user_id to persist settings per user.

## Architecture Scope

### What's Included:

- **Comprehensive PWA Manifest**: Full metadata with 8 icon sizes, screenshots, shortcuts, share_target
- **Service Worker**: Offline support and caching strategy
- **Dedicated Settings Page**: 4-tab interface (Account, Models, Company, Advanced) separate from chat
- **Minimal Chat UI**: Ollama-style interface with model selector in input area
- **Settings Persistence**: Per-user settings storage linked to Phase 2.0 user_id
- **Share Target Handler**: Accept shared content from other apps/system share menu
- **Static Asset Management**: Serve PWA icons, screenshots, and service worker
- **Navigation System**: Route between chat interface and settings page

### What's Explicitly Excluded:

- File upload functionality (Phase 2.2 - stubbed only in 2.1)
- Approval dialogs (Phase 2.2 - stubbed only)
- Agent/tool configuration (Phase 2.3+)
- MCP tool management (Phase 2.7)
- Advanced analytics dashboards
- Multi-language UI support (English + Dutch only)
- Custom theme creation (Light/Dark/Auto presets only)
- Offline agent execution (cache manifest/SW only)

## Architectural Decisions

### 1. Progressive Web App Architecture

**Core Approach**: Transform Gradio interface into installable PWA with comprehensive manifest

**PWA Manifest Requirements**:
```json
{
  "name": "Agent Workbench",
  "short_name": "Workbench",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait-primary",
  "categories": ["productivity", "developer-tools", "utilities"],
  "icons": [...],          // 8 sizes: 72, 96, 128, 144, 152, 192, 384, 512
  "screenshots": [...],    // Desktop (wide) + Mobile (narrow)
  "shortcuts": [...],      // New Chat, Settings, History
  "share_target": {        // Accept shared content
    "action": "/share",
    "method": "POST",
    "enctype": "multipart/form-data"
  }
}
```

**Icon Size Strategy**:
- **72x72**: Android old devices
- **96x96**: Android notifications, shortcut icons (3 shortcuts)
- **128x128**: Chrome Web Store
- **144x144**: Windows tiles
- **152x152**: iOS devices
- **192x192**: Android home screen (REQUIRED, maskable)
- **384x384**: High-resolution displays
- **512x512**: Splash screens and app stores (REQUIRED, maskable)

**Screenshot Requirements**:
- **Desktop (wide)**: 1280x720 minimum (16:9 aspect ratio)
  - `desktop-home.png`: Main chat interface
  - `desktop-settings.png`: Settings page layout
- **Mobile (narrow)**: 750x1334 minimum (typical phone aspect)
  - `mobile-chat.png`: Mobile chat view
  - `mobile-settings.png`: Mobile settings view

### 2. Service Worker Strategy

**Offline Support Approach**: Cache static assets, fail gracefully for API calls

```javascript
// Cache-first for static assets
const CACHE_NAME = 'agent-workbench-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

// Network-first for API calls (graceful degradation)
```

**Lifecycle Strategy**:
1. **Install**: Pre-cache manifest and critical icons
2. **Activate**: Clean up old caches on version bump
3. **Fetch**: Cache-first for static, network-first for API
4. **Update**: Check for updates on app launch

### 3. Settings Page Architecture (Ollama Pattern)

**Separation of Concerns**: Settings in dedicated page, NOT in chat UI

**4-Tab Layout**:

1. **Account Tab**:
   - HuggingFace profile (username, email - read-only)
   - Theme selection (Light/Dark/Auto)
   - Language preference (English/Nederlands)

2. **Models Tab** (moved from chat UI):
   - Provider selection (OpenRouter, Anthropic, OpenAI, Ollama)
   - Model dropdown (provider-specific models)
   - Model parameters (temperature, max_tokens)
   - API key management (password fields)

3. **Company Tab** (SEO Coach mode only):
   - Business profile (name, website, industry)
   - Brand settings (voice, target audience)
   - SEO-specific preferences

4. **Advanced Tab**:
   - Debug mode toggle
   - Verbose logging
   - Experimental features (MCP tools, Firecrawl)

**Tab Visibility Logic**:
```python
# Company tab only visible in seo_coach mode
company_tab = gr.Tab("Company", visible=(mode == "seo_coach"))
```

### 4. Minimal Chat Interface (Ollama-Style)

**Design Philosophy**: Remove all configuration controls from chat view

**Layout Components**:
```
┌─────────────────────────────────────┐
│                🤖                   │  ← Centered logo/icon
│                                     │
│  ┌───────────────────────────────┐ │
│  │ User: Hello                   │ │  ← Chat messages
│  │ Assistant: Hi! How can I help?│ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌─────────────────────────────────┴─┐
│  │ Send a message      [claude-4] ↑ │ ← Input + model selector + submit
│  └───────────────────────────────────┘
│                                     │
│                             ⚙️      │  ← Settings icon (top-right)
└─────────────────────────────────────┘
```

**Model Selector Positioning**:
- Bottom-right of message input (inline)
- Minimal dropdown (no label)
- Only shows model name (not full provider/model string)
- Loads from user settings on startup

**CSS Strategy**:
```css
.chat-container {
    max-width: 800px;        /* Centered like Ollama */
    margin: 0 auto;
    padding-top: 10vh;
}
.model-selector {
    position: absolute;
    bottom: 12px;
    right: 60px;
    font-size: 0.9rem;
}
```

### 5. Settings Persistence Strategy

**Database Schema** (uses Phase 2.0 UserSettingModel):
```python
# Existing from Phase 2.0
class UserSettingModel(Base):
    __tablename__ = "user_settings"
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    key = Column(String(255), nullable=False)      # e.g., "provider", "model"
    value = Column(JSON)                           # e.g., "OpenRouter", 0.7
    is_active = Column(Boolean, default=True)
    category = Column(String(100))                 # "account", "models", "company", "advanced"
```

**Service Layer Pattern**:
```python
class UserSettingsService:
    async def get_all_settings(self, user_id: UUID) -> Dict[str, Any]:
        """Load settings grouped by category (account, models, company, advanced)."""

    async def save_model_settings(self, user_id: UUID, provider: str, model: str, ...):
        """Save model configuration settings to database."""

    async def get_active_model_config(self, user_id: UUID) -> Dict[str, Any]:
        """Get user's active model config for agent initialization."""
```

**Loading Strategy**:
- Settings page: Load on `gr.Blocks.load()` event
- Chat interface: Load model config on app startup
- Apply settings: Inject into agent initialization in Phase 2.3

### 6. Share Target Integration

**Share Target Manifest Configuration**:
```json
"share_target": {
  "action": "/share",
  "method": "POST",
  "enctype": "multipart/form-data",
  "params": {
    "title": "title",
    "text": "text",
    "url": "url",
    "files": [
      {
        "name": "documents",
        "accept": ["text/*", "application/pdf", ".md", ".txt"]
      }
    ]
  }
}
```

**Use Cases**:
- Share website URL → Extract SEO insights
- Share text selection → Summarize or analyze
- Share document → Process and answer questions
- Share notes → AI processing

**Endpoint Implementation**:
```python
@app.post("/share")
async def share_handler(
    title: str = Form(None),
    text: str = Form(None),
    url: str = Form(None),
    documents: List[UploadFile] = File(None)
):
    """
    Handle shared content from other apps.
    Create new conversation with shared content pre-filled.
    """
    # Build initial message from shared content
    # Store files (Phase 2.4)
    # Redirect to chat with conversation_id and pre-filled message
    return RedirectResponse(url=f"/?conversation_id={conv_id}&message={quoted_msg}")
```

### 7. Navigation System

**Route Structure**:
```
/                  → Main chat interface (minimal UI)
/settings          → Settings page (4 tabs)
/history           → Conversation history (shortcut)
/share             → Share target handler (POST only)
/manifest.json     → PWA manifest
/service-worker.js → Service worker script
/static/icons/*    → PWA icon assets
/static/screenshots/* → App store screenshots
```

**Gradio Integration**:
```python
# Chat interface
settings_link = gr.Button("⚙️", size="sm")
settings_link.click(fn=lambda: None, js="window.location.href = '/settings'")

# Settings page
back_to_chat = gr.Button("← Back to Chat")
back_to_chat.click(fn=lambda: None, js="window.location.href = '/'")
```

## Implementation Boundaries

### Files to CREATE:

```
static/
├── manifest.json                      # PWA manifest with full metadata
├── service-worker.js                  # Offline support and caching
├── icons/
│   ├── icon-72.png                   # Android old devices
│   ├── icon-96.png                   # Android notifications
│   ├── icon-128.png                  # Chrome Web Store
│   ├── icon-144.png                  # Windows tiles
│   ├── icon-152.png                  # iOS devices
│   ├── icon-192.png                  # Android home (REQUIRED)
│   ├── icon-384.png                  # High-res displays
│   ├── icon-512.png                  # Splash screens (REQUIRED)
│   ├── shortcut-chat.png (96x96)     # New Chat shortcut
│   ├── shortcut-settings.png (96x96) # Settings shortcut
│   └── shortcut-history.png (96x96)  # History shortcut
└── screenshots/
    ├── desktop-home.png (1280x720)   # Main chat (wide)
    ├── desktop-settings.png (1280x720) # Settings page (wide)
    ├── mobile-chat.png (750x1334)    # Mobile chat (narrow)
    └── mobile-settings.png (750x1334) # Mobile settings (narrow)

src/agent_workbench/
├── ui/
│   ├── settings_page.py              # Dedicated settings interface (4 tabs)
│   └── minimal_chat.py               # Ollama-style chat interface
├── services/
│   └── user_settings_service.py      # Settings CRUD operations
└── api/routes/
    └── share.py                      # Share target handler endpoint
```

### Files to MODIFY:

```
src/agent_workbench/
├── ui/
│   ├── app.py                        # Use minimal_chat interface
│   └── seo_coach_app.py              # Use minimal_chat + company settings tab
├── main.py                           # Add PWA routes and static file serving
└── ui/mode_factory.py                # Register settings page route
```

### Exact Function Signatures:

```python
# CREATE: ui/settings_page.py
def create_settings_page(user_id: str, mode: str = "workbench") -> gr.Blocks:
    """
    Create dedicated settings page with 4-tab layout.

    Args:
        user_id: Current user's UUID (from Phase 2.0 auth)
        mode: App mode ("workbench" or "seo_coach") - controls Company tab visibility

    Returns:
        Gradio Blocks interface with Account, Models, Company, Advanced tabs
    """

async def load_user_settings(user_id: str) -> Tuple:
    """
    Load all user settings from database for settings page.

    Args:
        user_id: User UUID

    Returns:
        Tuple of all settings values for Gradio outputs
    """

async def save_model_settings(
    user_id: str,
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int
) -> str:
    """
    Save model configuration settings to database.

    Args:
        user_id: User UUID
        provider: LLM provider name
        model: Model identifier
        temperature: Model temperature parameter
        max_tokens: Maximum tokens parameter

    Returns:
        Status message for UI feedback
    """

async def save_company_settings(
    user_id: str,
    company_name: str,
    website: str,
    industry: str,
    brand_voice: str
) -> str:
    """Save company profile settings (SEO Coach mode only)."""

async def save_advanced_settings(
    user_id: str,
    debug_mode: bool,
    enable_mcp_tools: bool,
    enable_firecrawl: bool
) -> str:
    """Save advanced/experimental feature flags."""

# CREATE: ui/minimal_chat.py
def create_minimal_chat_interface(user_id: str) -> gr.Blocks:
    """
    Create Ollama-style minimal chat interface.

    Args:
        user_id: Current user UUID (loads model config from settings)

    Returns:
        Gradio Blocks with centered chat, inline model selector, settings icon
    """

async def load_user_model_config(user_id: str) -> Dict[str, Any]:
    """
    Load user's active model configuration for chat interface.

    Args:
        user_id: User UUID

    Returns:
        Dict with provider, model, temperature, max_tokens
    """

# CREATE: services/user_settings_service.py
class UserSettingsService:
    """Service for user settings persistence and retrieval."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def get_all_settings(self, user_id: UUID) -> Dict[str, Any]:
        """
        Load all user settings grouped by category.

        Returns:
            {
                "account": {"theme": "Auto", "language": "English"},
                "models": {"provider": "OpenRouter", "model": "...", ...},
                "company": {"name": "...", "website": "...", ...},
                "advanced": {"debug_mode": False, ...}
            }
        """

    async def save_model_settings(
        self,
        user_id: UUID,
        provider: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> None:
        """Save model configuration settings to database."""

    async def get_active_model_config(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user's active model configuration for agent initialization.

        Returns:
            {"provider": "...", "model": "...", "temperature": 0.7, "max_tokens": 2000}
        """

    async def save_company_settings(
        self,
        user_id: UUID,
        company_name: Optional[str],
        website: Optional[str],
        industry: Optional[str],
        brand_voice: Optional[str]
    ) -> None:
        """Save company profile settings (SEO Coach only)."""

    async def save_advanced_settings(
        self,
        user_id: UUID,
        debug_mode: bool,
        enable_mcp_tools: bool,
        enable_firecrawl: bool
    ) -> None:
        """Save advanced/experimental feature flags."""

# CREATE: api/routes/share.py
from fastapi import APIRouter, Form, File, UploadFile
from fastapi.responses import RedirectResponse
from typing import List, Optional
from uuid import uuid4
from urllib.parse import quote_plus

router = APIRouter(prefix="", tags=["share"])

@router.post("/share")
async def share_handler(
    title: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    documents: Optional[List[UploadFile]] = File(None)
) -> RedirectResponse:
    """
    Handle shared content from other apps (PWA share target).

    Creates new conversation with shared content pre-filled.
    Supports text, URLs, and files from system share menu.

    Args:
        title: Shared title (optional)
        text: Shared text content (optional)
        url: Shared URL (optional)
        documents: Shared files (optional, Phase 2.4 implementation)

    Returns:
        Redirect to chat with conversation_id and pre-filled message
    """

# MODIFY: main.py (add PWA routes)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Mount static files for PWA assets
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/manifest.json")
async def manifest() -> FileResponse:
    """Serve PWA manifest."""
    return FileResponse("static/manifest.json", media_type="application/manifest+json")

@app.get("/service-worker.js")
async def service_worker() -> FileResponse:
    """Serve service worker script."""
    return FileResponse("static/service-worker.js", media_type="application/javascript")

@app.get("/settings")
async def settings_page_route():
    """
    Route to settings page.

    Returns Gradio interface from create_settings_page().
    User authentication required via Phase 2.0 middleware.
    """

# MODIFY: ui/app.py (use minimal chat)
from ui.minimal_chat import create_minimal_chat_interface

def create_fastapi_mounted_gradio_interface() -> gr.Blocks:
    """Create workbench interface with minimal chat UI."""
    # Replace current chat UI with minimal_chat
    return create_minimal_chat_interface(user_id=get_current_user_id())

# MODIFY: ui/seo_coach_app.py (use minimal chat + company tab)
def create_seo_coach_app() -> gr.Blocks:
    """Create SEO Coach interface with minimal chat UI."""
    # Use minimal_chat interface
    # Settings page will show Company tab when mode="seo_coach"
```

### Additional Dependencies:

```toml
# No new dependencies required
# Reuses existing:
# - gradio >= 4.0.0 (UI framework)
# - fastapi (API routes)
# - sqlalchemy (settings persistence via Phase 2.0 UserSettingModel)
# - aiosqlite (async database)
```

### FORBIDDEN Actions:

- Implementing file upload processing (Phase 2.4 - stub in share handler only)
- Creating approval dialog logic (Phase 2.2 - stub only)
- Implementing agent/tool configuration (Phase 2.3+ - settings UI only)
- Adding MCP server management UI (Phase 2.7)
- Creating custom theme editor (use presets only)
- Implementing multi-language translations (show language selector, apply in Phase 3)
- Adding offline agent execution (cache static assets only)
- Creating settings export/import (manual database backup only)

## Testing Strategy

Based on `phase2_testing_strategy.md`, Phase 2.1 focuses on PWA features and UI integration.

### E2E Tests (Priority: HIGH)

```python
# tests/e2e/test_pwa_installation.py

def test_pwa_manifest_valid():
    """Validate manifest.json structure and completeness."""
    # Load static/manifest.json
    manifest = json.load(open("static/manifest.json"))

    # Verify required fields
    assert "name" in manifest
    assert "short_name" in manifest
    assert "start_url" in manifest
    assert manifest["display"] == "standalone"

    # Verify 8 icon sizes present
    icon_sizes = {icon["sizes"] for icon in manifest["icons"]}
    required_sizes = {"72x72", "96x96", "128x128", "144x144",
                      "152x152", "192x192", "384x384", "512x512"}
    assert required_sizes.issubset(icon_sizes)

    # Verify icon files exist
    for icon in manifest["icons"]:
        icon_path = f"static/{icon['src'].lstrip('/')}"
        assert os.path.exists(icon_path), f"Icon missing: {icon_path}"

    # Verify screenshot dimensions
    for screenshot in manifest["screenshots"]:
        # Desktop screenshots: 1280x720 minimum
        if screenshot["form_factor"] == "wide":
            width, height = map(int, screenshot["sizes"].split("x"))
            assert width >= 1280 and height >= 720
        # Mobile screenshots: 750x1334 minimum
        elif screenshot["form_factor"] == "narrow":
            width, height = map(int, screenshot["sizes"].split("x"))
            assert width >= 750 and height >= 1334

    # Verify shortcuts (max 4)
    assert len(manifest.get("shortcuts", [])) <= 4

    # Verify share_target configured
    assert "share_target" in manifest
    assert manifest["share_target"]["action"] == "/share"

async def test_share_target_handler():
    """Test sharing content to app via PWA share target."""
    from httpx import AsyncClient
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test text sharing
        response = await client.post(
            "/share",
            data={"title": "Test Title", "text": "Test content", "url": "https://example.com"}
        )
        assert response.status_code == 303  # Redirect
        assert "conversation_id" in response.headers["location"]
        assert "message" in response.headers["location"]

        # Test file sharing (stub in Phase 2.1, full in 2.4)
        with open("test_file.txt", "wb") as f:
            f.write(b"Test content")

        with open("test_file.txt", "rb") as f:
            response = await client.post(
                "/share",
                data={"text": "Process this file"},
                files={"documents": ("test_file.txt", f, "text/plain")}
            )
        assert response.status_code == 303
        assert "Attached Files" in urllib.parse.unquote(response.headers["location"])

def test_service_worker_exists():
    """Verify service worker script exists and loads."""
    assert os.path.exists("static/service-worker.js")

    # Basic syntax check (not full JS execution)
    with open("static/service-worker.js") as f:
        content = f.read()
        assert "addEventListener" in content
        assert "install" in content
        assert "fetch" in content
```

### UI Integration Tests (Priority: MEDIUM)

```python
# tests/ui/test_settings_page.py

def test_settings_page_renders():
    """Test settings page UI structure."""
    from ui.settings_page import create_settings_page

    # Create settings page
    settings_page = create_settings_page(user_id="test-user-123", mode="workbench")

    # Verify Gradio Blocks created
    assert isinstance(settings_page, gr.Blocks)

    # Verify tabs exist (Account, Models, Advanced visible; Company hidden in workbench mode)
    # Note: Gradio doesn't expose tab names directly, verify via rendering
    # This is integration test - manual verification required

def test_settings_page_seo_coach_mode():
    """Test Company tab visible in SEO Coach mode."""
    from ui.settings_page import create_settings_page

    settings_page = create_settings_page(user_id="test-user-123", mode="seo_coach")

    # Verify Company tab visible in seo_coach mode
    # Manual verification: render and check tab count

async def test_model_settings_save_persistence(db, authenticated_user):
    """Test model settings persist to database."""
    from services.user_settings_service import UserSettingsService

    service = UserSettingsService(db)

    # Save model settings
    await service.save_model_settings(
        user_id=authenticated_user.id,
        provider="OpenRouter",
        model="anthropic/claude-sonnet-4-5",
        temperature=0.8,
        max_tokens=3000
    )

    # Load active config
    config = await service.get_active_model_config(authenticated_user.id)

    assert config["provider"] == "OpenRouter"
    assert config["model"] == "anthropic/claude-sonnet-4-5"
    assert config["temperature"] == 0.8
    assert config["max_tokens"] == 3000

def test_minimal_chat_interface():
    """Test Ollama-style chat UI."""
    from ui.minimal_chat import create_minimal_chat_interface

    chat_ui = create_minimal_chat_interface(user_id="test-user-123")

    # Verify Gradio Blocks created
    assert isinstance(chat_ui, gr.Blocks)

    # Verify CSS applied (centered layout)
    assert "chat-container" in str(chat_ui)

    # Manual verification required:
    # - Model selector in bottom-right
    # - No config controls in chat
    # - Settings icon in top-right

async def test_settings_load_on_page_load(db, authenticated_user):
    """Test settings loaded automatically on page load."""
    from services.user_settings_service import UserSettingsService

    service = UserSettingsService(db)

    # Pre-populate settings
    await service.save_model_settings(
        user_id=authenticated_user.id,
        provider="Anthropic",
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=2000
    )

    # Load all settings
    settings = await service.get_all_settings(authenticated_user.id)

    assert settings["models"]["provider"] == "Anthropic"
    assert settings["models"]["model"] == "claude-3-opus-20240229"
    assert settings["account"]["theme"] == "Auto"  # Default
    assert settings["advanced"]["enable_mcp_tools"] == True  # Default
```

### Service Layer Tests (Priority: HIGH)

```python
# tests/unit/services/test_user_settings_service.py

async def test_get_all_settings_grouped_by_category(db, authenticated_user):
    """Test settings grouped by category (account, models, company, advanced)."""
    from services.user_settings_service import UserSettingsService

    service = UserSettingsService(db)

    settings = await service.get_all_settings(authenticated_user.id)

    # Verify structure
    assert "account" in settings
    assert "models" in settings
    assert "company" in settings
    assert "advanced" in settings

    # Verify defaults
    assert settings["account"]["theme"] == "Auto"
    assert settings["models"]["provider"] == "OpenRouter"
    assert settings["advanced"]["enable_mcp_tools"] == True

async def test_save_model_settings_updates_database(db, authenticated_user):
    """Test model settings saved correctly."""
    from services.user_settings_service import UserSettingsService

    service = UserSettingsService(db)

    await service.save_model_settings(
        user_id=authenticated_user.id,
        provider="OpenAI",
        model="gpt-4-turbo",
        temperature=0.5,
        max_tokens=1500
    )

    # Verify each setting saved
    settings = await service.get_all_settings(authenticated_user.id)
    assert settings["models"]["provider"] == "OpenAI"
    assert settings["models"]["model"] == "gpt-4-turbo"
    assert settings["models"]["temperature"] == 0.5
    assert settings["models"]["max_tokens"] == 1500

async def test_get_active_model_config_for_agent_init(db, authenticated_user):
    """Test active model config returned for agent initialization."""
    from services.user_settings_service import UserSettingsService

    service = UserSettingsService(db)

    # Save custom config
    await service.save_model_settings(
        user_id=authenticated_user.id,
        provider="Ollama",
        model="llama3:70b",
        temperature=0.9,
        max_tokens=4000
    )

    # Load for agent
    config = await service.get_active_model_config(authenticated_user.id)

    assert config == {
        "provider": "Ollama",
        "model": "llama3:70b",
        "temperature": 0.9,
        "max_tokens": 4000
    }
```

### Test Coverage Goals

- **PWA Manifest & Assets**: 80% (comprehensive validation)
- **Settings Page UI**: 60% (Gradio rendering limits automated testing)
- **Service Layer**: 90% (critical for settings persistence)
- **Share Handler**: 70% (endpoint tested, file handling stubbed)

**Overall Phase 2.1 Target: 70% coverage**

### Manual Testing Checklist

**PWA Installation:**
- [ ] Open app in Chrome/Edge desktop
- [ ] Click install icon in address bar
- [ ] Verify app installs and opens in standalone window
- [ ] Test on Android: "Add to Home Screen"
- [ ] Test on iOS: "Add to Home Screen"

**Settings Page:**
- [ ] Navigate to /settings
- [ ] Verify all 4 tabs render correctly
- [ ] Change model settings and save
- [ ] Refresh page and verify settings persisted
- [ ] Test in SEO Coach mode: Company tab visible
- [ ] Test in Workbench mode: Company tab hidden

**Chat Interface:**
- [ ] Verify centered layout (Ollama style)
- [ ] Verify model selector in bottom-right
- [ ] Verify NO config controls in chat
- [ ] Click settings icon → navigates to /settings

**Share Target:**
- [ ] Share text from another app (mobile)
- [ ] Verify redirects to chat with pre-filled message
- [ ] Share URL from browser
- [ ] Verify URL included in message

## Success Criteria

- [ ] **PWA Installation**: App installs on mobile (Android/iOS) and desktop (Chrome/Edge)
- [ ] **Manifest Valid**: All 8 icon sizes present, screenshots correct dimensions
- [ ] **Service Worker Active**: Offline support works (static assets cached)
- [ ] **Settings Page Functional**: All 4 tabs render, save buttons work
- [ ] **Model Settings Persist**: User's model/provider selection saved to database
- [ ] **Company Tab Visibility**: Company tab only visible in seo_coach mode
- [ ] **Minimal Chat UI**: Ollama-style interface with inline model selector
- [ ] **No Config in Chat**: All model/provider settings moved to settings page
- [ ] **Settings Navigation**: Settings icon in chat navigates to /settings page
- [ ] **Share Target Works**: Shared content opens chat with pre-filled message
- [ ] **Shortcuts Functional**: App shortcuts (New Chat, Settings, History) work
- [ ] **70%+ test coverage** for Phase 2.1 components
- [ ] **Manual testing checklist** 100% complete
- [ ] **Lighthouse PWA score**: 90+ (installability, offline support, HTTPS)
- [ ] **Mobile responsive**: Settings page and chat work on small screens
- [ ] **Phase 2.0 integration**: Settings linked to user_id from authentication

## Migration Notes

### From Phase 1 to Phase 2.1

**Existing Users**:
1. First login after Phase 2.1 → default settings created
2. Model/provider selection → moved from chat UI to settings page
3. Existing conversations → unaffected (settings stored per-user, not per-conversation)

**Database Changes**:
- Reuses Phase 2.0 `UserSettingModel` (no new migrations)
- Settings seeded with defaults on first settings page load

**UI Changes**:
- Chat interface redesigned (Ollama pattern)
- Model selector moved from sidebar/top to input area (bottom-right)
- Settings now in dedicated page, not embedded in chat

**Deployment**:
- Static files served via `/static` mount
- PWA manifest served at `/manifest.json`
- Service worker served at `/service-worker.js`
- HuggingFace Spaces: Add `static/` directory to repo

## Future Enhancements (Phase 3+)

**Not Implemented in Phase 2.1:**
- Settings sync across devices (requires cloud sync)
- Custom theme editor (only presets: Light/Dark/Auto)
- Advanced model parameter tuning (only temperature/max_tokens)
- Settings export/import (manual database backup only)
- Multi-language translations (UI shows language selector, translations in Phase 3)
- Offline agent execution (cache static assets only, no offline LLM)
- Settings version control/history (no audit trail yet)

## References

- **Phase 2.0**: `AUTH-001-user-authentication.md` (user_id dependency)
- **Phase 1**: Gradio mounting pattern (`GRADIO_STANDARDIZATION_COMPLETE.md`)
- **Testing Strategy**: `phase2_testing_strategy.md` (Phase 2.1 section)
- **Architecture Plan**: `phase2_architecture_plan.md` (lines 2039-2777)
- **PWA Standards**: https://web.dev/progressive-web-apps/
- **Ollama UI Reference**: https://ollama.com (design inspiration)
