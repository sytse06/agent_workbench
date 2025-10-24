# UI-004: Authentication Behavior & Implementation Strategy

## Status

**Status**: Architecture Complete
**Date**: October 20, 2025
**Parent Task**: UI-004-pwa-app-user-settings
**Phase**: 2.1
**Dependencies**: Phase 2.0 authentication foundation (feature/CORE-003-user-authentication)

## Context

This document clarifies the authentication behavior for the Agent Workbench PWA, resolving the apparent conflict between the architecture document's "login-first" pattern and the UX design's "login-in-settings" pattern.

**Key Realization**: The application supports **optional authentication with feature-gated access**, not mandatory login-before-use.

## Architectural Decisions

### 1. Authentication Requirement Level: Optional with Reduced Features

**Decision**: Authentication is **OPTIONAL** with a freemium model.

**Rationale**:
- **Lower barrier to entry**: Users can try the app immediately without creating an account
- **Freemium business model**: Free tier has token limits, paid features require authentication
- **Progressive engagement**: Users naturally upgrade when they hit limitations

**Access Levels**:

| Feature | Unauthenticated | Authenticated (Free) | Authenticated (Pro) |
|---------|-----------------|---------------------|---------------------|
| **Chat Access** | ✅ Limited | ✅ Standard | ✅ Unlimited |
| **Token Limit** | 10 messages/day | 100 messages/day | Unlimited |
| **Model Selection** | Basic models only | All open-source models | All models + premium |
| **Conversation History** | ❌ None (lost on refresh) | ✅ Saved | ✅ Saved |
| **Settings Persistence** | ❌ None | ✅ Saved | ✅ Saved |
| **File Upload** | ❌ Disabled | ✅ Limited (5MB) | ✅ Unlimited |
| **Web Search** | ❌ Disabled | ✅ Limited | ✅ Unlimited |
| **MCP Tools** | ❌ Disabled | ❌ Disabled | ✅ Enabled |
| **Priority Support** | ❌ None | ❌ None | ✅ Yes |

**Implementation**:
```python
async def check_auth_and_limits(request: gr.Request) -> dict:
    """Check authentication status and feature access."""

    # Try to get authenticated user
    user = await get_user_from_request(request)

    if not user:
        # Unauthenticated user
        return {
            "authenticated": False,
            "tier": "free_anonymous",
            "daily_message_limit": 10,
            "messages_used_today": get_anon_message_count(request.client.host),
            "available_models": ["gpt-3.5-turbo", "llama-3-8b"],
            "features": {
                "conversation_history": False,
                "file_upload": False,
                "web_search": False,
                "mcp_tools": False
            }
        }

    # Check user's subscription tier
    subscription = await get_user_subscription(user["id"])

    if subscription["tier"] == "pro":
        return {
            "authenticated": True,
            "user_id": user["id"],
            "tier": "pro",
            "daily_message_limit": None,  # Unlimited
            "available_models": get_all_models(),
            "features": {
                "conversation_history": True,
                "file_upload": True,
                "web_search": True,
                "mcp_tools": True
            }
        }
    else:
        # Free authenticated user
        return {
            "authenticated": True,
            "user_id": user["id"],
            "tier": "free",
            "daily_message_limit": 100,
            "messages_used_today": await get_user_message_count_today(user["id"]),
            "available_models": get_free_models(),
            "features": {
                "conversation_history": True,
                "file_upload": True,  # Limited
                "web_search": True,   # Limited
                "mcp_tools": False
            }
        }
```

### 2. Login UI Location: Settings Page with Upgrade Prompts

**Decision**: Primary login/register UI is located in the **Settings page**, with **upgrade prompts** in the chat interface when users hit limits.

**UX Flow**:

**First Visit (Unauthenticated)**:
```
User visits app (/)
    ↓
Chat interface loads immediately (NO login gate)
    ↓
Banner at top: "Limited to 10 messages/day. Sign in for 100 messages/day."
    ↓
User can chat with basic models (token limit tracked by IP)
    ↓
After 10 messages: "Daily limit reached. Sign in to continue with 100 free messages/day."
    ↓
User clicks "Sign In" → Redirected to /settings
```

