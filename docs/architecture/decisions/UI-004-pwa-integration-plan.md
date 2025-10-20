# UI-004: PWA Integration Implementation Plan

## Status

**Status**: Architecture Complete
**Date**: October 20, 2025
**Parent Task**: UI-004-pwa-app-user-settings
**Phase**: 2.1

## Context

This document details the implementation plan for integrating the existing PWA infrastructure (located in `/deploy/pwa/`) with the main Agent Workbench application.

**Existing PWA Assets Audit** (as of 2025-10-20):
- ✅ Service Worker (`deploy/pwa/static/sw.js`) - Production-ready with caching, offline support, background sync
- ✅ Offline Page (`deploy/pwa/static/offline.html`) - Fully styled with auto-reconnect
- ✅ PWA Wrapper Template (`deploy/pwa/templates/pwa-wrapper.html`) - Complete with meta tags, install prompt
- ✅ Basic Manifest (`deploy/pwa/static/manifest.json`) - Needs enhancement
- ✅ Design Icons (`design/icons/logo_*.png`) - All 8 required sizes available
- ✅ UI Icons (`design/icons/*.png`) - Available for shortcuts and features
- ⚠️  Icon Deployment - Design icons not yet copied to deployment directory
- ❌ Screenshots - To be created after UI implementation

## Architecture Decisions

### 1. Asset Organization Strategy

**Decision**: Use single `static/` directory at application root, not `/deploy/pwa/static/`

**Rationale**:
- FastAPI `StaticFiles` mounting expects assets at runtime location
- `/deploy/pwa/` is a staging directory for PWA development/testing
- Production deployment (HuggingFace Spaces) requires assets in application structure
- Simplifies path references in manifest.json and service worker

**Directory Structure**:
```
src/agent_workbench/
└── static/                          # Served at /static/ in production
    ├── manifest.json                # PWA manifest
    ├── sw.js                        # Service worker (renamed from service-worker.js)
    ├── offline.html                 # Offline fallback page
    ├── icons/
    │   ├── icon-72.png             # Copied from design/icons/logo_72.png
    │   ├── icon-96.png             # Copied from design/icons/logo_96.png
    │   ├── icon-128.png            # Copied from design/icons/logo_128.png
    │   ├── icon-144.png            # Copied from design/icons/logo_144.png
    │   ├── icon-152.png            # Copied from design/icons/logo_152.png
    │   ├── icon-192.png            # Copied from design/icons/logo_192.png (REQUIRED)
    │   ├── icon-384.png            # Copied from design/icons/logo_384.png
    │   ├── icon-512.png            # Copied from design/icons/logo_512.png (REQUIRED)
    │   ├── apple-touch-icon.png    # iOS icon (180x180, use logo_192.png)
    │   ├── shortcut-chat.png       # New Chat shortcut (96x96)
    │   ├── shortcut-settings.png   # Settings shortcut (96x96)
    │   └── shortcut-history.png    # History shortcut (96x96)
    ├── screenshots/                 # Created after UI implementation
    │   ├── desktop-home.png        # 1280x720 (wide)
    │   ├── desktop-settings.png    # 1280x720 (wide)
    │   ├── mobile-chat.png         # 750x1334 (narrow)
    │   └── mobile-settings.png     # 750x1334 (narrow)
    └── assets/
        └── fonts/
            └── Ubuntu/              # Copy from design/assets/Ubuntu/
                ├── Ubuntu-Regular.ttf
                ├── Ubuntu-Bold.ttf
                └── ...
```

### 2. Icon Asset Preparation

**Main App Icons** (8 required sizes):

