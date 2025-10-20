# UI-004: Local Development Authentication Strategy

## Status

**Status**: Architecture Complete
**Date**: October 20, 2025
**Parent Task**: UI-004-pwa-app-user-settings
**Phase**: 2.1

## Context

**Problem**: OAuth providers (HuggingFace, Google, GitHub) require HTTPS and registered redirect URIs, making them unusable for local development at `http://localhost:8000`.

**Why HuggingFace OAuth Doesn't Work Locally**:
1. **Redirect URI Mismatch**: OAuth apps are registered with production URLs (e.g., `https://app.example.com/auth/callback/huggingface`)
2. **HTTPS Requirement**: Most OAuth providers require HTTPS for security (localhost is HTTP)
3. **Environment Separation**: Can't use production OAuth credentials in dev environment (security risk)

**Solution Required**: Multiple authentication methods based on environment.

## Architectural Decision

### Multi-Method Authentication Strategy

**Decision**: Support **4 authentication methods** with automatic selection based on `AUTH_MODE` environment variable.

```python
AUTH_MODE = os.getenv("AUTH_MODE", "development")

# Valid values:
# "disabled"      - No authentication (Phase 1 behavior)
# "development"   - Mock user for local testing
# "staging"       - OAuth with staging credentials
# "production"    - Full OAuth with production credentials
```

### Method 1: Disabled (Phase 1 Backward Compatibility)

**When**: Phase 1 testing, demo mode, or when auth features not needed

**Configuration**:
```bash
# .env or config/development.env
AUTH_MODE=disabled
```

**Behavior**:
- No login required
- No session tracking
- All features available (no freemium gates)
- Single anonymous user
- No database user records created

**Implementation**:
```python
# services/auth_service.py

async def check_auth_and_limits(request: gr.Request) -> dict:
    """Check authentication based on AUTH_MODE."""

    auth_mode = os.getenv("AUTH_MODE", "development")

    if auth_mode == "disabled":
        # No authentication - Phase 1 behavior
        return {
            "authenticated": False,
            "auth_mode": "disabled",
            "tier": "unlimited",
            "daily_message_limit": None,  # Unlimited
            "available_models": get_all_models(),
            "features": {
                "conversation_history": True,  # Local only
                "file_upload": True,
                "web_search": True,
                "mcp_tools": True
            }
        }
```

**Use Cases**:
- Local development without auth complexity
- Demos and presentations
- Testing non-auth features

### Method 2: Development (Mock User)

**When**: Local testing of authentication-dependent features

**Configuration**:
```bash
# config/development.env
AUTH_MODE=development
DEV_USER_USERNAME=developer
DEV_USER_EMAIL=dev@localhost
DEV_USER_TIER=pro  # or "free" to test limits
```

**Behavior**:
- Auto-login as mock user (no login form shown)
- Mock user created in database on first load
- Full feature access or test freemium limits
- Session tracking works (for testing session features)
- User settings persistence works

**Implementation**:
```python
# services/auth_service.py

async def get_or_create_dev_user() -> dict:
    """Create mock user for development testing."""

    dev_username = os.getenv("DEV_USER_USERNAME", "developer")
    dev_email = os.getenv("DEV_USER_EMAIL", "dev@localhost")
    dev_tier = os.getenv("DEV_USER_TIER", "pro")

    # Check if dev user exists
    user = db.get_user_by_username(dev_username)

    if not user:
        # Create dev user
        user = db.create_user(
            username=dev_username,
            email=dev_email,
            auth_provider="development",
            provider_data={
                "dev_mode": True,
                "tier": dev_tier
            }
        )
        logger.info(f"Created development user: {dev_username}")

    return user

# In check_auth_and_limits()
if auth_mode == "development":
    # Auto-login as dev user
    dev_user = await get_or_create_dev_user()

    # Create or get active session
    session = await auth_service.get_active_session(dev_user["id"])
    if not session:
        session = await auth_service.create_mock_session(dev_user["id"])

    dev_tier = dev_user.get("provider_data", {}).get("tier", "pro")

    return {
        "authenticated": True,
        "auth_mode": "development",
        "user_id": dev_user["id"],
        "username": dev_user["username"],
        "tier": dev_tier,
        "daily_message_limit": None if dev_tier == "pro" else 100,
        "messages_used_today": 0,  # Reset daily for dev
        "available_models": get_all_models() if dev_tier == "pro" else get_free_models(),
        "features": {
            "conversation_history": True,
            "file_upload": True,
            "web_search": True,
            "mcp_tools": dev_tier == "pro"
        }
    }
```

