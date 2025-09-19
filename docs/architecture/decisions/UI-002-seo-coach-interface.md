# UI-002: SEO Coach Interface

## Status

**Status**: Implementation Ready - Foundation Verified  
**Date**: September 19, 2025  
**Decision Makers**: Human Architect  
**Task ID**: UI-002-seo-coach-interface  
**Dependencies**: UI-001 Enhanced (with consolidated service), LLM-001C (consolidated workflow), Phase 1A completion

## Context

Implement SEO Coach interface that leverages the proven consolidated service foundation. With LangGraph workflows, dual-mode routing, and `WorkbenchState` management already operational, UI-002 focuses on creating the Dutch business coaching interface that routes through `workflow_mode="seo_coach"` while maintaining the architectural patterns established in UI-001 Enhanced.

## Verified Foundation

### **What UI-002 Can Build On (Confirmed Working):**
- **LangGraph Workflows**: Consolidated service with dual-mode support operational
- **API Endpoints**: `/api/v1/chat/consolidated` endpoint handles both modes
- **State Management**: `WorkbenchState` with business profile support
- **Dual-Mode Routing**: Mode detection and conditional workflow routing
- **Error Handling**: Mode-aware error responses with Dutch fallbacks
- **UI-001 Enhanced**: Verified workbench interface using consolidated service

### **What UI-002 Will Implement:**
- **Mode Factory**: Environment-based interface switching
- **SEO Coach Interface**: Dutch business coaching UI
- **Business Profile Management**: Simple forms using `WorkbenchState.business_profile`
- **Consolidated Service Integration**: All API calls through verified endpoints
- **Phase 2 Feature Stubs**: Clear placeholders for document processing and MCP tools

## Implementation Boundaries

### Files to CREATE:

```
src/agent_workbench/ui/
├── mode_factory.py                     # Mode-based interface factory
├── seo_coach_app.py                    # Dutch SEO coaching interface
└── clients/
    └── seo_coach_client.py            # SEO coach API client

src/agent_workbench/ui/components/
├── business_profile_form.py            # Business profile creation forms
└── dutch_messages.py                  # Basic Dutch localization

tests/ui/
├── test_mode_factory.py               # Mode switching tests
├── test_seo_coach_interface.py        # SEO coach functionality tests  
└── test_consolidated_integration.py   # End-to-end integration tests
```

### Files to MODIFY:

```
src/agent_workbench/main.py             # Add mode factory integration
src/agent_workbench/api/routes/consolidated_chat.py  # Add conversation state endpoint
```

## Detailed Implementation

### **1. Mode Factory Implementation**

```python
# src/agent_workbench/ui/mode_factory.py
import os
from typing import Optional
import gradio as gr
from .app import create_workbench_app          # UI-001 Enhanced
from .seo_coach_app import create_seo_coach_app  # UI-002

def create_interface_for_mode(mode: Optional[str] = None) -> gr.Blocks:
    """Create interface based on APP_MODE environment variable"""
    
    effective_mode = mode or os.getenv("APP_MODE", "workbench")
    
    if effective_mode == "seo_coach":
        return create_seo_coach_app()
    elif effective_mode == "workbench":
        return create_workbench_app()
    else:
        raise ValueError(f"Invalid mode: {effective_mode}. Use 'workbench' or 'seo_coach'")

def get_mode_from_environment() -> str:
    """Get current mode from environment"""
    return os.getenv("APP_MODE", "workbench")

def validate_mode_configuration(mode: str) -> bool:
    """Validate mode is supported"""
    return mode in ["workbench", "seo_coach"]

# Extension point for Phase 2
def register_extension_mode(mode_name: str, interface_factory):
    """Phase 2: Register additional interface modes"""
    # Placeholder for Phase 2 extension registration
    pass
```

### **2. SEO Coach Client (Consolidated Service Integration)**

