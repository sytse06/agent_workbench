# UI-002: Advanced Features - Dual-Mode, Documents & Tools

## Status

**Status**: Awaiting UI-001 Completion  
**Date**: September 18, 2025  
**Decision Makers**: Human Architect  
**Task ID**: UI-002-advanced-interface-features  
**Dependencies**: UI-001 (LangGraph-first foundation), DOC-001 (document processing), MCP-001 (tool integration)

## Context

Build advanced interface features on the solid UI-001 foundation: dual-mode switching (workbench/SEO coach), document processing integration, and MCP tool selection. Maintains the LangGraph-first architecture and stateless UI principles established in UI-001.

## Architecture Scope

### What's Included:

- **Dual-Mode Interface**: Environment-based switching between workbench and SEO coach modes
- **Document Processing UI**: File upload, URL input, and document context integration
- **MCP Tool Management**: Tool discovery, selection, and execution interface
- **Advanced Workflow Controls**: Tool confirmation, execution monitoring, multi-step workflows
- **Enhanced Error Handling**: Context-aware error messages, retry mechanisms
- **Responsive Design**: Mobile-optimized layouts for both modes

### What's Explicitly Excluded:

- Authentication or user management systems
- Multi-user collaboration features
- Custom MCP tool creation interface
- Vector database search interface
- File management system (beyond single document processing)
- Real-time collaboration or sharing features

## Architectural Decisions

### 1. Mode-Based Architecture Extension

**Build on UI-001 Foundation**: Extend single workbench interface to support dual modes

```python
# Extends UI-001's simple architecture
class ModeAwareInterface:
    def __init__(self):
        self.base_client = LangGraphClient()  # From UI-001
        self.app_mode = os.getenv("APP_MODE", "workbench")
        self.document_service = DocumentProcessingClient()
        self.tool_service = MCPToolClient()
    
    def create_interface(self) -> gr.Blocks:
        """Factory method that returns appropriate interface"""
        if self.app_mode == "seo_coach":
            return self.create_seo_coach_interface()
        else:
            return self.create_advanced_workbench_interface()
```

### 2. Stateless Document Integration

**No Document State in UI**: Documents processed and stored in LangGraph context

```python
# Document handling - no UI state caching
async def process_document(file_path: str, conversation_id: str):
    """Process document and add to LangGraph context"""
    
    # Process document
    doc_result = await document_service.process_document(file_path)
    
    # Add to LangGraph workflow context (not UI state)
    await langgraph_client.update_workflow_context(
        conversation_id=conversation_id,
        context_update={
            "document_context": doc_result.content,
            "document_metadata": doc_result.metadata,
            "document_chunks": doc_result.chunks
        }
    )
    
    return doc_result.metadata  # Only return metadata for UI display
```

### 3. Tool Selection UI Pattern

**Explicit Tool Management**: Clear tool selection and confirmation workflow

```python
# Tool selection - explicit user control
class ToolSelectionManager:
    async def get_available_tools(self) -> List[ToolInfo]:
        """Fetch available MCP tools"""
        return await mcp_service.discover_tools()
    
    async def execute_tool_with_confirmation(
        self, 
        tool_name: str, 
        tool_params: Dict[str, Any],
        conversation_id: str
    ):
        """Execute tool with explicit user confirmation"""
        
        # Add tool execution to workflow context
        await langgraph_client.execute_tool_workflow({
            "conversation_id": conversation_id,
            "tool_name": tool_name,
            "tool_params": tool_params,
            "requires_confirmation": True
        })
```

### 4. Enhanced Error Context

**Mode-Aware Error Handling**: Different error presentation for different audiences

```python
def format_error_for_mode(error: Exception, mode: str, context: str) -> str:
    """Format errors appropriately for each mode"""
    
    if mode == "workbench":
        # Technical details for developers
        return f"Error in {context}: {str(error)}\nType: {type(error).__name__}"
    
    elif mode == "seo_coach":
        # User-friendly Dutch messages for business users
        error_translations = {
            "HTTPError": "Er ging iets mis met de internetverbinding. Probeer het opnieuw.",
            "ValidationError": "De ingevoerde gegevens zijn niet correct. Controleer je invoer.",
            "TimeoutError": "De verwerking duurt te lang. Probeer een kleiner bestand."
        }
        return error_translations.get(type(error).__name__, 
                                    "Er is een technische fout opgetreden. Probeer het later opnieuw.")
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/ui/
├── mode_factory.py                    # Mode-based interface factory
├── seo_coach_interface.py            # Dutch SEO coaching interface
├── advanced_workbench_interface.py   # Enhanced workbench with tools/docs
├── components/
│   ├── document_processor.py         # Document upload and processing UI
│   ├── tool_selector.py             # MCP tool selection and management
│   ├── workflow_controls.py         # Advanced workflow execution controls
│   ├── error_display.py             # Mode-aware error presentation
│   └── responsive_layout.py         # Mobile-responsive layout utilities
├── clients/
│   ├── document_client.py           # Document processing API client
│   └── mcp_client.py               # MCP tool management client
└── localization/
    ├── __init__.py
    ├── dutch_seo.py                 # Dutch SEO coaching messages
    └── technical_terms.py           # Technical workbench terminology

tests/ui/
├── test_dual_mode_switching.py      # Mode switching functionality
├── test_document_processing_ui.py   # Document upload and processing
├── test_tool_selection.py          # MCP tool selection and execution
├── test_seo_coach_flows.py         # Dutch SEO coaching workflows
├── test_mobile_responsiveness.py   # Mobile layout testing
└── test_error_handling_modes.py    # Mode-specific error handling
```

