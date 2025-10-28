# UI-005 Implementation Order

**Status:** Ready for Implementation
**Created:** 2025-01-27
**Decision:** Option B - Minimal Style with Phased Visual Enhancement
**Dependencies:** UI-004 (PWA + existing settings complete)

---

## Executive Summary

This document defines the implementation order for UI-005, which refactors the UI from environment-specific mounting to Gradio native routing with configuration-driven mode separation.

**Architecture Decision:** Model selector in settings page (not in chat input bar)
**Route Decision:** Root route at `/` (not `/app`)
**Approach:** Phased delivery (foundation → visual polish)

---

## Document Alignment

After choosing **Option B**, the following documents are now aligned:

| Document | Purpose | Key Decision |
|----------|---------|--------------|
| **UI-005-multi-page-app.md** | Routing foundation | Root route at `/`, mode factory pattern |
| **UI-005-chat-page.md** | Minimal chat interface | Chatbox + input only, sidebar feature-flagged |
| **UI-005-settings-page.md** | Settings with model controls | Model selector HERE (moved from chat) |
| **UI-005-target-ux-implementation.md** | Visual polish layer | Ubuntu font, dynamic logo, connectivity status |

**All documents updated** to reflect:
- ✅ Model selector in settings (not chat input)
- ✅ Root route at `/` (not `/app`)
- ✅ Phased delivery (functional foundation → visual polish)

---

## Implementation Phases

### **Phase 1: Routing Foundation** (Week 1)

**Goal:** Multipage routing with mode factory pattern

**Tasks:**
1. Create `ui/pages/` directory structure
2. Create `ui/styles.py` with `SHARED_CSS`
3. Create `ui/pages/chat.py` (minimal render function)
4. Create `ui/pages/settings.py` (placeholder render function)
5. Create `ui/mode_factory_v2.py` with `build_gradio_app(config)`
6. Update `main.py` to use new mode factory

**Deliverable:**
- Routing works (can navigate between `/` and `/settings`)
- Both modes use same code with different config
- Always-define component pattern in place
- Single `queue()` call in `main.py`

**Success Criteria:**
- [ ] Navigate from `/` to `/settings` without page reload
- [ ] Workbench mode shows different config than SEO coach
- [ ] No console errors or warnings
- [ ] Back button navigates correctly
- [ ] PWA manifest updated to `start_url: "/"`

**Reference:** UI-005-multi-page-app.md (lines 1170-1246)

---

### **Phase 2: Minimal Chat + Settings** (Week 2)

**Goal:** Functional chat and settings without visual polish

**Tasks:**

**Chat Page:**
1. Implement `ui/pages/chat.py` render function
   - Chatbox (gr.Chatbot)
   - Text input (gr.Textbox)
   - Send button (gr.Button)
   - NO model selector (moved to settings)
2. Wire `handle_chat_message` (reuse existing)
3. Test chat functionality

**Settings Page:**
1. Implement `ui/pages/settings.py` render function
   - User profile section (if authenticated)
   - Account section (theme radio)
   - Models section (provider, model, parameters)
   - Company section (SEO coach only)
   - Advanced section (debug mode checkbox)
2. Implement settings persistence
   - Database for authenticated users
   - localStorage for guests
3. Wire model config service
   - Load dynamic provider/model lists
   - Save selections to database
4. Test settings save/load

**Deliverable:**
- Chat works with model controls in settings
- Settings persist across page reloads
- Model selection affects chat responses
- Standard Gradio styling (no custom CSS yet)

**Success Criteria:**
- [ ] Can send messages and receive responses
- [ ] Model selector in settings updates chat model
- [ ] Settings persist after page reload
- [ ] Theme selection works (Light/Dark/Auto)
- [ ] Company section visible in SEO coach mode only
- [ ] Settings save to database for authenticated users
- [ ] Settings save to localStorage for guests

**Reference:**
- UI-005-chat-page.md (lines 559-603)
- UI-005-settings-page.md (lines 119-252)