**UI Integration**:
```python
# ui/settings_page.py

def create_settings_page() -> gr.Blocks:
    with gr.Blocks() as settings:
        def load_settings(request: gr.Request):
            auth_mode = os.getenv("AUTH_MODE", "development")

            if auth_mode == "development":
                # Show dev user profile (not editable)
                dev_user = get_dev_user()
                return {
                    "show_login": False,
                    "show_profile": True,
                    "show_settings_tabs": True,
                    "profile_html": f"""
                        <div class="dev-mode-banner">
                            ⚠️ Development Mode - Mock User
                        </div>
                        <div class="user-profile">
                            <p><strong>Username:</strong> {dev_user['username']}</p>
                            <p><strong>Email:</strong> {dev_user['email']}</p>
                            <p><strong>Tier:</strong> {dev_user['provider_data']['tier']}</p>
                            <p><em>Auto-logged in for local testing</em></p>
                        </div>
                    """
                }
```

**Advantages**:
- ✅ Test authentication features locally without OAuth complexity
- ✅ Test user-specific features (settings, conversation history)
- ✅ Test freemium limits by changing DEV_USER_TIER
- ✅ No external OAuth providers needed
- ✅ Fast iteration (no OAuth roundtrips)

**Use Cases**:
- Testing settings persistence
- Testing user-specific features
- Testing freemium limits and upgrade prompts
- Testing session management

### Method 3: Local OAuth (Optional - Advanced)

**When**: Need to test actual OAuth flows locally

**Why It's Challenging**:
- OAuth providers require HTTPS
- Redirect URIs must match registered URLs
- Can't use production OAuth credentials (security risk)

**Solution: ngrok or LocalTunnel + Separate OAuth App**

**Setup Steps**:
1. **Install ngrok**:
   ```bash
   brew install ngrok  # macOS
   # or download from https://ngrok.com
   ```

2. **Start ngrok tunnel**:
   ```bash
   # Start app on localhost:8000
   make start-app

   # In separate terminal, create tunnel
   ngrok http 8000
   # Output: https://abc123.ngrok.io -> http://localhost:8000
   ```

3. **Register OAuth App with Tunnel URL**:
   - Go to HuggingFace OAuth Apps: https://huggingface.co/settings/applications
   - Create new OAuth app:
     - **Name**: Agent Workbench (Local Dev)
     - **Redirect URI**: `https://abc123.ngrok.io/auth/callback/huggingface`
   - Copy Client ID and Client Secret

4. **Configure Environment**:
   ```bash
   # config/development.env
   AUTH_MODE=staging

   # Local OAuth credentials (separate from production)
   HF_CLIENT_ID=your_dev_client_id
   HF_CLIENT_SECRET=your_dev_client_secret
   BASE_URL=https://abc123.ngrok.io
   ```

5. **Access via Tunnel**:
   - Visit: `https://abc123.ngrok.io` (NOT localhost:8000)
   - OAuth will work because tunnel provides HTTPS

**Advantages**:
- ✅ Test real OAuth flows
- ✅ Test multiple OAuth providers
- ✅ Test OAuth error handling

**Disadvantages**:
- ❌ Requires ngrok setup
- ❌ Tunnel URL changes on each restart (free tier)
- ❌ Need separate OAuth app registrations
- ❌ Slower iteration (OAuth roundtrips)

**Implementation**:
```python
# api/routes/auth.py

def get_oauth_credentials(provider: str) -> tuple:
    """Get OAuth credentials based on AUTH_MODE."""

    auth_mode = os.getenv("AUTH_MODE", "development")

    if auth_mode in ["staging", "development"]:
        # Use dev/staging credentials
        client_id = os.getenv(f"{provider.upper()}_DEV_CLIENT_ID")
        client_secret = os.getenv(f"{provider.upper()}_DEV_CLIENT_SECRET")
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
    else:
        # Use production credentials
        client_id = os.getenv(f"{provider.upper()}_CLIENT_ID")
        client_secret = os.getenv(f"{provider.upper()}_CLIENT_SECRET")
        base_url = os.getenv("BASE_URL", "https://app.example.com")

    return client_id, client_secret, base_url
```