### Files to MODIFY:

```
src/agent_workbench/ui/app.py          # Add mode factory integration
src/agent_workbench/main.py           # Add document and tool service deps
```

### Exact Function Signatures:

```python
# mode_factory.py
def create_interface_for_mode(mode: str) -> gr.Blocks
def get_mode_from_environment() -> str
def validate_mode_configuration(mode: str) -> bool

# seo_coach_interface.py
def create_seo_coach_interface() -> gr.Blocks
async def handle_seo_message(
    message: str,
    conversation_id: str,
    business_profile: Dict[str, str]
) -> Tuple[List[Tuple[str, str]], str]

async def handle_website_analysis(
    website_url: str,
    business_type: str,
    conversation_id: str
) -> Tuple[Dict[str, Any], str]

async def generate_seo_action_plan(
    analysis_results: Dict[str, Any],
    conversation_id: str
) -> str

# advanced_workbench_interface.py  
def create_advanced_workbench_interface() -> gr.Blocks
async def handle_workbench_message_with_tools(
    message: str,
    conversation_id: str,
    selected_tools: List[str],
    model_config: Dict[str, Any]
) -> Tuple[List[Tuple[str, str]], str, List[str]]

# components/document_processor.py
def create_document_upload_panel() -> gr.Column
async def process_uploaded_file(
    file_path: str,
    conversation_id: str
) -> Tuple[Dict[str, Any], str]

async def process_url_content(
    url: str,
    conversation_id: str
) -> Tuple[Dict[str, Any], str]

def create_document_status_display() -> gr.HTML

# components/tool_selector.py
def create_tool_selection_panel() -> gr.Column
async def load_available_tools() -> List[Dict[str, Any]]
async def execute_selected_tool(
    tool_name: str,
    tool_params: Dict[str, Any],
    conversation_id: str
) -> Dict[str, Any]

def create_tool_execution_monitor() -> gr.Column

# components/workflow_controls.py
def create_workflow_control_panel() -> gr.Column
async def confirm_tool_execution(
    tool_name: str,
    tool_description: str,
    estimated_cost: Optional[float]
) -> bool

def create_workflow_progress_display() -> gr.HTML

# components/error_display.py
def create_error_display_component(mode: str) -> gr.HTML
def format_error_for_display(
    error: Exception,
    mode: str,
    context: str
) -> str

def create_retry_mechanism() -> gr.Button

# clients/document_client.py
class DocumentProcessingClient:
    async def upload_and_process_file(
        self,
        file_path: str,
        conversation_id: str
    ) -> DocumentProcessingResult
    
    async def process_url_content(
        self,
        url: str,
        conversation_id: str
    ) -> DocumentProcessingResult
    
    async def get_document_status(
        self,
        conversation_id: str
    ) -> Optional[DocumentMetadata]

# clients/mcp_client.py
class MCPToolClient:
    async def discover_available_tools(self) -> List[ToolInfo]
    async def get_tool_details(self, tool_name: str) -> ToolDetails
    async def execute_tool(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        conversation_id: str
    ) -> ToolExecutionResult
```

## Detailed Interface Implementations

### **Advanced Workbench Interface**

```python
# advanced_workbench_interface.py
import gradio as gr
from typing import Dict, List, Tuple, Any
from .components.document_processor import create_document_upload_panel
from .components.tool_selector import create_tool_selection_panel
from .components.workflow_controls import create_workflow_control_panel
from .clients.document_client import DocumentProcessingClient
from .clients.mcp_client import MCPToolClient
import uuid

def create_advanced_workbench_interface() -> gr.Blocks:
    """Enhanced workbench with document processing and MCP tools"""
    
    doc_client = DocumentProcessingClient()
    mcp_client = MCPToolClient()
    
    with gr.Blocks(title="Agent Workbench - Advanced", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🛠️ Agent Workbench - Advanced")
        gr.Markdown("*AI development with document processing and tool integration*")
        
        # State management - minimal as per UI-001 pattern
        conversation_id = gr.State(str(uuid.uuid4()))
        is_processing = gr.State(False)
        
        with gr.Row():
            with gr.Column(scale=1):
                # Model Configuration (from UI-001)
                gr.Markdown("### ⚙️ Model Configuration")
                provider = gr.Dropdown(
                    choices=["openrouter", "ollama", "anthropic"],
                    value="openrouter",
                    label="Provider"
                )
                model = gr.Dropdown(
                    choices=["claude-3-5-sonnet-20241022", "gpt-4o", "llama-3.1-70b"],
                    value="claude-3-5-sonnet-20241022",
                    label="Model"
                )
                temperature = gr.Slider(0.0, 2.0, 0.7, label="Temperature")
                
                # Document Processing Panel
                gr.Markdown("### 📄 Document Processing")
                doc_panel = create_document_upload_panel()
                
                # MCP Tool Selection Panel
                gr.Markdown("### 🔧 Available Tools")
                tool_panel = create_tool_selection_panel()
                
                # Workflow Controls
                gr.Markdown("### 🎯 Workflow Controls")
                workflow_panel = create_workflow_control_panel()
                
            with gr.Column(scale=2):
                # Chat Interface (enhanced from UI-001)
                chatbot = gr.Chatbot(
                    height=500,
                    label="Advanced Chat with Tools & Documents",
                    placeholder="Upload documents or select tools, then start chatting..."
                )
                
                with gr.Row():
                    message = gr.Textbox(
                        placeholder="Ask about your documents or request tool usage...",
                        label="Message",
                        scale=4,
                        lines=3
                    )
                    send = gr.Button("Send", variant="primary", scale=1)
                
                # Status displays
                with gr.Row():
                    doc_status = gr.HTML(label="Document Status")
                    tool_status = gr.HTML(label="Tool Status")
        
        # Enhanced message handler with tools and documents
        async def handle_advanced_message(
            msg: str,
            conv_id: str,
            provider_val: str,
            model_val: str,
            temp_val: float,
            selected_tools: List[str]
        ):
            if not msg.strip():
                return "", gr.update()
            
            try:
                # Get current document context from LangGraph
                doc_context = await doc_client.get_document_status(conv_id)
                
                # Send enhanced request to LangGraph
                response = await langgraph_client.send_message_with_context(
                    message=msg,
                    conversation_id=conv_id,
                    model_config={
                        "provider": provider_val,
                        "model": model_val,
                        "temperature": temp_val
                    },
                    available_tools=selected_tools,
                    document_context=doc_context
                )
                
                # Get updated chat history (single source of truth)
                history = await langgraph_client.get_chat_history(conv_id)
                
                return "", history
                
            except Exception as e:
                error_msg = format_error_for_mode(e, "workbench", "chat")
                history = await langgraph_client.get_chat_history(conv_id)
                history.append((msg, f"Error: {error_msg}"))
                return "", history
        
        # Wire up events
        send.click(
            fn=handle_advanced_message,
            inputs=[message, conversation_id, provider, model, temperature, tool_panel],
            outputs=[message, chatbot]
        )
        
        message.submit(
            fn=handle_advanced_message,
            inputs=[message, conversation_id, provider, model, temperature, tool_panel],
            outputs=[message, chatbot]
        )
    
    return interface
```

