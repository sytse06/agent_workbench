"""Entry point for running agent_workbench as a module."""

import logging
import os

_log_level = getattr(
    logging, os.getenv("LOG_LEVEL", "WARNING").upper(), logging.WARNING
)
logging.basicConfig(level=_log_level, format="%(levelname)s %(name)s: %(message)s")

# Suppress verbose low-level loggers that flood output even at DEBUG level
for _noisy in ("aiosqlite", "sqlalchemy.engine", "sqlalchemy.pool"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

import uvicorn  # noqa: E402

from .main import app  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
