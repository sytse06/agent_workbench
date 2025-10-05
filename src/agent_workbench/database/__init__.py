"""Database layer with Protocol-based backend abstraction.

This package provides a clean separation between database interface
and implementation, supporting both SQLite and HuggingFace Hub DB backends.
"""

from .adapter import AdaptiveDatabase
from .detection import detect_environment, is_hub_db_environment
from .protocol import DatabaseBackend

__all__ = [
    "DatabaseBackend",
    "AdaptiveDatabase",
    "detect_environment",
    "is_hub_db_environment",
]