### **SEO Coach Interface (Dutch)**

```python
# seo_coach_interface.py
import gradio as gr
from typing import Dict, List, Tuple, Any
from .localization.dutch_seo import get_seo_message, get_business_types
from .clients.document_client import DocumentProcessingClient
import uuid

def create_seo_coach_interface() -> gr.Blocks:
    """Dutch SEO coaching interface for small businesses"""
    
    doc_client = DocumentProcessingClient()
    
    with gr.Blocks(title="AI SEO Coach", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🚀 AI SEO Coach voor Nederlandse Bedrijven")
        gr.Markdown("*Verbeter je website ranking met persoonlijke AI coaching*")
        
        conversation_id = gr.State(str(uuid.uuid4()))
        business_profile = gr.State({})
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🏢 Bedrijfsprofiel")
                
                business_name = gr.Textbox(
                    label="Bedrijfsnaam",
                    placeholder="Bijv. Restaurant De Gouden Lepel"
                )
                
                business_type = gr.Dropdown(
                    choices=get_business_types(),
                    label="Type bedrijf",
                    value="Restaurant"
                )
                
                location = gr.Textbox(
                    label="Locatie",
                    placeholder="Bijv. Amsterdam, Rotterdam"
                )
                
                website_url = gr.Textbox(
                    label="Website URL",
                    placeholder="https://jouw-website.nl"
                )
                
                target_keywords = gr.Textbox(
                    label="Belangrijkste zoekwoorden",
                    placeholder="Bijv. restaurant amsterdam, italiaans eten",
                    lines=2
                )
                
                # Website analysis button
                analyze_btn = gr.Button(
                    "🔍 Analyseer mijn website",
                    variant="primary",
                    size="lg"
                )
                
                # Progress display
                gr.Markdown("### 📊 Voortgang")
                progress_display = gr.HTML(
                    value=get_seo_message("welcome_message")
                )
                
            with gr.Column(scale=2):
                gr.Markdown("### 💬 Je persoonlijke SEO coach")
                
                chatbot = gr.Chatbot(
                    height=450,
                    label="",
                    placeholder=get_seo_message("chat_placeholder")
                )
                
                with gr.Row():
                    message = gr.Textbox(
                        placeholder=get_seo_message("input_placeholder"),
                        label="Jouw vraag",
                        scale=4,
                        lines=2
                    )
                    send = gr.Button("Verstuur", variant="primary", scale=1)
                
                # Quick action buttons
                with gr.Row():
                    quick_seo_audit = gr.Button("🔍 SEO Check", size="sm")
                    keyword_help = gr.Button("🔑 Zoekwoord Tips", size="sm")
                    content_ideas = gr.Button("✍️ Content Ideeën", size="sm")
        
        # Website analysis handler
        async def analyze_website(
            url: str,
            biz_name: str,
            biz_type: str,
            location: str,
            keywords: str,
            conv_id: str
        ):
            if not url.strip():
                return [], {}, get_seo_message("error_no_url")
            
            try:
                # Create business profile
                profile = {
                    "business_name": biz_name or "Je bedrijf",
                    "business_type": biz_type,
                    "location": location,
                    "website_url": url,
                    "target_keywords": keywords,
                    "language": "dutch",
                    "experience_level": "beginner"
                }
                
                # Process website content
                doc_result = await doc_client.process_url_content(url, conv_id)
                
                # Send to SEO analysis workflow
                analysis_message = get_seo_message("analysis_request", 
                                                 business_type=biz_type, 
                                                 website_url=url)
                
                response = await langgraph_client.execute_seo_workflow({
                    "conversation_id": conv_id,
                    "user_message": analysis_message,
                    "business_profile": profile,
                    "website_content": doc_result.content
                })
                
                # Create initial chat history
                welcome_msg = get_seo_message("analysis_start", business_name=biz_name)
                chat_history = [
                    (None, welcome_msg),
                    (analysis_message, response["assistant_response"])
                ]
                
                # Generate progress HTML
                progress_html = generate_dutch_progress_display(
                    profile, doc_result.metadata, response.get("seo_score", 0)
                )
                
                return chat_history, profile, progress_html
                
            except Exception as e:
                error_msg = format_error_for_mode(e, "seo_coach", "website_analysis")
                error_html = f"<div class='error'>{error_msg}</div>"
                return [], {}, error_html
        
        # Message handler for coaching
        async def handle_seo_coaching(
            msg: str,
            conv_id: str,
            profile: Dict[str, Any]
        ):
            if not msg.strip():
                return "", gr.update()
            
            try:
                response = await langgraph_client.execute_seo_workflow({
                    "conversation_id": conv_id,
                    "user_message": msg,
                    "business_profile": profile,
                    "workflow_mode": "seo_coach"
                })
                
                history = await langgraph_client.get_chat_history(conv_id)
                return "", history
                
            except Exception as e:
                error_msg = format_error_for_mode(e, "seo_coach", "coaching")
                history = await langgraph_client.get_chat_history(conv_id)
                history.append((msg, f"Sorry, {error_msg}"))
                return "", history
        
        # Quick action handlers
        async def quick_seo_check(conv_id: str, profile: Dict[str, Any]):
            msg = get_seo_message("quick_seo_check")
            return await handle_seo_coaching(msg, conv_id, profile)
        
        async def get_keyword_tips(conv_id: str, profile: Dict[str, Any]):
            msg = get_seo_message("keyword_tips", 
                                business_type=profile.get("business_type", "bedrijf"))
            return await handle_seo_coaching(msg, conv_id, profile)
        
        async def get_content_ideas(conv_id: str, profile: Dict[str, Any]):
            msg = get_seo_message("content_ideas",
                                business_type=profile.get("business_type", "bedrijf"))
            return await handle_seo_coaching(msg, conv_id, profile)
        
        # Wire up events
        analyze_btn.click(
            fn=analyze_website,
            inputs=[website_url, business_name, business_type, 
                   location, target_keywords, conversation_id],
            outputs=[chatbot, business_profile, progress_display]
        )
        
        send.click(
            fn=handle_seo_coaching,
            inputs=[message, conversation_id, business_profile],
            outputs=[message, chatbot]
        )
        
        message.submit(
            fn=handle_seo_coaching,
            inputs=[message, conversation_id, business_profile],
            outputs=[message, chatbot]
        )
        
        # Quick actions
        quick_seo_audit.click(
            fn=quick_seo_check,
            inputs=[conversation_id, business_profile],
            outputs=[chatbot]
        )
        
        keyword_help.click(
            fn=get_keyword_tips,
            inputs=[conversation_id, business_profile],
            outputs=[chatbot]
        )
        
        content_ideas.click(
            fn=get_content_ideas,
            inputs=[conversation_id, business_profile],
            outputs=[chatbot]
        )
    
    return interface

def generate_dutch_progress_display(
    profile: Dict[str, Any],
    doc_metadata: Dict[str, Any],
    seo_score: int
) -> str:
    """Generate Dutch progress display for SEO coaching"""
    
    business_name = profile.get("business_name", "Je bedrijf")
    website_url = profile.get("website_url", "")
    
    score_color = "#22c55e" if seo_score >= 70 else "#f59e0b" if seo_score >= 40 else "#ef4444"
    
    return f"""
    <div style='background: #f0fdf4; padding: 20px; border-radius: 12px; border-left: 4px solid {score_color};'>
        <h3 style='margin: 0 0 15px 0; color: #15803d;'>📊 SEO Analyse Resultaat</h3>
        
        <div style='display: grid; gap: 10px; margin-bottom: 15px;'>
            <div><strong>Bedrijf:</strong> {business_name}</div>
            <div><strong>Website:</strong> <a href='{website_url}' target='_blank'>{website_url}</a></div>
            <div><strong>SEO Score:</strong> 
                <span style='color: {score_color}; font-weight: bold; font-size: 1.2em;'>{seo_score}/100</span>
            </div>
        </div>
        
        <div style='background: #e5e7eb; border-radius: 8px; overflow: hidden; margin: 10px 0;'>
            <div style='background: {score_color}; height: 12px; width: {seo_score}%; transition: width 0.5s ease;'></div>
        </div>
        
        <div style='font-size: 0.9em; color: #64748b; margin-top: 15px;'>
            <div style='margin-bottom: 8px;'><strong>✅ Analyse voltooid:</strong></div>
            <div>• Website content gescand</div>
            <div>• SEO-problemen geïdentificeerd</div>
            <div>• Verbeterpunten bepaald</div>
            <div>• Actieplan gegenereerd</div>
        </div>
        
        <div style='margin-top: 15px; padding: 10px; background: rgba(59, 130, 246, 0.1); border-radius: 6px; border-left: 3px solid #3b82f6;'>
            <div style='color: #1e40af; font-weight: 500;'>💡 Volgende stap:</div>
            <div style='color: #64748b; font-size: 0.9em; margin-top: 5px;'>
                Stel vragen over de gevonden verbeterpunten of vraag om een gedetailleerd actieplan.
            </div>
        </div>
    </div>
    """
```

