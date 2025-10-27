# UI-005-settings-page: Settings Page Implementation

## Status

**Status**: Ready for Implementation
**Date**: October 27, 2025
**Decision Makers**: Human Architect
**Task ID**: UI-005-settings-page
**Phase**: 2.1 Extension
**Dependencies**: UI-005-multi-page-app (routing foundation)
**Related**: UI-005-target-ux-implementation (visual design)

---

## Context

### Current State (After UI-005-multi-page-app)

UI-005-multi-page-app delivers the routing foundation with placeholder settings functionality:

**What Works:**
- ✅ Settings page accessible at `/settings` route
- ✅ Model controls moved from chat to settings
- ✅ All components defined (use `visible=` to hide)
- ✅ Tabs structure with Account, Models, Appearance, Context
- ✅ Placeholder save/reset handlers

**What's Missing (Deferred to This Task):**
- ❌ Settings persistence (database writes)
- ❌ Authentication system integration
- ❌ Model list population from `model_config_service`
- ❌ User settings loading on page load
- ❌ Settings validation
- ❌ Error handling for save failures

### Why This is Separate

UI-005-multi-page-app focused on **structural refactoring** (routing, component layout).

UI-005-settings-page focuses on **functional implementation** (persistence, auth, data loading).

**Separation Benefits:**
1. UI-005 ships quickly with working UI (placeholder functionality)
2. Settings implementation can be tested thoroughly without blocking routing
3. Database schema can evolve independently
4. Authentication can be implemented properly (not rushed)

---

## Scope

### ✅ In Scope

**1. Settings Persistence:**
- Database writes for all settings tabs
- Settings retrieval on page load
- User-specific settings storage
- Default settings fallback

**2. Model Configuration Integration:**
- Use existing `model_config_service.get_provider_choices_for_ui()`
- Populate provider/model dropdowns dynamically
- Save model preferences per user
- Load user's model selection on app start

**3. Authentication Integration:**
- Sign in/sign out functionality
- User session management
- Settings tied to authenticated user
- Guest mode with localStorage fallback

**4. Settings Validation:**
- Temperature range validation (0-2)
- Max tokens range validation
- URL format validation for context fields
- Required field validation

**5. Error Handling:**
- Database write failures
- Network errors (if API calls)
- Validation errors with user feedback
- Rollback on save failure

**6. Page Reload Optimization (Future):**
- Current: Full page reload after save
- Future: Gradio state updates without reload
- Deferred to separate optimization task

### ❌ Out of Scope (Deferred to Other Tasks)

- ❌ Visual design (iOS toggles, Ubuntu font) → UI-005-target-ux-implementation
- ❌ Chat history sidebar → Separate feature (dev plan exists)
- ❌ PWA manifest updates → Handled in UI-005-multi-page-app
- ❌ Multi-language i18n → Phase 3
- ❌ Settings import/export → Future enhancement
- ❌ Settings sync across devices → Future enhancement

---

## Architecture Decisions

### 1. Settings Persistence Strategy

**Decision:** Use database (SQLite/HubDB) for authenticated users, localStorage for guests

**Rationale:**
- Consistent with existing patterns (conversation persistence)
- Settings survive page refresh
- Can sync across devices (future)
- Gradual rollout: localStorage first, then database

**Implementation:**

```python
# services/user_settings_service.py

async def save_settings(
    user_id: Optional[str],
    model_config: Dict[str, Any],
    appearance: Dict[str, Any],
    context: Dict[str, Any]
) -> bool:
    """
    Save user settings to database or localStorage.

    Args:
        user_id: User UUID (None for guests)
        model_config: Provider, model, temperature, max_tokens
        appearance: Theme preference
        context: Project/business info

    Returns:
        True if saved successfully, False otherwise

    Storage Strategy:
        - Authenticated users: Database (user_settings table)
        - Guests: localStorage (client-side only)
    """
    if user_id:
        # Database save
        return await _save_to_database(user_id, model_config, appearance, context)
    else:
        # LocalStorage save (via JavaScript)
        return await _save_to_localstorage(model_config, appearance, context)
```

**Database Schema:**

