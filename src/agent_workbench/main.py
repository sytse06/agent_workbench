import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from uuid import UUID

import gradio as gr
import httpx
from fastapi import FastAPI, Request

# Import dotenv conditionally - not needed for HuggingFace Spaces
try:
    from dotenv import load_dotenv

    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
from fastapi.middleware.cors import CORSMiddleware

from .api.adaptive_database import init_adaptive_database
from .api.database import get_session
from .api.routes import (
    agent_configs,
    chat,
    consolidated_chat,
    conversations,
    direct_chat,
    health,
    messages,
    models,
)
from .models.database import ConversationModel, MessageModel
from .models.schemas import ModelConfig
from .services.context_service import ContextService
from .services.langgraph_bridge import LangGraphStateBridge
from .services.langgraph_service import WorkbenchLangGraphService
from .services.llm_service import ChatService
from .services.model_config_service import model_config_service
from .services.state_manager import StateManager


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
    env_file = f"config/{app_env}.env"
    if os.path.exists(env_file):
        load_dotenv(env_file, override=True)
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

    # Mount FastAPI-Gradio interface during startup
    try:
        print("🎯 Mounting FastAPI-Gradio interface...")
        gradio_interface = create_fastapi_mounted_gradio_interface()

        # Apply queue for responsiveness (must be before mounting)
        gradio_interface.queue()

        # CRITICAL: Call startup_events() before mounting (GitHub issue #8839)
        # This initializes the event handlers properly
        print("🎯 Calling startup_events() to initialize event handlers...")
        try:
            if hasattr(gradio_interface, 'startup_events'):
                gradio_interface.startup_events()
                print("✅ startup_events() called successfully")
            else:
                print("⚠️ No startup_events() method found, skipping")
        except Exception as e:
            print(f"⚠️ startup_events() failed (may be deprecated): {e}")

        # Use Gradio's official FastAPI mounting method
        print("🎯 Using gr.mount_gradio_app() for proper event routing...")
        app = gr.mount_gradio_app(app, gradio_interface, path="/")
        print("✅ FastAPI-mounted Gradio interface with database persistence")

    except Exception as e:
        # Fallback to API-only mode
        error_msg = f"Failed to mount FastAPI-Gradio interface: {e}"
        print(f"❌ {error_msg}")
        import traceback

        print(f"🎯 Traceback: {traceback.format_exc()}")
        print("⚠️ Starting in API-only mode")

        @app.get("/api/interface-error")
        async def get_interface_error():
            return {
                "error": "Interface not available",
                "message": error_msg,
                "mode": "api_only",
            }

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
# Register consolidated routes BEFORE legacy chat routes to avoid conflicts
app.include_router(consolidated_chat.router, prefix="/api/v1")
app.include_router(direct_chat.router, prefix="/api/v1")  # Direct LLM baseline
app.include_router(chat.router)  # Legacy routes
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(models.router)
app.include_router(agent_configs.router)


