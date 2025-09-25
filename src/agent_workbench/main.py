import logging
import os
import time
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv


def load_environment():
    """Load environment using standard APP_ENV pattern."""
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

from .api.database import get_session
from .api.routes import agent_configs, chat, consolidated_chat, conversations, direct_chat, health, messages, models
from .models.schemas import ModelConfig
from .services.context_service import ContextService
from .services.langgraph_bridge import LangGraphStateBridge
from .services.langgraph_service import WorkbenchLangGraphService
from .services.llm_service import ChatService
from .services.state_manager import StateManager

# Mode factory imports will be done within functions to avoid circular imports

app = FastAPI(
    title="Agent Workbench", description="Agent Workbench API", version="0.1.0"
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
                    body_text = body.decode('utf-8')
                    # Only log first 500 chars to avoid spam
                    logger.debug(f"📤 Body (first 500 chars): {body_text[:500]}")
                except:
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


# Complex UI mounting with queue fix - Testing the same solution on layered architecture
@app.on_event("startup")
async def mount_complex_interface_with_queue_fix():
    """Mount complex layered UI with the same queue fix that worked for simple UI."""
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Import complex mode factory
        from .ui.mode_factory import InterfaceCreationError, InvalidModeError, ModeFactory
        
        # Create mode factory
        factory = ModeFactory()
        
        # Get current mode
        current_mode = factory._determine_mode_safe(None)
        
        # Create complex interface
        gradio_interface = factory.create_interface(current_mode)
        
        # CRITICAL FIX: Apply the same queue fix that worked for simple UI
        # This should resolve the original responsiveness issues
        gradio_interface.queue()
        gradio_interface.run_startup_events()
        
        # Mount interface
        app.mount("/", gradio_interface.app, name="gradio")
        
        logger.info(f"✅ Successfully mounted {current_mode} interface with queue fix")
        
    except InvalidModeError as e:
        # Configuration error - should not start
        error_msg = f"Invalid mode configuration: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
        
    except InterfaceCreationError as e:
        # Interface creation failed - fallback to API-only mode
        error_msg = f"Interface creation failed: {e}"
        logger.error(error_msg)
        logger.warning("Starting in API-only mode")
        
        # Add error endpoint for monitoring
        error_message = str(e)
        
        @app.get("/api/interface-error")
        async def get_interface_error():
            return {
                "error": "Interface not available",
                "message": error_message,
                "mode": "api_only",
            }
            
    except Exception as e:
        # Unexpected error - fallback to API-only mode
        error_msg = f"Unexpected error mounting interface: {e}"
        logger.error(error_msg, exc_info=True)
        logger.warning("Starting in API-only mode")
        
        @app.get("/api/interface-error")
        async def get_interface_error():
            return {
                "error": "Interface not available",
                "message": "Unexpected error during interface mounting",
                "mode": "api_only",
            }


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
            concurrency_count=5 if current_mode == "seo_coach" else 3,
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
