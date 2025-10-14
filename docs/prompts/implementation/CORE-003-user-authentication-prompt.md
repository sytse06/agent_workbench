# Implementation Prompt: CORE-003-user-authentication

You are implementing **CORE-003-user-authentication** within strict architectural boundaries.

## Architecture Reference
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

### 1. Provider-Agnostic Authentication Strategy

**Design Philosophy**: Build authentication layer that supports multiple providers without schema migration

**Core Approach**: Generic user fields + provider-specific data in JSON

```python
# UserModel - Provider-agnostic design
class UserModel(Base):
    # Generic fields (work with any auth provider)
    username: Mapped[str]              # Provider username
    email: Mapped[Optional[str]]       # User email (if available)
    auth_provider: Mapped[str]         # "huggingface", "google", "github", etc.

    # Provider-specific data (flexible JSON storage)
    provider_data: Mapped[Optional[JSON]]  # HF: {hf_user_id, hf_avatar_url, ...}
```

**Initial Implementation: HuggingFace OAuth**

Use Gradio's built-in HF authentication via `auth="huggingface"`:

```python
# Gradio app configuration
app = gr.Blocks()
app.launch(auth="huggingface")  # Enables HF OAuth

# Access authenticated user in handlers
async def on_load(request: gr.Request):
    username = request.username  # HF username from OAuth
    user = await auth_service.get_or_create_user_from_request(
        request=request,
        provider="huggingface"
    )
```

**Future Provider Support**: Adding new providers requires:
1. Update AuthService with provider-specific extraction logic
2. No database schema changes
3. No data migration needed

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
    """Handle multi-provider OAuth and session management."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def get_or_create_user_from_request(
        self,
        request: Request,
        provider: str = "huggingface"
    ) -> UserModel:
        """
        Get or create user from Gradio request.

        Args:
            request: Gradio request object with authenticated user info
            provider: Authentication provider name ("huggingface", "google", etc.)

        Returns:
            UserModel with populated generic and provider-specific fields

        Implementation:
            - Extract username from request.username
            - Extract provider-specific data into provider_data JSON
            - Populate generic fields (username, email, avatar_url)
            - Create or update user record
        """
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
    # User methods (provider-agnostic)
    def get_user_by_username(self, username: str) -> Optional[UserModel]: ...
    def get_user_by_email(self, email: str, provider: str) -> Optional[UserModel]: ...
    def create_user(
        self,
        username: str,
        auth_provider: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider_data: Optional[dict] = None
    ) -> UserModel: ...
    def update_user_last_login(self, user_id: UUID) -> None: ...
    def update_user_provider_data(self, user_id: UUID, provider_data: dict) -> None: ...

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

    # Generic authentication fields (provider-agnostic)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(index=True)
    avatar_url: Mapped[Optional[str]]
    auth_provider: Mapped[str] = mapped_column(default="huggingface", index=True)

    # Provider-specific data (flexible JSON storage)
    # HuggingFace: {"hf_user_id": "...", "hf_avatar_url": "...", ...}
    # Google: {"google_id": "...", "picture": "...", ...}
    # GitHub: {"github_id": "...", "login": "...", ...}
    provider_data: Mapped[Optional[JSON]]

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

# User lookup by username (provider-agnostic)
Index('idx_users_username',
      UserModel.username)

# User lookup by provider + email (for multi-provider support)
Index('idx_users_provider_email',
      UserModel.auth_provider,
      UserModel.email)

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
INSERT INTO users (
    id,
    username,
    auth_provider,
    provider_data
)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system',
    'internal',
    '{"internal_user": true}'
);

-- Link existing conversations to system user
UPDATE conversations SET user_id = '00000000-0000-0000-0000-000000000000'
WHERE user_id IS NULL;

-- Make user_id NOT NULL after migration
ALTER TABLE conversations ALTER COLUMN user_id SET NOT NULL;
```

### Future: Adding New Authentication Provider

**Scenario**: You want to add Google OAuth or GitHub OAuth in the future.

**Required Changes** (no database migration needed):

1. **Add provider-specific extraction logic** in `AuthService`:

```python
# services/auth_service.py

async def get_or_create_user_from_request(
    self,
    request: Request,
    provider: str = "huggingface"
) -> UserModel:
    """Extract user info from request based on provider."""

    if provider == "huggingface":
        username = request.username
        # Extract HF-specific data
        provider_data = {
            "hf_user_id": request.user_id,  # if available
            "hf_avatar": request.avatar_url  # if available
        }

    elif provider == "google":
        # Extract from Google OAuth token
        username = request.username
        email = request.email
        provider_data = {
            "google_id": request.sub,
            "picture": request.picture
        }

    elif provider == "github":
        # Extract from GitHub OAuth token
        username = request.username
        email = request.email
        provider_data = {
            "github_id": request.id,
            "github_login": request.login
        }

    # Create or update user with generic fields
    user = await self.db.get_user_by_username(username)
    if not user:
        user = await self.db.create_user(
            username=username,
            email=email,
            auth_provider=provider,
            provider_data=provider_data
        )

    return user
```

2. **Update Gradio configuration** in `main.py`:

```python
# For Google OAuth (if Gradio supports it in the future)
app.launch(auth="google")

# Or use custom OAuth handler
app.launch(auth_callback=custom_oauth_handler)
```

3. **No database changes needed** - all new data fits into existing schema

**Benefits of Provider-Agnostic Design**:
- ✅ No schema migration when adding providers
- ✅ Users from different providers coexist in same table
- ✅ Generic fields (username, email) work across all providers
- ✅ Provider-specific data isolated in JSON field
- ✅ Easy to query users by provider: `WHERE auth_provider = 'google'`

## Notes

- **Session Timeout**: 30 minutes is configurable via environment variable
- **Request Metadata**: Extract IP, user agent, referrer from Gradio Request
- **Privacy**: HF OAuth only provides username, not email (requires additional API call)
- **Gradio Pattern**: `request.username` is the standard way to access authenticated user
- **Provider-Agnostic Design**: Architecture supports multiple auth providers without schema changes
- **Future-Proof**: Adding new providers requires only service layer changes, no database migration

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
