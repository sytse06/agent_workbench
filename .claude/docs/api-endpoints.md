# API Endpoints

## Primary: Full LangGraph Workflow
```
POST   /api/v1/chat/workflow              - Execute full workflow
POST   /api/v1/chat/workflow/stream       - Stream workflow execution
GET    /api/v1/chat/consolidated/state/{id} - Get conversation state
```

## Utility: Minimal Workflow (Testing)
```
POST   /api/v1/chat/simple               - Execute 2-node workflow
POST   /api/v1/chat/test-model            - Test model connectivity
GET    /api/v1/chat/providers             - List available providers
```

## CRUD Operations
```
POST   /api/v1/conversations              - Create conversation
GET    /api/v1/conversations/{id}         - Get conversation
GET    /api/v1/conversations              - List conversations
DELETE /api/v1/conversations/{id}         - Delete conversation

POST   /api/v1/messages                   - Create message
GET    /api/v1/conversations/{id}/messages - Get messages
DELETE /api/v1/messages/{id}              - Delete message

POST   /api/v1/agent-configs              - Create agent config
GET    /api/v1/agent-configs/{id}         - Get agent config
```

## SEO Coach Specific
```
POST   /api/v1/chat/seo/business-profile  - Create business profile
PUT    /api/v1/chat/seo/analysis/{id}     - Update analysis
```
