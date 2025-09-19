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


# Mount Gradio app
@app.on_event("startup")
async def mount_gradio_app():
    """Mount the Gradio interface"""
    # The Gradio app will be launched separately, but we can set up the route
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
