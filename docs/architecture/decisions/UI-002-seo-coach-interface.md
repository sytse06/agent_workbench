# UI-002: SEO Coach Interface (Aligned Implementation)

## Status

**Status**: Implementation Ready - Foundation Verified & Aligned  
**Date**: September 21, 2025  
**Decision Makers**: Human Architect  
**Task ID**: UI-002-seo-coach-interface  
**Dependencies**: UI-001 Enhanced (operational), LLM-001C (consolidated service operational), Phase 1A complete

## Context

Implement SEO Coach interface leveraging the proven consolidated service foundation with simplified client architecture and aligned file structure. With LangGraph workflows, dual-mode routing, and `WorkbenchState` management already operational, UI-002 focuses on creating the Dutch business coaching interface using direct httpx integration and following established UI patterns.

## Verified Foundation

### **Operational Components (Confirmed Working):**
- **LangGraph Workflows**: Consolidated service with `workflow_mode="seo_coach"` operational
- **API Endpoints**: `/api/v1/chat/consolidated` handling dual-mode routing
- **State Management**: `WorkbenchState` with business profile support
- **UI-001 Enhanced**: Verified workbench interface using consolidated service
- **Error Handling**: Mode-aware responses with proper fallbacks

### **What UI-002 Will Implement:**
- **Mode Factory**: Environment-based interface switching (APP_MODE)
- **SEO Coach Interface**: Dutch business coaching UI with simplified client
- **Business Profile Forms**: Direct integration with `WorkbenchState.business_profile`
- **Streamlined Integration**: Direct httpx calls, minimal abstraction layers

## Implementation Boundaries

### Files to CREATE:

```
src/agent_workbench/ui/
├── mode_factory.py                     # Mode-based interface factory
├── seo_coach_app.py                    # Dutch SEO coaching interface
└── components/
    ├── business_profile_form.py        # Business profile creation forms
    └── dutch_messages.py               # Basic Dutch localization

tests/ui/
├── test_mode_factory.py               # Mode switching tests
├── test_seo_coach_interface.py        # SEO coach functionality tests  
└── test_seo_coach_integration.py      # End-to-end integration tests
```

### Files to MODIFY:

```
src/agent_workbench/main.py             # Add mode factory integration
```

## Architectural Decisions

### **1. Simplified Client Architecture**
- **Decision**: Use direct httpx calls in Gradio event handlers instead of complex client abstraction
- **Rationale**: Reduces complexity, follows UI-001 Enhanced patterns, easier maintenance
- **Implementation**: Direct async httpx.AsyncClient() calls in handler functions

### **2. Mode Factory Pattern**
- **Decision**: Environment variable-based interface switching via APP_MODE
- **Rationale**: Single codebase deployment to different environments, clear separation
- **Implementation**: Factory function creates appropriate Gradio interface based on mode

### **3. Business Profile Integration**
- **Decision**: Store business profiles in `WorkbenchState.business_profile` via consolidated service
- **Rationale**: Leverages existing state management, consistent with LangGraph patterns
- **Implementation**: Pass business_profile in consolidated service requests

### **4. Dutch Localization Strategy**
- **Decision**: Separate dutch_messages.py component with message formatting
- **Rationale**: Clean separation of concerns, easy to extend for other languages
- **Implementation**: Message keys with parameter substitution

### **5. Phase 2 Feature Stubs**
- **Decision**: Visible but disabled components with clear "Phase 2" messaging
- **Rationale**: Shows roadmap without implementing functionality, prevents scope creep
- **Implementation**: Disabled Gradio components with explanatory text

## Technical Implementation Approach

### **Gradio Interface Structure**
```
SEO Coach App:
├── Left Panel: Business Profile Setup
│   ├── Business profile form (name, type, URL, location)
│   ├── Website analysis button
│   ├── Status display
│   └── Phase 2 stubs (document upload, tools)
└── Right Panel: Coaching Chat
    ├── Chat history display
    ├── Message input
    └── Quick action buttons (SEO check, keywords, content, local)
```

### **API Integration Pattern**
```python
# Direct httpx integration (simplified from amendments)
async def handle_coaching_message(msg, conv_id, profile):
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/api/v1/chat/consolidated",
            json={
                "user_message": msg,
                "conversation_id": conv_id,
                "workflow_mode": "seo_coach",
                "business_profile": profile,
                "model_config": {...}
            }
        )
```

### **Error Handling Strategy**
- **Network Errors**: Timeout handling with Dutch user-friendly messages
- **Validation Errors**: Business profile validation before API calls
- **API Errors**: Status code handling with appropriate Dutch responses
- **State Errors**: Graceful fallback when conversation state unavailable

### **State Management Pattern**
```python
# Minimal state following UI-001 patterns
conversation_id = gr.State(str(uuid.uuid4()))
business_profile = gr.State({})  # Stored via consolidated service
```

## Success Criteria

### **Functional Requirements**
- [ ] Mode factory correctly switches between workbench and SEO coach based on APP_MODE
- [ ] SEO coach interface loads and displays correctly in Dutch
- [ ] Business profile form integrates with consolidated service
- [ ] Website analysis triggers appropriate Dutch coaching responses  
- [ ] Conversation history persists correctly across interactions
- [ ] Quick action buttons provide immediate SEO value
- [ ] Phase 2 stubs clearly communicate future roadmap

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
- [ ] Clear separation between Phase 1 and Phase 2 features

## Implementation Scope

### **INCLUDED in UI-002:**
- Mode factory with environment-based switching
- Complete SEO coach Gradio interface
- Business profile form with validation
- Direct httpx integration with consolidated service
- Dutch localization for coaching workflow
- Quick action buttons for common SEO tasks
- Phase 2 feature stubs (visible but disabled)

### **EXCLUDED from UI-002:**
- Document processing functionality (Phase 2)
- MCP tool integration (Phase 2)
- Advanced SEO analytics (Phase 2)
- Multi-language support beyond Dutch (Phase 2)
- Complex client abstraction layers
- Backend API modifications (existing endpoints sufficient)

### **FORBIDDEN Changes:**
- Modifying consolidated service API contracts
- Adding new dependencies beyond httpx
- Implementing Phase 2 features
- Complex state management beyond Gradio State
- Authentication or user management

## Testing Strategy

### **Unit Tests**
- Mode factory functionality and validation
- Business profile form validation logic
- Dutch message formatting and localization
- Error handling scenarios

### **Integration Tests**
- Complete SEO coach workflow with consolidated service
- Mode switching between workbench and SEO coach
- Business profile persistence via LangGraph state
- Dutch coaching conversation flow

### **End-to-End Tests**
- Full website analysis workflow
- Quick action button functionality
- Error recovery scenarios
- Performance under normal load

This aligned UI-002 implementation leverages the verified consolidated service foundation while delivering the complete dual-mode system for Phase 1 deployment using simplified architecture and direct integration patterns.