```sql
-- Reuse existing user_settings table
-- See: models/database.py

-- Settings stored as JSON in settings column
-- Example:
{
    "model_config": {
        "provider": "openai",
        "model": "gpt-4-turbo",
        "temperature": 0.7,
        "max_tokens": 2000
    },
    "appearance": {
        "theme": "Auto"
    },
    "context": {
        "name": "My Project",
        "url": "https://example.com",
        "description": "Project description"
    }
}
```

**LocalStorage Strategy (Guests):**

```javascript
// Save to localStorage when not authenticated
function saveSettingsToLocalStorage(settings) {
    localStorage.setItem('agent_workbench_settings', JSON.stringify(settings));
}

// Load from localStorage on page load
function loadSettingsFromLocalStorage() {
    const saved = localStorage.getItem('agent_workbench_settings');
    return saved ? JSON.parse(saved) : getDefaultSettings();
}
```

### 2. Authentication Integration

**Decision:** Defer full auth system, implement basic session check

**Current State (UI-005-multi-page-app):**
- `handle_signin()` is a stub
- `handle_signout()` is a stub
- No credential validation

**This Task (UI-005-settings-page):**
- Check for existing session on page load
- Display user info if authenticated
- Enable database settings save if authenticated
- Fallback to localStorage if not authenticated

**Future Task (UI-007-authentication):**
- Real credential validation
- OAuth integration
- Session token management
- User registration

**Interim Implementation:**

```python
# services/auth_service.py (basic version)

async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user from session.

    Returns:
        User dict if authenticated, None otherwise

    Note: This is a basic implementation.
    Full auth system in UI-007-authentication.
    """
    # Check session cookie
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    # Validate session (basic check)
    # TODO: Implement proper session validation in UI-007
    user = await _validate_session(session_id)
    return user


async def sign_in_placeholder(username: str, password: str) -> Optional[str]:
    """
    Placeholder sign-in (basic validation only).

    Returns:
        Session ID if successful, None otherwise

    TODO: Implement real authentication in UI-007-authentication
    """
    # Placeholder: Accept any username/password
    # In production, validate against database
    session_id = str(uuid.uuid4())

    # Store session (in-memory for now)
    _active_sessions[session_id] = {
        "username": username,
        "authenticated": True,
        "timestamp": datetime.now()
    }

    return session_id
```

### 3. Model Configuration Integration

**Decision:** Use existing `model_config_service`, enhance as needed

**Current Issue (UI-005-multi-page-app):**
- Hardcoded model lists in config

**This Task (UI-005-settings-page):**
- Import and use `model_config_service.get_provider_choices_for_ui()`
- Import and use `model_config_service.get_model_choices_for_ui()`
- Save user selection to settings
- Load user selection on app start

**Implementation:**

```python
# ui/pages/settings.py (update)

from services.model_config_service import model_config_service

def render_models_tab(config: Dict[str, Any]) -> Dict[str, gr.Component]:
    """Render models configuration tab."""

    # Get dynamic lists from service (not hardcoded)
    provider_choices, default_provider = model_config_service.get_provider_choices_for_ui()
    model_choices, default_model = model_config_service.get_model_choices_for_ui()

    allow_selection = config.get('allow_model_selection', False)

    provider = gr.Dropdown(
        choices=provider_choices,
        value=default_provider,
        label=config['labels']['provider_label'],
        visible=allow_selection
    )

    model = gr.Dropdown(
        choices=model_choices,
        value=default_model,
        label=config['labels']['model_label'],
        visible=allow_selection
    )

    # ... rest of implementation
```

**Service Enhancement (if needed):**

```python
# services/model_config_service.py (enhance)

def get_provider_choices_for_mode(mode: str) -> List[str]:
    """
    Get provider choices filtered by mode.

    Args:
        mode: "workbench" (all providers) or "seo_coach" (restricted)

    Returns:
        List of provider names
    """
    all_providers = ["openai", "anthropic", "groq", "ollama"]

    if mode == "seo_coach":
        # Restrict to best option only
        return ["openai"]

    return all_providers
```

### 4. Settings Load on Page Init

**Decision:** Load settings on page render, apply to components

**Implementation:**