### **Document Processing Components**

```python
# components/document_processor.py
import gradio as gr
from typing import Dict, Tuple, Any
from ..clients.document_client import DocumentProcessingClient

def create_document_upload_panel() -> gr.Column:
    """Create document upload and processing interface"""
    
    with gr.Column() as panel:
        gr.Markdown("#### 📄 Upload Document")
        
        # File upload
        file_upload = gr.File(
            label="Upload File",
            file_types=[".pdf", ".docx", ".txt", ".md"],
            file_count="single"
        )
        
        # URL input
        url_input = gr.Textbox(
            label="Or enter URL",
            placeholder="https://example.com/page"
        )
        
        # Process buttons
        with gr.Row():
            process_file_btn = gr.Button("Process File", variant="secondary", size="sm")
            process_url_btn = gr.Button("Process URL", variant="secondary", size="sm")
        
        # Status display
        doc_status = create_document_status_display()
        
        # Hidden state for current document
        current_doc = gr.State(None)
        
        # Event handlers
        async def handle_file_upload(file, conversation_id):
            if not file:
                return None, "<div class='error'>No file selected</div>"
            
            try:
                doc_client = DocumentProcessingClient()
                result = await doc_client.upload_and_process_file(
                    file_path=file.name,
                    conversation_id=conversation_id
                )
                
                status_html = f"""
                <div class='success'>
                    <strong>✅ File processed:</strong> {result.metadata.source_value}<br>
                    <strong>Type:</strong> {result.metadata.file_type}<br>
                    <strong>Chunks:</strong> {result.metadata.chunk_count}<br>
                    <em>Document context added to conversation</em>
                </div>
                """
                
                return result.metadata, status_html
                
            except Exception as e:
                error_html = f"<div class='error'>❌ Processing failed: {str(e)}</div>"
                return None, error_html
        
        async def handle_url_processing(url, conversation_id):
            if not url.strip():
                return None, "<div class='error'>No URL provided</div>"
            
            try:
                doc_client = DocumentProcessingClient()
                result = await doc_client.process_url_content(
                    url=url,
                    conversation_id=conversation_id
                )
                
                status_html = f"""
                <div class='success'>
                    <strong>✅ URL processed:</strong> <a href='{url}' target='_blank'>{url}</a><br>
                    <strong>Content length:</strong> {len(result.content)} characters<br>
                    <strong>Chunks:</strong> {result.metadata.chunk_count}<br>
                    <em>Web content added to conversation</em>
                </div>
                """
                
                return result.metadata, status_html
                
            except Exception as e:
                error_html = f"<div class='error'>❌ URL processing failed: {str(e)}</div>"
                return None, error_html
        
        # Wire up events - these would connect to the main interface's conversation_id
        # process_file_btn.click(handle_file_upload, [file_upload, conversation_id], [current_doc, doc_status])
        # process_url_btn.click(handle_url_processing, [url_input, conversation_id], [current_doc, doc_status])
    
    return panel

def create_document_status_display() -> gr.HTML:
    """Create HTML component for document status display"""
    return gr.HTML(
        value="<div class='info'>📄 No document loaded</div>",
        label="Document Status"
    )

async def process_uploaded_file(
    file_path: str,
    conversation_id: str
) -> Tuple[Dict[str, Any], str]:
    """Process uploaded file and return metadata and status"""
    # Implementation as shown in handle_file_upload above
    pass

async def process_url_content(
    url: str,
    conversation_id: str
) -> Tuple[Dict[str, Any], str]:
    """Process URL content and return metadata and status"""
    # Implementation as shown in handle_url_processing above
    pass
```