# Dependency injection for LangGraph service
async def get_langgraph_service() -> WorkbenchLangGraphService:
    """
    Get initialized LangGraph service instance.

    This provides proper dependency injection for LangGraph workflows
    using existing service infrastructure.
    """
    # Get database session
    async for db_session in get_session():
        # Initialize core services
        state_manager = StateManager(db_session)
        context_service = ContextService()

        # Create default model config using configuration service
        from .services.model_config_service import model_config_service

        default_config_dict = model_config_service.get_default_model_config()
        default_config = ModelConfig(**default_config_dict)

        # Initialize LLM service with required model config
        llm_service = ChatService(default_config)

        # Initialize LangGraph bridge
        state_bridge = LangGraphStateBridge(state_manager, context_service)

        # Create and return LangGraph service
        service = WorkbenchLangGraphService(
            state_bridge=state_bridge,
            llm_service=llm_service,
            context_service=context_service,
        )

        return service

    # If no database session is available, create service with minimal setup
    # This should not happen in normal operation but ensures function always returns
    context_service = ContextService()
    import os

    default_config = ModelConfig(
        provider="anthropic",
        model_name=os.getenv("DEFAULT_PRIMARY_MODEL", "claude-3-5-sonnet-20241022"),
        temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "2000")),
    )
    llm_service = ChatService(default_config)

    # Create a minimal state bridge (this would need proper DB session in production)
    # For now we'll raise an error to indicate configuration issue
    raise RuntimeError(
        "Unable to get database session for LangGraph service initialization"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def create_fastapi_mounted_gradio_interface():
    """Create FastAPI-mounted Gradio interface - SIMPLIFIED VERSION.

    Bypass all the complex layering and create interface directly.
    """
    print("🎯 Creating SIMPLIFIED Gradio interface directly")

    # Just create the enhanced interface directly - no factory, no wrapping
    return _create_enhanced_workbench_interface()


def _enhance_interface_with_database_persistence(interface: gr.Blocks, mode: str):
    """Enhance existing interface with database persistence capabilities."""

    # For now, we'll create a new interface that combines the mode-specific UI
    # with database persistence. In a future iteration, we could modify the
    # existing interface handlers directly.

    if mode == "seo_coach":
        return _create_enhanced_seo_coach_interface()
    else:
        return _create_enhanced_workbench_interface()


def _create_enhanced_workbench_interface():
    """Create enhanced workbench interface with database persistence."""

    # Get dynamic configuration from environment
    model_choices, default_model = model_config_service.get_model_choices_for_ui()

    title = "Agent Workbench - FastAPI-Mounted with Database Persistence"

    with gr.Blocks(title=title) as interface:
        gr.Markdown(f"# 🛠️ {title}")
        gr.Markdown("**Database Persistence Enabled** - All conversations saved!")

        conversation_id = gr.State(str(uuid.uuid4()))

        with gr.Row():
            with gr.Column(scale=1):
                # Single dropdown for provider/model combinations
                model_selection = gr.Dropdown(
                    choices=model_choices,
                    value=default_model,
                    label="Model Configuration",
                    info="Select provider and model combination",
                )

                temperature = gr.Slider(
                    0.0,
                    2.0,
                    model_config_service.default_temperature,
                    label="Temperature",
                )
                max_tokens = gr.Slider(
                    100,
                    4000,
                    model_config_service.default_max_tokens,
                    label="Max Tokens",
                )

                # Database status
                gr.Markdown("### 💾 Database Status")
                db_status = gr.HTML(value="<div class='info'>Ready</div>")

            with gr.Column(scale=2):
                # Test button at the top
                with gr.Row():
                    test_btn = gr.Button("🧪 Test Event System", variant="secondary")
                    test_output = gr.Textbox(label="Test Output", scale=3)

                chatbot = gr.Chatbot(
                    height=400,
                    label="Enhanced Chat with Database Persistence",
                    type="messages",
                )

                with gr.Row():
                    message = gr.Textbox(
                        placeholder="Enter message (saved to database)...",
                        label="Message",
                        scale=4,
                        lines=2,
                    )
                    send = gr.Button("Send", variant="primary", scale=1)

        # Test handler
        def test_handler():
            """Simple test to verify Gradio events work."""
            print("=" * 80)
            print("🧪 TEST BUTTON CLICKED - EVENT SYSTEM WORKS!")
            print("=" * 80)
            return "✅ Event system is working! Button click detected."

        test_btn.click(fn=test_handler, outputs=test_output)

        async def handle_workbench_message_with_persistence(
            msg, conv_id, model_selection_val, temp_val, max_tokens_val
        ):
            """Direct service call with database persistence for workbench mode."""
            # Parse provider and model from selection
            provider_val, model_val = model_config_service.parse_model_selection(
                model_selection_val
            )

            return await _handle_message_with_database_persistence(
                msg,
                conv_id,
                provider_val,
                model_val,
                temp_val,
                max_tokens_val,
                "workbench",
            )

        # Sync wrapper for async handler
        def handle_message_sync(*args):
            """Sync wrapper for Gradio that runs async handler."""
            import asyncio

            print("🚨 Wrapper called, running async handler...")
            return asyncio.run(handle_workbench_message_with_persistence(*args))

        # Wire up events
        send.click(
            fn=handle_message_sync,
            inputs=[message, conversation_id, model_selection, temperature, max_tokens],
            outputs=[message, chatbot, db_status],
        )

        message.submit(
            fn=handle_message_sync,
            inputs=[message, conversation_id, model_selection, temperature, max_tokens],
            outputs=[message, chatbot, db_status],
        )

    return interface


def _create_enhanced_seo_coach_interface():
    """Create enhanced SEO coach interface with database persistence."""

    title = "AI SEO Coach - FastAPI-Mounted with Database Persistence"

    with gr.Blocks(
        title=title,
        theme=gr.themes.Soft(),
        css="""
        .business-panel {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }
        .coaching-panel { min-height: 500px; }
        .success {
            color: #155724;
            background: #d4edda;
            padding: 10px;
            border-radius: 4px;
        }
        .error {
            color: #721c24;
            background: #f8d7da;
            padding: 10px;
            border-radius: 4px;
        }
        .info {
            color: #0c5460;
            background: #d1ecf1;
            padding: 10px;
            border-radius: 4px;
        }
        """,
    ) as interface:

        # Header
        gr.Markdown(f"# 🚀 {title}")
        gr.Markdown("*Verbeter je website ranking met persoonlijke AI coaching*")
        gr.Markdown("**Database Persistence Enabled** - All conversations saved!")

        # State management
        conversation_id = gr.State(str(uuid.uuid4()))
        business_profile = gr.State({})

        with gr.Row():
            # Left Panel: Business Profile
            with gr.Column(scale=1, elem_classes=["business-panel"]):
                gr.Markdown("### 🏢 Jouw Bedrijf")

                business_name = gr.Textbox(
                    label="Bedrijfsnaam", placeholder="Bijv. Bakkerij De Korenwolf"
                )
                business_type = gr.Dropdown(
                    choices=[
                        "Restaurant",
                        "Webshop",
                        "Dienstverlening",
                        "Productie",
                        "Anders",
                    ],
                    label="Type Bedrijf",
                )
                website_url = gr.Textbox(
                    label="Website URL", placeholder="https://jouwbedrijf.nl"
                )
                location = gr.Textbox(
                    label="Locatie", placeholder="Amsterdam, Nederland"
                )

                analyze_btn = gr.Button(
                    "🔍 Analyseer Mijn Website", variant="primary", size="lg"
                )

                # Database status
                gr.Markdown("### 💾 Database Status")
                db_status = gr.HTML(value="<div class='info'>Ready</div>")

            # Right Panel: Coaching Chat
            with gr.Column(scale=2, elem_classes=["coaching-panel"]):
                gr.Markdown("### 💬 Je Persoonlijke SEO Coach")

                chatbot = gr.Chatbot(
                    height=450,
                    label="",
                    placeholder="Welkom! Ik ben je SEO coach. "
                    "Vul je bedrijfsgegevens in om te beginnen.",
                    type="messages",
                )

                with gr.Row():
                    message_input = gr.Textbox(
                        placeholder="Stel je SEO vraag...",
                        label="Bericht",
                        lines=2,
                        scale=4,
                    )
                    send_button = gr.Button("Verstuur", variant="primary", scale=1)

        async def handle_seo_analysis_with_persistence(
            url, biz_name, biz_type, location, conv_id
        ):
            """Handle SEO analysis with database persistence."""
            if not all([url, biz_name, biz_type, location]):
                return [], {}, "<div class='error'>❌ Vul alle velden in</div>"

            # Create business profile
            profile = {
                "business_name": biz_name,
                "business_type": biz_type,
                "website_url": url,
                "location": location,
            }

            analysis_message = (
                f"Analyseer mijn {biz_type.lower()} website {url} "
                f"voor SEO verbeteringen"
            )

            # Use the enhanced message handler with SEO coach mode
            _, history, status = await _handle_message_with_database_persistence(
                analysis_message,
                conv_id,
                "anthropic",
                "claude-3-5-sonnet-20241022",
                0.7,
                2000,
                "seo_coach",
                profile,
            )

            success_html = f"""
            <div class='success'>
                ✅ Website geanalyseerd en opgeslagen<br>
                <strong>Bedrijf:</strong> {biz_name}<br>
                <strong>Website:</strong> <a href='{url}' target='_blank'>{url}</a>
            </div>
            """

            return history, profile, success_html

        async def handle_seo_message_with_persistence(msg, conv_id, profile):
            """Handle SEO coaching message with database persistence."""
            if not msg.strip():
                return "", []

            if not profile:
                return "", [
                    {
                        "role": "assistant",
                        "content": "Vul eerst je bedrijfsgegevens in om te beginnen.",
                    }
                ]

            # Use the enhanced message handler with SEO coach mode
            _, history, _ = await _handle_message_with_database_persistence(
                msg,
                conv_id,
                "anthropic",
                "claude-3-5-sonnet-20241022",
                0.7,
                2000,
                "seo_coach",
                profile,
            )

            return "", history

        # Wire up events
        analyze_btn.click(
            fn=handle_seo_analysis_with_persistence,
            inputs=[
                website_url,
                business_name,
                business_type,
                location,
                conversation_id,
            ],
            outputs=[chatbot, business_profile, db_status],
        )

        send_button.click(
            fn=handle_seo_message_with_persistence,
            inputs=[message_input, conversation_id, business_profile],
            outputs=[message_input, chatbot],
        )

        message_input.submit(
            fn=handle_seo_message_with_persistence,
            inputs=[message_input, conversation_id, business_profile],
            outputs=[message_input, chatbot],
        )

    return interface


def _create_fallback_workbench_interface():
    """Create simple fallback workbench interface."""
    with gr.Blocks(title="Agent Workbench - Fallback Mode") as interface:
        gr.Markdown("# 🛠️ Agent Workbench - Fallback Mode")
        gr.Markdown("**Database Persistence Enabled** - Simplified interface")

        conversation_id = gr.State(str(uuid.uuid4()))

        chatbot = gr.Chatbot(height=400, type="messages")
        message = gr.Textbox(placeholder="Enter your message...", label="Message")
        send = gr.Button("Send", variant="primary")

        async def simple_handler(msg, conv_id):
            if not msg.strip():
                return "", []

            # Simple database persistence
            _, history, _ = await _handle_message_with_database_persistence(
                msg,
                conv_id,
                "anthropic",
                "claude-3-5-sonnet-20241022",
                0.7,
                2000,
                "workbench",
            )
            return "", history

        send.click(
            fn=simple_handler,
            inputs=[message, conversation_id],
            outputs=[message, chatbot],
        )
        message.submit(
            fn=simple_handler,
            inputs=[message, conversation_id],
            outputs=[message, chatbot],
        )

    return interface


async def _handle_message_with_database_persistence(
    msg,
    conv_id,
    provider_val,
    model_val,
    temp_val,
    max_tokens_val,
    mode="workbench",
    business_profile=None,
):
    """Enhanced message handler with database persistence for both modes."""
    print(f"🎯 FastAPI-Gradio: handle_message called with msg='{msg}', mode='{mode}'")

    if not msg.strip():
        return "", [], "<div class='info'>Ready</div>"

    try:
        # Create model config (skip DB persistence for Hub DB)
        print("🎯 Creating model config...")
        model_config = ModelConfig(
            provider=provider_val,
            model_name=model_val,
            temperature=temp_val,
            max_tokens=max_tokens_val,
        )
        print(f"✅ Model config created: {provider_val}/{model_val}")

        # Direct LLM service call - no HTTP
        print("🎯 Initializing ChatService...")
        llm_service = ChatService(model_config)

        # Enhance message for SEO coach mode
        if mode == "seo_coach" and business_profile:
            enhanced_msg = f"""
            Context: Je bent een Nederlandse SEO expert voor websites.
            Bedrijf: {business_profile.get('business_name', 'Onbekend')}
            Type: {business_profile.get('business_type', 'Onbekend')}
            Website: {business_profile.get('website_url', 'Onbekend')}
            Locatie: {business_profile.get('location', 'Onbekend')}

            Vraag: {msg}

            Geef praktische, Nederlandse SEO adviezen specifiek voor dit bedrijf.
            """
            print("🎯 Calling chat_completion (SEO coach mode)...")
            response = await llm_service.chat_completion(
                message=enhanced_msg, conversation_id=None
            )
        else:
            print("🎯 Calling chat_completion (workbench mode)...")
            response = await llm_service.chat_completion(
                message=msg, conversation_id=None
            )

        print(f"✅ Got response: {response.reply[:100]}...")

        # Simple history (no database persistence for now)
        history = [
            {"role": "user", "content": msg},
            {"role": "assistant", "content": response.reply},
        ]

        # Success status
        success_html = f"""
        <div class='success'>
            ✅ Chat successful<br>
            <strong>Mode:</strong> {mode}<br>
            <strong>Provider:</strong> {provider_val}<br>
            <strong>Model:</strong> {model_val}
        </div>
        """

        return "", history, success_html

    except Exception as e:
        print(f"🎯 FastAPI-Gradio: Exception: {str(e)}")
        import traceback

        print(f"🎯 FastAPI-Gradio: Traceback: {traceback.format_exc()}")

        error_html = f"""
        <div class='error'>
            ❌ Database Error: {str(e)}<br>
            <small>Check logs for details</small>
        </div>
        """
        history = [
            {"role": "user", "content": msg},
            {"role": "assistant", "content": f"Error: {str(e)}"},
        ]
        return "", history, error_html


# Note: Gradio interface mounting is now handled in the lifespan function above


@app.get("/api/mode")
async def get_mode_info():
    """Get current mode information with enhanced error handling (UI-003)"""
    import logging

    from .ui.mode_factory import ModeFactory

    logger = logging.getLogger(__name__)

    try:
        factory = ModeFactory()
        current_mode = factory._determine_mode_safe(None)

        return {
            "current_mode": current_mode,
            "available_modes": factory.get_available_modes(),
            "extension_modes": list(factory.extension_registry.keys()),
            "status": "healthy",
            "interface_available": True,
            "phase": "1",
            "features": {
                "workbench": "Technical AI development interface",
                "seo_coach": "Dutch SEO coaching for businesses",
            },
        }
    except Exception as e:
        logger.error(f"Failed to get mode info: {e}")
        from fastapi import HTTPException

        raise HTTPException(
            status_code=500, detail=f"Failed to determine current mode: {str(e)}"
        )


@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check including mode factory status (UI-003)"""
    import logging
    from datetime import datetime

    from .ui.mode_factory import ModeFactory

    logger = logging.getLogger(__name__)

    try:
        factory = ModeFactory()
        current_mode = factory._determine_mode_safe(None)

        # Test interface creation
        interface = factory.create_interface(current_mode)
        interface_available = interface is not None

        return {
            "status": "healthy",
            "mode": current_mode,
            "interface_available": interface_available,
            "available_modes": factory.get_available_modes(),
            "extension_modes": list(factory.extension_registry.keys()),
            "timestamp": datetime.now().isoformat(),
            "phase": "1",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "mode": "api_only",
            "interface_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "phase": "1",
        }


def create_hf_spaces_app(mode: Optional[str] = None):
    """
    Create HuggingFace Spaces optimized Gradio app.

    This function is called by the generated HF Spaces app.py files
    to create a properly configured Gradio interface for deployment.

    Args:
        mode: Override mode (workbench or seo_coach)

    Returns:
        Gradio Blocks interface optimized for HF Spaces
    """
    import logging
    import os

    from .ui.mode_factory import InterfaceCreationError, InvalidModeError, ModeFactory

    logger = logging.getLogger(__name__)

    try:
        # Override mode if specified
        if mode:
            os.environ["APP_MODE"] = mode

        # Create mode factory
        factory = ModeFactory()

        # Get current mode
        current_mode = factory._determine_mode_safe(None)
        logger.info(f"Creating HF Spaces app for mode: {current_mode}")

        # Create interface
        interface = factory.create_interface(current_mode)

        if interface is None:
            raise InterfaceCreationError(f"Failed to create {current_mode} interface")

        # Configure for HF Spaces deployment
        interface.queue(
            max_size=30 if current_mode == "seo_coach" else 20,
            api_open=False,  # Disable API access for security
        )

        logger.info(f"✅ Successfully created {current_mode} interface for HF Spaces")
        return interface

    except (InvalidModeError, InterfaceCreationError) as e:
        logger.error(f"Failed to create HF Spaces app: {e}")
        # Create fallback error interface
        import gradio as gr

        error_msg = (
            "❌ Import Fout: Ontbrekende afhankelijkheden."
            if mode == "seo_coach"
            else "❌ Import Error: Missing dependencies."
        )
        title = "SEO Coach - Fout" if mode == "seo_coach" else "Agent Workbench - Error"

        error_interface = gr.Interface(
            fn=lambda: error_msg,
            inputs=[],
            outputs=gr.Textbox(label="Error" if mode != "seo_coach" else "Fout"),
            title=title,
            description=(
                "Er was een fout bij het starten van de applicatie."
                if mode == "seo_coach"
                else "There was an error starting the application."
            ),
        )
        return error_interface

    except Exception as e:
        logger.error(f"Unexpected error creating HF Spaces app: {e}", exc_info=True)
        # Create fallback error interface
        import gradio as gr

        error_msg = f"❌ Startup Error: {str(e)}"
        error_interface = gr.Interface(
            fn=lambda: error_msg,
            inputs=[],
            outputs=gr.Textbox(label="Error"),
            title="Application Error",
            description="There was an unexpected error starting the application.",
        )
        return error_interface


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
