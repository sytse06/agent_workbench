# Implementation Prompt: UI-003-dual-mode-support

You are implementing **UI-003-dual-mode-support** within strict architectural boundaries.

## Architecture Reference
# UI-003: Dual-Mode Frontend Integration

## Status

**Status**: Ready for Implementation
**Date**: September 22, 2025
**Decision Makers**: Human Architect
**Task ID**: UI-003-dual-mode-support
**Dependencies**: UI-001 (workbench interface), UI-002 (SEO coach interface), LLM-002 (LangGraph state), LLM-001C (consolidated workflow)

## Context

Integrate completed UI-001 workbench interface and UI-002 SEO coach interface into a unified deployment system supporting environment-based mode switching. Leverages the operational LLM-001C consolidated workflow foundation to provide seamless dual-mode operation through a single codebase deployed to different environments.

## Verified Foundation

### **Operational Components (Confirmed Working):**
- **LangGraph Workflows**: Consolidated service with `workflow_mode` routing operational in LLM-001C
- **API Endpoints**: `/api/v1/chat/consolidated` handling dual-mode routing
- **State Management**: `WorkbenchState` with business profile support from LLM-002
- **UI-001 Workbench**: Technical interface using consolidated service endpoints
- **UI-002 SEO Coach**: Dutch business coaching interface with business profile integration

### **What UI-003 Will Deliver:**
- Environment-based mode factory switching between workbench and SEO coach interfaces
- Unified FastAPI integration mounting appropriate Gradio interface based on APP_MODE
- Integration testing ensuring both modes operate independently without interference
- Extension pathways for Phase 2 multi-mode and document processing features

## Architectural Decisions

### **1. Environment-Based Mode Selection**
- **Decision**: Use APP_MODE environment variable to determine which interface to mount
- **Rationale**: Single codebase deployment to different environments, clean separation of concerns
- **Implementation**: Mode factory pattern creates appropriate Gradio interface based on environment

### **2. Unified FastAPI Integration**
- **Decision**: Mount single mode-specific Gradio interface per deployment instance
- **Rationale**: Simplifies deployment, reduces resource usage, clear user experience
- **Implementation**: FastAPI mounts workbench OR seo_coach interface, not both simultaneously

### **3. State Isolation Strategy**
- **Decision**: Each mode operates independently with no shared UI state
- **Rationale**: Prevents cross-mode contamination, simplifies testing, easier maintenance
- **Implementation**: Separate interface instances with isolated Gradio state management

### **4. Extension Pathway Design**
- **Decision**: Registry pattern for Phase 2 extensions (document processing, multi-mode)
- **Rationale**: Maintains clean architecture while enabling future feature addition
- **Implementation**: Extension registry in mode factory with clear Phase 2 placeholders

## Implementation Boundaries

### Files to CREATE:

```
src/agent_workbench/ui/
└── mode_factory.py                     # Environment-based interface factory

tests/ui/
├── test_mode_factory.py               # Mode switching and factory logic tests
├── test_dual_mode_integration.py      # End-to-end dual-mode functionality tests
└── test_extension_pathways.py         # Phase 2 extension point validation tests
```

### Files to MODIFY:

```
src/agent_workbench/main.py             # Add mode factory integration for unified deployment
```

### Technical Implementation Approach

**Mode Factory Integration Pattern**:
- Environment variable-based interface selection via APP_MODE
- Single interface mounted per deployment instance (workbench OR seo_coach)
- Extension registry pattern for Phase 2 features (document processing, multi-mode)
- Direct integration with existing UI-001 and UI-002 interface functions

**Deployment Strategy**:
- Docker containers set APP_MODE environment variable
- Same codebase deployed to different environments with different modes
- Mode information endpoint for monitoring and validation
- Clear separation between Phase 1 and Phase 2 capabilities

## Testing Strategy

### **Unit Tests**
- Mode factory functionality and environment variable handling
- Interface creation logic and error handling for invalid modes
- Extension registry management for Phase 2 features

### **Integration Tests**
- Complete dual-mode deployment with mode switching via APP_MODE
- Workbench mode integration with LLM-001C consolidated service
- SEO coach mode integration with business profile workflow
- Mode isolation verification (no cross-mode state contamination)

### **End-to-End Tests**
- Full workbench workflow with technical parameter control
- Complete SEO coach workflow with Dutch business coaching
- Error recovery scenarios in both modes
- Performance validation under normal production load

## Success Criteria

### **Functional Requirements**
- [ ] Mode factory correctly creates workbench and SEO coach interfaces based on APP_MODE
- [ ] Single interface deployment works correctly in both modes
- [ ] No state contamination between modes when switching deployment environments
- [ ] Mode information endpoint provides accurate deployment information
- [ ] Extension registry supports Phase 2 feature registration

### **Integration Requirements**
- [ ] Workbench mode integrates seamlessly with UI-001 implementation
- [ ] SEO coach mode integrates seamlessly with UI-002 implementation
- [ ] Both modes use LLM-001C consolidated service without conflicts
- [ ] Error handling provides mode-appropriate user feedback
- [ ] No breaking changes to existing UI-001 or UI-002 functionality

### **Deployment Requirements**
- [ ] Docker deployment supports both modes via environment variable
- [ ] Single codebase deployment to different environments works correctly
- [ ] Both modes stable under normal production load
- [ ] Clear documentation for Phase 2 extension integration

## Implementation Scope

### **INCLUDED in UI-003:**
- Mode factory with environment-based interface switching
- Unified FastAPI integration for dual-mode deployment
- Integration testing for both modes using consolidated service
- Extension registry pattern for Phase 2 features
- Mode information endpoint for deployment monitoring

### **EXCLUDED from UI-003:**
- Specific UI component implementations (handled by UI-001 and UI-002)
- Backend API modifications (LLM-001C provides sufficient endpoints)
- Phase 2 feature implementations (document processing, multi-mode, MCP tools)
- Authentication or user management
- Complex state management beyond environment-based mode selection

### **FORBIDDEN Changes:**
- Modifying UI-001 or UI-002 interface implementations
- Adding new LangGraph workflows or state models
- Implementing Phase 2 features beyond extension placeholders
- Changing existing API contracts from LLM-001C
- Complex client abstraction layers beyond mode factory

This aligned UI-003 implementation provides the integration layer between completed UI-001 and UI-002 interfaces while maintaining architectural clarity and preparing for Phase 2 extensions.
## CRITICAL CONSTRAINTS
- **ONLY implement** what's listed in 'What's Included'
- **NEVER implement** what's in 'What's Excluded'
- **Follow exact function signatures** if provided above
- **Create only the files** specified in Implementation Boundaries
- **Include comprehensive tests** for all new functionality

## Scope Violation Detection
If you want to add something not listed in scope, STOP.
Implementation will be validated against these exact boundaries.

## Ready for Implementation
Implement exactly what's specified above. No more, no less.
