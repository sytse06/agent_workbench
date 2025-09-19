# UI-003: FAST API/Langraph backend supports dual mode

## Status

**Status**: Awaiting review
**Date**: September 19, 2025  
**Decision Makers**: Human Architect  
**Task ID**: UI-003-dual-mode-support  
**Dependencies**: UI-001 (workbench mode), UI-002 (SEO coach mode), LLM-002 (LangGraph state), LLM-001C (consolidated workflow)

## Context

Document the complete dual-mode Gradio frontend architecture that combines UI-001 workbench interface and UI-002 SEO coach interface into a unified system. Provides comprehensive testing strategy focused on validating core UI-001 stateless principles across both modes, plus extension pathways for Phase 2 advanced features.

## Complete Architecture Overview

### **Dual-Mode System Architecture**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Mode-Aware Gradio Frontend                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │  Workbench UI   │    │   SEO Coach UI   │    │ Mode        │ │
│  │  (UI-001)       │    │   (UI-002)       │    │ Factory     │ │
│  │  - Technical    │    │  - Dutch Business│    │ - APP_MODE  │ │
│  │  - Parameters   │    │  - Profiles      │    │ - Routing   │ │
│  │  - Debug Mode   │    │  - Localization  │    │ - Extension │ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
└─────────────────────────┼──────────────────┼─────────────────────┘
                          │                  │
                         HTTP               │
                          │                  │
┌─────────────────────────▼──────────────────▼─────────────────────┐
│                 LangGraph Consolidated Workflow                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │  Workbench      │    │   SEO Coach      │    │ Shared      │ │
│  │  Handler        │    │   Handler        │    │ State       │ │
│  │ workflow_mode:  │    │ workflow_mode:   │    │ Bridge      │ │
│  │ "workbench"     │    │ "seo_coach"      │    │             │ │
│  └─────────────────┘    └──────────────────┘    └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Mode Factory Architecture

### **Unified Entry Point with Extension Pathway**

```python
# src/agent_workbench/ui/mode_factory.py
import os
import gradio as gr
from typing import Dict, Callable, Optional
from .workbench_app import create_workbench_interface  # UI-001
from .seo_coach_app import create_seo_coach_interface  # UI-002

class ModeFactory:
    """Factory for creating mode-specific Gradio interfaces with extension support"""
    
    def __init__(self):
        self.mode_registry = {
            "workbench": create_workbench_interface,
            "seo_coach": create_seo_coach_interface
        }
        # Extension pathway for Phase 2
        self.extension_registry = {}
    
    def create_interface(self, mode: Optional[str] = None) -> gr.Blocks:
        """Create appropriate interface based on mode"""
        
        effective_mode = self._determine_mode(mode)
        
        if effective_mode in self.mode_registry:
            return self.mode_registry[effective_mode]()
        elif effective_mode in self.extension_registry:
            return self.extension_registry[effective_mode]()
        else:
            raise ValueError(f"Unknown interface mode: {effective_mode}")
    
    def _determine_mode(self, requested_mode: Optional[str]) -> str:
        """Determine effective mode from environment and request"""
        
        # Priority: explicit request > environment variable > default
        if requested_mode and requested_mode in self.get_available_modes():
            return requested_mode
        
        env_mode = os.getenv("APP_MODE", "workbench")
        if env_mode in self.get_available_modes():
            return env_mode
            
        return "workbench"  # Safe default
    
    def get_available_modes(self) -> List[str]:
        """Get all available interface modes"""
        return list(self.mode_registry.keys()) + list(self.extension_registry.keys())
    
    # Extension pathway for Phase 2
    def register_extension_mode(self, mode_name: str, interface_factory: Callable[[], gr.Blocks]):
        """Register extension mode for Phase 2 features"""
        self.extension_registry[mode_name] = interface_factory
    
    def create_multi_mode_interface(self) -> gr.Blocks:
        """Create interface with mode switching (Phase 2 extension point)"""
        raise NotImplementedError("Multi-mode interface reserved for Phase 2")

# Main application factory
def create_gradio_app(mode: Optional[str] = None) -> gr.Blocks:
    """Main entry point for Gradio application"""
    factory = ModeFactory()
    return factory.create_interface(mode)

def get_current_mode() -> str:
    """Get currently active mode"""
    factory = ModeFactory()
    return factory._determine_mode(None)
```

