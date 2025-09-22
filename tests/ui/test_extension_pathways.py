"""
Phase 2 extension point validation tests for UI-003.

Tests extension pathways for document processing, multi-mode, and MCP tools.
"""

from unittest.mock import MagicMock, patch

import pytest

from agent_workbench.ui.mode_factory import ModeFactory


class TestExtensionRegistry:
    """Test extension registry functionality for Phase 2"""

    def test_extension_registry_initialization(self):
        """Test extension registry starts empty"""
        factory = ModeFactory()

        assert len(factory.extension_registry) == 0
        assert isinstance(factory.extension_registry, dict)

    def test_extension_mode_registration(self):
        """Test basic extension mode registration"""
        factory = ModeFactory()

        mock_extension = MagicMock()
        factory.register_extension_mode("test_extension", mock_extension)

        assert "test_extension" in factory.extension_registry
        assert factory.extension_registry["test_extension"] == mock_extension

    def test_multiple_extension_registration(self):
        """Test registering multiple extension modes"""
        factory = ModeFactory()

        mock_ext1 = MagicMock()
        mock_ext2 = MagicMock()
        mock_ext3 = MagicMock()

        factory.register_extension_mode("extension1", mock_ext1)
        factory.register_extension_mode("extension2", mock_ext2)
        factory.register_extension_mode("extension3", mock_ext3)

        assert len(factory.extension_registry) == 3
        assert "extension1" in factory.extension_registry
        assert "extension2" in factory.extension_registry
        assert "extension3" in factory.extension_registry

    def test_extension_mode_conflict_prevention(self):
        """Test prevention of conflicts with core modes"""
        factory = ModeFactory()

        mock_extension = MagicMock()

        # Should raise error for core mode conflicts
        with pytest.raises(ValueError) as exc_info:
            factory.register_extension_mode("workbench", mock_extension)

        assert "conflicts with core mode" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            factory.register_extension_mode("seo_coach", mock_extension)

        assert "conflicts with core mode" in str(exc_info.value)

    def test_extension_mode_available_modes_integration(self):
        """Test extension modes appear in available modes"""
        factory = ModeFactory()

        # Initial state
        initial_modes = factory.get_available_modes()
        assert "workbench" in initial_modes
        assert "seo_coach" in initial_modes

        # Add extension
        mock_extension = MagicMock()
        factory.register_extension_mode("document_processor", mock_extension)

        # Should appear in available modes
        updated_modes = factory.get_available_modes()
        assert "document_processor" in updated_modes
        assert len(updated_modes) == len(initial_modes) + 1


class TestDocumentProcessingExtension:
    """Test document processing extension pathway (Phase 2)"""

    def test_document_extension_registration(self):
        """Test document processing extension registration"""
        factory = ModeFactory()

        # Mock document processing interface factory
        def create_document_interface():
            mock_interface = MagicMock()
            mock_interface.title = "Document Processor"
            return mock_interface

        # Register document processing extension
        factory.register_extension_mode("document_processor", create_document_interface)

        # Should be registered and callable
        assert "document_processor" in factory.extension_registry
        interface = factory.create_interface("document_processor")
        assert interface.title == "Document Processor"

    def test_document_extension_isolation(self):
        """Test document extension doesn't interfere with core modes"""
        with patch("agent_workbench.ui.mode_factory.create_workbench_app") as mock_wb:
            mock_wb.return_value = MagicMock()

            factory = ModeFactory()

            # Register document extension
            mock_doc_factory = MagicMock()
            factory.register_extension_mode("document_processor", mock_doc_factory)

            # Core modes should still work
            workbench = factory.create_interface("workbench")
            assert workbench is not None
            mock_wb.assert_called_once()

    def test_document_extension_feature_placeholder(self):
        """Test document extension feature placeholders"""
        # This tests the interface that would be implemented in Phase 2

        class DocumentExtension:
            @staticmethod
            def create_document_interface():
                """Phase 2: Document processing interface"""
                raise NotImplementedError("Document processing - Phase 2")

            @staticmethod
            def register_document_mode(factory: ModeFactory):
                """Phase 2: Register document processing mode"""
                factory.register_extension_mode(
                    "document_processor", DocumentExtension.create_document_interface
                )

        factory = ModeFactory()
        DocumentExtension.register_document_mode(factory)

        # Should be registered but not implemented
        assert "document_processor" in factory.extension_registry

        from agent_workbench.ui.mode_factory import InterfaceCreationError

        with pytest.raises(InterfaceCreationError) as exc_info:
            factory.create_interface("document_processor")

        assert "Document processing - Phase 2" in str(exc_info.value)


