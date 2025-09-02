# CORE-002: Database Models & API Foundation

## Status
- **Status**: In Progress
- **Date**: September 02, 2025
- **Decision Makers**: Human Architect
- **Task ID**: CORE-002-database-models-api-foundation

## Context
Establish the foundational data layer for Agent Workbench with SQLAlchemy models, Pydantic schemas, Alembic migrations, and FastAPI router structure. This provides type-safe database operations and API contracts for all future features.

## Architecture Scope

### What's Included:
- [ ] SQLAlchemy async models for conversations, messages, agent_configs tables
- [ ] Pydantic schemas for API request/response validation and serialization
- [ ] Alembic migration scripts for schema versioning and database setup
- [ ] FastAPI router structure with async database sessions
- [ ] Database connection management with proper connection pooling
- [ ] Basic CRUD operations for all core entities
- [ ] Comprehensive error handling for database operations

### What's Explicitly Excluded:
- LLM provider integrations or AI-specific logic
- UI components or Gradio interface code
- Complex business logic beyond basic data operations
- Authentication/authorization systems
- Caching mechanisms (Redis, etc.)
- Vector database integrations
- File storage beyond metadata tracking

## Architectural Decisions

### 1. Database Schema Design

**Core Tables:**
```sql
-- Conversations: Top-level conversation containers
conversations (
    id: UUID PRIMARY KEY,
    user_id: UUID,  -- Future: for multi-user support
    title: VARCHAR(255),
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Messages: Individual messages within conversations  
messages (
    id: UUID PRIMARY KEY,
    conversation_id: UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role: VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'tool', 'system')),
    content: TEXT NOT NULL,
    metadata: JSON,  -- Store model params, tool calls, etc.
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)

-- Agent Configurations: Reusable agent setups
agent_configs (
    id: UUID PRIMARY KEY,
    name: VARCHAR(255) NOT NULL,
    description: TEXT,
    config: JSON NOT NULL,  -- Store model settings, tool selections, etc.
    created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Rationale:**
- UUID primary keys for distributed system compatibility
- JSON metadata fields for flexibility while maintaining structure
- Cascade deletes to maintain referential integrity
- Role constraints to prevent invalid message types

### 2. SQLAlchemy Model Architecture

**Async Architecture:**
- Use SQLAlchemy 2.0+ async syntax
- AsyncSession for all database operations
- Connection pooling with asyncpg for PostgreSQL compatibility

**Model Structure:**
- Base model class with common fields (id, created_at, updated_at)
- Relationship definitions with proper lazy loading
- JSON field handling with proper serialization

### 3. Pydantic Schema Design

**Schema Categories:**
- **Database Models**: Direct SQLAlchemy model representations
- **API Request Models**: Input validation with constraints
- **API Response Models**: Output serialization with computed fields
- **Configuration Models**: Type-safe config handling

**Validation Strategy:**
- Strict type checking with Pydantic v2
- Custom validators for business rules
- Automatic OpenAPI schema generation

### 4. FastAPI Router Structure

**Router Organization:**
- `/api/v1/conversations/` - Conversation CRUD operations
- `/api/v1/messages/` - Message operations within conversations
- `/api/v1/agent-configs/` - Agent configuration management
- `/api/v1/health/` - System health and database connectivity

**Endpoint Design:**
- RESTful conventions with proper HTTP methods
- Consistent error response format
- Request/response validation via Pydantic
- Async request handlers for non-blocking operations

### 5. Database Session Management

**Session Strategy:**
- Dependency injection for database sessions
- Automatic session cleanup via FastAPI dependencies
- Connection pooling for production performance
- Proper transaction handling with rollback on errors

## Implementation Boundaries for AI

### Files to CREATE:
```
src/agent_workbench/models/
├── __init__.py
├── database.py          # SQLAlchemy models and base classes
├── schemas.py           # Pydantic request/response models
└── config.py            # Database configuration models

src/agent_workbench/api/
├── __init__.py
├── database.py          # Session management and dependencies
├── exceptions.py        # API exception classes
└── routes/
    ├── __init__.py
    ├── conversations.py # Conversation CRUD endpoints
    ├── messages.py      # Message CRUD endpoints
    ├── agent_configs.py # Agent config CRUD endpoints
    └── health.py        # Health check endpoints

alembic/versions/
└── 001_initial_schema.py # Initial database schema migration