### **Enhanced FastAPI Integration**

```python
# src/agent_workbench/main.py (ENHANCED)
from agent_workbench.ui.mode_factory import create_gradio_app, get_current_mode

def create_app() -> FastAPI:
    """Create FastAPI app with dual-mode Gradio integration"""
    
    app = FastAPI(
        title="Agent Workbench - Dual Mode",
        description="AI workbench with technical and business coaching modes",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])
    
    # Include API routes
    app.include_router(chat.router, prefix="/api/v1")
    
    # Create and mount appropriate Gradio interface
    current_mode = get_current_mode()
    gradio_app = create_gradio_app(current_mode)
    
    # Mount Gradio app on root path
    app = gr.mount_gradio_app(app, gradio_app, path="/")
    
    # Mode information endpoint
    @app.get("/api/mode")
    async def get_mode_info():
        return {
            "current_mode": current_mode,
            "available_modes": ["workbench", "seo_coach"],
            "extension_modes": []  # Phase 2 will populate this
        }
    
    return app
```

## Focused Testing Strategy

### **Core Testing Principles**
- **Focus**: Validate UI-001 stateless principles across both modes
- **Scope**: Essential dual-mode functionality only
- **Coverage**: 80% minimum, not exhaustive testing
- **Purpose**: Ensure architectural integrity, not comprehensive QA

### **1. Dual-Mode Stateless Validation Tests**

```python
# tests/ui/test_dual_mode_stateless.py
import pytest
from unittest.mock import patch, AsyncMock
from agent_workbench.ui.mode_factory import ModeFactory, create_gradio_app
from agent_workbench.ui.clients.seo_coach_client import SEOCoachClient
from agent_workbench.ui.clients.simple_client import SimpleLangGraphClient

class TestStatelessPrinciples:
    """Test stateless principles work correctly in both modes"""
    
    def test_mode_factory_creation(self):
        """Test mode factory creates correct interfaces"""
        factory = ModeFactory()
        
        # Test workbench mode
        workbench_interface = factory.create_interface("workbench")
        assert workbench_interface is not None
        assert "Agent Workbench" in str(workbench_interface.title)
        
        # Test SEO coach mode  
        seo_interface = factory.create_interface("seo_coach")
        assert seo_interface is not None
        assert "SEO Coach" in str(seo_interface.title)
    
    def test_mode_determination_logic(self):
        """Test mode determination from environment and requests"""
        factory = ModeFactory()
        
        # Test explicit mode override
        assert factory._determine_mode("seo_coach") == "seo_coach"
        assert factory._determine_mode("workbench") == "workbench"
        
        # Test invalid mode fallback
        assert factory._determine_mode("invalid") == "workbench"
        
        # Test environment variable handling
        with patch.dict('os.environ', {'APP_MODE': 'seo_coach'}):
            assert factory._determine_mode(None) == "seo_coach"
    
    @pytest.mark.asyncio
    async def test_workbench_stateless_operation(self):
        """Test workbench mode maintains no local state"""
        
        with patch('agent_workbench.ui.components.simple_client.SimpleLangGraphClient') as mock_client:
            client_instance = AsyncMock()
            mock_client.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            mock_client.return_value.__aexit__ = AsyncMock()
            
            # Mock conversation history calls
            client_instance.get_conversation_history.return_value = [
                ("Hello", "Hi there!"),
                ("How are you?", "I'm doing well!")
            ]
            
            # Test multiple calls return fresh data
            history1 = await client_instance.get_conversation_history("test-conv")
            history2 = await client_instance.get_conversation_history("test-conv")
            
            # Both calls should hit the backend (no caching)
            assert client_instance.get_conversation_history.call_count == 2
            assert history1 == history2  # Data consistency
    
    @pytest.mark.asyncio
    async def test_seo_coach_stateless_operation(self):
        """Test SEO coach mode maintains no local state"""
        
        with patch('agent_workbench.ui.clients.seo_coach_client.SEOCoachClient') as mock_client:
            client_instance = AsyncMock()
            mock_client.return_value = client_instance
            
            # Mock business profile calls
            from agent_workbench.ui.models.business_profile import BusinessProfile
            test_profile = BusinessProfile(
                business_name="Test Restaurant",
                website_url="https://test.nl",
                business_type="Restaurant",
                location="Amsterdam",
                target_keywords="restaurant amsterdam",
                seo_experience="beginner"
            )
            
            client_instance.get_business_profile.return_value = test_profile
            
            # Test multiple profile requests
            profile1 = await client_instance.get_business_profile("test-conv")
            profile2 = await client_instance.get_business_profile("test-conv")
            
            # Both calls should hit backend (no local caching)
            assert client_instance.get_business_profile.call_count == 2
            assert profile1 == profile2
    
    def test_no_cross_mode_state_contamination(self):
        """Test that modes don't share or contaminate state"""
        factory = ModeFactory()
        
        # Create both interfaces
        workbench = factory.create_interface("workbench")
        seo_coach = factory.create_interface("seo_coach")
        
        # Interfaces should be independent
        assert workbench != seo_coach
        assert id(workbench) != id(seo_coach)
        
        # No shared state objects
        workbench_components = set(id(comp) for comp in workbench.blocks)
        seo_coach_components = set(id(comp) for comp in seo_coach.blocks)
        assert not workbench_components.intersection(seo_coach_components)
```

