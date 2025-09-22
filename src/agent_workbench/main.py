from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.database import get_session
from .api.routes import agent_configs, chat, conversations, health, messages, models
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router)
app.include_router(chat.router)
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

        # Create default model config for ChatService
        default_config = ModelConfig(
            provider="ollama",
            model_name="llama3.1",
            temperature=0.7,
            max_tokens=1000,
        )

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
    default_config = ModelConfig(
        provider="ollama",
        model_name="llama3.1",
        temperature=0.7,
        max_tokens=1000,
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


# Enhanced Gradio mounting with comprehensive error handling
@app.on_event("startup")
async def mount_gradio_interface_safe():
    """Mount Gradio interface with comprehensive error handling (UI-003)"""
    import logging

    from .ui.mode_factory import InterfaceCreationError, InvalidModeError, ModeFactory

    logger = logging.getLogger(__name__)

    try:
        # Create mode factory
        factory = ModeFactory()

        # Get current mode
        current_mode = factory._determine_mode_safe(None)

        # Create interface
        gradio_interface = factory.create_interface(current_mode)

        # Mount interface
        app.mount("/", gradio_interface.app, name="gradio")

        logger.info(f"✅ Successfully mounted {current_mode} interface")

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