**Settings Page (Unauthenticated)**:
```
/settings page loads
    ↓
Top section shows:
    ┌─────────────────────────────────────────────┐
    │ 👤 Not signed in                            │
    │                                             │
    │ [Sign In] [Create Account]                  │
    │                                             │
    │ Create an account to:                       │
    │ • Save conversation history                 │
    │ • Get 100 free messages/day                 │
    │ • Access advanced models                    │
    └─────────────────────────────────────────────┘
    ↓
User clicks "Sign In" → OAuth flow or custom login form
    ↓
After authentication → Settings page refreshes
```

**Settings Page (Authenticated)**:
```
/settings page loads
    ↓
Top section shows:
    ┌─────────────────────────────────────────────┐
    │ 👤 sytse                                    │
    │    sytse@vdschaaf.nl                        │
    │                                             │
    │ Plan: Free (85/100 messages today)          │
    │                                             │
    │ [Upgrade to Pro] [Manage] [Sign Out]        │
    └─────────────────────────────────────────────┘
    ↓
Rest of settings tabs (Account, Models, Company, Advanced)
```

**Upgrade Prompts in Chat**:
```python
# In chat interface - show contextual upgrade prompts

if not auth["authenticated"]:
    # Unauthenticated user approaching limit
    if auth["messages_used_today"] >= 8:
        gr.Info("You've used 8/10 free messages today. Sign in for 100 messages/day.")

elif auth["tier"] == "free":
    # Authenticated free user approaching limit
    if auth["messages_used_today"] >= 90:
        gr.Info("You've used 90/100 messages today. Upgrade to Pro for unlimited messages.")

# When trying to use locked features
if user_tries_to_enable_web_search and not auth["features"]["web_search"]:
    gr.Warning("Web search requires a Pro account. Upgrade in Settings.")
```

### 3. Cross-Route Session Sharing: HTTP-Only Cookies (Least Effort, Most Effective)

**Decision**: Use **HTTP-only cookies** for session persistence across routes.

**Rationale**:
- ✅ **Least Effort**: FastAPI has built-in cookie support, no additional libraries needed
- ✅ **Most Effective**: Cookies persist across page navigation and refreshes
- ✅ **Secure**: HTTP-only flag prevents XSS attacks
- ✅ **Cross-Route**: Works seamlessly between `/` (chat) and `/settings`
- ✅ **PWA Compatible**: Cookies work in installed PWA apps

**Implementation**:

**Cookie Structure**:
```python
# Cookie name
SESSION_COOKIE_NAME = "aw_session"  # Agent Workbench session

# Cookie attributes
cookie_attributes = {
    "httponly": True,        # Not accessible to JavaScript (XSS protection)
    "secure": True,          # HTTPS only (production)
    "samesite": "Lax",       # CSRF protection
    "max_age": 2592000,      # 30 days in seconds
    "path": "/"              # Available to all routes
}

# Cookie value: session token (UUID or JWT)
session_token = str(uuid.uuid4())
```

**Setting Cookie After Login** (in custom OAuth handler):
```python
# api/routes/auth.py (NEW FILE)

from fastapi import APIRouter, Response, Request, Form
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login")
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...)  # Or OAuth token
):
    """
    Handle user login and set session cookie.

    Called from settings page login form.
    """
    # Authenticate user
    auth_service = AuthService()
    user = await auth_service.authenticate(username, password)

    if not user:
        return {"error": "Invalid credentials"}

    # Create session
    session = await auth_service.create_session(
        user_id=user["id"],
        request=request
    )

    # Set HTTP-only cookie
    response.set_cookie(
        key="aw_session",
        value=session["token"],
        httponly=True,
        secure=True,  # Use False for local dev
        samesite="Lax",
        max_age=2592000,  # 30 days
        path="/"
    )

    # Return success (or redirect)
    return RedirectResponse(url="/settings", status_code=303)

@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    Handle user logout and clear session cookie.

    Called from settings page "Sign Out" button.
    """
    # Get session token from cookie
    session_token = request.cookies.get("aw_session")

    if session_token:
        # End session in database
        auth_service = AuthService()
        await auth_service.end_session_by_token(session_token)

    # Clear cookie
    response.delete_cookie(key="aw_session", path="/")

    return RedirectResponse(url="/", status_code=303)

@router.get("/session")
async def check_session(request: Request):
    """
    Check if user has active session (used by frontend).

    Returns user info and auth status.
    """
    session_token = request.cookies.get("aw_session")

    if not session_token:
        return {"authenticated": False}

    # Validate session
    auth_service = AuthService()
    session = await auth_service.validate_session(session_token)

    if not session:
        return {"authenticated": False}

    # Get user
    user = await auth_service.get_user(session["user_id"])

    return {
        "authenticated": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "avatar_url": user["avatar_url"]
        },
        "tier": await get_user_tier(user["id"]),
        "messages_today": await get_message_count_today(user["id"])
    }
```