| Size | Source | Destination | Purpose | Required |
|------|--------|-------------|---------|----------|
| 72x72 | design/icons/logo_72.png | static/icons/icon-72.png | Android old devices | ✅ |
| 96x96 | design/icons/logo_96.png | static/icons/icon-96.png | Android notifications | ✅ |
| 128x128 | design/icons/logo_128.png | static/icons/icon-128.png | Chrome Web Store | ✅ |
| 144x144 | design/icons/logo_144.png | static/icons/icon-144.png | Windows tiles | ✅ |
| 152x152 | design/icons/logo_152.png | static/icons/icon-152.png | iOS devices | ✅ |
| 192x192 | design/icons/logo_192.png | static/icons/icon-192.png | Android home (maskable) | **REQUIRED** |
| 384x384 | design/icons/logo_384.png | static/icons/icon-384.png | High-res displays | ✅ |
| 512x512 | design/icons/logo_512.png | static/icons/icon-512.png | Splash screens (maskable) | **REQUIRED** |

**Apple Touch Icon**:
- Source: `design/icons/logo_192.png` (192x192)
- Destination: `static/icons/apple-touch-icon.png`
- iOS expects 180x180, but 192x192 works (iOS will scale)

**Shortcut Icons** (3 shortcuts, 96x96 each):

| Shortcut | Source Icon | Action URL | Purpose |
|----------|-------------|------------|---------|
| New Chat | design/icons/chat_add_icon.png | `/?new=true` | Start new conversation |
| Settings | design/icons/settings_icon.png | `/settings` | Open settings page |
| History | design/icons/left_panel_open_icon.png | `/?history=true` | Open chat history |

**Note**: Shortcut icons may need resizing to exactly 96x96 if source icons are different dimensions.

### 3. Manifest.json Configuration

**Complete manifest.json** (with all enhancements):

```json
{
  "name": "Agent Workbench",
  "short_name": "AgentWB",
  "description": "AI-powered workbench for technical users and SEO coaching",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "orientation": "portrait-primary",
  "categories": ["business", "productivity", "developer-tools"],

  "icons": [
    {
      "src": "/static/icons/icon-72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/icons/icon-384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/icons/apple-touch-icon.png",
      "sizes": "180x180",
      "type": "image/png",
      "purpose": "any"
    }
  ],

  "shortcuts": [
    {
      "name": "New Chat",
      "short_name": "New Chat",
      "description": "Start a new conversation",
      "url": "/?new=true",
      "icons": [
        {
          "src": "/static/icons/shortcut-chat.png",
          "sizes": "96x96",
          "type": "image/png"
        }
      ]
    },
    {
      "name": "Settings",
      "short_name": "Settings",
      "description": "Open application settings",
      "url": "/settings",
      "icons": [
        {
          "src": "/static/icons/shortcut-settings.png",
          "sizes": "96x96",
          "type": "image/png"
        }
      ]
    },
    {
      "name": "History",
      "short_name": "History",
      "description": "View conversation history",
      "url": "/?history=true",
      "icons": [
        {
          "src": "/static/icons/shortcut-history.png",
          "sizes": "96x96",
          "type": "image/png"
        }
      ]
    }
  ],

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
          "accept": ["text/*", "application/pdf", ".md", ".txt", "image/*"]
        }
      ]
    }
  },

  "screenshots": [
    {
      "src": "/static/screenshots/desktop-home.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide",
      "label": "Main chat interface"
    },
    {
      "src": "/static/screenshots/desktop-settings.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide",
      "label": "Settings page"
    },
    {
      "src": "/static/screenshots/mobile-chat.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow",
      "label": "Mobile chat view"
    },
    {
      "src": "/static/screenshots/mobile-settings.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow",
      "label": "Mobile settings"
    }
  ]
}
```

**Changes from existing manifest**:
- ✅ Added all 8 icon sizes (was only 3)
- ✅ Added `shortcuts` array with 3 shortcuts
- ✅ Added `share_target` configuration
- ✅ Added `scope` field
- ✅ Added `orientation` field
- ✅ Enhanced `screenshots` with labels
- ✅ Updated `categories` to include "developer-tools"

### 4. FastAPI Integration Strategy

**File**: `src/agent_workbench/main.py`

**Add Static Files Mount**:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Get the directory where main.py is located
BASE_DIR = Path(__file__).resolve().parent