---

### **Phase 3: Conversation History Sidebar** (Week 3)

**Goal:** Add conversation history sidebar (feature-flagged)

**Tasks:**
1. Create `ui/components/sidebar.py`
   - Conversation list (grouped by date)
   - Card-based UI (title, timestamp, preview)
   - Click to load conversation
2. Implement sidebar toggle logic
   - Hybrid approach (state + CSS + click-away)
   - gr.State for visibility
   - CSS animation for smooth transition
   - Click-away to collapse
3. Implement conversation loading
   - Fetch from `/api/v1/conversations/{id}`
   - Load messages into chatbot
   - Custom JavaScript event pattern
4. Add feature flag
   - `SHOW_CONV_BROWSER` environment variable
   - Enabled in workbench by default
   - Disabled in SEO coach initially
5. Test sidebar functionality

**Deliverable:**
- Sidebar shows conversation history (workbench only)
- Clicking conversation loads it into chatbot
- Toggle button and click-away work
- Smooth animation
- Feature flag controls visibility

**Success Criteria:**
- [ ] Sidebar visible in workbench mode (flag enabled)
- [ ] Sidebar hidden in SEO coach mode (flag disabled)
- [ ] Conversation list fetches from API
- [ ] Clicking card loads conversation into chatbot
- [ ] Toggle button collapses/expands sidebar
- [ ] Click-away collapses sidebar
- [ ] Animation is smooth (300ms transition)
- [ ] ARIA attributes set correctly
- [ ] Empty state shows helpful message
- [ ] User isolation enforced (can't see others' conversations)

**Reference:** UI-005-chat-page.md (lines 96-333)

---

### **Phase 4: Visual Polish** (Week 4)

**Goal:** Apply Ollama-inspired visual design

**Tasks:**

**Ubuntu Font:**
1. Copy font files to `static/assets/fonts/`
2. Create `static/assets/css/fonts.css` with `@font-face` declarations
3. Update Gradio theme to use Ubuntu font
4. Test font rendering

**iOS-Style Toggles:**
1. Create `static/assets/css/ios-toggles.css`
2. Apply to all checkboxes in settings
3. Test toggle animation

**Dynamic Logo:**
1. Create `ui/components/dynamic_logo.py`
2. Logo visible in idle state
3. Logo fades during processing
4. Processing icon appears
5. Logo returns on new chat

**Connectivity Status:**
1. Add cloud on/off icon in header
2. JavaScript to detect `navigator.onLine`
3. Update icon based on status
4. Disable cloud features when offline

**Theme System:**
1. Create `themes/ollama_light.py`
2. Create `themes/ollama_dark.py`
3. Create `themes/ollama_auto.py`
4. Wire theme selection to settings

**CSS Refinements:**
1. Create `static/assets/css/ollama-chat.css`
2. Create `static/assets/css/ollama-settings.css`
3. Responsive breakpoints (desktop, tablet, mobile)
4. Smooth animations and transitions

**Deliverable:**
- Interface matches Ollama-style design
- Ubuntu font throughout
- iOS-style toggles in settings
- Dynamic logo behavior
- Connectivity indicator
- Light/Dark/Auto themes

**Success Criteria:**
- [ ] Ubuntu font loads and applies correctly
- [ ] iOS toggles animate smoothly
- [ ] Logo fades during processing
- [ ] Connectivity icon shows online/offline state
- [ ] Theme selection works (Light/Dark/Auto)
- [ ] Responsive on mobile (320px+)
- [ ] Visual match >90% to design screenshots
- [ ] No font flash (FOUT) on page load

**Reference:** UI-005-target-ux-implementation.md (lines 620-993)

---

## Testing Strategy

### Phase 1 Tests
```bash
# Unit tests
pytest tests/ui/test_mode_factory.py -v
pytest tests/ui/test_routing.py -v

# Integration tests
pytest tests/integration/test_multipage_routing.py -v

# Manual tests
- Navigate between / and /settings
- Test in both modes (workbench, SEO coach)
- Verify PWA manifest routes
```