**Reading Cookie in Gradio Interface**:
```python
# ui/app.py - Chat interface

def create_workbench_app() -> gr.Blocks:
    with gr.Blocks() as app:
        # On page load, check authentication
        def check_auth_on_load(request: gr.Request):
            """Check session cookie and return auth status."""
            session_token = request.cookies.get("aw_session")

            if not session_token:
                # Unauthenticated
                return {
                    "authenticated": False,
                    "show_upgrade_banner": True,
                    "banner_text": "Limited to 10 messages/day. Sign in for 100 messages/day."
                }

            # Validate session
            auth_service = AuthService()
            session = auth_service.validate_session_sync(session_token)

            if not session:
                # Expired session
                return {
                    "authenticated": False,
                    "show_upgrade_banner": True,
                    "banner_text": "Session expired. Sign in to continue."
                }

            # Get user and subscription
            user = auth_service.get_user_sync(session["user_id"])
            tier = get_user_tier_sync(user["id"])

            return {
                "authenticated": True,
                "user_id": user["id"],
                "username": user["username"],
                "tier": tier,
                "show_upgrade_banner": tier == "free",
                "banner_text": f"Free tier: 85/100 messages today. Upgrade to Pro for unlimited."
            }

        # State to store auth info
        auth_state = gr.State({})

        # Load auth state on page load
        app.load(fn=check_auth_on_load, outputs=[auth_state])

        # Use auth_state throughout interface to enable/disable features
        # ...
```

**Reading Cookie in Settings Page**:
```python
# ui/settings_page.py

def create_settings_page() -> gr.Blocks:
    with gr.Blocks(title="Settings") as settings:
        # Check authentication on load
        def load_settings(request: gr.Request):
            """Load user settings or show login prompt."""
            session_token = request.cookies.get("aw_session")

            if not session_token:
                # Show login UI
                return {
                    "show_login": True,
                    "show_profile": False,
                    "show_settings_tabs": False
                }

            # Validate session and load user
            auth_service = AuthService()
            session = auth_service.validate_session_sync(session_token)

            if not session:
                return {
                    "show_login": True,
                    "show_profile": False,
                    "show_settings_tabs": False
                }

            user = auth_service.get_user_sync(session["user_id"])
            settings_service = UserSettingsService()
            user_settings = settings_service.get_all_settings_sync(user["id"])

            return {
                "show_login": False,
                "show_profile": True,
                "show_settings_tabs": True,
                "user": user,
                "settings": user_settings
            }

        # UI components
        with gr.Column(visible=True) as login_ui:
            gr.Markdown("## Sign In")
            gr.HTML("""
                <form action="/auth/login" method="POST">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Sign In</button>
                </form>
                <p>Or sign in with:</p>
                <a href="/auth/oauth/huggingface">HuggingFace</a>
                <a href="/auth/oauth/google">Google</a>
                <a href="/auth/oauth/github">GitHub</a>
            """)

        with gr.Column(visible=False) as profile_ui:
            user_profile = gr.HTML()  # Populated with user info
            logout_btn = gr.Button("Sign Out")

            # Logout handler
            logout_btn.click(
                fn=lambda: None,
                js="window.location.href = '/auth/logout'"
            )

        with gr.Column(visible=False) as settings_tabs_ui:
            # Account, Models, Company, Advanced tabs
            # ...

        # Load auth state on page load
        settings.load(
            fn=load_settings,
            outputs=[login_ui, profile_ui, settings_tabs_ui, user_profile]
        )
```

**Advantages Over Alternatives**:

| Method | Effort | Effectiveness | Security | PWA Support |
|--------|--------|---------------|----------|-------------|
| **HTTP-only Cookies** | Low | High | High | ✅ Yes |
| LocalStorage | Medium | Medium | Low (XSS vulnerable) | ✅ Yes |
| Gradio State | Low | Low (lost on refresh) | Medium | ❌ No persistence |
| FastAPI Session Middleware | High | High | High | ✅ Yes |

**Decision**: HTTP-only cookies provide the best balance of simplicity, security, and functionality.

### 4. Toggle UI State: Logout and Page Reload

**Decision**: UI state toggles by **signing out** (which clears the cookie) and **reloading** the page.

**Settings Page State Toggle**:
```python
# When user is unauthenticated
with gr.Column(visible=True, elem_id="login-section") as login_ui:
    gr.Markdown("## Not signed in")
    gr.HTML("""
        <form action="/auth/login" method="POST">
            <!-- Login form -->
        </form>
    """)

# When user is authenticated
with gr.Column(visible=False, elem_id="profile-section") as profile_ui:
    gr.Markdown("## Your Profile")
    username_display = gr.Textbox(label="Username", interactive=False)
    email_display = gr.Textbox(label="Email", interactive=False)
    tier_display = gr.Textbox(label="Plan", interactive=False)

    logout_btn = gr.Button("Sign Out", variant="secondary")

# Toggle visibility based on auth state
def toggle_auth_ui(request: gr.Request):
    session_token = request.cookies.get("aw_session")
    authenticated = validate_session(session_token)

    return {
        login_ui: gr.Column(visible=not authenticated),
        profile_ui: gr.Column(visible=authenticated)
    }

# Load on page load
app.load(fn=toggle_auth_ui, outputs=[login_ui, profile_ui])
```

**Logout Flow**:
```python
# User clicks "Sign Out" button
logout_btn.click(
    fn=lambda: None,
    js="""
        async () => {
            // Call logout endpoint
            await fetch('/auth/logout', { method: 'POST' });
            // Reload page to refresh UI
            window.location.href = '/settings';
        }
    """
)
```

**Why Page Reload**:
- ✅ Simple: No complex state management in Gradio
- ✅ Reliable: Guarantees UI reflects actual auth state
- ✅ Fast: Page loads are instant with PWA caching
- ✅ Clean: Avoids partial UI states or stale data

### 5. Custom OAuth Flow (Future-Proof for Multiple Providers)

**Decision**: Implement **custom OAuth flow** instead of `gr.LoginButton()`.

**Rationale**:
- ✅ **Multi-Provider Support**: Can add Google, GitHub, Microsoft in future
- ✅ **Settings Integration**: Login UI can be embedded in settings page
- ✅ **Custom Branding**: Full control over login UI/UX
- ✅ **Subscription Integration**: Can add tier selection during signup
- ✅ **FastAPI Native**: Uses standard FastAPI OAuth patterns

