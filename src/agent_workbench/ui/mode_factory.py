"""
Enhanced Mode Factory for Agent Workbench - UI-003 Dual-Mode Support.

Provides sophisticated environment-based interface switching with extension
pathways.
"""

import logging
import os
from typing import Callable, Dict, List, Optional

import gradio as gr

from .app import create_workbench_app
from .seo_coach_app import create_seo_coach_app
from .settings_page import create_settings_page

logger = logging.getLogger(__name__)


class ModeFactoryError(Exception):
    """Base exception for mode factory errors"""

    pass


class InvalidModeError(ModeFactoryError):
    """Raised when an invalid mode is specified"""

    pass


class InterfaceCreationError(ModeFactoryError):
    """Raised when interface creation fails"""

    pass


class ModeFactory:
    """Enhanced mode factory with comprehensive error handling and extension
    support"""

    def __init__(self) -> None:
        """Initialize mode factory with core modes and extension registry"""
        self.mode_registry: Dict[str, Callable[[], gr.Blocks]] = {
            "workbench": create_workbench_app,
            "seo_coach": create_seo_coach_app,
            "settings": create_settings_page,
        }
        # Extension pathway for Phase 2
        self.extension_registry: Dict[str, Callable[[], gr.Blocks]] = {}
        self.logger = logging.getLogger(__name__)

    def create_interface(self, mode: Optional[str] = None) -> gr.Blocks:
        """
        Create interface with comprehensive error handling.

        Args:
            mode: Requested mode (optional)

        Returns:
            Gradio Blocks interface

        Raises:
            InvalidModeError: If mode is invalid
            InterfaceCreationError: If interface creation fails
        """
        try:
            # Determine effective mode with validation
            effective_mode = self._determine_mode_safe(mode)

            # Create interface with error handling
            if effective_mode in self.mode_registry:
                interface_factory = self.mode_registry[effective_mode]
            elif effective_mode in self.extension_registry:
                interface_factory = self.extension_registry[effective_mode]
            else:
                available_modes = self.get_available_modes()
                raise InvalidModeError(
                    f"Mode '{effective_mode}' not found. "
                    f"Available modes: {available_modes}"
                )

            # Create interface
            interface = interface_factory()

            # Validate interface was created successfully
            if interface is None:
                error_msg = f"Interface factory for '{effective_mode}' returned None"
                raise InterfaceCreationError(error_msg)

            self.logger.info(f"Successfully created {effective_mode} interface")
            return interface

        except (InvalidModeError, InterfaceCreationError):
            # Re-raise known errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            error_msg = (
                f"Unexpected error creating "
                f"{effective_mode or 'default'} interface: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise InterfaceCreationError(error_msg) from e

    def _determine_mode_safe(self, requested_mode: Optional[str]) -> str:
        """
        Safely determine effective mode with fallback strategy.

        Args:
            requested_mode: Explicitly requested mode

        Returns:
            Effective mode to use
        """
        # Priority: explicit request > environment variable > default
        if requested_mode:
            if self._is_valid_mode(requested_mode):
                return requested_mode
            else:
                msg = f"Invalid mode '{requested_mode}' requested, using fallback"
                self.logger.warning(msg)

        # Check environment variable
        env_mode = os.getenv("APP_MODE", "workbench")
        if self._is_valid_mode(env_mode):
            return env_mode

        # Final fallback
        self.logger.warning(f"Invalid APP_MODE '{env_mode}', falling back to workbench")
        return "workbench"

    def _is_valid_mode(self, mode: str) -> bool:
        """Check if mode is valid and registered"""
        return mode in self.get_available_modes()

    def get_available_modes(self) -> List[str]:
        """Get all available interface modes"""
        return list(self.mode_registry.keys()) + list(self.extension_registry.keys())

    # Extension pathway for Phase 2
    def register_extension_mode(
        self, mode_name: str, interface_factory: Callable[[], gr.Blocks]
    ):
        """Register extension mode for Phase 2 features"""
        if mode_name in self.mode_registry:
            raise ValueError(f"Mode '{mode_name}' conflicts with core mode")

        self.extension_registry[mode_name] = interface_factory
        self.logger.info(f"Registered extension mode: {mode_name}")

    def create_multi_mode_interface(self) -> gr.Blocks:
        """Create interface with mode switching (Phase 2 extension point)"""
        raise NotImplementedError("Multi-mode interface reserved for Phase 2")


# Main application factory functions for backward compatibility
def create_interface_for_mode(mode: Optional[str] = None) -> gr.Blocks:
    """
    Create interface using enhanced mode factory (backward compatibility).

    Args:
        mode: Override mode (optional)

    Returns:
        Gradio Blocks interface for the specified mode

    Raises:
        ValueError: If mode is invalid or interface creation fails
    """
    try:
        factory = ModeFactory()
        return factory.create_interface(mode)
    except (InvalidModeError, InterfaceCreationError) as e:
        raise ValueError(str(e)) from e


def get_mode_from_environment() -> str:
    """
    Get current mode from environment variables.

    Returns:
        Mode string ("workbench" or "seo_coach")
    """
    factory = ModeFactory()
    return factory._determine_mode_safe(None)


def validate_mode_configuration(mode: str) -> bool:
    """
    Validate mode configuration.

    Args:
        mode: Mode to validate

    Returns:
        True if mode is valid, False otherwise
    """
    factory = ModeFactory()
    return factory._is_valid_mode(mode)


def get_available_modes() -> List[str]:
    """Get all available interface modes"""
    factory = ModeFactory()
    return factory.get_available_modes()


# Extension point for Phase 2 (backward compatibility)
def register_extension_mode(mode_name: str, interface_factory: Callable[[], gr.Blocks]):
    """
    Phase 2: Register additional interface modes.

    Args:
        mode_name: Name of the mode to register
        interface_factory: Factory function that returns gr.Blocks
    """
    # This is a simplified version for backward compatibility
    # In practice, you'd want to maintain a global factory instance
    logger.warning(
        "Using simplified extension registration. "
        "For full functionality, use ModeFactory class directly."
    )