```python
# ui/pages/settings.py

async def load_user_settings(user_id: Optional[str]) -> Dict[str, Any]:
    """
    Load user settings from database or localStorage.

    Args:
        user_id: User UUID (None for guests)

    Returns:
        Settings dict with defaults for missing values
    """
    if user_id:
        # Load from database
        from services.user_settings_service import UserSettingsService
        service = UserSettingsService()
        settings = await service.get_all_settings(user_id)
    else:
        # Load from localStorage (via JavaScript callback)
        settings = await _load_from_localstorage()

    # Merge with defaults (in case some settings missing)
    return {
        "model_config": settings.get("model_config", {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "temperature": 0.7,
            "max_tokens": 2000
        }),
        "appearance": settings.get("appearance", {
            "theme": "Auto"
        }),
        "context": settings.get("context", {
            "name": "",
            "url": "",
            "description": ""
        })
    }


def render(config: Dict[str, Any], user_state: gr.State) -> None:
    """Render settings interface with loaded settings."""

    # Load settings on render
    user_id = user_state.value.get("user_id") if user_state.value else None
    settings = await load_user_settings(user_id)

    # ... render with loaded values

    provider = gr.Dropdown(
        choices=provider_choices,
        value=settings["model_config"]["provider"],  # From loaded settings
        label=config['labels']['provider_label'],
        visible=allow_selection
    )
```

### 5. Settings Validation

**Decision:** Validate on save, show errors in UI

**Validation Rules:**

```python
# services/user_settings_service.py

class SettingsValidationError(Exception):
    """Raised when settings validation fails."""
    pass


def validate_model_settings(
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int
) -> None:
    """
    Validate model settings.

    Raises:
        SettingsValidationError: If validation fails
    """
    # Temperature range
    if not 0 <= temperature <= 2:
        raise SettingsValidationError(
            "Temperature must be between 0 and 2"
        )

    # Max tokens range
    if not 100 <= max_tokens <= 4000:
        raise SettingsValidationError(
            "Max tokens must be between 100 and 4000"
        )

    # Provider exists
    valid_providers = ["openai", "anthropic", "groq", "ollama"]
    if provider not in valid_providers:
        raise SettingsValidationError(
            f"Invalid provider: {provider}"
        )

    # Model available for provider
    available_models = get_models_for_provider(provider)
    if model not in available_models:
        raise SettingsValidationError(
            f"Model {model} not available for provider {provider}"
        )


def validate_context_settings(
    name: str,
    url: str,
    description: str
) -> None:
    """
    Validate context settings.

    Raises:
        SettingsValidationError: If validation fails
    """
    # URL format (if provided)
    if url and not url.startswith(("http://", "https://")):
        raise SettingsValidationError(
            "URL must start with http:// or https://"
        )

    # Name length
    if len(name) > 100:
        raise SettingsValidationError(
            "Name must be less than 100 characters"
        )

    # Description length
    if len(description) > 500:
        raise SettingsValidationError(
            "Description must be less than 500 characters"
        )
```

**UI Error Display:**

```python
# ui/pages/settings.py

async def save_settings(
    user_state: Dict[str, Any],
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    theme: str,
    context_name: str,
    context_url: str,
    context_description: str,
    business_type: Optional[str],
    location: Optional[str]
) -> Tuple[Dict[str, Any], str]:
    """
    Save user settings with validation.

    Returns:
        Tuple of (updated_user_state, status_message)
    """
    from services.user_settings_service import (
        UserSettingsService,
        SettingsValidationError
    )

    try:
        # Validate
        validate_model_settings(provider, model, temperature, max_tokens)
        validate_context_settings(context_name, context_url, context_description)

        # Save
        user_id = user_state.get("user_id")
        service = UserSettingsService()

        success = await service.save_settings(
            user_id=user_id,
            model_config={
                "provider": provider,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            appearance={"theme": theme},
            context={
                "name": context_name,
                "url": context_url,
                "description": context_description,
                "business_type": business_type,
                "location": location
            }
        )

        if success:
            # Update user state
            user_state["settings"] = {...}
            return user_state, "✅ Settings saved successfully"
        else:
            return user_state, "❌ Failed to save settings"

    except SettingsValidationError as e:
        return user_state, f"❌ Validation error: {str(e)}"
    except Exception as e:
        logging.error(f"Settings save error: {e}")
        return user_state, "❌ An error occurred while saving settings"


# Wire up to save button
save_btn.click(
    fn=save_settings,
    inputs=[...],
    outputs=[user_state, status_message],  # Show status in UI
    js="() => { window.location.href = '/?reload=1'; }"  # Reload after save
)
```