**OAuth Provider Registry Pattern**:
```python
# api/routes/auth.py

from typing import Protocol

class OAuthProvider(Protocol):
    """Protocol for OAuth providers."""

    async def get_authorization_url(self, state: str) -> str:
        """Get OAuth authorization URL."""
        ...

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token."""
        ...

    async def get_user_info(self, access_token: str) -> dict:
        """Get user info from provider."""
        ...

class HuggingFaceOAuth:
    """HuggingFace OAuth implementation."""

    def __init__(self):
        self.client_id = os.getenv("HF_CLIENT_ID")
        self.client_secret = os.getenv("HF_CLIENT_SECRET")
        self.redirect_uri = os.getenv("BASE_URL") + "/auth/callback/huggingface"

    async def get_authorization_url(self, state: str) -> str:
        """Get HuggingFace OAuth authorization URL."""
        return (
            f"https://huggingface.co/oauth/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&state={state}"
            f"&scope=openid%20profile%20email"
        )

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange code for token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://huggingface.co/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.redirect_uri
                }
            )
            return response.json()

    async def get_user_info(self, access_token: str) -> dict:
        """Get user info from HuggingFace."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://huggingface.co/oauth/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return response.json()

class GoogleOAuth:
    """Google OAuth implementation (future)."""
    # Similar pattern
    pass

class GitHubOAuth:
    """GitHub OAuth implementation (future)."""
    # Similar pattern
    pass

# Provider registry
OAUTH_PROVIDERS = {
    "huggingface": HuggingFaceOAuth(),
    "google": GoogleOAuth(),
    "github": GitHubOAuth(),
}

@router.get("/oauth/{provider}")
async def oauth_initiate(provider: str):
    """Initiate OAuth flow for provider."""
    if provider not in OAUTH_PROVIDERS:
        return {"error": "Invalid provider"}

    # Generate state token (CSRF protection)
    state = str(uuid.uuid4())
    # Store state in session or cache (verify on callback)

    # Get authorization URL
    oauth = OAUTH_PROVIDERS[provider]
    auth_url = await oauth.get_authorization_url(state)

    return RedirectResponse(url=auth_url)

@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str,
    code: str,
    state: str,
    response: Response
):
    """Handle OAuth callback from provider."""
    if provider not in OAUTH_PROVIDERS:
        return {"error": "Invalid provider"}

    # Verify state (CSRF protection)
    # ...

    # Exchange code for token
    oauth = OAUTH_PROVIDERS[provider]
    token_data = await oauth.exchange_code_for_token(code)

    # Get user info
    user_info = await oauth.get_user_info(token_data["access_token"])

    # Create or update user
    auth_service = AuthService()
    user = await auth_service.get_or_create_user_from_oauth(
        provider=provider,
        provider_user_id=user_info["id"],
        username=user_info["username"],
        email=user_info.get("email"),
        avatar_url=user_info.get("avatar_url"),
        provider_data=user_info
    )

    # Create session
    session = await auth_service.create_session(user["id"])

    # Set cookie
    response.set_cookie(
        key="aw_session",
        value=session["token"],
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=2592000,
        path="/"
    )

    # Redirect to settings
    return RedirectResponse(url="/settings", status_code=303)
```

**Settings Page OAuth UI**:
```python
# ui/settings_page.py

with gr.Column(visible=True) as login_ui:
    gr.Markdown("## Sign In to Agent Workbench")

    gr.Markdown("### Sign in with OAuth")
    with gr.Row():
        hf_btn = gr.HTML("""
            <a href="/auth/oauth/huggingface" class="oauth-button">
                <img src="/static/icons/hf-logo.png" width="20"/>
                HuggingFace
            </a>
        """)
        google_btn = gr.HTML("""
            <a href="/auth/oauth/google" class="oauth-button">
                <img src="/static/icons/google-logo.png" width="20"/>
                Google
            </a>
        """)
        github_btn = gr.HTML("""
            <a href="/auth/oauth/github" class="oauth-button">
                <img src="/static/icons/github-logo.png" width="20"/>
                GitHub
            </a>
        """)

    gr.Markdown("### Or sign in with username/password")
    gr.HTML("""
        <form action="/auth/login" method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>
    """)
```

**Advantages of Custom OAuth**:
1. **Future-Proof**: Easy to add new providers (just implement protocol)
2. **Flexible**: Can customize login flow, add tier selection, etc.
3. **Standard Pattern**: Uses FastAPI OAuth libraries (authlib, python-jose)
4. **Testable**: Can mock OAuth providers in tests
5. **Settings Integration**: Works naturally with settings-based login UI

## Implementation Checklist

### Phase 1: Core Authentication (Must Have)
- [ ] Create `/api/routes/auth.py` with login/logout/session endpoints
- [ ] Implement HTTP-only cookie session management
- [ ] Add `check_auth_and_limits()` utility function
- [ ] Modify chat interface to show upgrade banners
- [ ] Modify settings page to show login/profile toggle
- [ ] Implement HuggingFace OAuth provider
- [ ] Add authentication checks in message handler
- [ ] Implement anonymous user tracking (IP-based message limits)

### Phase 2: Freemium Features (Must Have)
- [ ] Create subscription/tier system (database schema)
- [ ] Implement message counting per user/IP
- [ ] Add feature gates (file upload, web search, etc.)
- [ ] Show upgrade prompts when hitting limits
- [ ] Create `/settings` route with Gradio interface
- [ ] Add "Upgrade to Pro" button with pricing modal

### Phase 3: Additional Providers (Nice to Have)
- [ ] Implement Google OAuth provider
- [ ] Implement GitHub OAuth provider
- [ ] Add provider selection UI in settings
- [ ] Support multiple linked accounts (same user, multiple OAuth providers)

