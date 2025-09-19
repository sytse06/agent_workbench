# UI-001: Gradio Frontend Integration

## Architecture Philosophy: Minimize State Synchronization

### **Core Principle**: Let LangGraph Own All State
- Gradio holds **minimal UI state** (input fields, loading states)
- LangGraph workflows manage **all conversation state**
- UI pulls state from LangGraph when needed, never maintains parallel state

## Implementation Boundaries

### **Phase 1: LangGraph-First Foundation**

#### Files to MODIFY (Complete LangGraph Integration):
```
src/agent_workbench/api/routes/chat.py     # Route all requests through LangGraph
src/agent_workbench/main.py                # Complete dependency injection
```

#### Files to CREATE (Basic UI):
```
src/agent_workbench/ui/
├── __init__.py
├── app.py                                 # Single-mode interface (workbench only)
├── components/
│   ├── __init__.py
│   ├── chat.py                           # Simple chat interface
│   └── simple_client.py                  # Minimal HTTP client
tests/ui/
├── test_gradio_integration.py            # UI component tests
├── test_langgraph_client.py              # API client tests
└── test_state_consistency.py            # State synchronization tests
```

### **Phase 2: Core Interface + Comprehensive Testing**

#### Additional Files to CREATE:
```
src/agent_workbench/ui/components/
├── settings.py                           # Model selection panel
└── error_handling.py                    # Error display components
tests/ui/
├── test_chat_flows.py                   # End-to-end chat testing
├── test_error_scenarios.py             # Error handling tests
└── test_model_switching.py             # Configuration change tests
```

## Simplified State Management

### **Anti-Pattern: Bidirectional Sync**
```python
# DON'T DO THIS - Complex state synchronization
class WorkflowState(BaseModel):
    conversation_id: str
    chat_history: List[Tuple[str, str]]
    current_steps: List[str]
    execution_successful: bool
    context_data: Dict[str, Any]

# Gradio State ↔ LangGraph State (PROBLEMATIC)
```

### **Better Pattern: Stateless UI with LangGraph Queries**
```python
# DO THIS - Minimal UI state, query LangGraph when needed
class MinimalUIState(BaseModel):
    conversation_id: str
    is_loading: bool = False
    last_error: Optional[str] = None

async def get_chat_history(conversation_id: str) -> List[Tuple[str, str]]:
    """Always fetch from LangGraph, never cache in UI"""
    response = await langgraph_client.get_conversation_history(conversation_id)
    return [(msg.content, msg.response) for msg in response.messages]

async def send_message(message: str, conversation_id: str):
    """Send to LangGraph, let it handle all state"""
    return await langgraph_client.execute_workflow({
        "conversation_id": conversation_id,
        "user_message": message,
        "workflow_mode": "workbench"
    })
```

## Simplified Gradio Interface

### **Single-Mode Workbench Interface**
```python
# app.py - Simplified single interface
import gradio as gr
from components.simple_client import LangGraphClient
from components.chat import create_simple_chat_interface
import uuid

def create_workbench_app() -> gr.Blocks:
    """Create simplified workbench interface - no dual modes"""
    
    client = LangGraphClient()
    
    with gr.Blocks(title="Agent Workbench") as app:
        gr.Markdown("# 🛠️ Agent Workbench")
        
        # Minimal state - just conversation ID and loading
        conversation_id = gr.State(str(uuid.uuid4()))
        is_loading = gr.State(False)
        
        with gr.Row():
            with gr.Column(scale=1):
                # Simple model selection
                provider = gr.Dropdown(
                    choices=["openrouter", "ollama"],
                    value="openrouter",
                    label="Provider"
                )
                
                model = gr.Dropdown(
                    choices=["claude-3-5-sonnet-20241022", "gpt-4"],
                    value="claude-3-5-sonnet-20241022",
                    label="Model"
                )
                
                temperature = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    value=0.7,
                    step=0.1,
                    label="Temperature"
                )
                
            with gr.Column(scale=2):
                # Simple chat interface - no complex state management
                chatbot = gr.Chatbot(height=400, label="Chat")
                
                with gr.Row():
                    message = gr.Textbox(
                        placeholder="Enter your message...",
                        label="Message",
                        scale=4,
                        lines=2
                    )
                    send = gr.Button("Send", variant="primary", scale=1)
        
        # Simple event handler - no complex state sync
        async def handle_message(msg, conv_id, provider_val, model_val, temp_val):
            if not msg.strip():
                return "", gr.update()
            
            try:
                # Send to LangGraph
                response = await client.send_message(
                    message=msg,
                    conversation_id=conv_id,
                    model_config={
                        "provider": provider_val,
                        "model": model_val,
                        "temperature": temp_val
                    }
                )
                
                # Get updated history from LangGraph (single source of truth)
                history = await client.get_chat_history(conv_id)
                
                return "", history
                
            except Exception as e:
                # Simple error handling
                error_history = await client.get_chat_history(conv_id)
                error_history.append((msg, f"Error: {str(e)}"))
                return "", error_history
        
        # Wire up events
        send.click(
            fn=handle_message,
            inputs=[message, conversation_id, provider, model, temperature],
            outputs=[message, chatbot]
        )
        
        message.submit(
            fn=handle_message,
            inputs=[message, conversation_id, provider, model, temperature],
            outputs=[message, chatbot]
        )
    
    return app
```