### **MCP Tool Selection Components**

```python
# components/tool_selector.py
import gradio as gr
from typing import List, Dict, Any
from ..clients.mcp_client import MCPToolClient

def create_tool_selection_panel() -> gr.Column:
    """Create MCP tool selection and management interface"""
    
    with gr.Column() as panel:
        gr.Markdown("#### 🔧 MCP Tools")
        
        # Tool discovery and loading
        refresh_tools_btn = gr.Button("🔄 Refresh Tools", size="sm")
        
        # Available tools checklist
        available_tools = gr.CheckboxGroup(
            choices=[],
            label="Available Tools",
            value=[],
            interactive=True
        )
        
        # Tool details display
        tool_details = gr.HTML(
            value="<div class='info'>Select tools to see details</div>",
            label="Tool Information"
        )
        
        # Tool execution area
        gr.Markdown("#### ⚡ Tool Execution")
        
        # Manual tool execution (for advanced users)
        with gr.Accordion("Manual Tool Execution", open=False):
            selected_tool = gr.Dropdown(
                choices=[],
                label="Select Tool",
                interactive=True
            )
            
            tool_params = gr.Code(
                language="json",
                label="Tool Parameters (JSON)",
                value="{}",
                lines=5
            )
            
            execute_tool_btn = gr.Button("Execute Tool", variant="primary")
            
            execution_result = gr.HTML(
                value="<div class='info'>No execution results</div>",
                label="Execution Result"
            )
        
        # Hidden state
        tool_list = gr.State([])
        
        # Event handlers
        async def refresh_available_tools():
            """Refresh list of available MCP tools"""
            try:
                mcp_client = MCPToolClient()
                tools = await mcp_client.discover_available_tools()
                
                tool_choices = [(f"{tool.name} - {tool.description}", tool.name) 
                               for tool in tools]
                tool_names = [tool.name for tool in tools]
                
                return gr.update(choices=tool_choices), gr.update(choices=tool_names), tools
                
            except Exception as e:
                error_html = f"<div class='error'>❌ Failed to load tools: {str(e)}</div>"
                return gr.update(choices=[]), gr.update(choices=[]), []
        
        async def show_tool_details(selected_tools: List[str], tools: List[Dict]):
            """Display details for selected tools"""
            if not selected_tools:
                return "<div class='info'>Select tools to see details</div>"
            
            details_html = "<div class='tool-details'>"
            for tool_name in selected_tools:
                tool = next((t for t in tools if t.name == tool_name), None)
                if tool:
                    details_html += f"""
                    <div style='margin-bottom: 15px; padding: 10px; border: 1px solid #e5e7eb; border-radius: 6px;'>
                        <h4 style='margin: 0 0 5px 0; color: #374151;'>{tool.name}</h4>
                        <p style='margin: 0 0 8px 0; color: #6b7280; font-size: 0.9em;'>{tool.description}</p>
                        <div style='font-size: 0.8em; color: #9ca3af;'>
                            <strong>Parameters:</strong> {', '.join(tool.parameters.keys()) if tool.parameters else 'None'}
                        </div>
                    </div>
                    """
            details_html += "</div>"
            
            return details_html
        
        async def execute_manual_tool(
            tool_name: str,
            params_json: str,
            conversation_id: str
        ):
            """Execute tool manually with provided parameters"""
            if not tool_name:
                return "<div class='error'>❌ No tool selected</div>"
            
            try:
                import json
                params = json.loads(params_json) if params_json.strip() else {}
                
                mcp_client = MCPToolClient()
                result = await mcp_client.execute_tool(
                    tool_name=tool_name,
                    tool_params=params,
                    conversation_id=conversation_id
                )
                
                result_html = f"""
                <div class='success'>
                    <h4 style='margin: 0 0 10px 0;'>✅ Tool Execution Result</h4>
                    <div style='background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace;'>
                        <strong>Tool:</strong> {tool_name}<br>
                        <strong>Status:</strong> {result.status}<br>
                        <strong>Result:</strong><br>
                        <pre style='margin: 5px 0 0 0; white-space: pre-wrap;'>{result.output}</pre>
                    </div>
                </div>
                """
                
                return result_html
                
            except json.JSONDecodeError:
                return "<div class='error'>❌ Invalid JSON in parameters</div>"
            except Exception as e:
                return f"<div class='error'>❌ Execution failed: {str(e)}</div>"
        
        # Wire up events (these would connect to main interface state)
        refresh_tools_btn.click(
            fn=refresh_available_tools,
            outputs=[available_tools, selected_tool, tool_list]
        )
        
        available_tools.change(
            fn=show_tool_details,
            inputs=[available_tools, tool_list],
            outputs=[tool_details]
        )
        
        # execute_tool_btn.click(
        #     fn=execute_manual_tool,
        #     inputs=[selected_tool, tool_params, conversation_id],
        #     outputs=[execution_result]
        # )
    
    return panel

def create_tool_execution_monitor() -> gr.Column:
    """Create tool execution monitoring display"""
    
    with gr.Column() as monitor:
        gr.Markdown("#### 📊 Tool Execution Monitor")
        
        execution_log = gr.HTML(
            value="<div class='info'>No tool executions yet</div>",
            label="Execution Log"
        )
        
        # Real-time execution status
        current_execution = gr.HTML(
            value="<div class='info'>Ready</div>",
            label="Current Status"
        )
    
    return monitor

async def load_available_tools() -> List[Dict[str, Any]]:
    """Load and return available MCP tools"""
    mcp_client = MCPToolClient()
    tools = await mcp_client.discover_available_tools()
    return [tool.dict() for tool in tools]

async def execute_selected_tool(
    tool_name: str,
    tool_params: Dict[str, Any],
    conversation_id: str
) -> Dict[str, Any]:
    """Execute selected tool with parameters"""
    mcp_client = MCPToolClient()
    result = await mcp_client.execute_tool(tool_name, tool_params, conversation_id)
    return result.dict()
```