### Phase 4: User Management (Nice to Have)
- [ ] Username/password authentication (custom signup)
- [ ] Email verification flow
- [ ] Password reset flow
- [ ] Account deletion

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_auth.py

async def test_unauthenticated_user_has_message_limit():
    """Test anonymous users have 10 message/day limit."""
    auth_status = await check_auth_and_limits(mock_request_unauthenticated)
    assert auth_status["daily_message_limit"] == 10
    assert auth_status["authenticated"] == False

async def test_free_user_has_higher_limit():
    """Test authenticated free users have 100 message/day limit."""
    auth_status = await check_auth_and_limits(mock_request_authenticated_free)
    assert auth_status["daily_message_limit"] == 100
    assert auth_status["tier"] == "free"

async def test_pro_user_has_no_limit():
    """Test Pro users have unlimited messages."""
    auth_status = await check_auth_and_limits(mock_request_authenticated_pro)
    assert auth_status["daily_message_limit"] is None
    assert auth_status["tier"] == "pro"
```

### Integration Tests
```python
# tests/integration/test_auth_flow.py

async def test_login_sets_cookie(client):
    """Test login endpoint sets session cookie."""
    response = await client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass"}
    )
    assert response.status_code == 303
    assert "aw_session" in response.cookies

async def test_logout_clears_cookie(client):
    """Test logout endpoint clears session cookie."""
    # Login first
    login_response = await client.post("/auth/login", data={...})
    cookies = login_response.cookies

    # Logout
    logout_response = await client.post("/auth/logout", cookies=cookies)
    assert logout_response.cookies.get("aw_session") == ""

async def test_settings_page_shows_login_when_unauthenticated(client):
    """Test settings page shows login UI for unauthenticated users."""
    response = await client.get("/settings")
    assert "Sign In" in response.text
    assert "Create Account" in response.text

async def test_settings_page_shows_profile_when_authenticated(client):
    """Test settings page shows user profile for authenticated users."""
    # Login first
    login_response = await client.post("/auth/login", data={...})

    # Visit settings
    response = await client.get("/settings", cookies=login_response.cookies)
    assert "testuser" in response.text
    assert "Sign Out" in response.text
```

### E2E Tests
```python
# tests/e2e/test_auth_ux.py

def test_anonymous_user_can_chat_with_limits():
    """Test anonymous user can send 10 messages then sees upgrade prompt."""
    # Send 10 messages without auth
    for i in range(10):
        response = send_message(f"Message {i}")
        assert response.status_code == 200

    # 11th message shows limit
    response = send_message("Message 11")
    assert "Daily limit reached" in response.text
    assert "Sign in" in response.text

def test_user_can_login_via_settings():
    """Test user can access settings page and login."""
    # Visit settings
    response = browser.get("/settings")
    assert "Sign In" in response.text

    # Click HuggingFace OAuth
    browser.click("a[href='/auth/oauth/huggingface']")

    # (OAuth flow simulation)
    # ...

    # After OAuth, redirected back to settings
    assert browser.current_url == "/settings"
    assert "testuser" in browser.page_source
```

## Success Criteria

- [ ] Anonymous users can chat with 10 message/day limit
- [ ] Authenticated free users can chat with 100 message/day limit
- [ ] Pro users have unlimited messages
- [ ] Settings page shows login UI when unauthenticated
- [ ] Settings page shows user profile when authenticated
- [ ] "Sign Out" button clears session and reloads page
- [ ] Session cookie persists across page navigation
- [ ] Session cookie persists across browser sessions (30 days)
- [ ] HuggingFace OAuth flow works end-to-end
- [ ] Upgrade prompts appear when users hit limits
- [ ] Feature gates work (file upload, web search, etc.)
- [ ] All tests pass (unit, integration, E2E)

## References

- **Parent Architecture**: `docs/architecture/decisions/UI-004-pwa-app-user-settings.md`
- **UX Design**: `design/UI-004-target-ux.md`
- **Phase 2.0 Auth**: `feature/CORE-003-user-authentication` branch
- **Auth Service**: `src/agent_workbench/services/auth_service.py`
- **Database Models**: `src/agent_workbench/models/database.py` (UserModel, UserSessionModel)