### 6. Page Reload After Save

**Decision:** Ship with reload now, optimize later

**Current Approach (Acceptable for MVP):**
```javascript
// Full page reload after save
js="() => { window.location.href = '/?reload=1'; }"
```

**Pros:**
- Simple, reliable
- Ensures settings applied everywhere
- No state synchronization issues

**Cons:**
- Not ideal UX (brief flash)
- Loses any unsaved chat state

**Future Optimization (Deferred to UI-008-settings-optimization):**
```python
# Use Gradio state updates instead of reload
save_btn.click(
    fn=save_settings,
    inputs=[...],
    outputs=[
        user_state,           # Update state
        model_selector,       # Update chat page model selector
        theme_state,          # Update theme
        status_message        # Show success message
    ]
    # No JS redirect - updates via Gradio state
)
```

**Trade-off Decision:** Ship with reload for UI-005-settings-page, optimize in future task.

---

## Implementation Plan

### Phase 1: Database Persistence (Week 1)

**Tasks:**
1. Implement `UserSettingsService.save_settings()`
2. Implement `UserSettingsService.get_all_settings()`
3. Add validation functions
4. Unit tests for service

**Files to Modify:**
```
services/
├── user_settings_service.py    # Add save/load methods
└── __init__.py                   # Export SettingsValidationError

tests/
└── services/
    └── test_user_settings_service.py  # Add tests
```

**Success Criteria:**
- [ ] Settings saved to database
- [ ] Settings retrieved on page load
- [ ] Validation prevents invalid data
- [ ] Tests pass (80%+ coverage)

### Phase 2: Model Integration (Week 1)

**Tasks:**
1. Import `model_config_service` in settings page
2. Replace hardcoded lists with service calls
3. Add mode-aware provider filtering
4. Test dynamic dropdowns

**Files to Modify:**
```
ui/pages/
└── settings.py                  # Use model_config_service

services/
└── model_config_service.py      # Add get_provider_choices_for_mode()
```

**Success Criteria:**
- [ ] Provider dropdown populated dynamically
- [ ] Model dropdown populated dynamically
- [ ] SEO coach sees restricted providers only
- [ ] Workbench sees all providers

### Phase 3: Authentication Integration (Week 2)

**Tasks:**
1. Implement basic session check
2. Add user info display
3. Enable database save for authenticated users
4. Fallback to localStorage for guests

**Files to Create:**
```
services/
└── auth_service.py              # Basic session validation
```

**Files to Modify:**
```
ui/pages/
└── settings.py                  # Check auth status, load user info

main.py                           # Add session middleware
```

**Success Criteria:**
- [ ] Authenticated users see profile info
- [ ] Settings saved to database for authenticated
- [ ] Settings saved to localStorage for guests
- [ ] Sign out clears session

### Phase 4: Settings Load on Init (Week 2)

**Tasks:**
1. Load settings on settings page render
2. Load settings on chat page init (model selector)
3. Apply theme on app load
4. Add error handling for load failures

**Files to Modify:**
```
ui/pages/
├── settings.py                  # Load on render
└── chat.py                      # Load model config on init

ui/
└── mode_factory.py              # Load theme on app create
```

**Success Criteria:**
- [ ] Settings page shows saved values
- [ ] Chat page model selector shows user's choice
- [ ] Theme applied on app load
- [ ] Defaults used if no saved settings

### Phase 5: Error Handling & Polish (Week 3)

**Tasks:**
1. Add status messages to UI
2. Handle save failures gracefully
3. Add loading spinners
4. Test edge cases

**Files to Modify:**
```
ui/pages/
└── settings.py                  # Add status messages, loading states
```

**Success Criteria:**
- [ ] User sees "Saving..." spinner
- [ ] User sees success/error messages
- [ ] Validation errors shown in UI
- [ ] Failed saves don't lose data

---

## Testing Strategy

### Unit Tests (Priority: HIGH)

