import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import dotenv conditionally - not needed for HuggingFace Spaces
try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import (
    agent_configs,
    chat_workflow,
    health,
    models,
    share,
    simple_chat,
)
from .database import init_adaptive_database
from .services.model_config_service import model_config_service


def load_environment():
    """Load environment using standard APP_ENV pattern."""
    # Check if we're in HuggingFace Spaces (dotenv not needed)
    if not DOTENV_AVAILABLE or os.getenv("SPACE_ID"):
        print("🚀 Running in HuggingFace Spaces - using environment variables directly")
        return os.getenv("APP_ENV", "production")

    # 1. Load base .env (backwards compatibility)
    load_dotenv(".env", override=False)

    # 2. Get environment
    app_env = os.getenv("APP_ENV", "development")

    # 3. Load environment-specific config
    # Note: override=False preserves environment variables set on command line
    # This allows: APP_MODE=seo_coach make start-app
    env_file = f"config/{app_env}.env"
    if os.path.exists(env_file):
        load_dotenv(env_file, override=False)
        print(f"✅ Loaded {app_env} environment from {env_file}")
    else:
        print(f"⚠️  No config file found for {app_env}, using base .env")

    return app_env


# Load environment at startup
current_env = load_environment()
print(f"🚀 Starting Agent Workbench in {current_env} mode")

# Refresh model config service to pick up environment changes
model_config_service.refresh_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources and services for FastAPI-mounted Gradio."""
    print("🔧 Initializing FastAPI lifespan services...")

    # Initialize shared HTTP client for external APIs
    app.requests_client = httpx.AsyncClient(timeout=30.0)

    # Initialize adaptive database (automatically chooses SQLite or Hub DB)
    try:
        mode = os.getenv("APP_MODE", "workbench")
        db = await init_adaptive_database(mode=mode)
        app.adaptive_db = db

        # Provide session compatibility for existing code
        if hasattr(db, "get_session"):
            app.get_session = db.get_session
        else:
            # For Hub DB, provide a dummy session
            app.get_session = lambda: None

        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("🔧 Continuing without database persistence...")
        app.adaptive_db = None
        app.get_session = lambda: None

    # Initialize services that will be used by Gradio interface
    # These will be accessed directly by Gradio handlers
    print("✅ FastAPI lifespan services initialized")

    # Create and mount Gradio interfaces
    # Note: We store references to prevent garbage collection
    print("🎯 Creating Gradio interfaces...")

    # Create single Gradio interface with routes (UI-005)
    try:
        app.state.gradio_interface = create_fastapi_mounted_gradio_interface()
        app.state.gradio_interface.queue()
        # Set max_file_size so Gradio's upload handler doesn't AttributeError.
        # Blocks.launch() normally sets this; we skip launch() in the FastAPI-mount pattern.
        if not hasattr(app.state.gradio_interface, "max_file_size"):
            app.state.gradio_interface.max_file_size = None
        if hasattr(app.state.gradio_interface, "run_startup_events"):
            app.state.gradio_interface.run_startup_events()
        print("✅ Gradio interface created with multipage routing")
    except Exception as e:
        print(f"❌ Failed to create Gradio interface: {e}")
        import traceback

        print(traceback.format_exc())
        app.state.gradio_interface = None

    # Mount interface at root path
    # UI-005: Single Gradio app with internal routes (/ and /settings)
    if app.state.gradio_interface:
        print("🎯 Mounting Gradio interface at root /...")
        app.mount("/", app.state.gradio_interface.app, name="gradio")
        print("✅ Gradio interface mounted at / with routes: / (chat) and /settings")

    yield

    # Cleanup
    print("🔧 Cleaning up FastAPI lifespan services...")
    await app.requests_client.aclose()
    print("✅ FastAPI lifespan cleanup complete")


app = FastAPI(
    title="Agent Workbench",
    description="Agent Workbench API with FastAPI-mounted Gradio",
    version="0.1.0",
    lifespan=lifespan,
)

# Get base directory for static files
BASE_DIR = Path(__file__).resolve().parent


# ============================================================================
# Google Fonts Injection Middleware
# ============================================================================
# Workaround for Gradio's Constructable Stylesheets limitation
# Injects Google Fonts link into HTML responses
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

        # Inject Google Fonts link before </head>
        google_fonts_url = (
            "https://fonts.googleapis.com/css2?"
            "family=Lora:ital,wght@0,400..700;1,400..700&"
            "family=Ubuntu:ital,wght@0,300;0,400;0,500;0,700;"
            "1,300;1,400;1,500;1,700&display=swap"
        )
        google_fonts_link = f"""
    <!-- Google Fonts: Ubuntu (headers) + Lora (body text) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="{google_fonts_url}" rel="stylesheet">
