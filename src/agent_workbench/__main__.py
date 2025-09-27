import logging
import os

import uvicorn
from dotenv import load_dotenv

from .main import app

# Load environment variables from .env file, overriding existing ones
load_dotenv(override=True)


def setup_debug_logging():
    """Setup debug logging based on environment variables."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )

    # Configure specific loggers for debug mode
    if log_level == "DEBUG":
        # Enable SQLAlchemy query logging if requested
        if os.getenv("SQLALCHEMY_ECHO", "").lower() == "1":
            logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
            logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)

        # Enable HTTP client debugging
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logging.getLogger("httpcore").setLevel(logging.DEBUG)

        # Enable our application debug logging
        logging.getLogger("agent_workbench").setLevel(logging.DEBUG)

        print("🔍 DEBUG MODE ENABLED")
        print(f"📊 Log Level: {log_level}")
        if os.getenv("SQLALCHEMY_ECHO"):
            print("📝 SQL Query Logging: ON")
        if os.getenv("CORS_DEBUG"):
            print("🌐 CORS Debug: ON")


if __name__ == "__main__":
    setup_debug_logging()

    # Check for debug mode
    fastapi_debug = os.getenv("FASTAPI_DEBUG", "").lower() == "1"
    log_level = os.getenv("LOG_LEVEL", "INFO").lower()

    # Configure uvicorn
    uvicorn_config = {
        "host": "0.0.0.0",
        "port": 8000,
        "log_level": log_level,
    }

    # Add reload only if we can use import string
    if fastapi_debug:
        uvicorn_config["app"] = "agent_workbench.main:app"
        uvicorn_config["reload"] = True
    else:
        uvicorn_config["app"] = app

    if fastapi_debug:
        print("🛠️ FastAPI Debug Mode: ON")
        print("🔄 Auto-reload: ON")
        print("📚 API Docs available at: http://localhost:8000/docs")

    uvicorn.run(**uvicorn_config)