tests/unit/models/       # Unit tests for models
tests/unit/api/          # Unit tests for API routes
tests/integration/       # Integration tests for database operations
```

### Exact Function Signatures:

**Database Models (database.py):**
```python
class ConversationModel(Base):
    async def create(cls, session: AsyncSession, **kwargs) -> "ConversationModel"
    async def get_by_id(cls, session: AsyncSession, id: UUID) -> Optional["ConversationModel"]
    async def get_by_user(cls, session: AsyncSession, user_id: UUID) -> List["ConversationModel"]
    async def update(self, session: AsyncSession, **kwargs) -> "ConversationModel"
    async def delete(self, session: AsyncSession) -> None

class MessageModel(Base):
    async def create(cls, session: AsyncSession, **kwargs) -> "MessageModel"
    async def get_by_conversation(cls, session: AsyncSession, conversation_id: UUID) -> List["MessageModel"]
    async def get_by_id(cls, session: AsyncSession, id: UUID) -> Optional["MessageModel"]
```

**API Routes:**
```python
# conversations.py
@router.post("/", response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest, session: AsyncSession = Depends(get_session))

@router.get("/{conversation_id}", response_model=ConversationResponse)  
async def get_conversation(conversation_id: UUID, session: AsyncSession = Depends(get_session))

@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(user_id: Optional[UUID] = None, session: AsyncSession = Depends(get_session))
```

**Session Management (database.py):**
```python
async def get_session() -> AsyncGenerator[AsyncSession, None]
async def init_database() -> None
async def close_database() -> None
```

### FORBIDDEN Actions:
- Adding dependencies beyond SQLAlchemy, Alembic, asyncpg, fastapi, pydantic
- Implementing LLM integrations or AI-specific business logic
- Adding authentication or authorization middleware
- Creating UI components or Gradio interface elements  
- Implementing complex business rules beyond basic validation
- Adding external service integrations (Redis, etc.)
- Modifying existing core files beyond necessary imports

### Required Dependencies:
```toml
# Add to pyproject.toml [dependencies]
sqlalchemy = "^2.0.0"
alembic = "^1.12.0" 
asyncpg = "^0.29.0"
fastapi = "^0.104.0"
pydantic = "^2.5.0"
```

## Success Criteria
- [ ] All database models defined with proper async relationships
- [ ] Pydantic schemas provide complete type safety for API contracts
- [ ] Alembic migrations create and version schema successfully
- [ ] FastAPI routes handle all basic CRUD operations with proper validation
- [ ] Database sessions managed properly with dependency injection
- [ ] Comprehensive error handling for all database operations
- [ ] >90% test coverage for all new components
- [ ] No scope creep beyond defined boundaries
- [ ] All endpoints documented in auto-generated OpenAPI schema

## Migration Strategy
- **Initial Migration**: Create all tables with proper constraints and indexes
- **Version Control**: Each schema change requires new Alembic migration
- **Rollback Support**: All migrations must be reversible
- **Development**: Use SQLite for development, PostgreSQL for production

## Error Handling Strategy
- **Database Errors**: Catch SQLAlchemy exceptions and convert to HTTP errors
- **Validation Errors**: Let Pydantic handle request validation automatically
- **Not Found**: Return 404 for missing resources with clear error messages
- **Constraint Violations**: Return 400 with specific constraint error details

## Performance Considerations
- **Connection Pooling**: Configure appropriate pool size for expected load
- **Lazy Loading**: Use appropriate relationship loading strategies
- **Indexing**: Add indexes on frequently queried columns (conversation_id, user_id)
- **Query Optimization**: Use async sessions to prevent blocking operations

## Testing Strategy
- **Unit Tests**: Test each model method and API endpoint independently
- **Integration Tests**: Test full database operations with real database
- **Schema Tests**: Verify Alembic migrations work correctly up and down
- **API Tests**: Test all endpoints with various input scenarios

## Consequences

**Positive:**
- Solid foundation for all future features
- Type safety across entire data layer
- Scalable database architecture
- Clear separation of concerns between data and business logic

**Risks:**
- Over-engineering for current simple requirements
- JSON fields may need restructuring as requirements evolve
- Migration complexity may increase with schema changes

**Dependencies Created:**
- All future features depend on these models and schemas
- API contract changes require careful versioning
- Database schema changes require migration planning

## Next Phase Dependencies
- **LLM-001**: Will use ConversationModel and MessageModel for chat persistence
- **UI-001**: Will consume these API endpoints for data operations
- **DOC-001**: Will extend MessageModel.metadata for document references