</head>""".encode("utf-8")

        # Replace </head> with fonts + </head>
        modified_body = body.replace(b"</head>", google_fonts_link)

        # Return modified response with updated headers
        from fastapi.responses import Response

        # Copy headers but remove Content-Length (will be recalculated)
        headers = dict(response.headers)
        headers.pop("content-length", None)

        return Response(
            content=modified_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )

    return response


# Mount static files BEFORE Gradio mount (critical order)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ============================================================================
# Gradio Interface Mounting (via startup event)
# IMPORTANT: Mounting must happen after all functions are defined
# ============================================================================

# Interfaces will be created and mounted in startup event below


# PWA Routes - must be registered before Gradio mount
@app.get("/manifest.json")
async def pwa_manifest():
    """
    Serve dynamically generated PWA manifest.

    Adapts URLs based on environment (HF Spaces vs local/Docker).
    Returns manifest.json with proper MIME type for PWA installation.
    """
    from fastapi.responses import JSONResponse

    # Detect environment
    is_hf_spaces = os.getenv("SPACE_ID") is not None
    app_mode = os.getenv("APP_MODE", "workbench")

    # Set URLs - UI-005: Root route at / for all environments
    start_url = "/"
    settings_url = "/settings"
    new_chat_url = "/?new=true"
    history_url = "/?history=true"

    # Set theme based on mode
    theme_colors = {
        "workbench": "#3b82f6",  # Blue
        "seo_coach": "#10b981",  # Green
    }
    theme_color = theme_colors.get(app_mode, "#3b82f6")

    # Set names based on mode
    names = {
        "workbench": {
            "name": "Agent Workbench",
            "short_name": "AgentWB",
            "description": "AI-powered workbench for technical users",
        },
        "seo_coach": {
            "name": "SEO Coach",
            "short_name": "SEO-Coach",
            "description": "AI-powered SEO coaching voor Nederlandse bedrijven",
        },
    }
    app_names = names.get(app_mode, names["workbench"])

    manifest = {
        "name": app_names["name"],
        "short_name": app_names["short_name"],
        "description": app_names["description"],
        "start_url": start_url,
        "scope": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": theme_color,
        "orientation": "portrait-primary",
        "categories": ["business", "productivity", "developer-tools"],
        "icons": [
            {
                "src": "/static/icons/icon-72.png",
                "sizes": "72x72",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/static/icons/icon-96.png",
                "sizes": "96x96",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/static/icons/icon-128.png",
                "sizes": "128x128",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/static/icons/icon-144.png",
                "sizes": "144x144",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/static/icons/icon-152.png",
                "sizes": "152x152",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/icons/icon-384.png",
                "sizes": "384x384",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/icons/apple-touch-icon.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
        ],
        "shortcuts": [
            {
                "name": "New Chat",
                "short_name": "New Chat",
                "description": "Start a new conversation",
                "url": new_chat_url,
                "icons": [
                    {
                        "src": "/static/icons/shortcut-chat.png",
                        "sizes": "96x96",
                        "type": "image/png",
                    }
                ],
            },
            {
                "name": "Settings" if not is_hf_spaces else "Home",
                "short_name": "Settings" if not is_hf_spaces else "Home",
                "description": (
                    "Open application settings" if not is_hf_spaces else "Go to home"
                ),
                "url": settings_url,
                "icons": [
                    {
                        "src": "/static/icons/shortcut-settings.png",
                        "sizes": "96x96",
                        "type": "image/png",
                    }
                ],
            },
            {
                "name": "History",
                "short_name": "History",
                "description": "View conversation history",
                "url": history_url,
                "icons": [
                    {
                        "src": "/static/icons/shortcut-history.png",
                        "sizes": "96x96",
                        "type": "image/png",
                    }
                ],
            },
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
                        "accept": [
                            "text/*",
                            "application/pdf",
                            ".md",
                            ".txt",
                            "image/*",
                        ],
                    }
                ],
            },
        },
    }

    return JSONResponse(
        content=manifest,
        media_type="application/manifest+json",
        headers={"Cache-Control": "public, max-age=3600"},
    )


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
            "Service-Worker-Allowed": "/",  # Allow SW to control root scope
        },
    )


@app.get("/offline")
async def offline_page() -> FileResponse:
    """
    Serve offline fallback page.

    Shown when user is offline and requested page is not cached.
    """
    offline_path = BASE_DIR / "static" / "offline.html"
    return FileResponse(offline_path, media_type="text/html")


# Root redirect removed - UI-005: Gradio mounted at "/" with internal routing
# Gradio handles root path with routes: / (chat) and /settings


# Authentication Configuration
# AUTH_MODE determines authentication behavior:
# - "disabled" (default): No authentication
# - "development": Local mock authentication (for testing auth features)
# - "oauth": Production OAuth (HuggingFace, requires proper callback setup)
AUTH_MODE = os.getenv("AUTH_MODE", "disabled")  # "disabled", "development", or "oauth"
AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "huggingface")

# Enable auth if mode is development or oauth
ENABLE_AUTH = AUTH_MODE in ["development", "oauth"]

# Log authentication configuration
print("=" * 80)
print("🔐 AUTHENTICATION CONFIGURATION")
print(f"   AUTH_MODE: {AUTH_MODE}")
if ENABLE_AUTH:
    print("   Status: Authentication enabled")
    print(f"   AUTH_PROVIDER: {AUTH_PROVIDER}")
    if AUTH_MODE == "development":
        dev_user = os.getenv("DEV_USERNAME", "local-dev-user")
        print(f"   DEV_USERNAME: {dev_user}")
else:
    print("   Status: Authentication disabled")
print("=" * 80)

# Add CORS middleware
cors_debug = os.getenv("CORS_DEBUG", "").lower() == "1"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add debug middleware if enabled
if os.getenv("LOG_LEVEL", "").upper() == "DEBUG":
    logger = logging.getLogger("agent_workbench.debug")

    @app.middleware("http")
    async def debug_middleware(request: Request, call_next):
        """Debug middleware for request/response logging."""
        start_time = time.time()

        # Log request details
        logger.debug(f"🔵 REQUEST: {request.method} {request.url}")
        logger.debug(f"📄 Headers: {dict(request.headers)}")

        # Get request body for POST requests (only for debug)
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    # Try to decode as text (don't parse JSON to avoid errors)
                    body_text = body.decode("utf-8")
                    # Only log first 500 chars to avoid spam
                    logger.debug(f"📤 Body (first 500 chars): {body_text[:500]}")
                except (UnicodeDecodeError, Exception):
                    logger.debug(f"📤 Body: {len(body)} bytes (binary)")

        # Process request
        response = await call_next(request)

        # Log response details
        process_time = time.time() - start_time
        logger.debug(f"🔴 RESPONSE: {response.status_code} ({process_time:.3f}s)")
        logger.debug(f"📄 Response headers: {dict(response.headers)}")

        # Add debug headers if CORS debug is enabled
        if cors_debug:
            response.headers["X-Debug-Process-Time"] = str(process_time)
            response.headers["X-Debug-Request-Method"] = request.method

        return response


# Include API routes
app.include_router(health.router)

# PRIMARY: Full LangGraph workflow (workbench + seo_coach modes)
app.include_router(chat_workflow.router, prefix="/api/v1")

# UTILITY: Minimal 2-node LangGraph workflow for testing/debugging
app.include_router(simple_chat.router, prefix="/api/v1")

# PWA Share handler
app.include_router(share.router)

# Other routes
app.include_router(models.router)
app.include_router(agent_configs.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def create_fastapi_mounted_gradio_interface():
    """Create FastAPI-mounted Gradio interface using Mode Factory V2.

    UI-005: Creates single Gradio app with internal routing (/ and /settings).
    Uses mode_factory_v2 for configuration-driven multipage routing.
    """
    import os

    from .ui.mode_factory_v2 import create_app

    mode = os.getenv("APP_MODE", "workbench")
    print(f"🎯 Creating Gradio interface with multipage routing for mode: {mode}")

    # Create single interface with routes
    interface = create_app()

    # Apply Gradio OAuth if authentication is enabled
    # Note: For HuggingFace Spaces, OAuth is handled automatically via Space settings
    # We rely on Space-level auth + our on_load handlers for user management
    if ENABLE_AUTH and AUTH_MODE == "oauth":
        print(f"🔐 OAuth mode enabled: {AUTH_PROVIDER}")
        print("ℹ️  HuggingFace Spaces: OAuth handled at Space level")
        print("ℹ️  Application will use on_load handlers for user management")
    elif ENABLE_AUTH and AUTH_MODE == "development":
        print("⚠️  Development mode - no OAuth (local testing only)")
    else:
        print("⚠️  Authentication disabled")

    print(f"✅ Created {mode} interface with routes: / (chat) and /settings")
    return interface


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