### Phase 2 Tests
```bash
# Unit tests
pytest tests/ui/test_chat_page.py -v
pytest tests/ui/test_settings_page.py -v

# Integration tests
pytest tests/integration/test_settings_persistence.py -v
pytest tests/integration/test_model_config_service.py -v

# Manual tests
- Send message, verify model from settings used
- Change model in settings, verify chat updates
- Test theme selection
- Test settings persistence
```

### Phase 3 Tests
```bash
# Unit tests
pytest tests/ui/test_sidebar.py -v

# Integration tests
pytest tests/integration/test_conversation_loading.py -v
pytest tests/integration/test_user_isolation.py -v

# E2E tests (Playwright)
pytest tests/e2e/test_sidebar_animation.py -v
pytest tests/e2e/test_conversation_click.py -v

# Manual tests
- Test sidebar toggle
- Test click-away
- Test conversation loading
- Test feature flag (enable/disable)
```

### Phase 4 Tests
```bash
# Visual tests
pytest tests/ui/test_ubuntu_font.py -v
pytest tests/ui/test_ios_toggles.py -v

# Chrome DevTools MCP (manual)
- Test font loading (network requests)
- Test CSS theme variables
- Screenshot comparison with design
- Test responsive breakpoints
```

---

## Deployment Strategy

### Development Testing
```bash
# Terminal 1: Start app in workbench mode
APP_MODE=workbench SHOW_CONV_BROWSER=true make start-app-verbose

# Terminal 2: Start app in SEO coach mode
APP_MODE=seo_coach SHOW_CONV_BROWSER=false make start-app

# Test both modes side-by-side
```

### Staging Deployment
```bash
# Deploy to staging from develop branch
git checkout develop
git pull origin develop

# Build staging image
make docker-staging

# Deploy to staging environment
# Verify both modes work
# Run full test suite
```

### Production Rollout

**Phase 1-3 (Functional Foundation):**
```bash
# Merge to main after staging validation
git checkout main
git merge develop

# Tag release
git tag -a v2.1.0-routing -m "UI-005: Multipage routing foundation"

# Build production images
make docker-prod

# Deploy workbench image
# - Sidebar enabled (SHOW_CONV_BROWSER=true)
# - Test with internal users

# Deploy SEO coach image (1 week later)
# - Sidebar disabled (SHOW_CONV_BROWSER=false)
# - Monitor user feedback
```

**Phase 4 (Visual Polish):**
```bash
# Merge visual enhancements after foundation stable
git tag -a v2.1.1-visual -m "UI-005: Ollama-style visual polish"

# Gradual rollout
# - Deploy to 10% of users
# - Monitor performance
# - Deploy to 100% if metrics good
```

---

## Rollback Plan

### Phase 1 Rollback
```bash
# If routing breaks, revert to old mounting
git revert <commit-hash>
git push origin main

# Emergency: Environment variable flag
USE_OLD_MOUNTING=true make start-app
```

### Phase 2 Rollback
```bash
# Settings page issues: disable route
ENABLE_SETTINGS_PAGE=false make start-app

# Chat page issues: revert to old chat page
git checkout main -- ui/app.py
```

### Phase 3 Rollback
```bash
# Sidebar issues: disable feature flag
SHOW_CONV_BROWSER=false make start-app

# No code changes needed
```

### Phase 4 Rollback
```bash
# Visual issues: disable custom CSS
USE_OLLAMA_THEME=false make start-app

# Or revert theme files only
git checkout main -- themes/
git checkout main -- static/assets/css/
```

---

## Success Metrics

### Phase 1 (Routing)
- [ ] Zero console errors in browser
- [ ] Navigation latency <100ms
- [ ] All tests pass (100%)
- [ ] PWA installation works