# Mount static files BEFORE Gradio mount
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
```

**Add PWA Manifest Route**:
```python
@app.get("/manifest.json")
async def pwa_manifest() -> FileResponse:
    """
    Serve PWA manifest file.

    Returns manifest.json with proper MIME type for PWA installation.
    """
    manifest_path = BASE_DIR / "static" / "manifest.json"
    return FileResponse(
        manifest_path,
        media_type="application/manifest+json",
        headers={
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
    )
```

**Add Service Worker Route**:
```python
@app.get("/sw.js")
@app.get("/service-worker.js")  # Support both naming conventions
async def service_worker() -> FileResponse:
    """
    Serve service worker script.

    Returns sw.js with proper JavaScript MIME type.
    IMPORTANT: No caching for service worker (always fetch fresh).
    """
    sw_path = BASE_DIR / "static" / "sw.js"
    return FileResponse(
        sw_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Service-Worker-Allowed": "/"  # Allow SW to control root scope
        }
    )
```

**Add Offline Page Route** (fallback):
```python
@app.get("/offline")
async def offline_page() -> FileResponse:
    """
    Serve offline fallback page.

    Shown when user is offline and requested page is not cached.
    """
    offline_path = BASE_DIR / "static" / "offline.html"
    return FileResponse(offline_path, media_type="text/html")
```

**Integration Order** (CRITICAL):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources and mount Gradio interface."""

    # 1. Initialize database FIRST
    db = await init_adaptive_database(mode=mode)
    app.adaptive_db = db

    # 2. Create Gradio interface
    gradio_interface = create_fastapi_mounted_gradio_interface()

    # 3. Apply queue and startup events
    gradio_interface.queue()
    gradio_interface.run_startup_events()

    # 4. Mount Gradio at root path
    app.mount("/", gradio_interface.app, name="gradio")

    yield

    await app.requests_client.aclose()

# Create FastAPI app
app = FastAPI(lifespan=lifespan)

# Mount static files BEFORE lifespan runs
# (Static mount must happen before Gradio mount)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Add PWA routes BEFORE lifespan
app.get("/manifest.json")(pwa_manifest)
app.get("/sw.js")(service_worker)
app.get("/service-worker.js")(service_worker)
app.get("/offline")(offline_page)

# API routes registered elsewhere
# ...
```

