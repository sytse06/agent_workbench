"""
Mode Factory for Agent Workbench - UI-002 SEO Coach Interface.

Provides environment-based interface switching between workbench and SEO coach modes.
"""

import os
from typing import Optional

import gradio as gr

from .app import create_workbench_app
from .seo_coach_app import create_seo_coach_app


def create_interface_for_mode(mode: Optional[str] = None) -> gr.Blocks:
    """
    Create interface based on APP_MODE environment variable.

    Args:
        mode: Override mode (optional). If not provided, uses APP_MODE env var.

    Returns:
        Gradio Blocks interface for the specified mode

    Raises:
        ValueError: If mode is invalid
    """
    effective_mode = mode or os.getenv("APP_MODE", "workbench")

    if effective_mode == "seo_coach":
        return create_seo_coach_app()
    elif effective_mode == "workbench":
        return create_workbench_app()
    else:
        raise ValueError(
            f"Invalid mode: {effective_mode}. Use 'workbench' or 'seo_coach'"
        )


def get_mode_from_environment() -> str:
    """
    Get current mode from environment variables.

    Returns:
        Mode string ("workbench" or "seo_coach")
    """
    return os.getenv("APP_MODE", "workbench")


def validate_mode_configuration(mode: str) -> bool:
    """
    Validate mode configuration.

    Args:
        mode: Mode to validate

    Returns:
        True if mode is valid, False otherwise
    """
    return mode in ["workbench", "seo_coach"]


# Extension point for Phase 2
def register_extension_mode(mode_name: str, interface_factory):
    """
    Phase 2: Register additional interface modes.

    Args:
        mode_name: Name of the mode to register
        interface_factory: Factory function that returns gr.Blocks
    """
    # Placeholder for Phase 2 extension registration
    pass