```python
# src/agent_workbench/ui/clients/seo_coach_client.py
import httpx
import uuid
from typing import Dict, Any, List, Optional
import os

class SEOCoachClient:
    """Client for SEO coach workflow using consolidated service"""
    
    def __init__(self):
        self.base_url = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_coaching_message(
        self, 
        message: str, 
        conversation_id: str, 
        business_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send message through SEO coach workflow"""
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat/consolidated",
            json={
                "user_message": message,
                "conversation_id": conversation_id,
                "workflow_mode": "seo_coach",              # SEO coach mode
                "business_profile": business_profile,
                "model_config": self._get_dutch_coaching_config(),
                "streaming": False,
                "context_data": {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def start_website_analysis(
        self, 
        website_url: str, 
        business_profile: Dict[str, Any], 
        conversation_id: str
    ) -> Dict[str, Any]:
        """Start website analysis for SEO coaching"""
        
        analysis_message = f"Analyseer mijn {business_profile.get('business_type', 'bedrijf').lower()} website {website_url} voor SEO verbeteringen. Geef praktische tips die ik zelf kan uitvoeren."
        
        return await self.send_coaching_message(
            message=analysis_message,
            conversation_id=conversation_id,
            business_profile=business_profile
        )
    
    async def get_chat_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history from consolidated service"""
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/conversations/{conversation_id}/state"
        )
        
        if response.status_code == 404:
            return []
            
        response.raise_for_status()
        state = response.json()
        return state.get("conversation_history", [])
    
    def _get_dutch_coaching_config(self) -> Dict[str, Any]:
        """Get model configuration optimized for Dutch SEO coaching"""
        return {
            "provider": "openrouter",
            "model_name": "openai/gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 1500,
            "system_prompt": "Je bent een Nederlandse SEO expert die helpt kleine bedrijven hun website te verbeteren. Geef praktische, uitvoerbare adviezen in het Nederlands."
        }
```

### **3. SEO Coach Gradio Interface**