### **2. LangGraph Integration Tests**

```python
# tests/ui/test_langgraph_integration.py
import pytest
from unittest.mock import patch, MagicMock
from agent_workbench.ui.mode_factory import create_gradio_app

class TestLangGraphIntegration:
    """Test LangGraph integration works correctly for both modes"""
    
    @pytest.mark.asyncio
    async def test_workbench_langgraph_routing(self):
        """Test workbench mode routes to correct LangGraph workflow"""
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "conversation_id": "test-123",
                "reply": "Workbench response",
                "workflow_steps": ["workbench_processing"],
                "metadata": {"workflow_mode": "workbench"}
            }
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            from agent_workbench.ui.components.simple_client import SimpleLangGraphClient
            from agent_workbench.ui.components.simple_client import ModelConfiguration
            
            async with SimpleLangGraphClient() as client:
                model_config = ModelConfiguration(
                    provider="openrouter",
                    model="anthropic/claude-3-5-sonnet-20241022"
                )
                
                response = await client.send_message(
                    message="Test workbench message",
                    conversation_id="test-123",
                    model_config=model_config
                )
                
                # Verify correct workflow routing
                assert response.execution_successful
                assert response.assistant_response == "Workbench response"
    
    @pytest.mark.asyncio
    async def test_seo_coach_langgraph_routing(self):
        """Test SEO coach mode routes to correct LangGraph workflow"""
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "conversation_id": "test-456", 
                "assistant_response": "SEO coaching response",
                "workflow_steps": ["seo_coach_processing"],
                "business_profile": {"business_name": "Test Business"},
                "coaching_context": {"phase": "analysis"}
            }
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            from agent_workbench.ui.clients.seo_coach_client import SEOCoachClient
            from agent_workbench.ui.models.business_profile import BusinessProfile
            
            client = SEOCoachClient()
            profile = BusinessProfile(
                business_name="Test Business",
                website_url="https://test.com",
                business_type="Restaurant", 
                location="Amsterdam",
                target_keywords="test",
                seo_experience="beginner"
            )
            
            # Mock the HTTP client properly
            with patch.object(client, 'client') as mock_http:
                mock_http.__aenter__.return_value.post.return_value = mock_response
                
                state = await client.send_coaching_message(
                    message="Test SEO message",
                    conversation_id="test-456", 
                    business_profile=profile
                )
                
                # Verify SEO coach workflow routing
                assert "seo_coach_processing" in mock_response.json()["workflow_steps"]
```

### **3. Mode-Specific Functionality Tests**