**When to Use**:
- Testing OAuth-specific bugs
- Testing multiple provider integration
- Final pre-deployment testing

### Method 4: Staging Environment (Shared Dev Server)

**When**: Team collaboration, pre-production testing

**Setup**:
- Deploy to staging server with HTTPS (e.g., `https://staging.agentworkbench.dev`)
- Register OAuth apps with staging URL
- Use staging database (separate from production)

**Configuration**:
```bash
# config/staging.env
AUTH_MODE=staging
APP_ENV=staging

# Staging OAuth credentials
HF_CLIENT_ID=staging_client_id
HF_CLIENT_SECRET=staging_client_secret
GOOGLE_CLIENT_ID=staging_google_id
GOOGLE_CLIENT_SECRET=staging_google_secret
BASE_URL=https://staging.agentworkbench.dev

# Staging database
DATABASE_URL=postgresql://staging_db:5432/agentworkbench
```

**Advantages**:
- ✅ Real OAuth without ngrok complexity
- ✅ Shared environment for team testing
- ✅ Mirrors production setup
- ✅ Test with real HTTPS

**Use Cases**:
- Pre-deployment testing
- QA testing
- Team collaboration

## Recommended Development Workflow

### Daily Development (Most Common)

```bash
# 1. Start with disabled auth for non-auth features
AUTH_MODE=disabled make start-app
# Fast iteration, no auth complexity

# 2. Switch to development mode for auth features
AUTH_MODE=development make start-app
# Test settings, user-specific features, freemium limits
```

### Testing Authentication Features

```bash
# 1. Test as Pro user
AUTH_MODE=development DEV_USER_TIER=pro make start-app

# 2. Test as Free user with limits
AUTH_MODE=development DEV_USER_TIER=free make start-app

# 3. Test unauthenticated experience
AUTH_MODE=disabled make start-app
# Then manually test upgrade prompts
```

### Testing OAuth (Occasional)

```bash
# Option A: Use ngrok (if needed)
make start-app
ngrok http 8000
# Update .env with ngrok URL, restart app

# Option B: Use staging server
git push origin develop
# Test on https://staging.agentworkbench.dev
```

## Configuration Examples

### Local Development (Default)

```bash
# config/development.env
APP_ENV=development
AUTH_MODE=development

# Dev user
DEV_USER_USERNAME=developer
DEV_USER_EMAIL=dev@localhost
DEV_USER_TIER=pro

# No OAuth credentials needed
```

### Local OAuth Testing (Advanced)

```bash
# config/development.env
APP_ENV=development
AUTH_MODE=staging

# ngrok tunnel URL (update each time)
BASE_URL=https://abc123.ngrok.io

# Dev OAuth credentials (separate registrations)
HF_DEV_CLIENT_ID=local_dev_client_id
HF_DEV_CLIENT_SECRET=local_dev_client_secret
GOOGLE_DEV_CLIENT_ID=local_google_id
GOOGLE_DEV_CLIENT_SECRET=local_google_secret
```

### Staging Server

```bash
# config/staging.env
APP_ENV=staging
AUTH_MODE=staging

BASE_URL=https://staging.agentworkbench.dev

# Staging OAuth credentials
HF_CLIENT_ID=staging_hf_id
HF_CLIENT_SECRET=staging_hf_secret
GOOGLE_CLIENT_ID=staging_google_id
GOOGLE_CLIENT_SECRET=staging_google_secret
GITHUB_CLIENT_ID=staging_github_id
GITHUB_CLIENT_SECRET=staging_github_secret
```

### Production

```bash
# config/production.env
APP_ENV=production
AUTH_MODE=production

BASE_URL=https://agentworkbench.dev

# Production OAuth credentials
HF_CLIENT_ID=prod_hf_id
HF_CLIENT_SECRET=prod_hf_secret
GOOGLE_CLIENT_ID=prod_google_id
GOOGLE_CLIENT_SECRET=prod_google_secret
GITHUB_CLIENT_ID=prod_github_id
GITHUB_CLIENT_SECRET=prod_github_secret
```

