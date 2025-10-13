# CORE-001: User Authentication & Settings

## Status

**Status**: Ready for Implementation
**Date**: October 13, 2025
**Decision Makers**: Human Architect
**Task ID**: CORE-001-user-authentication
**Dependencies**: Phase 1 (Database, Conversations)
**Phase**: 2.0

## Context

Implement user authentication and per-user settings management as the foundation for all Phase 2 features. This enables user-specific conversations, personalized agent behavior, usage tracking, and session management. Uses HuggingFace OAuth for seamless integration with HF Spaces deployment.

**Why First?**
- All Phase 2 features require user context
- Per-user conversation isolation
- User-specific settings (model preferences, UI state)
- Usage analytics per user
- Session tracking for billing/monitoring

## Architecture Scope

### What's Included:

- User model with HuggingFace OAuth integration
- User settings (key-value store for flexibility)
- User session tracking with activity logging
- Session reuse logic (30-minute timeout)
- AuthService with Gradio Request pattern
- Database backend methods for users/sessions
- Comprehensive database indexing

### What's Explicitly Excluded:

- Custom authentication system (use HF OAuth only)
- User registration UI (HF handles this)
- Password management (OAuth flow)
- Role-based access control (RBAC)
- Multi-tenancy or organizations
- Payment/billing integration
- Email notifications

## Architectural Decisions

### 1. HuggingFace OAuth Strategy

**Core Approach**: Use Gradio's built-in HF authentication via `auth="huggingface"`

```python
# Gradio app configuration
app = gr.Blocks()
app.launch(auth="huggingface")  # Enables HF OAuth

# Access authenticated user in handlers
async def on_load(request: gr.Request):
    username = request.username  # HF username from OAuth
    # Create/load user from username
```

**Pattern**: Extract username from `request.username` (provided by Gradio after HF OAuth)

### 2. Session Management Pattern

**Session Reuse Logic** (prevents database pollution):

```python
async def on_load(request: Request):
    """Initialize user session on app load."""

    # Get or create user
    user = await auth_service.get_or_create_user_from_request(request)

    # Check for active session (within last 30 min)
    active_session = await auth_service.get_active_session(
        user_id=user.id,
        max_age_minutes=30
    )

    if active_session:
        # Reuse existing session
        session = active_session
        await auth_service.update_session_activity(session.id)
    else:
        # Create new session
        session = await auth_service.create_session(
            user_id=user.id,
            request=request
        )

    return welcome_message, user, session.id
```

### 3. User Settings Architecture

**Key-Value Store** for flexibility without schema changes:

```python
class UserSettingModel(Base):
    """Flexible user settings storage."""
    user_id: UUID
    setting_key: str        # "preferred_model", "ui_theme", etc.
    setting_value: JSON     # Flexible JSON value
    setting_type: str       # "active" (user-set) or "passive" (system-learned)
    category: str           # "ui", "agent", "workflow"
```

**Benefits**:
- No schema migration when adding new settings
- Supports complex nested values (JSON)
- Distinguish user preferences from learned behavior

### 4. Database Schema Extensions

**New Models**:
```python
# UserModel - HF OAuth account
# UserSettingModel - Flexible key-value settings
# UserSessionModel - Session tracking with activity
# SessionActivityModel - Granular activity logging
```

**Updated Models**:
```python
# ConversationModel - Add user_id foreign key
# MessageModel - Unchanged (linked via conversation)
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/models/
├── database.py             # Add UserModel, UserSettingModel, UserSessionModel

src/agent_workbench/services/
├── auth_service.py         # AuthService with HF OAuth
└── user_settings_service.py # Settings CRUD operations

src/agent_workbench/database/backends/
├── sqlite.py               # Add user/session methods
└── hub.py                  # Add user/session methods (HF Spaces)

src/agent_workbench/api/routes/
└── users.py                # User management endpoints (optional)
```

### Files to MODIFY:

```
src/agent_workbench/models/database.py          # Add user foreign keys to ConversationModel
src/agent_workbench/database/adapter.py         # Add user/session methods to protocol
src/agent_workbench/ui/app.py                   # Add on_load with auth
src/agent_workbench/ui/seo_coach_app.py         # Add on_load with auth
src/agent_workbench/main.py                     # Configure auth="huggingface"
```

### Exact Function Signatures:

```python
# CREATE: services/auth_service.py
class AuthService:
    """Handle HuggingFace OAuth and session management."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def get_or_create_user_from_request(self, request: Request) -> UserModel:
        """Get or create user from Gradio request."""
        pass

    async def get_active_session(
        self,
        user_id: UUID,
        max_age_minutes: int = 30
    ) -> Optional[UserSessionModel]:
        """Get active session within timeout window."""
        pass

    async def update_session_activity(self, session_id: UUID) -> None:
        """Update session last_activity timestamp."""
        pass

    async def create_session(
        self,
        user_id: UUID,
        request: Request
    ) -> UserSessionModel:
        """Create new user session."""
        pass

    async def log_session_activity(
        self,
        session_id: UUID,
        user_id: UUID,
        action: str,
        metadata: Optional[dict] = None
    ) -> None:
        """Log activity within session."""
        pass

    async def end_session(self, session_id: UUID) -> None:
        """Mark session as ended."""
        pass

# CREATE: services/user_settings_service.py
class UserSettingsService:
    """Manage user settings."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def get_setting(
        self,
        user_id: UUID,
        setting_key: str,
        default: Any = None
    ) -> Any:
        """Get user setting value."""
        pass

    async def set_setting(
        self,
        user_id: UUID,
        setting_key: str,
        setting_value: Any,
        category: str = "general",
        setting_type: Literal["active", "passive"] = "active"
    ) -> None:
        """Save user setting."""
        pass

    async def get_settings_by_category(
        self,
        user_id: UUID,
        category: str
    ) -> Dict[str, Any]:
        """Get all settings in category."""
        pass

    async def delete_setting(
        self,
        user_id: UUID,
        setting_key: str
    ) -> bool:
        """Delete user setting."""
        pass

# Database backend methods (ADD to protocol)
class DatabaseBackend(Protocol):
    # User methods
    def get_user_by_hf_username(self, hf_username: str) -> Optional[UserModel]: ...
    def get_user_by_hf_id(self, hf_user_id: str) -> Optional[UserModel]: ...
    def create_user(self, **kwargs) -> UserModel: ...
    def update_user_last_login(self, user_id: UUID) -> None: ...

    # Session methods
    def create_user_session(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> UserSessionModel: ...

    def get_active_user_session(
        self,
        user_id: UUID,
        since: datetime
    ) -> Optional[UserSessionModel]: ...

    def update_session_activity(self, session_id: UUID) -> None: ...
    def increment_session_messages(self, session_id: UUID) -> None: ...
    def increment_session_tool_calls(self, session_id: UUID) -> None: ...
    def create_session_activity(
        self,
        session_id: UUID,
        user_id: UUID,
        action: str,
        metadata: Optional[dict] = None
    ) -> None: ...

    # Settings methods
    def get_user_settings(self, user_id: UUID) -> list[UserSettingModel]: ...
    def get_user_setting(
        self,
        user_id: UUID,
        setting_key: str
    ) -> Optional[UserSettingModel]: ...
    def create_user_setting(
        self,
        user_id: UUID,
        **kwargs
    ) -> UserSettingModel: ...
    def update_user_setting(
        self,
        user_id: UUID,
        setting_key: str,
        setting_value: Dict[str, Any]
    ) -> None: ...

# Database models
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # HuggingFace OAuth data
    hf_username: Mapped[str] = mapped_column(unique=True, index=True)
    hf_user_id: Mapped[str] = mapped_column(unique=True)
    hf_email: Mapped[Optional[str]]
    hf_avatar_url: Mapped[Optional[str]]

    # Account metadata
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_login: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    conversations: Mapped[list["ConversationModel"]] = relationship(back_populates="user")
    settings: Mapped[list["UserSettingModel"]] = relationship(back_populates="user")
    sessions: Mapped[list["UserSessionModel"]] = relationship(back_populates="user")

class UserSettingModel(Base):
    __tablename__ = "user_settings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    setting_key: Mapped[str] = mapped_column(index=True)
    setting_value: Mapped[JSON]
    setting_type: Mapped[str]  # "active" or "passive"

    category: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["UserModel"] = relationship(back_populates="settings")

class UserSessionModel(Base):
    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    # Session tracking
    session_start: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    session_end: Mapped[Optional[datetime]]
    last_activity: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Request metadata
    ip_address: Mapped[Optional[str]]
    user_agent: Mapped[Optional[str]]
    referrer: Mapped[Optional[str]]

    # Activity tracking
    total_messages: Mapped[int] = mapped_column(default=0)
    total_tool_calls: Mapped[int] = mapped_column(default=0)

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="sessions")
    activities: Mapped[list["SessionActivityModel"]] = relationship(back_populates="session")

class SessionActivityModel(Base):
    __tablename__ = "session_activities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("user_sessions.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    action: Mapped[str]  # "message_sent", "tool_called", "settings_updated"
    metadata: Mapped[Optional[JSON]]

    session: Mapped["UserSessionModel"] = relationship(back_populates="activities")
```