```python
# tests/services/test_user_settings_service.py

async def test_save_settings_authenticated_user(db):
    """Test saving settings for authenticated user."""
    service = UserSettingsService(db)

    user_id = "test-user-123"
    model_config = {
        "provider": "openai",
        "model": "gpt-4-turbo",
        "temperature": 0.7,
        "max_tokens": 2000
    }

    success = await service.save_settings(
        user_id=user_id,
        model_config=model_config,
        appearance={"theme": "Dark"},
        context={}
    )

    assert success == True

    # Verify saved
    loaded = await service.get_all_settings(user_id)
    assert loaded["model_config"]["provider"] == "openai"
    assert loaded["appearance"]["theme"] == "Dark"


async def test_settings_validation_invalid_temperature():
    """Test validation rejects invalid temperature."""
    from services.user_settings_service import (
        validate_model_settings,
        SettingsValidationError
    )

    with pytest.raises(SettingsValidationError):
        validate_model_settings(
            provider="openai",
            model="gpt-4-turbo",
            temperature=3.0,  # Invalid: > 2
            max_tokens=2000
        )


async def test_load_settings_with_defaults(db):
    """Test loading settings merges with defaults."""
    service = UserSettingsService(db)

    user_id = "new-user"

    # No settings saved yet
    loaded = await service.get_all_settings(user_id)

    # Should return defaults
    assert loaded["model_config"]["provider"] == "openai"
    assert loaded["appearance"]["theme"] == "Auto"
```

### Integration Tests (Priority: HIGH)

```python
# tests/integration/test_settings_persistence.py

async def test_settings_persist_across_page_reload(browser):
    """Test settings persist after page reload."""

    # Navigate to settings
    await browser.goto("http://localhost:8000/settings")

    # Change model to claude
    model_dropdown = await browser.query_selector('[data-testid="model-dropdown"]')
    await model_dropdown.select_option("claude-sonnet-4-5")

    # Save
    save_btn = await browser.query_selector('[data-testid="save-btn"]')
    await save_btn.click()

    # Wait for reload
    await browser.wait_for_url("http://localhost:8000/")

    # Navigate back to settings
    await browser.goto("http://localhost:8000/settings")

    # Verify model still selected
    model_dropdown = await browser.query_selector('[data-testid="model-dropdown"]')
    value = await model_dropdown.get_attribute("value")
    assert value == "claude-sonnet-4-5"


async def test_model_config_service_integration():
    """Test settings page uses model_config_service."""
    from ui.pages.settings import render_models_tab
    from services.model_config_service import model_config_service

    # Get choices from service
    provider_choices, default_provider = model_config_service.get_provider_choices_for_ui()

    # Render tab
    config = {"labels": {...}, "allow_model_selection": True}
    components = render_models_tab(config)

    # Verify dropdown uses service choices
    assert components["provider"].choices == provider_choices
```

### Manual Testing Checklist

**Settings Persistence:**
- [ ] Change model settings, save, reload → Settings persist
- [ ] Change theme, save, reload → Theme applied
- [ ] Change context, save, reload → Context persists
- [ ] Sign out, sign in → Settings loaded for user
- [ ] Guest mode (not signed in) → Settings saved to localStorage

**Validation:**
- [ ] Set temperature to 3.0 → Error message shown
- [ ] Set max tokens to 10000 → Error message shown
- [ ] Enter invalid URL → Error message shown
- [ ] Leave required field empty → Error message shown

**Model Integration:**
- [ ] Provider dropdown shows dynamic list
- [ ] Model dropdown updates when provider changes
- [ ] SEO coach mode shows restricted providers
- [ ] Workbench mode shows all providers

**Authentication:**
- [ ] Signed in user sees profile info
- [ ] Guest sees sign-in button
- [ ] Sign out clears settings from UI
- [ ] Settings saved to database (authenticated) vs localStorage (guest)

**Error Handling:**
- [ ] Network error during save → Error message shown
- [ ] Database write failure → Error message shown
- [ ] Validation error → Specific error message shown
- [ ] Settings page still usable after error

---

## Success Criteria

### Functional Requirements