## Implementation Checklist

- [ ] Add `AUTH_MODE` environment variable support
- [ ] Implement `disabled` mode (Phase 1 behavior)
- [ ] Implement `development` mode (mock user)
- [ ] Add `get_or_create_dev_user()` function
- [ ] Update `check_auth_and_limits()` to handle all modes
- [ ] Add dev mode banner in settings page
- [ ] Document ngrok setup for local OAuth testing
- [ ] Create staging OAuth app registrations
- [ ] Test all 4 auth modes

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_auth_modes.py

def test_disabled_mode_allows_all_features():
    """Test AUTH_MODE=disabled provides unlimited access."""
    os.environ["AUTH_MODE"] = "disabled"
    auth = check_auth_and_limits(mock_request)
    assert auth["tier"] == "unlimited"
    assert auth["daily_message_limit"] is None

def test_development_mode_creates_mock_user():
    """Test AUTH_MODE=development auto-creates dev user."""
    os.environ["AUTH_MODE"] = "development"
    auth = check_auth_and_limits(mock_request)
    assert auth["authenticated"] == True
    assert auth["username"] == "developer"

def test_development_mode_respects_tier():
    """Test dev tier can be configured."""
    os.environ["AUTH_MODE"] = "development"
    os.environ["DEV_USER_TIER"] = "free"
    auth = check_auth_and_limits(mock_request)
    assert auth["tier"] == "free"
    assert auth["daily_message_limit"] == 100
```

### Manual Testing

**Test disabled mode**:
```bash
AUTH_MODE=disabled make start-app
# ✓ Chat works immediately
# ✓ All features available
# ✓ No login prompts
```

**Test development mode (Pro)**:
```bash
AUTH_MODE=development DEV_USER_TIER=pro make start-app
# ✓ Settings shows "developer" profile
# ✓ All features enabled
# ✓ No message limits
# ✓ Settings persist
```

**Test development mode (Free)**:
```bash
AUTH_MODE=development DEV_USER_TIER=free make start-app
# ✓ Settings shows "developer" profile
# ✓ 100 message/day limit
# ✓ Upgrade prompts appear at 90 messages
# ✓ MCP tools disabled
```

## Answer to Your Question

**Q: "I couldn't use HuggingFace login in local tests. Would that be possible if we add other (multiple) OAuth services?"**

**A: No, OAuth providers (HuggingFace, Google, GitHub) all have the same local testing limitations:**

1. **All require HTTPS** (localhost is HTTP)
2. **All require registered redirect URIs** (can't use localhost:8000)
3. **All need separate dev credentials** (can't use production creds)

**Solutions in Order of Recommendation**:

1. **Best for Daily Development**: Use `AUTH_MODE=development` (mock user)
   - ✅ No OAuth complexity
   - ✅ Fast iteration
   - ✅ Test all auth-dependent features
   - ✅ Works out of the box

2. **For OAuth Testing (Occasional)**: Use ngrok + dev OAuth apps
   - ✅ Real OAuth flows
   - ✅ Test multiple providers
   - ❌ Setup overhead
   - ❌ Slower iteration

3. **For Team Testing**: Use staging server with HTTPS
   - ✅ Real OAuth without ngrok
   - ✅ Shared environment
   - ✅ Mirrors production
   - ❌ Requires deployment

**Recommendation**: Use `AUTH_MODE=development` for 95% of local development. Only use ngrok/staging when you specifically need to test OAuth flows.

## Success Criteria

- [ ] `AUTH_MODE=disabled` works (no auth, unlimited features)
- [ ] `AUTH_MODE=development` creates mock user automatically
- [ ] Dev user appears in settings page
- [ ] Dev user settings persist to database
- [ ] Can switch between Pro/Free tier in dev mode
- [ ] OAuth works on staging server
- [ ] Documentation explains all 4 auth modes
- [ ] Team understands when to use each mode

## References

- **Parent Architecture**: `docs/architecture/decisions/UI-004-authentication-behavior.md`
- **OAuth Best Practices**: https://oauth.net/2/
- **ngrok Documentation**: https://ngrok.com/docs