## Dutch Localization System

```python
# localization/dutch_seo.py
from typing import Dict, Any

SEO_MESSAGES = {
    "welcome_message": """
    <div class='welcome'>
        <h4>👋 Welkom bij je AI SEO Coach!</h4>
        <p>Vul je bedrijfsgegevens in en ik help je stap voor stap je website te verbeteren voor Google.</p>
    </div>
    """,
    
    "chat_placeholder": "👋 Hoi! Ik ben je SEO coach. Analyseer eerst je website, dan kunnen we aan de slag!",
    
    "input_placeholder": "Vraag me alles over SEO, zoekwoorden, content...",
    
    "error_no_url": """
    <div class='error'>
        ❌ Vul eerst je website URL in om te beginnen met de analyse.
    </div>
    """,
    
    "analysis_request": "Ik wil een SEO analyse van mijn {business_type} website: {website_url}. Geef me praktische verbeterpunten die ik zelf kan uitvoeren.",
    
    "analysis_start": "🔍 Welkom {business_name}! Ik ga je website nu grondig analyseren voor SEO-mogelijkheden...",
    
    "quick_seo_check": "Geef me een snelle SEO-check van mijn huidige website. Wat zijn de 3 belangrijkste dingen die ik direct kan verbeteren?",
    
    "keyword_tips": "Help me met het vinden van goede zoekwoorden voor mijn {business_type}. Welke zoekwoorden gebruikt mijn doelgroep?",
    
    "content_ideas": "Geef me 5 concrete content-ideeën voor mijn {business_type} die goed zullen scoren in Google."
}

BUSINESS_TYPES = [
    "Restaurant",
    "Webshop",
    "Dienstverlening",
    "B2B Bedrijf",
    "Freelancer",
    "Zorgverlening",
    "Advocatenkantoor",
    "Accountantskantoor",
    "Bouw & Installatie",
    "Kapper/Schoonheidssalon",
    "Tandartspraktijk",
    "Fysiotherapie",
    "Makelaar",
    "Autogarage",
    "Café/Bar",
    "Hotel/B&B",
    "Webdesign Bureau",
    "Marketing Bureau",
    "IT Bedrijf",
    "Anders"
]

def get_seo_message(key: str, **kwargs) -> str:
    """Get localized SEO message with optional formatting"""
    message = SEO_MESSAGES.get(key, f"Message not found: {key}")
    return message.format(**kwargs)

def get_business_types() -> List[str]:
    """Get list of Dutch business types"""
    return BUSINESS_TYPES

def format_dutch_error(error_type: str, context: str) -> str:
    """Format error messages in Dutch for business users"""
    
    error_messages = {
        "network": "Er ging iets mis met de internetverbinding. Controleer je verbinding en probeer het opnieuw.",
        "timeout": "De website analyse duurt te lang. Dit kan gebeuren bij grote websites. Probeer het later opnieuw.",
        "invalid_url": "De website URL is niet geldig. Controleer of je 'https://' hebt toegevoegd.",
        "access_denied": "Ik kan je website niet bereiken. Controleer of de website online is.",
        "processing": "Er ging iets mis tijdens het verwerken. Probeer het over een paar minuten opnieuw.",
        "general": "Er is een technische fout opgetreden. Ons team is automatisch op de hoogte gebracht."
    }
    
    return error_messages.get(error_type, error_messages["general"])
```