- [ ] **Settings Persistence**: All tabs save to database (authenticated) or localStorage (guest)
- [ ] **Settings Load**: Settings loaded on page render with correct values
- [ ] **Model Integration**: Provider/model dropdowns populated from `model_config_service`
- [ ] **Validation**: Invalid settings rejected with clear error messages
- [ ] **Error Handling**: Graceful handling of save failures, network errors
- [ ] **Authentication**: Basic session check, user info display, sign out
- [ ] **Page Reload**: Settings applied after reload (current approach acceptable)

### Code Quality

- [ ] **80%+ test coverage** for `UserSettingsService`
- [ ] **All validation rules tested** with unit tests
- [ ] **Integration tests** for save/load cycle
- [ ] **Type hints** on all new functions
- [ ] **Error logging** for debugging

### User Experience

- [ ] User sees "Saving..." indicator during save
- [ ] User sees success/error message after save
- [ ] Validation errors displayed clearly
- [ ] Settings page loads within 2 seconds
- [ ] No data loss on save failure

---

## Known Issues & Open Questions

### ⚠️ DECISIONS NEEDED

1. **Guest Settings Expiration**
   - **Question:** Should localStorage settings expire after X days?
   - **Options:**
     - A) Never expire (persist forever)
     - B) Expire after 30 days
     - C) Clear on browser close (sessionStorage)
   - **Recommendation:** A) Never expire (better UX)

2. **Settings Migration**
   - **Question:** What happens when we add new settings?
   - **Options:**
     - A) Merge with defaults (recommended)
     - B) Prompt user to review settings
     - C) Reset to defaults
   - **Recommendation:** A) Merge (seamless)

3. **Theme Application**
   - **Question:** Should theme change require page reload?
   - **Current:** Yes (full reload)
   - **Future:** No (Gradio state update)
   - **Recommendation:** Ship with reload, optimize later

### 🔍 TESTING GAPS

1. **Browser Compatibility**
   - localStorage may not work in incognito/private mode
   - Need to test graceful degradation

2. **Concurrent Saves**
   - What if user opens settings in two tabs and saves different values?
   - Need to test last-write-wins behavior

3. **Large Settings Objects**
   - What if context description is 10,000 characters?
   - Need to test localStorage size limits

---

## Migration Path

### From UI-005-multi-page-app

**What's Already Working:**
- Settings page renders
- All components defined
- Placeholder save/reset handlers

**What This Task Adds:**
- Real save implementation
- Settings load on init
- Validation and error handling
- Model service integration

**Migration Steps:**
1. Implement `UserSettingsService.save_settings()`
2. Update settings.py to use service
3. Add validation
4. Test with existing UI-005 structure

**No Breaking Changes:**
- UI-005 placeholder handlers replaced
- No changes to component structure
- No changes to routing
- Backward compatible

---

## Future Enhancements (Post UI-005-settings-page)

**Deferred to Later Tasks:**

1. **UI-008-settings-optimization**
   - Remove page reload after save
   - Use Gradio state updates
   - Instant theme switching

2. **UI-007-authentication**
   - Real credential validation
   - OAuth integration
   - Password reset
   - User registration

3. **UI-009-settings-sync**
   - Sync settings across devices
   - Settings import/export
   - Settings history/versioning

4. **Phase 3: Advanced Settings**
   - Custom theme editor
   - Advanced model parameters
   - Keyboard shortcuts configuration
   - Accessibility settings

---

## References

- **UI-005-multi-page-app**: Routing foundation (prerequisite)
- **UI-005-target-ux-implementation**: Visual design (iOS toggles, Ubuntu font)
- **Existing Service**: `services/model_config_service.py`
- **Database Schema**: `models/database.py` (user_settings table)
- **Auth Patterns**: To be defined in UI-007-authentication

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-27 | Use database for authenticated, localStorage for guests | Consistent with existing patterns, enables future sync |
| 2025-10-27 | Import model_config_service (not hardcoded lists) | Use existing service, enhance as needed |
| 2025-10-27 | Ship with page reload, optimize later | Simple, reliable, optimize in future task |
| 2025-10-27 | Basic auth integration (full auth in UI-007) | Unblock settings persistence, full auth later |
| 2025-10-27 | Validate on save, show errors in UI | Prevent invalid data, good UX |
| 2025-10-27 | Merge saved settings with defaults | Seamless migration when new settings added |

---

**End of UI-005-settings-page Architecture Document**