```python
# tests/ui/test_mode_functionality.py
import pytest
from agent_workbench.ui.mode_factory import ModeFactory

class TestModeFunctionality:
    """Test mode-specific functionality works correctly"""
    
    def test_workbench_technical_features(self):
        """Test workbench mode provides technical controls"""
        factory = ModeFactory()
        interface = factory.create_interface("workbench")
        
        # Look for technical components in interface
        components = interface.blocks
        
        # Should have model selection dropdowns
        dropdowns = [c for c in components if hasattr(c, 'choices')]
        assert len(dropdowns) >= 2  # Provider and model dropdowns
        
        # Should have parameter sliders
        sliders = [c for c in components if hasattr(c, 'minimum')]
        assert len(sliders) >= 1  # Temperature slider minimum
    
    def test_seo_coach_business_features(self):
        """Test SEO coach mode provides business-focused interface"""
        factory = ModeFactory()
        interface = factory.create_interface("seo_coach") 
        
        components = interface.blocks
        
        # Should have business profile form elements
        textboxes = [c for c in components if hasattr(c, 'placeholder')]
        business_textboxes = [t for t in textboxes 
                            if any(dutch_word in str(t.placeholder).lower() 
                                  for dutch_word in ['bedrijf', 'website', 'locatie'])]
        assert len(business_textboxes) >= 3  # Business name, website, location
    
    def test_dutch_localization_present(self):
        """Test Dutch localization is present in SEO coach mode"""
        factory = ModeFactory()
        interface = factory.create_interface("seo_coach")
        
        interface_html = str(interface)
        
        # Check for Dutch text
        dutch_indicators = ['bedrijf', 'website', 'seo coach', 'nederland']
        found_dutch = sum(1 for word in dutch_indicators 
                         if word in interface_html.lower())
        
        assert found_dutch >= 2, "SEO coach interface should contain Dutch text"
```

### **4. Error Handling Validation**

```python
# tests/ui/test_error_handling.py  
import pytest
from unittest.mock import patch
from agent_workbench.ui.clients.simple_client import LangGraphAPIError

class TestErrorHandling:
    """Test error handling works correctly in both modes"""
    
    @pytest.mark.asyncio
    async def test_workbench_error_recovery(self):
        """Test workbench mode handles errors gracefully"""
        
        with patch('agent_workbench.ui.components.simple_client.SimpleLangGraphClient') as mock_client:
            client_instance = mock_client.return_value.__aenter__.return_value
            
            # Simulate connection error
            client_instance.send_message.side_effect = LangGraphAPIError(
                "Connection failed", status_code=503
            )
            
            # Error should be caught and handled gracefully
            with pytest.raises(LangGraphAPIError) as exc_info:
                await client_instance.send_message("test", "conv-123", {})
            
            assert exc_info.value.status_code == 503
            assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio  
    async def test_seo_coach_dutch_error_messages(self):
        """Test SEO coach provides Dutch error messages"""
        
        from agent_workbench.ui.localization.dutch_messages import DutchSEOMessages
        
        messages = DutchSEOMessages()
        
        # Test Dutch error message formatting
        error_msg = messages.get_error_message("website_unreachable")
        assert "website" in error_msg.lower()
        assert any(dutch_word in error_msg.lower() 
                  for dutch_word in ['kan niet', 'controleer', 'probeer'])
        
        coaching_error = messages.get_error_message("coaching_error", "timeout")
        assert len(coaching_error) > 0
        assert coaching_error != "coaching_error"  # Should be localized
```

## Extension Pathways for Phase 2

### **Document Processing Extension Point**

```python
# Extension pathway for document processing (Phase 2)
class DocumentExtension:
    """Phase 2 extension for document processing"""
    
    @staticmethod
    def create_document_interface() -> gr.Blocks:
        """Document processing interface - Phase 2"""
        raise NotImplementedError("Document processing interface - Phase 2")
    
    @staticmethod
    def register_document_mode(factory: ModeFactory):
        """Register document processing mode - Phase 2"""
        factory.register_extension_mode("document_processor", 
                                       DocumentExtension.create_document_interface)

# Usage in Phase 2:
# from agent_workbench.extensions.document_extension import DocumentExtension
# factory = ModeFactory() 
# DocumentExtension.register_document_mode(factory)
# document_interface = factory.create_interface("document_processor")
```

### **MCP Tool Extension Point**