class TestMCPToolExtension:
    """Test MCP tool integration extension pathway (Phase 2)"""

    def test_mcp_tool_extension_registration(self):
        """Test MCP tool extension registration"""
        factory = ModeFactory()

        # Mock MCP tool enhancement
        def create_enhanced_workbench():
            mock_interface = MagicMock()
            mock_interface.title = "Workbench with MCP Tools"
            mock_interface.tools_enabled = True
            return mock_interface

        # Register MCP-enhanced mode
        factory.register_extension_mode("workbench_plus", create_enhanced_workbench)

        # Should create enhanced interface
        enhanced = factory.create_interface("workbench_plus")
        assert enhanced.title == "Workbench with MCP Tools"
        assert enhanced.tools_enabled is True

    def test_mcp_tool_extension_feature_placeholder(self):
        """Test MCP tool extension feature placeholders"""

        class MCPToolExtension:
            @staticmethod
            def create_tool_management_interface():
                """Phase 2: Tool management interface"""
                raise NotImplementedError("MCP tool management - Phase 2")

            @staticmethod
            def enhance_workbench_with_tools(base_interface):
                """Phase 2: Enhance workbench with tool capabilities"""
                raise NotImplementedError("Workbench tool enhancement - Phase 2")

            @staticmethod
            def register_tool_modes(factory: ModeFactory):
                """Phase 2: Register tool-enhanced modes"""
                factory.register_extension_mode(
                    "tool_manager", MCPToolExtension.create_tool_management_interface
                )
                factory.register_extension_mode(
                    "workbench_plus",
                    lambda: MCPToolExtension.enhance_workbench_with_tools(None),
                )

        factory = ModeFactory()
        MCPToolExtension.register_tool_modes(factory)

        # Should be registered but not implemented
        assert "tool_manager" in factory.extension_registry
        assert "workbench_plus" in factory.extension_registry

        from agent_workbench.ui.mode_factory import InterfaceCreationError

        with pytest.raises(InterfaceCreationError):
            factory.create_interface("tool_manager")


class TestMultiModeExtension:
    """Test multi-mode interface extension pathway (Phase 2)"""

    def test_multi_mode_interface_not_implemented(self):
        """Test multi-mode interface is reserved for Phase 2"""
        factory = ModeFactory()

        with pytest.raises(NotImplementedError) as exc_info:
            factory.create_multi_mode_interface()

        assert "Multi-mode interface reserved for Phase 2" in str(exc_info.value)

    def test_multi_mode_extension_feature_placeholder(self):
        """Test multi-mode extension feature placeholder"""

        class MultiModeExtension:
            @staticmethod
            def create_tabbed_interface():
                """Phase 2: Tabbed interface with mode switching"""
                mock_interface = MagicMock()
                mock_interface.title = "Agent Workbench - Multi Mode"
                mock_interface.tabs = ["Workbench", "SEO Coach", "Documents", "Tools"]
                return mock_interface

            @staticmethod
            def register_multi_mode(factory: ModeFactory):
                """Phase 2: Register multi-mode interface"""
                factory.register_extension_mode(
                    "multi_mode", MultiModeExtension.create_tabbed_interface
                )

        factory = ModeFactory()
        MultiModeExtension.register_multi_mode(factory)

        # Should be able to create multi-mode interface via extension
        multi_interface = factory.create_interface("multi_mode")
        assert multi_interface.title == "Agent Workbench - Multi Mode"
        assert "Workbench" in multi_interface.tabs