## API Client Implementations

```python
# clients/document_client.py
import httpx
from typing import Dict, Any, Optional
from pydantic import BaseModel
import os

class DocumentMetadata(BaseModel):
    source_type: str
    source_value: str
    file_type: Optional[str] = None
    chunk_count: int
    processed_at: str

class DocumentProcessingResult(BaseModel):
    metadata: DocumentMetadata
    content: str
    chunks: List[str]
    success: bool

class DocumentProcessingClient:
    """Client for document processing API endpoints"""
    
    def __init__(self):
        self.base_url = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
        self.client = httpx.AsyncClient(timeout=60.0)  # Longer timeout for document processing
    
    async def upload_and_process_file(
        self,
        file_path: str,
        conversation_id: str
    ) -> DocumentProcessingResult:
        """Upload and process a file document"""
        
        try:
            with open(file_path, 'rb') as f:
                files = {"file": (os.path.basename(file_path), f)}
                data = {"conversation_id": conversation_id}
                
                response = await self.client.post(
                    f"{self.base_url}/api/v1/documents/upload",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                
                return DocumentProcessingResult(**response.json())
                
        except httpx.HTTPError as e:
            raise Exception(f"Document upload failed: {str(e)}")
    
    async def process_url_content(
        self,
        url: str,
        conversation_id: str
    ) -> DocumentProcessingResult:
        """Process content from URL"""
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/documents/url",
                json={
                    "url": url,
                    "conversation_id": conversation_id
                }
            )
            response.raise_for_status()
            
            return DocumentProcessingResult(**response.json())
            
        except httpx.HTTPError as e:
            raise Exception(f"URL processing failed: {str(e)}")
    
    async def get_document_status(
        self,
        conversation_id: str
    ) -> Optional[DocumentMetadata]:
        """Get current document status for conversation"""
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/conversations/{conversation_id}/document"
            )
            
            if response.status_code == 404:
                return None
                
            response.raise_for_status()
            return DocumentMetadata(**response.json())
            
        except httpx.HTTPError as e:
            raise Exception(f"Document status check failed: {str(e)}")

# clients/mcp_client.py
import httpx
from typing import List, Dict, Any
from pydantic import BaseModel
import os

class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    cost_estimate: Optional[float] = None

class ToolExecutionResult(BaseModel):
    tool_name: str
    status: str
    output: Any
    execution_time: float
    cost: Optional[float] = None

class MCPToolClient:
    """Client for MCP tool management and execution"""
    
    def __init__(self):
        self.base_url = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
        self.client = httpx.AsyncClient(timeout=120.0)  # Longer timeout for tool execution
    
    async def discover_available_tools(self) -> List[ToolInfo]:
        """Discover available MCP tools"""
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/mcp/tools"
            )
            response.raise_for_status()
            
            tools_data = response.json()["tools"]
            return [ToolInfo(**tool) for tool in tools_data]
            
        except httpx.HTTPError as e:
            raise Exception(f"Tool discovery failed: {str(e)}")
    
    async def get_tool_details(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific tool"""
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/mcp/tools/{tool_name}"
            )
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            raise Exception(f"Tool details retrieval failed: {str(e)}")
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        conversation_id: str
    ) -> ToolExecutionResult:
        """Execute MCP tool with parameters"""
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/mcp/tools/{tool_name}/execute",
                json={
                    "parameters": tool_params,
                    "conversation_id": conversation_id
                }
            )
            response.raise_for_status()
            
            return ToolExecutionResult(**response.json())
            
        except httpx.HTTPError as e:
            raise Exception(f"Tool execution failed: {str(e)}")
```

## Comprehensive Testing Strategy

