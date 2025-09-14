from fastapi import FastAPI

from .api.routes import agent_configs, chat, conversations, health, messages, models

app = FastAPI(
    title="Agent Workbench", description="Agent Workbench API", version="0.1.0"
)

# Include API routes
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(models.router)
app.include_router(agent_configs.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