class TestExtensionIntegration:
    """Test integration between extensions and core system"""

    def test_extension_mode_determination(self):
        """Test mode determination works with extensions"""
        factory = ModeFactory()

        # Register extension
        mock_extension = MagicMock()
        factory.register_extension_mode("test_extension", mock_extension)

        # Should determine extension mode correctly
        mode = factory._determine_mode_safe("test_extension")
        assert mode == "test_extension"

    def test_extension_environment_variable_support(self):
        """Test extension modes work with environment variables"""
        factory = ModeFactory()

        # Register extension
        mock_extension = MagicMock()
        mock_extension.return_value = MagicMock()
        factory.register_extension_mode("test_extension", mock_extension)

        # Test with environment variable
        with patch.dict("os.environ", {"APP_MODE": "test_extension"}):
            mode = factory._determine_mode_safe(None)
            assert mode == "test_extension"

            # Should be able to create interface
            interface = factory.create_interface()
            assert interface is not None
            mock_extension.assert_called_once()

    def test_extension_mode_validation(self):
        """Test extension modes are properly validated"""
        factory = ModeFactory()

        # Register extension
        mock_extension = MagicMock()
        factory.register_extension_mode("test_extension", mock_extension)

        # Should validate extension modes
        assert factory._is_valid_mode("test_extension") is True
        assert factory._is_valid_mode("non_existent_extension") is False

    def test_extension_error_handling(self):
        """Test error handling in extension modes"""
        factory = ModeFactory()

        # Register extension that raises error
        def failing_extension():
            raise Exception("Extension failed")

        factory.register_extension_mode("failing_extension", failing_extension)

        # Should handle extension errors gracefully
        from agent_workbench.ui.mode_factory import InterfaceCreationError

        with pytest.raises(InterfaceCreationError) as exc_info:
            factory.create_interface("failing_extension")

        assert "Unexpected error creating" in str(exc_info.value)

    def test_extension_logging(self):
        """Test logging for extension operations"""
        factory = ModeFactory()

        with patch.object(factory, "logger") as mock_logger:
            mock_extension = MagicMock()
            factory.register_extension_mode("test_extension", mock_extension)

            # Should log extension registration
            mock_logger.info.assert_called_with(
                "Registered extension mode: test_extension"
            )


class TestPhase2Readiness:
    """Test Phase 2 readiness and compatibility"""

    def test_extension_registry_persistence(self):
        """Test extension registry persists across operations"""
        factory = ModeFactory()

        # Register multiple extensions
        mock_ext1 = MagicMock()
        mock_ext2 = MagicMock()

        factory.register_extension_mode("extension1", mock_ext1)
        factory.register_extension_mode("extension2", mock_ext2)

        # Should persist after creating core interfaces
        with patch("agent_workbench.ui.mode_factory.create_workbench_app"):
            factory.create_interface("workbench")

        # Extensions should still be registered
        assert "extension1" in factory.extension_registry
        assert "extension2" in factory.extension_registry

    def test_backward_compatibility_with_extensions(self):
        """Test backward compatibility when extensions are added"""
        from agent_workbench.ui.mode_factory import (
            create_interface_for_mode,
            get_available_modes,
        )

        # Should work without extensions
        modes_without_ext = get_available_modes()
        assert "workbench" in modes_without_ext
        assert "seo_coach" in modes_without_ext

        # Register extension through factory
        factory = ModeFactory()
        mock_extension = MagicMock()
        factory.register_extension_mode("test_extension", mock_extension)

        # Core functions should still work
        with patch("agent_workbench.ui.mode_factory.create_workbench_app") as mock_wb:
            mock_wb.return_value = MagicMock()
            interface = create_interface_for_mode("workbench")
            assert interface is not None

    def test_extension_namespace_isolation(self):
        """Test extension namespaces don't conflict"""
        factory1 = ModeFactory()
        factory2 = ModeFactory()

        # Different factories should have isolated registries
        mock_ext1 = MagicMock()
        mock_ext2 = MagicMock()

        factory1.register_extension_mode("shared_name", mock_ext1)
        factory2.register_extension_mode("shared_name", mock_ext2)

        # Should have different extensions
        assert factory1.extension_registry["shared_name"] == mock_ext1
        assert factory2.extension_registry["shared_name"] == mock_ext2
        assert (
            factory1.extension_registry["shared_name"]
            != factory2.extension_registry["shared_name"]
        )

    def test_extension_api_stability(self):
        """Test extension API is stable for Phase 2"""
        factory = ModeFactory()

        # Core extension methods should be available
        assert hasattr(factory, "register_extension_mode")
        assert hasattr(factory, "extension_registry")
        assert hasattr(factory, "create_multi_mode_interface")

        # Extension methods should have correct signatures
        import inspect

        register_sig = inspect.signature(factory.register_extension_mode)
        assert len(register_sig.parameters) == 2
        assert "mode_name" in register_sig.parameters
        assert "interface_factory" in register_sig.parameters

        multi_mode_sig = inspect.signature(factory.create_multi_mode_interface)
        assert len(multi_mode_sig.parameters) == 0  # No parameters for Phase 2