```python
# src/agent_workbench/ui/seo_coach_app.py
import gradio as gr
import uuid
from typing import Dict, Any
from .clients.seo_coach_client import SEOCoachClient
from .components.business_profile_form import create_business_profile_form
from .components.dutch_messages import get_dutch_message

def create_seo_coach_app() -> gr.Blocks:
    """Create Dutch SEO coaching interface using consolidated service"""
    
    client = SEOCoachClient()
    
    with gr.Blocks(
        title="AI SEO Coach",
        theme=gr.themes.Soft(),
        css="""
        .business-panel { background: #f8f9fa; padding: 20px; border-radius: 8px; }
        .coaching-panel { min-height: 500px; }
        .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 4px; }
        .error { color: #721c24; background: #f8d7da; padding: 10px; border-radius: 4px; }
        .processing { color: #0c5460; background: #d1ecf1; padding: 10px; border-radius: 4px; }
        """
    ) as interface:
        
        # Header
        gr.Markdown("# 🚀 AI SEO Coach voor Nederlandse Bedrijven")
        gr.Markdown("*Verbeter je website ranking met persoonlijke AI coaching*")
        
        # State management (minimal, following UI-001 patterns)
        conversation_id = gr.State(str(uuid.uuid4()))
        business_profile = gr.State({})
        
        with gr.Row():
            # Left Panel: Business Profile
            with gr.Column(scale=1, elem_classes=["business-panel"]):
                gr.Markdown("### 🏢 Jouw Bedrijf")
                
                business_name = gr.Textbox(
                    label="Bedrijfsnaam",
                    placeholder="Bijv. Restaurant De Gouden Lepel"
                )
                
                business_type = gr.Dropdown(
                    choices=[
                        "Restaurant", "Webshop", "Dienstverlening", "B2B Bedrijf",
                        "Freelancer", "Advocatenkantoor", "Zorgverlening", "Anders"
                    ],
                    label="Type bedrijf",
                    value="Restaurant"
                )
                
                website_url = gr.Textbox(
                    label="Website URL",
                    placeholder="https://jouw-website.nl"
                )
                
                location = gr.Textbox(
                    label="Locatie",
                    placeholder="Amsterdam, Rotterdam, etc."
                )
                
                # Analysis button
                analyze_btn = gr.Button(
                    "🔍 Analyseer Mijn Website",
                    variant="primary",
                    size="lg"
                )
                
                # Status display
                gr.Markdown("### 📊 Status")
                analysis_status = gr.HTML(
                    value="<div class='info'>Vul je bedrijfsgegevens in om te beginnen</div>"
                )
                
                # Phase 2 feature stubs
                gr.Markdown("### 📄 Documenten (Binnenkort)")
                gr.File(
                    label="Upload Document", 
                    interactive=False,
                    visible=True
                )
                gr.HTML("<em>Document analyse komt beschikbaar in Phase 2</em>")
                
            # Right Panel: Coaching Chat  
            with gr.Column(scale=2, elem_classes=["coaching-panel"]):
                gr.Markdown("### 💬 Je Persoonlijke SEO Coach")
                
                chatbot = gr.Chatbot(
                    height=450,
                    label="",
                    placeholder="👋 Hoi! Analyseer eerst je website, dan kunnen we aan de slag met SEO verbetering!",
                    type="messages"
                )
                
                with gr.Row():
                    message_input = gr.Textbox(
                        placeholder="Stel je vraag over SEO, zoekwoorden, content...",
                        label="Jouw vraag",
                        lines=2,
                        scale=4
                    )
                    
                    send_button = gr.Button(
                        "Verstuur",
                        variant="primary",
                        scale=1
                    )
                
                # Quick action buttons
                with gr.Row():
                    quick_audit = gr.Button("🔍 Snelle SEO Check", size="sm")
                    keyword_help = gr.Button("🔑 Zoekwoord Tips", size="sm")
                    content_ideas = gr.Button("✍️ Content Ideeën", size="sm")
        
        # Event handlers
        async def analyze_website(url, biz_name, biz_type, location_val, conv_id):
            """Handle website analysis"""
            
            if not url.strip():
                return [], {}, "<div class='error'>❌ Vul eerst een website URL in</div>"
            
            if not biz_name.strip():
                return [], {}, "<div class='error'>❌ Vul eerst je bedrijfsnaam in</div>"
            
            try:
                # Create business profile
                profile = {
                    "business_name": biz_name,
                    "business_type": biz_type,
                    "website_url": url,
                    "location": location_val or "Nederland",
                    "language": "dutch",
                    "seo_experience": "beginner"
                }
                
                # Show processing status
                processing_html = "<div class='processing'>🔄 Website wordt geanalyseerd door AI...</div>"
                
                # Start analysis
                response = await client.start_website_analysis(url, profile, conv_id)
                
                # Create initial chat history
                welcome_message = f"Welkom {biz_name}! Ik heb je {biz_type.lower()} website geanalyseerd."
                chat_history = [
                    {"role": "assistant", "content": welcome_message},
                    {"role": "assistant", "content": response["assistant_response"]}
                ]
                
                # Success status
                success_html = f"""
                <div class='success'>
                    ✅ Website analyse voltooid!<br>
                    <strong>Bedrijf:</strong> {biz_name}<br>
                    <strong>Website:</strong> <a href='{url}' target='_blank'>{url}</a><br>
                    <strong>Status:</strong> {'Succesvol' if response.get('execution_successful', True) else 'Waarschuwing'}
                </div>
                """
                
                return chat_history, profile, success_html
                
            except Exception as e:
                error_html = f"<div class='error'>❌ Analyse gefaald: {str(e)}</div>"
                return [], {}, error_html
        
        async def handle_coaching_message(msg, conv_id, profile_data):
            """Handle coaching conversation"""
            
            if not msg.strip():
                return "", gr.update()
            
            if not profile_data:
                error_msg = get_dutch_message("no_business_profile")
                return "", [{"role": "assistant", "content": error_msg}]
            
            try:
                response = await client.send_coaching_message(
                    message=msg,
                    conversation_id=conv_id,
                    business_profile=profile_data
                )
                
                # Get updated chat history (stateless pattern)
                updated_history = await client.get_chat_history(conv_id)
                
                return "", updated_history
                
            except Exception as e:
                # Add error to current history
                current_history = await client.get_chat_history(conv_id)
                current_history.extend([
                    {"role": "user", "content": msg},
                    {"role": "assistant", "content": f"Sorry, er ging iets mis: {str(e)}"}
                ])
                return "", current_history
        
        async def quick_seo_action(action_type, conv_id, profile_data):
            """Handle quick SEO action buttons"""
            
            messages = {
                "audit": "Geef me een snelle SEO-check van mijn website. Wat zijn de 3 belangrijkste verbeterpunten?",
                "keywords": f"Help me goede zoekwoorden te vinden voor mijn {profile_data.get('business_type', 'bedrijf').lower()}. Welke zoekwoorden gebruikt mijn doelgroep?",
                "content": f"Geef me 5 concrete content-ideeën voor mijn {profile_data.get('business_type', 'bedrijf').lower()} die goed scoren in Google."
            }
            
            message = messages.get(action_type, messages["audit"])
            return await handle_coaching_message(message, conv_id, profile_data)
        
        # Wire up events
        analyze_btn.click(
            fn=analyze_website,
            inputs=[website_url, business_name, business_type, location, conversation_id],
            outputs=[chatbot, business_profile, analysis_status]
        )
        
        send_button.click(
            fn=handle_coaching_message,
            inputs=[message_input, conversation_id, business_profile],
            outputs=[message_input, chatbot]
        )
        
        message_input.submit(
            fn=handle_coaching_message,
            inputs=[message_input, conversation_id, business_profile],
            outputs=[message_input, chatbot]
        )
        
        # Quick actions
        quick_audit.click(
            fn=lambda conv_id, profile: quick_seo_action("audit", conv_id, profile),
            inputs=[conversation_id, business_profile],
            outputs=[chatbot]
        )
        
        keyword_help.click(
            fn=lambda conv_id, profile: quick_seo_action("keywords", conv_id, profile),
            inputs=[conversation_id, business_profile],
            outputs=[chatbot]
        )
        
        content_ideas.click(
            fn=lambda conv_id, profile: quick_seo_action("content", conv_id, profile),
            inputs=[conversation_id, business_profile],
            outputs=[chatbot]
        )
    
    return interface
```