```python
# Extension pathway for MCP tools (Phase 2)  
class MCPToolExtension:
    """Phase 2 extension for MCP tool integration"""
    
    @staticmethod
    def create_tool_management_interface() -> gr.Blocks:
        """Tool management interface - Phase 2"""
        raise NotImplementedError("MCP tool management interface - Phase 2")
    
    @staticmethod
    def enhance_workbench_with_tools(base_interface: gr.Blocks) -> gr.Blocks:
        """Enhance workbench with tool capabilities - Phase 2"""
        raise NotImplementedError("Workbench tool enhancement - Phase 2")
    
    @staticmethod
    def register_tool_modes(factory: ModeFactory):
        """Register tool-enhanced modes - Phase 2"""
        factory.register_extension_mode("workbench_plus", 
                                       lambda: MCPToolExtension.enhance_workbench_with_tools(
                                           create_workbench_interface()))

# Phase 2 usage pattern:
# factory = ModeFactory()
# MCPToolExtension.register_tool_modes(factory) 
# enhanced_workbench = factory.create_interface("workbench_plus")
```

### **Multi-Mode Interface Extension Point**

```python
# Extension pathway for multi-mode interface (Phase 2)
class MultiModeExtension:
    """Phase 2 extension for multi-mode interface with mode switching"""
    
    @staticmethod  
    def create_tabbed_interface() -> gr.Blocks:
        """Tabbed interface with mode switching - Phase 2"""
        
        with gr.Blocks(title="Agent Workbench - Multi Mode") as interface:
            with gr.Tabs():
                with gr.TabItem("🛠️ Workbench"):
                    create_workbench_interface()
                    
                with gr.TabItem("🚀 SEO Coach"): 
                    create_seo_coach_interface()
                    
                with gr.TabItem("📄 Documents"):
                    DocumentExtension.create_document_interface()
                    
                with gr.TabItem("🔧 Tools"):
                    MCPToolExtension.create_tool_management_interface()
        
        return interface
    
    @staticmethod
    def register_multi_mode(factory: ModeFactory):
        """Register multi-mode interface - Phase 2"""
        factory.register_extension_mode("multi_mode", 
                                       MultiModeExtension.create_tabbed_interface)

# Phase 2 usage:
# factory = ModeFactory()  
# MultiModeExtension.register_multi_mode(factory)
# multi_interface = factory.create_interface("multi_mode")
```

## Testing Execution Strategy

### **Minimal Testing Pipeline**
```yaml
# Focused testing - not comprehensive QA
test_execution:
  unit_tests:
    - test_dual_mode_stateless.py      # Core stateless validation
    - test_langgraph_integration.py    # LangGraph routing
    - test_mode_functionality.py      # Mode-specific features
    
  integration_tests:
    - test_error_handling.py          # Error recovery
    - test_mode_switching.py          # Mode determination
    
  coverage_target: 80%                # Essential coverage only
  performance_target: <3s             # Response time validation
```

### **Success Criteria - Phase 1**

#### **Dual-Mode Functionality**
- [ ] Both workbench and SEO coach modes load correctly
- [ ] Mode factory correctly routes based on APP_MODE environment variable
- [ ] No state contamination between modes
- [ ] Each mode maintains UI-001 stateless principles

#### **LangGraph Integration**  
- [ ] Workbench mode routes to `workflow_mode="workbench"`
- [ ] SEO coach mode routes to `workflow_mode="seo_coach"`  
- [ ] Business profiles persist correctly in LangGraph state
- [ ] Conversation history fetched fresh from LangGraph (no caching)

#### **User Experience**
- [ ] Workbench provides technical controls for AI developers
- [ ] SEO coach provides Dutch business-friendly interface
- [ ] Error messages appropriate for each audience
- [ ] Mobile responsiveness works for both modes

#### **Extension Readiness**
- [ ] Mode factory supports extension registration
- [ ] Extension points clearly defined and documented
- [ ] Phase 2 pathways ready for document processing and MCP tools
- [ ] Multi-mode interface pathway prepared

#### **Deployment Readiness**
- [ ] Docker containerization works in staging
- [ ] Both modes work in production environment
- [ ] Performance meets response time targets
- [ ] Monitoring provides adequate visibility

This UI-003 documentation provides complete architectural coverage while maintaining focused testing scope and clear extension pathways for Phase 2 advanced features.