### Database Indexes:

```python
# Session reuse query optimization
Index('idx_session_user_activity',
      UserSessionModel.user_id,
      UserSessionModel.last_activity)

# User lookup by HF username
Index('idx_users_hf_username',
      UserModel.hf_username)

# Settings lookup
Index('idx_user_settings_key',
      UserSettingModel.user_id,
      UserSettingModel.setting_key)
```

### Additional Dependencies:

```toml
# No new dependencies - uses existing stack
# Gradio built-in OAuth
# SQLAlchemy for models
# Existing database backends
```

### FORBIDDEN Actions:

- Implementing custom OAuth flow (use Gradio's HF OAuth only)
- Creating user registration forms
- Password storage or management
- Role-based access control
- Multi-tenancy features
- Payment/subscription handling
- Custom authentication backends

## Testing Strategy

### Integration Tests (Priority: HIGH)

```python
# tests/integration/test_auth_flow.py

async def test_user_authentication_flow():
    """Test complete HF OAuth flow."""
    # Mock Gradio Request with username
    # Call get_or_create_user_from_request
    # Verify user created in DB
    # Verify last_login updated on second call

async def test_session_reuse_prevents_pollution():
    """Test session reuse logic (30min timeout)."""
    # Create user
    # Create session
    # Simulate page refresh within 30min
    # Verify same session returned
    # Verify last_activity updated
    # Simulate page refresh after 30min
    # Verify new session created

async def test_user_settings_persistence():
    """Test settings CRUD operations."""
    # Create user
    # Save setting (active)
    # Load setting
    # Update setting
    # Verify persistence across sessions
```

### Database Tests (Priority: MEDIUM)

```python
# tests/unit/database/test_user_models.py

def test_get_active_user_session_uses_index():
    """Verify idx_session_user_activity used."""
    # Use SQLAlchemy EXPLAIN to verify index usage

def test_session_activity_update():
    """Test update_session_activity method."""
    # Create session
    # Update activity
    # Verify timestamp changed
```

**Test Count**: ~8 tests
**Coverage Goal**: 80% (critical authentication path)

## Success Criteria

- [ ] **HF OAuth Integration**: Users authenticate via HuggingFace
- [ ] **User Creation**: Users auto-created on first login
- [ ] **Session Management**: Sessions reused within 30-minute window
- [ ] **Session Tracking**: Activity logged with timestamps
- [ ] **Settings Persistence**: User settings saved and loaded correctly
- [ ] **Database Indexes**: Query performance optimized
- [ ] **Conversation Linking**: Conversations linked to users
- [ ] **No Session Pollution**: Database doesn't accumulate duplicate sessions
- [ ] **>80% test coverage** for authentication flow
- [ ] **Migration script** to add user_id to existing conversations
- [ ] **Both modes work**: Workbench and SEO Coach with authentication

## Migration Path

### From Phase 1 (No Authentication)

```sql
-- Add user_id to conversations
ALTER TABLE conversations ADD COLUMN user_id UUID REFERENCES users(id);

-- Create default/system user for existing conversations
INSERT INTO users (id, hf_username, hf_user_id)
VALUES ('00000000-0000-0000-0000-000000000000', 'system', 'system');

-- Link existing conversations to system user
UPDATE conversations SET user_id = '00000000-0000-0000-0000-000000000000'
WHERE user_id IS NULL;

-- Make user_id NOT NULL after migration
ALTER TABLE conversations ALTER COLUMN user_id SET NOT NULL;
```

## Notes

- **Session Timeout**: 30 minutes is configurable via environment variable
- **Request Metadata**: Extract IP, user agent, referrer from Gradio Request
- **Privacy**: HF OAuth only provides username, not email (requires additional API call)
- **Gradio Pattern**: `request.username` is the standard way to access authenticated user