### **4. Dutch Messages Component**

```python
# src/agent_workbench/ui/components/dutch_messages.py
"""Basic Dutch localization for SEO coaching"""

DUTCH_MESSAGES = {
    "no_business_profile": "Vul eerst je bedrijfsgegevens in en analyseer je website voordat we kunnen beginnen met coaching.",
    "analysis_complete": "✅ Website analyse voltooid! Je kunt nu vragen stellen over SEO verbetering.",
    "processing": "🔄 Je verzoek wordt verwerkt...",
    "error_general": "Er ging iets mis. Probeer het opnieuw of neem contact op voor hulp.",
    "website_required": "Vul een website URL in om te beginnen.",
    "business_name_required": "Vul je bedrijfsnaam in.",
}

def get_dutch_message(key: str, **kwargs) -> str:
    """Get Dutch message with optional formatting"""
    message = DUTCH_MESSAGES.get(key, f"Bericht niet gevonden: {key}")
    return message.format(**kwargs) if kwargs else message
```

### **5. Required API Endpoint Addition**

```python
# src/agent_workbench/api/routes/consolidated_chat.py (MODIFY)

@router.get("/conversations/{conversation_id}/state")
async def get_conversation_state(
    conversation_id: str,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service)
):
    """Get conversation state for UI history display"""
    
    try:
        state = await service.get_conversation_state(UUID(conversation_id))
        return {
            "conversation_id": conversation_id,
            "conversation_history": state.get("conversation_history", []),
            "workflow_mode": state.get("workflow_mode", "workbench"),
            "business_profile": state.get("business_profile"),
            "context_data": state.get("context_data", {})
        }
    except Exception as e:
        raise HTTPException(
            status_code=404, 
            detail=f"Conversation not found: {str(e)}"
        )
```