### **Simple LangGraph Client**
```python
# components/simple_client.py
import httpx
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel

class LangGraphClient:
    """Simplified client that always queries LangGraph for state"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(
        self, 
        message: str, 
        conversation_id: str,
        model_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send message to LangGraph workflow"""
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat/message",  # Updated to use LangGraph
            json={
                "message": message,
                "conversation_id": conversation_id,
                "model_config": model_config,
                "workflow_mode": "workbench"
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def get_chat_history(self, conversation_id: str) -> List[Tuple[str, str]]:
        """Get conversation history from LangGraph (single source of truth)"""
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/conversations/{conversation_id}/messages"
        )
        response.raise_for_status()
        
        messages = response.json()["messages"]
        return [
            (msg["content"], msg.get("response", "")) 
            for msg in messages 
            if msg["role"] in ["user", "assistant"]
        ]
```

## Required FastAPI Changes (LangGraph-First)

### **Update Chat Routes to Use LangGraph**
```python
# src/agent_workbench/api/routes/chat.py
from fastapi import APIRouter, Depends
from agent_workbench.services.langgraph_service import WorkbenchLangGraphService

router = APIRouter()

@router.post("/api/v1/chat/message")
async def send_message(
    request: ChatRequest,
    langgraph_service: WorkbenchLangGraphService = Depends(get_langgraph_service)
):
    """All chat requests now go through LangGraph workflows"""
    
    # Convert to LangGraph workflow request
    workflow_config = WorkflowConfig(
        conversation_id=request.conversation_id or str(uuid.uuid4()),
        user_message=request.message,
        model_config=request.model_config,
        workflow_mode="workbench"
    )
    
    # Execute through LangGraph
    result = await langgraph_service.execute_workflow(workflow_config)
    
    return ChatResponse(
        reply=result["response"],
        conversation_id=result["conversation_id"],
        metadata=result.get("metadata", {})
    )

@router.get("/api/v1/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    langgraph_service: WorkbenchLangGraphService = Depends(get_langgraph_service)
):
    """Get conversation history from LangGraph state"""
    
    state = await langgraph_service.get_conversation_state(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "messages": state.get("messages", [])
    }
```

## Comprehensive Testing Strategy

### **Unit Tests for UI Components**
```python
# tests/ui/test_gradio_integration.py
import pytest
from agent_workbench.ui.app import create_workbench_app
from agent_workbench.ui.components.simple_client import LangGraphClient

@pytest.mark.asyncio
async def test_gradio_app_creation():
    """Test Gradio app can be created without errors"""
    app = create_workbench_app()
    assert app is not None
    # Verify key components exist
    assert len(app.blocks) > 0

@pytest.mark.asyncio 
async def test_message_handling():
    """Test message flow through simplified interface"""
    client = LangGraphClient()
    
    # Mock the HTTP client
    with patch.object(client.client, 'post') as mock_post:
        mock_post.return_value.json.return_value = {
            "response": "Test response",
            "conversation_id": "test-id"
        }
        
        result = await client.send_message(
            message="Hello",
            conversation_id="test-id",
            model_config={"provider": "openrouter", "model": "claude-3-5-sonnet-20241022"}
        )
        
        assert result["response"] == "Test response"
        assert result["conversation_id"] == "test-id"
```

### **Integration Tests for LangGraph-FastAPI Bridge**
```python
# tests/ui/test_langgraph_integration.py
import pytest
from fastapi.testclient import TestClient
from agent_workbench.main import app

def test_chat_endpoint_uses_langgraph():
    """Test that chat endpoint routes through LangGraph"""
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/chat/message",
        json={
            "message": "Hello",
            "conversation_id": "test-id",
            "model_config": {
                "provider": "openrouter",
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.7
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "conversation_id" in data

def test_conversation_history_endpoint():
    """Test conversation history retrieval"""
    client = TestClient(app)
    
    response = client.get("/api/v1/conversations/test-id/messages")
    
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert "conversation_id" in data
```

### **State Consistency Tests**
```python
# tests/ui/test_state_consistency.py
import pytest
from agent_workbench.ui.components.simple_client import LangGraphClient

@pytest.mark.asyncio
async def test_no_state_drift():
    """Verify UI doesn't maintain parallel state that can drift"""
    client = LangGraphClient()
    conversation_id = "test-consistency"
    
    # Send message
    await client.send_message("Hello", conversation_id, {"provider": "openrouter"})
    
    # Get history twice - should be identical (no caching/drift)
    history1 = await client.get_chat_history(conversation_id)
    history2 = await client.get_chat_history(conversation_id)
    
    assert history1 == history2
    assert len(history1) > 0

@pytest.mark.asyncio
async def test_error_recovery():
    """Test that UI gracefully handles LangGraph errors"""
    client = LangGraphClient()
    
    with patch.object(client.client, 'post') as mock_post:
        mock_post.side_effect = httpx.HTTPError("Network error")
        
        with pytest.raises(Exception) as exc_info:
            await client.send_message("Hello", "test-id", {})
        
        assert "Network error" in str(exc_info.value)
```

## Success Criteria for UI-001

### **Phase 1 Success Criteria:**
- [ ] All chat requests route through LangGraph workflows
- [ ] FastAPI dependency injection for LangGraph service works
- [ ] Basic Gradio interface loads and displays correctly
- [ ] Message sending and receiving works end-to-end
- [ ] Model selection updates workflow configuration
- [ ] Unit tests achieve >80% coverage for UI components

### **Phase 2 Success Criteria:**
- [ ] Error handling displays appropriate user feedback
- [ ] Conversation history persists correctly across sessions  
- [ ] Model parameter changes take effect immediately
- [ ] Integration tests cover all major user flows
- [ ] Performance benchmarks meet <3 second response targets
- [ ] State consistency tests pass (no drift/caching issues)

## UI-002: Advanced Features (Phases 3-4)

Leave for separate iteration:
- Dual-mode interface (workbench vs SEO coach)
- Document upload and processing UI
- MCP tool integration and selection
- Advanced workflow monitoring and controls
- Streaming response UI with progress indicators