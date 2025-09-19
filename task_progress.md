# Task Progress: UI-001-gradio-frontend-integration Test Fix

## TODO List - Based on Architecture Document

### Phase 1: LangGraph-First Foundation
- [x] Review architecture document for exact requirements  
- [ ] Fix FastAPI routes according to architecture specs
- [ ] Implement proper response format (reply field)
- [ ] Fix test expectations to match architecture
- [ ] Ensure API routes through LangGraph workflows
- [ ] Run validation command to verify fixes
- [ ] Run full test suite to ensure no regressions

## Architecture Requirements from Document

### API Route Structure:
- `/api/v1/chat/message` - Send message through LangGraph 
- `/api/v1/conversations/{conversation_id}/messages` - Get history from LangGraph

### Response Format:
- ChatResponse with "reply" field (NOT "content")
- Should route through LangGraph workflows
- Tests expect "reply" and "conversation_id" fields

### Key Issues to Fix:
1. API endpoints returning 404 (routing issues)
2. Response format mismatch (content vs reply) 
3. Tests not properly mocking async responses
4. Missing LangGraph workflow integration
