"""Environment detection for database backend selection.

Detects whether the application is running in HuggingFace Spaces
or local environment to choose the appropriate database backend.
"""

import os


def detect_environment() -> str:
    """Detect the current runtime environment.

    Returns:
        "hf_spaces" if running in HuggingFace Spaces
        "local" for local development or Docker

    Examples:
        >>> env = detect_environment()
        >>> print(f"Running in: {env}")
    """
    # HuggingFace Spaces sets these environment variables
    if os.getenv("SPACE_ID") or os.getenv("SPACE_AUTHOR_NAME"):
        return "hf_spaces"

    # Check if we're explicitly configured for Hub DB
    if os.getenv("USE_HUB_DB", "").lower() in ("true", "1", "yes"):
        return "hf_spaces"

    return "local"


def is_hub_db_environment() -> bool:
    """Check if we're running in an environment that should use Hub DB.

    Returns:
        True if Hub DB should be used, False for SQLite

    Examples:
        >>> if is_hub_db_environment():
        ...     print("Using Hub DB")
        ... else:
        ...     print("Using SQLite")
    """
    return detect_environment() == "hf_spaces"