**Why This Order Matters**:
1. Static mount must come BEFORE Gradio mount at `/`
2. PWA routes registered BEFORE lifespan (so they're available on startup)
3. Gradio mounts at `/` during lifespan (after static/PWA routes exist)
4. Result: `/static/*` and `/manifest.json` handled before Gradio catches all

### 5. Share Handler Implementation

**File**: `src/agent_workbench/api/routes/share.py`

**Share Handler Endpoint**:
```python
"""
Share target handler for PWA share functionality.

Allows users to share content from other apps/websites into Agent Workbench.
"""

from fastapi import APIRouter, Form, File, UploadFile, Request
from fastapi.responses import RedirectResponse
from typing import List, Optional
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["pwa", "share"])


@router.post("/share")
async def share_target_handler(
    request: Request,
    title: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    documents: Optional[List[UploadFile]] = File(None)
) -> RedirectResponse:
    """
    Handle shared content from other apps via PWA share target.

    Creates a new conversation with shared content pre-filled in the message input.

    Args:
        request: FastAPI request (for accessing user session)
        title: Shared title (optional)
        text: Shared text content (optional)
        url: Shared URL (optional)
        documents: Shared files (optional, Phase 2.4 full implementation)

    Returns:
        Redirect to main chat interface with pre-filled message

    Examples:
        - Share URL: "Check this out: https://example.com"
        - Share text: "Analyze this: [shared text]"
        - Share file: "Uploaded: document.pdf" (Phase 2.4)
    """
    logger.info(f"Share target received: title={title}, url={url}, files={len(documents) if documents else 0}")

    # Build message from shared content
    message_parts = []

    if title:
        message_parts.append(f"**{title}**")

    if url:
        message_parts.append(f"Shared URL: {url}")

    if text:
        # Limit text length to avoid overwhelming the chat
        max_text_length = 500
        truncated_text = text[:max_text_length] + "..." if len(text) > max_text_length else text
        message_parts.append(f"\n{truncated_text}")

    if documents:
        # Phase 2.1: Stub implementation (just list filenames)
        # Phase 2.4: Full file upload handling
        file_names = [doc.filename for doc in documents if doc.filename]
        if file_names:
            message_parts.append(f"\nAttached Files: {', '.join(file_names)}")
            logger.info(f"Files shared (not yet processed): {file_names}")

    # Combine message parts
    if not message_parts:
        # No content shared, just open chat
        return RedirectResponse(url="/", status_code=303)

    pre_filled_message = "\n".join(message_parts)

    # URL-encode message for query parameter
    encoded_message = quote_plus(pre_filled_message)

    # Redirect to chat with pre-filled message
    # The Gradio interface will read the 'message' query param and populate the input
    redirect_url = f"/?message={encoded_message}"

    logger.info(f"Redirecting to chat with pre-filled message ({len(pre_filled_message)} chars)")

    return RedirectResponse(url=redirect_url, status_code=303)
```

**Register Route in main.py**:
```python
from api.routes import share

# Register share handler
app.include_router(share.router)
```

**Gradio Interface Integration**:

The Gradio chat interface must read the `?message=` query parameter on load:

```python
# In ui/minimal_chat.py or ui/app.py

def create_minimal_chat_interface(user_id: str) -> gr.Blocks:
    with gr.Blocks() as app:
        # Chat components
        chatbot = gr.Chatbot()
        message_input = gr.Textbox(placeholder="Send a message")

        # On page load, check for pre-filled message
        def load_shared_message(request: gr.Request):
            """Load shared message from URL query parameter."""
            if hasattr(request, 'query_params') and 'message' in request.query_params:
                from urllib.parse import unquote_plus
                shared_msg = unquote_plus(request.query_params['message'])
                return shared_msg
            return ""

        # Populate message input on load
        app.load(fn=load_shared_message, outputs=[message_input])

    return app
```

### 6. Service Worker Updates

**File**: `src/agent_workbench/static/sw.js` (copied from `deploy/pwa/static/sw.js`)

**Changes Needed**:
- Update cache paths to match new structure
- Ensure `/static/` prefix in cached URLs
- Update version number for cache invalidation

**No major changes needed** - the existing service worker is already production-ready.

### 7. Ubuntu Font Integration

**Source**: All Ubuntu font files are available in `design/assets/Ubuntu/` (see `design/assets/Ubuntu font licence.html` for licensing).

**Available Font Files** (8 variants):
```
design/assets/Ubuntu/
├── Ubuntu-Regular.ttf        # 400 normal (primary)
├── Ubuntu-Bold.ttf           # 700 normal
├── Ubuntu-Light.ttf          # 300 normal
├── Ubuntu-Medium.ttf         # 500 normal
├── Ubuntu-Italic.ttf         # 400 italic
├── Ubuntu-BoldItalic.ttf     # 700 italic
├── Ubuntu-LightItalic.ttf    # 300 italic
└── Ubuntu-MediumItalic.ttf   # 500 italic
```

**Deployment Strategy**:

Copy all 8 Ubuntu font variants to `src/agent_workbench/static/assets/fonts/Ubuntu/`.

**Why all variants?**:
- Gradio UI uses various font weights (headings, buttons, labels)
- Prevents browser font synthesis (faux bold/italic)
- Better rendering quality
- PWA offline support (no external font CDN)

**Complete @font-face CSS**:

Create `src/agent_workbench/static/assets/css/fonts.css`:

```css
/* Ubuntu Font Family - Complete Integration
 * Source: design/assets/Ubuntu/
 * License: Ubuntu Font Licence (see Ubuntu font licence.html)
 */

/* Light */
@font-face {
  font-family: 'Ubuntu';
  src: url('/static/assets/fonts/Ubuntu/Ubuntu-Light.ttf') format('truetype');
  font-weight: 300;
  font-style: normal;
  font-display: swap;  /* Show fallback font while loading */
}

@font-face {
  font-family: 'Ubuntu';
  src: url('/static/assets/fonts/Ubuntu/Ubuntu-LightItalic.ttf') format('truetype');
  font-weight: 300;
  font-style: italic;
  font-display: swap;
}

/* Regular */
@font-face {
  font-family: 'Ubuntu';
  src: url('/static/assets/fonts/Ubuntu/Ubuntu-Regular.ttf') format('truetype');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Ubuntu';
  src: url('/static/assets/fonts/Ubuntu/Ubuntu-Italic.ttf') format('truetype');
  font-weight: 400;
  font-style: italic;
  font-display: swap;
}

/* Medium */
@font-face {
  font-family: 'Ubuntu';
  src: url('/static/assets/fonts/Ubuntu/Ubuntu-Medium.ttf') format('truetype');
  font-weight: 500;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Ubuntu';
  src: url('/static/assets/fonts/Ubuntu/Ubuntu-MediumItalic.ttf') format('truetype');
  font-weight: 500;
  font-style: italic;
  font-display: swap;
}

/* Bold */
@font-face {
  font-family: 'Ubuntu';
  src: url('/static/assets/fonts/Ubuntu/Ubuntu-Bold.ttf') format('truetype');
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Ubuntu';
  src: url('/static/assets/fonts/Ubuntu/Ubuntu-BoldItalic.ttf') format('truetype');
  font-weight: 700;
  font-style: italic;
  font-display: swap;
}

/* Global Font Application
 * Fallback stack: system fonts for better performance and cross-platform consistency
 */
:root {
  --font-family-primary: 'Ubuntu', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                         'Helvetica Neue', Arial, sans-serif;
}

/* Apply to all elements */
* {
  font-family: var(--font-family-primary);
}

/* Specific Gradio component overrides (if needed) */
.gradio-container {
  font-family: var(--font-family-primary) !important;
}

.gr-button, .gr-input, .gr-box {
  font-family: var(--font-family-primary) !important;
}
```

**Gradio Integration Method 1: Custom CSS File**:

```python
# ui/app.py or ui/minimal_chat.py

import gradio as gr

def create_workbench_app() -> gr.Blocks:
    # Load custom CSS file
    custom_css = """
        @import url('/static/assets/css/fonts.css');
    """

    with gr.Blocks(css=custom_css, title="Agent Workbench") as app:
        # ... interface components
        pass

    return app
```

**Gradio Integration Method 2: Inline CSS**:

```python
# ui/app.py

def create_workbench_app() -> gr.Blocks:
    with gr.Blocks(
        css="""
            /* Ubuntu Font Loading - Inline */
            @font-face {
                font-family: 'Ubuntu';
                src: url('/static/assets/fonts/Ubuntu/Ubuntu-Regular.ttf') format('truetype');
                font-weight: 400;
                font-style: normal;
                font-display: swap;
            }

            @font-face {
                font-family: 'Ubuntu';
                src: url('/static/assets/fonts/Ubuntu/Ubuntu-Bold.ttf') format('truetype');
                font-weight: 700;
                font-style: normal;
                font-display: swap;
            }

            @font-face {
                font-family: 'Ubuntu';
                src: url('/static/assets/fonts/Ubuntu/Ubuntu-Light.ttf') format('truetype');
                font-weight: 300;
                font-style: normal;
                font-display: swap;
            }

            /* Apply globally */
            * {
                font-family: 'Ubuntu', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            }
        """,
        title="Agent Workbench"
    ) as app:
        # ... interface
        pass

    return app
```

**Recommendation**: Use Method 1 (separate CSS file) for:
- Better organization
- Easier maintenance
- Reusability across multiple UI modes (workbench, seo_coach)
- Browser caching (fonts.css cached separately)

**Font Loading Performance Optimization**:

```python
# Add preload hints to HTML head (if using custom Gradio template)
# File: src/agent_workbench/static/pwa-wrapper.html (or custom template)

<head>
    <!-- Preload critical fonts for faster rendering -->
    <link rel="preload" href="/static/assets/fonts/Ubuntu/Ubuntu-Regular.ttf" as="font" type="font/ttf" crossorigin>
    <link rel="preload" href="/static/assets/fonts/Ubuntu/Ubuntu-Bold.ttf" as="font" type="font/ttf" crossorigin>

    <!-- Load fonts CSS -->
    <link rel="stylesheet" href="/static/assets/css/fonts.css">
</head>
```

**Testing Font Integration**:

1. **Visual Check**: Open app, inspect element, verify `font-family: Ubuntu` in computed styles
2. **Network Tab**: Check fonts load from `/static/assets/fonts/Ubuntu/`
3. **Offline Test**: Install PWA, go offline, verify fonts still render (cached by service worker)
4. **Cross-browser**: Test on Chrome, Firefox, Safari, Edge
5. **Mobile**: Test on iOS Safari and Android Chrome

**Troubleshooting**:

- **Fonts not loading**: Check static files mount order (must be BEFORE Gradio mount)
- **Fallback fonts showing**: Check browser Network tab for 404s, verify file paths
- **CORS errors**: Add `crossorigin="anonymous"` to font preload links
- **Bold/italic not working**: Ensure all 8 font variants are deployed

## Implementation Checklist

### Phase 1: Asset Preparation
- [ ] Create `src/agent_workbench/static/` directory structure
- [ ] Copy 8 main app icons from `design/icons/logo_*.png` to `static/icons/icon-*.png`
- [ ] Create/resize shortcut icons to 96x96:
  - [ ] `shortcut-chat.png` from `chat_add_icon.png`
  - [ ] `shortcut-settings.png` from `settings_icon.png`
  - [ ] `shortcut-history.png` from `left_panel_open_icon.png`
- [ ] Copy `logo_192.png` as `apple-touch-icon.png`
- [ ] Copy Ubuntu fonts to `static/assets/fonts/Ubuntu/`
- [ ] Copy `sw.js`, `offline.html` from `deploy/pwa/static/` to `static/`

### Phase 2: Configuration
- [ ] Update `manifest.json` with all 8 icons, shortcuts, and share_target
- [ ] Update `sw.js` cache paths (if needed)
- [ ] Verify all icon paths resolve correctly

### Phase 3: FastAPI Integration
- [ ] Add static files mount in `main.py` (BEFORE Gradio mount)
- [ ] Add `/manifest.json` route
- [ ] Add `/sw.js` and `/service-worker.js` routes
- [ ] Add `/offline` route
- [ ] Create `api/routes/share.py` with share handler
- [ ] Register share router in `main.py`

### Phase 4: Gradio Integration
- [ ] Add query parameter parsing to chat interface
- [ ] Load pre-filled message from `?message=` param
- [ ] Add Ubuntu font CSS to Gradio theme
- [ ] Add PWA meta tags to Gradio HTML head (if using custom template)

### Phase 5: Testing
- [ ] Test manifest.json serves correctly at `/manifest.json`
- [ ] Test service worker registers (check browser DevTools)
- [ ] Test offline page displays when offline
- [ ] Test PWA install prompt appears (Chrome/Edge desktop)
- [ ] Test "Add to Home Screen" on mobile (Android/iOS)
- [ ] Test share target with text, URL, file
- [ ] Test shortcuts work after installation
- [ ] Test Ubuntu font loads correctly
- [ ] Run Lighthouse PWA audit (target: 90+ score)

### Phase 6: Screenshots (After UI Implementation)
- [ ] Capture desktop-home.png (1280x720)
- [ ] Capture desktop-settings.png (1280x720)
- [ ] Capture mobile-chat.png (750x1334)
- [ ] Capture mobile-settings.png (750x1334)
- [ ] Add screenshots to `static/screenshots/`
- [ ] Verify screenshots in manifest.json

## Testing Strategy

### Manual Testing

**PWA Installation**:
1. Open app in Chrome/Edge desktop
2. Look for install icon in address bar
3. Click install → verify app opens in standalone window
4. Check app icon, title, theme color

**Mobile Installation**:
1. Open app on Android Chrome
2. Menu → "Add to Home Screen"
3. Verify icon appears on home screen
4. Launch app → verify standalone mode (no browser UI)

**Shortcuts**:
1. After installation, right-click app icon (desktop) or long-press (mobile)
2. Verify 3 shortcuts appear: New Chat, Settings, History
3. Test each shortcut opens correct URL

**Share Target**:
1. On mobile, find "Share" in another app (browser, notes, etc.)
2. Share text/URL to Agent Workbench
3. Verify app opens with shared content pre-filled

**Offline Mode**:
1. Open app and navigate around
2. Turn off network (airplane mode)
3. Refresh page → verify offline.html appears
4. Turn network back on → verify auto-reconnect

### Automated Testing

**E2E Test for Share Handler**:
```python
# tests/e2e/test_pwa_share.py

async def test_share_text_prefills_message():
    """Test sharing text populates chat input."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/share",
            data={"text": "Analyze this content", "url": "https://example.com"}
        )

        assert response.status_code == 303
        assert "message=" in response.headers["location"]
        assert "example.com" in response.headers["location"]
```

**Manifest Validation Test**:
```python
# tests/e2e/test_pwa_manifest.py

def test_manifest_structure():
    """Validate manifest.json structure."""
    manifest_path = Path(__file__).parent.parent.parent / "src" / "agent_workbench" / "static" / "manifest.json"
    manifest = json.load(open(manifest_path))

    # Required fields
    assert "name" in manifest
    assert "short_name" in manifest
    assert "start_url" in manifest
    assert "display" in manifest

    # Icons (8 sizes + apple)
    assert len(manifest["icons"]) == 9
    icon_sizes = {icon["sizes"] for icon in manifest["icons"]}
    required = {"72x72", "96x96", "128x128", "144x144", "152x152", "192x192", "384x384", "512x512"}
    assert required.issubset(icon_sizes)

    # Shortcuts (3)
    assert len(manifest["shortcuts"]) == 3
    shortcut_names = {s["name"] for s in manifest["shortcuts"]}
    assert {"New Chat", "Settings", "History"} == shortcut_names

    # Share target
    assert "share_target" in manifest
    assert manifest["share_target"]["action"] == "/share"
```

## Success Criteria

- [ ] All 8 icon sizes + shortcuts visible in manifest.json
- [ ] PWA installs successfully on Chrome/Edge desktop
- [ ] PWA installs successfully on Android Chrome
- [ ] PWA installs successfully on iOS Safari
- [ ] Share target works from mobile browser
- [ ] Offline page displays when network unavailable
- [ ] Service worker caches static assets
- [ ] Shortcuts work post-installation
- [ ] Ubuntu font loads and displays
- [ ] Lighthouse PWA score: 90+
- [ ] All E2E tests pass

## Migration Notes

**No Breaking Changes**:
- Static files added, no existing files modified (except main.py)
- Gradio mounting pattern unchanged
- Existing API routes unaffected

**Deployment Changes**:
- Add `static/` directory to version control
- Update `.gitignore` if needed (don't ignore static assets)
- Ensure HuggingFace Spaces includes `static/` in deployment

## References

- **Parent Architecture**: `docs/architecture/decisions/UI-004-pwa-app-user-settings.md`
- **UX Design**: `design/UI-004-target-ux.md`
- **PWA Standards**: https://web.dev/progressive-web-apps/
- **Service Worker API**: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API
- **Web App Manifest**: https://developer.mozilla.org/en-US/docs/Web/Manifest