```python
# tests/ui/test_dual_mode_switching.py
import pytest
import os
from agent_workbench.ui.mode_factory import create_interface_for_mode

def test_workbench_mode_creation():
    """Test workbench mode interface creation"""
    os.environ["APP_MODE"] = "workbench"
    
    interface = create_interface_for_mode("workbench")
    
    assert interface is not None
    assert "Agent Workbench" in str(interface.title)

def test_seo_coach_mode_creation():
    """Test SEO coach mode interface creation"""
    os.environ["APP_MODE"] = "seo_coach"
    
    interface = create_interface_for_mode("seo_coach")
    
    assert interface is not None
    assert "SEO Coach" in str(interface.title)

def test_invalid_mode_handling():
    """Test handling of invalid mode configuration"""
    with pytest.raises(ValueError):
        create_interface_for_mode("invalid_mode")

# tests/ui/test_document_processing_ui.py
import pytest
from unittest.mock import patch, MagicMock
from agent_workbench.ui.components.document_processor import (
    process_uploaded_file,
    process_url_content
)

@pytest.mark.asyncio
async def test_file_upload_processing():
    """Test file upload and processing flow"""
    
    with patch('agent_workbench.ui.clients.document_client.DocumentProcessingClient') as mock_client:
        mock_result = MagicMock()
        mock_result.metadata.source_value = "test.pdf"
        mock_result.metadata.chunk_count = 5
        mock_result.success = True
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.upload_and_process_file.return_value = mock_result
        
        metadata, status = await process_uploaded_file("test.pdf", "conv-123")
        
        assert metadata is not None
        assert "✅ File processed" in status
        assert "test.pdf" in status

@pytest.mark.asyncio
async def test_url_content_processing():
    """Test URL content processing flow"""
    
    with patch('agent_workbench.ui.clients.document_client.DocumentProcessingClient') as mock_client:
        mock_result = MagicMock()
        mock_result.metadata.source_value = "https://example.com"
        mock_result.content = "Sample content"
        mock_result.success = True
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.process_url_content.return_value = mock_result
        
        metadata, status = await process_url_content("https://example.com", "conv-123")
        
        assert metadata is not None
        assert "✅ URL processed" in status

# tests/ui/test_seo_coach_flows.py
import pytest
from unittest.mock import patch, MagicMock
from agent_workbench.ui.seo_coach_interface import (
    handle_website_analysis,
    handle_seo_coaching_message
)

@pytest.mark.asyncio
async def test_dutch_website_analysis():
    """Test Dutch SEO website analysis flow"""
    
    with patch('agent_workbench.ui.clients.document_client.DocumentProcessingClient') as mock_doc_client, \
         patch('agent_workbench.ui.components.simple_client.LangGraphClient') as mock_lg_client:
        
        # Mock document processing
        mock_doc_result = MagicMock()
        mock_doc_result.content = "Website content"
        mock_doc_result.metadata.chunk_count = 3
        
        mock_doc_client.return_value.process_url_content.return_value = mock_doc_result
        
        # Mock LangGraph response
        mock_lg_client.return_value.execute_seo_workflow.return_value = {
            "assistant_response": "Je website heeft goede basis-SEO...",
            "seo_score": 75
        }
        
        chat_history, profile, progress = await handle_website_analysis(
            website_url="https://test.nl",
            business_name="Test Restaurant",
            business_type="Restaurant",
            location="Amsterdam",
            keywords="restaurant amsterdam",
            conversation_id="test-conv"
        )
        
        assert len(chat_history) > 0
        assert profile["business_name"] == "Test Restaurant"
        assert "75" in progress  # SEO score in progress display

@pytest.mark.asyncio
async def test_dutch_error_messages():
    """Test Dutch error message formatting"""
    
    with patch('agent_workbench.ui.clients.document_client.DocumentProcessingClient') as mock_client:
        mock_client.return_value.process_url_content.side_effect = Exception("Network error")
        
        chat_history, profile, progress = await handle_website_analysis(
            website_url="https://invalid-url.nl",
            business_name="Test",
            business_type="Restaurant", 
            location="Amsterdam",
            keywords="test",
            conversation_id="test-conv"
        )
        
        assert "❌" in progress
        assert "internetverbinding" in progress or "technische fout" in progress

# tests/ui/test_mobile_responsiveness.py
import pytest
from agent_workbench.ui.components.responsive_layout import (
    create_mobile_optimized_layout,
    adjust_layout_for_screen_size
)

def test_mobile_layout_creation():
    """Test mobile-optimized layout creation"""
    layout = create_mobile_optimized_layout("workbench")
    
    # Test that mobile layout has appropriate structure
    assert layout is not None
    # Additional mobile-specific tests would go here

def test_screen_size_adjustments():
    """Test layout adjustments for different screen sizes"""
    desktop_layout = adjust_layout_for_screen_size("desktop", "workbench")
    mobile_layout = adjust_layout_for_screen_size("mobile", "workbench")
    
    assert desktop_layout != mobile_layout
    # Test specific differences between layouts
```

## Success Criteria for UI-002

### **Phase 3 Success Criteria:**
- [ ] Dual-mode interface switches correctly based on APP_MODE environment variable
- [ ] SEO Coach interface displays correctly in Dutch with business-focused UI
- [ ] Document upload and URL processing integrates with LangGraph context
- [ ] MCP tool selection and execution works with user confirmation
- [ ] Advanced workbench interface provides technical controls
- [ ] Mobile-responsive design works on common screen sizes
- [ ] Error handling provides appropriate feedback for each mode
- [ ] >85% test coverage for new UI components

### **Phase 4 Success Criteria:**
- [ ] End-to-end workflows complete successfully in both modes
- [ ] Performance meets <3 second response targets with documents
- [ ] Tool execution monitoring provides real-time feedback
- [ ] Dutch localization covers all user-facing messages
- [ ] Integration tests pass for all major user flows
- [ ] Documentation covers setup and usage for both modes
- [ ] Deployment works correctly with environment-based mode switching

## Implementation Timeline

- **Week 1**: Mode factory, advanced workbench interface, document processing components
- **Week 2**: SEO coach interface, Dutch localization, MCP tool selection
- **Week 3**: Error handling, responsive design, comprehensive testing
- **Week 4**: Integration testing, performance optimization, documentation

This UI-002 proposal builds directly on the solid foundation of UI-001 while adding the advanced features that make Agent Workbench a complete solution for both technical users and Dutch business owners.