### Phase 2 (Functional)
- [ ] Chat functionality identical to current
- [ ] Settings save success rate >99%
- [ ] Model switching works 100% of time
- [ ] Test coverage >80%

### Phase 3 (Sidebar)
- [ ] Conversation loading <500ms
- [ ] Sidebar animation smooth (60fps)
- [ ] User isolation 100% (security critical)
- [ ] Feature flag toggles correctly

### Phase 4 (Visual)
- [ ] Visual match >90% to design
- [ ] Font loading <200ms
- [ ] No layout shift (CLS <0.1)
- [ ] Lighthouse score >90

---

## Risk Mitigation

### High Risk Items

**1. Breaking Existing Chat**
- **Mitigation:** Reuse existing `handle_chat_message`
- **Test:** Comprehensive regression tests before deploy
- **Rollback:** Keep old UI files until validation complete

**2. Settings Data Loss**
- **Mitigation:** No database schema changes
- **Test:** Load existing settings in new UI
- **Rollback:** Settings format unchanged, rollback is safe

**3. User Isolation Breach (Sidebar)**
- **Mitigation:** Use existing authentication/authorization
- **Test:** Security-specific tests (user can't load others' convos)
- **Rollback:** Disable feature flag immediately

**4. Performance Regression**
- **Mitigation:** Monitor response times, add caching
- **Test:** Load testing with 100+ conversations
- **Rollback:** Disable sidebar if performance impact >10%

### Medium Risk Items

**1. PWA Manifest Issues**
- **Mitigation:** Test PWA installation before deploy
- **Test:** Install on iOS and Android
- **Rollback:** Revert manifest to old structure

**2. Font Loading Flash (FOUT)**
- **Mitigation:** Preload fonts in manifest
- **Test:** Hard refresh, throttled network
- **Rollback:** Remove custom fonts, use system fonts

**3. Theme Not Persisting**
- **Mitigation:** Test localStorage and DB persistence
- **Test:** Clear cache, reload, verify theme
- **Rollback:** Default to Light theme

---

## Documentation Updates

### User-Facing Docs
- [ ] Update README with new routes
- [ ] Update PWA installation guide
- [ ] Add settings page documentation
- [ ] Add conversation history guide (if sidebar enabled)

### Developer Docs
- [ ] Update CLAUDE.md with new UI structure
- [ ] Document mode factory pattern
- [ ] Document always-define component pattern
- [ ] Document settings persistence strategy

### API Docs
- [ ] No API changes (reusing existing endpoints)
- [ ] Document conversation list format
- [ ] Document settings format

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| **Phase 1** | Week 1 | Routing foundation |
| **Phase 2** | Week 2 | Minimal chat + settings |
| **Phase 3** | Week 3 | Conversation sidebar |
| **Phase 4** | Week 4 | Visual polish |
| **Testing** | Ongoing | All phases |
| **Deployment** | Week 5 | Production rollout |

**Total:** 5 weeks (phased delivery)

---

## Next Steps

**Immediate (Now):**
1. Review and approve this implementation order
2. Create feature branch: `git checkout -b feature/UI-005-routing-foundation`
3. Begin Phase 1 implementation

**This Week:**
1. Complete Phase 1 (routing foundation)
2. Test thoroughly with both modes
3. Merge to develop
4. Begin Phase 2

**Next Week:**
1. Complete Phase 2 (minimal chat + settings)
2. Test settings persistence
3. Begin Phase 3 (sidebar)

**Month 2:**
1. Complete Phase 3 (sidebar)
2. Complete Phase 4 (visual polish)
3. Deploy to production

---

## References

- **UI-005-multi-page-app.md** - Routing foundation architecture
- **UI-005-chat-page.md** - Minimal chat page with sidebar
- **UI-005-settings-page.md** - Settings page with model controls
- **UI-005-target-ux-implementation.md** - Visual polish specifications
- **CLAUDE.md** - Project overview and patterns
- **UI-004** - Current PWA implementation (baseline)

---

**End of Document**