### **6. Main Application Integration**

```python
# src/agent_workbench/main.py (MODIFY)
from agent_workbench.ui.mode_factory import create_interface_for_mode, get_mode_from_environment

def create_app() -> FastAPI:
    """Create FastAPI app with dual-mode Gradio integration"""
    
    # ... existing FastAPI setup ...
    
    # Include consolidated chat routes
    app.include_router(consolidated_chat.router, prefix="/api/v1")
    
    # Create mode-aware Gradio interface
    current_mode = get_mode_from_environment()
    gradio_app = create_interface_for_mode(current_mode)
    
    # Mount Gradio app
    app = gr.mount_gradio_app(app, gradio_app, path="/")
    
    # Mode information endpoint
    @app.get("/api/mode")
    async def get_mode_info():
        return {
            "current_mode": current_mode,
            "available_modes": ["workbench", "seo_coach"],
            "phase": "1",
            "features": {
                "workbench": "Technical AI development interface",
                "seo_coach": "Dutch SEO coaching for businesses"
            }
        }
    
    return app
```

## Testing Strategy

### **Focused Testing Approach**

```python
# tests/ui/test_mode_factory.py
def test_mode_factory_workbench():
    """Test workbench mode creation"""
    interface = create_interface_for_mode("workbench")
    assert "Agent Workbench" in str(interface.title)

def test_mode_factory_seo_coach():
    """Test SEO coach mode creation"""  
    interface = create_interface_for_mode("seo_coach")
    assert "SEO Coach" in str(interface.title)

# tests/ui/test_consolidated_integration.py  
@pytest.mark.asyncio
async def test_seo_coach_consolidated_integration():
    """Test SEO coach integrates correctly with consolidated service"""
    
    with patch('httpx.AsyncClient') as mock_client:
        # Mock consolidated service response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "assistant_response": "Nederlandse SEO tips...",
            "workflow_mode": "seo_coach",
            "execution_successful": True
        }
        
        client = SEOCoachClient()
        response = await client.send_coaching_message(
            "Help me met SEO", "conv-123", {"business_type": "Restaurant"}
        )
        
        assert response["workflow_mode"] == "seo_coach"
```

## Success Criteria

### **Functional Requirements**
- [ ] Mode factory correctly switches between workbench and SEO coach based on APP_MODE
- [ ] SEO coach interface loads and displays correctly in Dutch
- [ ] Business profile form integrates with consolidated service
- [ ] Website analysis triggers appropriate Dutch coaching responses  
- [ ] Conversation history persists correctly across interactions
- [ ] Quick action buttons provide immediate SEO value

### **Integration Requirements**  
- [ ] All API calls use `/api/v1/chat/consolidated` endpoint
- [ ] `workflow_mode="seo_coach"` routing works correctly
- [ ] Business profiles stored in `WorkbenchState.business_profile`
- [ ] Error handling provides Dutch business-friendly messages
- [ ] No interference with existing workbench mode functionality

### **Deployment Requirements**
- [ ] APP_MODE environment variable controls interface mode
- [ ] Docker deployment supports both modes
- [ ] Both modes stable under normal production load
- [ ] Phase 2 feature stubs clearly communicate future roadmap

This aligned UI-002 implementation leverages the verified consolidated service foundation while delivering the complete dual-mode system for Phase 1 deployment.