"""
Mode factory functionality tests for UI-003 dual-mode support.

Tests mode switching, factory logic, and error handling.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from agent_workbench.ui.mode_factory import (
    InterfaceCreationError,
    InvalidModeError,
    ModeFactory,
    create_interface_for_mode,
    get_available_modes,
    get_mode_from_environment,
    validate_mode_configuration,
)


# Mock the actual interface creation functions at module level
def create_mock_workbench_interface():
    mock = MagicMock()
    mock.title = "Agent Workbench"
    return mock


def create_mock_seo_interface():
    mock = MagicMock()
    mock.title = "SEO Coach"
    return mock


class TestModeFactory:
    """Test core mode factory functionality"""

    def test_mode_factory_initialization(self):
        """Test mode factory initializes with correct registry"""
        factory = ModeFactory()

        # Should have core modes registered
        assert "workbench" in factory.mode_registry
        assert "seo_coach" in factory.mode_registry

        # Extension registry should be empty initially
        assert len(factory.extension_registry) == 0

        # Should have expected available modes
        available = factory.get_available_modes()
        assert "workbench" in available
        assert "seo_coach" in available

    def test_mode_determination_logic(self):
        """Test mode determination with various inputs"""
        factory = ModeFactory()

        # Test explicit mode override
        assert factory._determine_mode_safe("workbench") == "workbench"
        assert factory._determine_mode_safe("seo_coach") == "seo_coach"

        # Test invalid mode fallback
        assert factory._determine_mode_safe("invalid") == "workbench"

        # Test environment variable handling
        with patch.dict("os.environ", {"APP_MODE": "seo_coach"}):
            assert factory._determine_mode_safe(None) == "seo_coach"

        # Test invalid environment fallback
        with patch.dict("os.environ", {"APP_MODE": "invalid"}):
            assert factory._determine_mode_safe(None) == "workbench"

    def test_interface_creation_success(self):
        """Test successful interface creation"""
        with patch(
            "agent_workbench.ui.mode_factory.create_workbench_app"
        ) as mock_workbench:
            mock_interface = MagicMock()
            mock_workbench.return_value = mock_interface

            factory = ModeFactory()
            result = factory.create_interface("workbench")
            assert result == mock_interface
            mock_workbench.assert_called_once()

    def test_interface_creation_invalid_mode(self):
        """Test interface creation with invalid mode"""
        with patch(
            "agent_workbench.ui.mode_factory.create_workbench_app"
        ) as mock_workbench:
            # Mock to raise error for invalid mode
            mock_workbench.side_effect = Exception("Invalid mode")

            factory = ModeFactory()

            with pytest.raises(InterfaceCreationError) as exc_info:
                factory.create_interface("completely_invalid_mode_that_doesnt_exist")

            assert "Unexpected error creating" in str(exc_info.value)

    def test_interface_creation_factory_returns_none(self):
        """Test interface creation when factory returns None"""
        with patch(
            "agent_workbench.ui.mode_factory.create_workbench_app"
        ) as mock_workbench:
            mock_workbench.return_value = None

            factory = ModeFactory()
            with pytest.raises(InterfaceCreationError) as exc_info:
                factory.create_interface("workbench")

            assert "returned None" in str(exc_info.value)

    def test_interface_creation_factory_exception(self):
        """Test interface creation when factory raises exception"""
        with patch(
            "agent_workbench.ui.mode_factory.create_workbench_app"
        ) as mock_workbench:
            mock_workbench.side_effect = Exception("Factory error")

            factory = ModeFactory()
            with pytest.raises(InterfaceCreationError) as exc_info:
                factory.create_interface("workbench")

            assert "Unexpected error creating" in str(exc_info.value)

    def test_extension_mode_registration(self):
        """Test Phase 2 extension mode registration"""
        factory = ModeFactory()

        # Create mock extension factory
        mock_extension = MagicMock()

        # Register extension mode
        factory.register_extension_mode("test_extension", mock_extension)

        # Should be in extension registry
        assert "test_extension" in factory.extension_registry
        assert factory.extension_registry["test_extension"] == mock_extension

        # Should be in available modes
        assert "test_extension" in factory.get_available_modes()

    def test_extension_mode_conflict(self):
        """Test extension mode conflicts with core mode"""
        factory = ModeFactory()

        mock_extension = MagicMock()

        # Should raise error when trying to register conflicting mode
        with pytest.raises(ValueError) as exc_info:
            factory.register_extension_mode("workbench", mock_extension)

        assert "conflicts with core mode" in str(exc_info.value)

    def test_extension_mode_interface_creation(self):
        """Test interface creation with extension mode"""
        factory = ModeFactory()

        # Register extension mode
        mock_extension = MagicMock()
        mock_interface = MagicMock()
        mock_extension.return_value = mock_interface

        factory.register_extension_mode("test_extension", mock_extension)

        # Should create interface using extension factory
        result = factory.create_interface("test_extension")
        assert result == mock_interface
        mock_extension.assert_called_once()

    def test_multi_mode_interface_not_implemented(self):
        """Test multi-mode interface raises NotImplementedError (Phase 2)"""
        factory = ModeFactory()

        with pytest.raises(NotImplementedError) as exc_info:
            factory.create_multi_mode_interface()

        assert "Multi-mode interface reserved for Phase 2" in str(exc_info.value)


class TestModeFactoryHelperFunctions:
    """Test helper functions for backward compatibility"""

    def test_create_interface_for_mode_success(self):
        """Test create_interface_for_mode helper function"""
        with patch("agent_workbench.ui.mode_factory.ModeFactory") as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_interface = MagicMock()
            mock_factory.create_interface.return_value = mock_interface

            result = create_interface_for_mode("workbench")

            assert result == mock_interface
            mock_factory.create_interface.assert_called_once_with("workbench")

    def test_create_interface_for_mode_error_handling(self):
        """Test create_interface_for_mode error handling"""
        with patch("agent_workbench.ui.mode_factory.ModeFactory") as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_interface.side_effect = InvalidModeError("Test error")

            with pytest.raises(ValueError) as exc_info:
                create_interface_for_mode("invalid")

            assert "Test error" in str(exc_info.value)

    def test_get_mode_from_environment(self):
        """Test get_mode_from_environment helper function"""
        with patch("agent_workbench.ui.mode_factory.ModeFactory") as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory._determine_mode_safe.return_value = "seo_coach"

            result = get_mode_from_environment()

            assert result == "seo_coach"
            mock_factory._determine_mode_safe.assert_called_once_with(None)

    def test_validate_mode_configuration(self):
        """Test validate_mode_configuration helper function"""
        with patch("agent_workbench.ui.mode_factory.ModeFactory") as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory._is_valid_mode.return_value = True

            result = validate_mode_configuration("workbench")

            assert result is True
            mock_factory._is_valid_mode.assert_called_once_with("workbench")

    def test_get_available_modes_helper(self):
        """Test get_available_modes helper function"""
        with patch("agent_workbench.ui.mode_factory.ModeFactory") as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.get_available_modes.return_value = ["workbench", "seo_coach"]

            result = get_available_modes()

            assert result == ["workbench", "seo_coach"]
            mock_factory.get_available_modes.assert_called_once()


class TestEnvironmentIntegration:
    """Test environment variable integration"""

    def test_app_mode_environment_variable(self):
        """Test APP_MODE environment variable handling"""
        factory = ModeFactory()

        # Test workbench mode
        with patch.dict("os.environ", {"APP_MODE": "workbench"}):
            mode = factory._determine_mode_safe(None)
            assert mode == "workbench"

        # Test seo_coach mode
        with patch.dict("os.environ", {"APP_MODE": "seo_coach"}):
            mode = factory._determine_mode_safe(None)
            assert mode == "seo_coach"

        # Test invalid mode fallback
        with patch.dict("os.environ", {"APP_MODE": "invalid"}):
            mode = factory._determine_mode_safe(None)
            assert mode == "workbench"  # Should fallback to default

    def test_no_environment_variable(self):
        """Test behavior when APP_MODE is not set"""
        factory = ModeFactory()

        with patch.dict("os.environ", {}, clear=True):
            # Remove APP_MODE if it exists
            if "APP_MODE" in os.environ:
                del os.environ["APP_MODE"]

            mode = factory._determine_mode_safe(None)
            assert mode == "workbench"  # Should use default

    def test_explicit_mode_overrides_environment(self):
        """Test explicit mode parameter overrides environment"""
        factory = ModeFactory()

        with patch.dict("os.environ", {"APP_MODE": "workbench"}):
            # Explicit mode should override environment
            mode = factory._determine_mode_safe("seo_coach")
            assert mode == "seo_coach"

            # Invalid explicit mode should fall back to environment
            mode = factory._determine_mode_safe("invalid")
            assert mode == "workbench"  # Falls back to environment


class TestLogging:
    """Test logging functionality"""

    def test_successful_interface_creation_logging(self):
        """Test logging on successful interface creation"""
        factory = ModeFactory()

        with patch(
            "agent_workbench.ui.mode_factory.create_workbench_app"
        ) as mock_workbench:
            mock_interface = MagicMock()
            mock_workbench.return_value = mock_interface

            with patch.object(factory, "logger") as mock_logger:
                factory.create_interface("workbench")
                mock_logger.info.assert_called_with(
                    "Successfully created workbench interface"
                )

    def test_invalid_mode_warning_logging(self):
        """Test warning logging for invalid modes"""
        factory = ModeFactory()

        with patch.object(factory, "logger") as mock_logger:
            factory._determine_mode_safe("invalid_mode")
            mock_logger.warning.assert_called()

    def test_extension_registration_logging(self):
        """Test logging on extension registration"""
        factory = ModeFactory()

        with patch.object(factory, "logger") as mock_logger:
            mock_extension = MagicMock()
            factory.register_extension_mode("test_extension", mock_extension)
            mock_logger.info.assert_called_with(
                "Registered extension mode: test_extension"
            )
