# UI-005: Ollama Design Implementation - Task List

**Status:** Ready for Implementation
**Created:** 2025-01-27
**Phase:** 4 (Visual Polish)
**Dependencies:** Phase 1-3 complete (routing, chat, settings, sidebar)
**CSS Foundation:** Normalized architecture complete (main.css, shared.css, fonts.css)

---

## Executive Summary

This document provides a comprehensive task list for implementing the Ollama-inspired visual design. The design is analyzed from screenshots in `/design/screenshots/` and will be implemented as `ollama-design.css` (separate file for safety, then optionally merged into `shared.css` after validation).

**Strategy:** Incremental implementation with component-by-component validation.

**Design References:**
- `/design/screenshots/Example_main_screen.png` - Main chat interface (idle state)
- `/design/screenshots/Example_expanded_sidebar_left.png` - Sidebar expanded
- `/design/screenshots/Example_settings_screen.png` - Settings modal
- `/design/screenshots/Example_login.png` - Login integration
- `UI-004-target-ux-ref.md` - Design specifications

---

## Design Analysis from Screenshots

### Main Screen (Example_main_screen.png)

**Visual Characteristics:**
- **Background:** Very light gray (#f5f5f5 or #f8f8f8)
- **Layout:** Centered, floating, minimal
- **Logo:** Large llama icon, center-top, prominent when idle
- **Whitespace:** Generous padding, breathing room
- **Window:** macOS-style with traffic lights (red/yellow/green dots)

**Top Navigation (Top-Left):**
- Sidebar toggle icon (hamburger/grid icon)
- New chat icon (red circle with plus)
- Both appear to be ~32px icons with subtle hover states

**Chat Input Bar (Bottom-Center):**
- Width: ~600-800px, centered
- Background: White with subtle shadow
- Border-radius: 12px
- Height: ~48px
- Components (left to right):
  1. Globe icon (web search toggle) - Blue (#007AFF)
  2. Text input "Send a message" - Light gray placeholder
  3. Model selector "gpt-oss:20b" - Dropdown with chevron
  4. Submit button - Circular (32px), gray when disabled

**Typography:**
- Font family: Clean, modern (likely Ubuntu per spec)
- Input text: ~15px
- Model selector: ~13px

### Sidebar Expanded (Example_expanded_sidebar_left.png)

**Sidebar Characteristics:**
- Width: ~280px
- Background: White
- Border-right: 1px solid light gray
- Shadow: Subtle right shadow
- Position: Fixed left, slides in/out
- Z-index: High (above main content)

**Sidebar Header:**
- "New Chat" button - Red circle icon + text
- Padding: 16px

**Conversation List:**
- Each item: Single line, truncated with "..."
- Text color: Dark gray (#333)
- Hover: Light gray background
- Active: Slightly darker background
- Font-size: 14px
- Padding: 8px 16px
- No visible dividers (clean list)

**Date Grouping:**
- "This week" header visible in screenshot
- Headers appear to be subtle (gray, small font)

### Settings Screen (Example_settings_screen.png)

**Settings Modal:**
- Width: ~600px
- Background: White
- Border-radius: 12px (rounded corners)
- Shadow: Strong shadow (0 8px 32px rgba(0,0,0,0.12))
- Position: Centered overlay
- Padding: 24px

**Header:**
- "Settings" title - Left-aligned, ~18px bold
- X close button - Top-right corner (32px clickable area)
- macOS traffic lights (red/yellow/green) top-left

**User Profile Section:**
- Username "sytse" - Bold, ~16px
- Email "sytse@schaaaf.nl" - Gray, ~14px
- Three buttons: "Upgrade" (dark), "Manage" (outline), "Sign out" (outline)
- Avatar icon - Right side (robot icon, ~48px)

**Settings Sections:**
- Each section has icon + title + description
- Toggles: iOS-style (rounded, animated)
- Sliders: Custom styled with value labels
- Spacing: 20px between sections
- Dividers: Subtle gray lines (1px, #e0e0e0)

**Toggle Switch Design:**
- Width: 44px
- Height: 24px
- Border-radius: 12px (pill shape)
- Off state: Light gray background
- On state: Blue background (#007AFF)
- Knob: White circle, 20px, smooth transition

---

## CSS Architecture Decision

**Create:** `static/assets/css/ollama-design.css` (~400 lines)

**Import Pattern:**
```css
/* main.css */
@import url('fonts.css');
@import url('shared.css');
@import url('ollama-design.css');  /* NEW - Ollama visual layer */
```

**Why Separate File:**
- ✅ Safe to test without breaking existing UI
- ✅ Easy to enable/disable with feature flag
- ✅ Clear separation: functional (shared.css) vs visual (ollama-design.css)
- ✅ Can merge into shared.css later once validated

**Alternative (if preferred):**
- Merge directly into `shared.css` (increases from 148 → ~550 lines)

---

## Implementation Tasks

### Phase 4.1: Foundation & Variables (Week 1, Day 1-2)

**Goal:** Set up CSS file structure and design system variables

#### Task 4.1.1: Create File Structure
- [ ] Create `static/assets/css/ollama-design.css`
- [ ] Add header comment with design attribution
- [ ] Import in `main.css`: `@import url('ollama-design.css');`
- [ ] Update `sw.js` to cache `ollama-design.css`
- [ ] Test file loads correctly (check DevTools Network tab)

**File:** `static/assets/css/ollama-design.css` (initial structure)
```css
/*
 * Ollama Design Layer
 *
 * Visual design implementation based on:
 * - /design/screenshots/Example_main_screen.png
 * - /design/screenshots/Example_expanded_sidebar_left.png
 * - /design/screenshots/Example_settings_screen.png
 *
 * This file contains Ollama-specific visual styling.
 * Functional styles remain in shared.css.
 */

/* ===== DESIGN TOKENS ===== */
/* Add CSS variables here */

/* ===== LAYOUT ===== */
/* Centered floating chat layout */

/* ===== COMPONENTS ===== */
/* Individual UI components */
```

#### Task 4.1.2: Define CSS Variables (Design Tokens)
- [ ] Extract colors from screenshots (use color picker)
- [ ] Define spacing scale (4px, 8px, 12px, 16px, 20px, 24px)
- [ ] Define typography scale
- [ ] Define shadow styles
- [ ] Define border-radius values
- [ ] Define transition timings

**Code:**
```css
:root {
    /* ===== COLORS ===== */

    /* Backgrounds */
    --ollama-bg: #f8f8f8;
    --ollama-surface: #ffffff;
    --ollama-sidebar-bg: #ffffff;

    /* Text */
    --ollama-text-primary: #333333;
    --ollama-text-secondary: #666666;
    --ollama-text-tertiary: #999999;
    --ollama-placeholder: #bbbbbb;

    /* Borders */
    --ollama-border: #e0e0e0;
    --ollama-border-light: #f0f0f0;

    /* Accent colors */
    --ollama-blue: #007AFF;
    --ollama-red: #FF3B30;
    --ollama-green: #34C759;
    --ollama-gray: #8E8E93;

    /* Button states */
    --ollama-btn-disabled: #e0e0e0;
    --ollama-btn-hover: #f5f5f5;
    --ollama-btn-active: #000000;

    /* ===== SPACING ===== */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 12px;
    --space-lg: 16px;
    --space-xl: 20px;
    --space-2xl: 24px;
    --space-3xl: 32px;
    --space-4xl: 40px;

    /* ===== TYPOGRAPHY ===== */
    --font-size-xs: 12px;
    --font-size-sm: 13px;
    --font-size-base: 15px;
    --font-size-lg: 16px;
    --font-size-xl: 18px;

    /* ===== SHADOWS ===== */
    --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.10);
    --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.12);

    /* ===== BORDERS ===== */
    --radius-sm: 6px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 9999px;

    /* ===== TRANSITIONS ===== */
    --transition-fast: 150ms ease;
    --transition-base: 250ms ease;
    --transition-slow: 350ms ease;
}
```

#### Task 4.1.3: Dark Mode Variables
- [ ] Analyze dark mode requirements from UI-004-target-ux-ref.md
- [ ] Define dark mode color palette
- [ ] Create `@media (prefers-color-scheme: dark)` block
- [ ] Test auto-detection with OS settings
- [ ] Create manual override classes (`.light-mode`, `.dark-mode`)

**Code:**
```css
@media (prefers-color-scheme: dark) {
    :root {
        /* Dark mode colors */
        --ollama-bg: #1a1a1a;
        --ollama-surface: #2a2a2a;
        --ollama-sidebar-bg: #242424;

        --ollama-text-primary: #e0e0e0;
        --ollama-text-secondary: #a0a0a0;
        --ollama-text-tertiary: #707070;
        --ollama-placeholder: #505050;

        --ollama-border: #404040;
        --ollama-border-light: #333333;

        /* Accent colors stay same or adjust slightly */
    }
}

/* Manual theme overrides */
body.light-mode {
    /* Force light theme */
}

body.dark-mode {
    /* Force dark theme */
}
```

**Validation:**
- [ ] Open DevTools → Elements → Computed styles
- [ ] Verify CSS variables are defined
- [ ] Toggle dark mode in OS → verify variables update
- [ ] Screenshot comparison with design

**Estimated Time:** 2-3 hours

---

### Phase 4.2: Main Layout (Week 1, Day 2-3)

**Goal:** Implement centered floating chat layout

#### Task 4.2.1: Page Background
- [ ] Set body background to `--ollama-bg`
- [ ] Remove default Gradio background
- [ ] Test background covers full viewport

**Code:**
```css
body {
    background: var(--ollama-bg);
    font-family: var(--font-family); /* From fonts.css */
}

/* Override Gradio default */
.gradio-container {
    background: transparent !important;
}
```

#### Task 4.2.2: Centered Chat Container
- [ ] Create `.ollama-chat-container` class
- [ ] Center horizontally with max-width
- [ ] Add vertical padding for breathing room
- [ ] Test on desktop (1920px), tablet (768px), mobile (375px)

**Code:**
```css
.ollama-chat-container {
    max-width: 800px;
    margin: 0 auto;
    padding: var(--space-4xl) var(--space-xl);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    gap: var(--space-2xl);
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .ollama-chat-container {
        padding: var(--space-2xl) var(--space-lg);
    }
}

@media (max-width: 480px) {
    .ollama-chat-container {
        padding: var(--space-xl) var(--space-md);
    }
}
```

#### Task 4.2.3: Main Logo (Idle State)
- [ ] Style `.ollama-logo` container
- [ ] Center logo horizontally
- [ ] Add vertical padding
- [ ] Prepare for fade animation (next phase)

**Code:**
```css
.ollama-logo {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: var(--space-4xl) 0;
    opacity: 1;
    transition: opacity var(--transition-base);
}

.ollama-logo img {
    width: 64px;
    height: 64px;
    /* Logo from design: llama icon */
}

/* Hidden state (for processing) - implemented in Phase 4.3 */
.ollama-logo.hidden {
    opacity: 0;
    pointer-events: none;
}
```

**Validation:**
- [ ] Logo appears centered
- [ ] Layout responsive on mobile
- [ ] Background color matches design
- [ ] No horizontal scroll on any viewport size

**Estimated Time:** 2-3 hours

---

### Phase 4.3: Chat Input Bar (Week 1, Day 3-4)

**Goal:** Implement bottom-centered input bar with integrated controls

#### Task 4.3.1: Input Bar Container
- [ ] Create `.ollama-input-bar` class
- [ ] Position sticky at bottom
- [ ] White background with shadow
- [ ] Rounded corners (12px)
- [ ] Flexbox layout for children

**Code:**
```css
.ollama-input-bar {
    position: sticky;
    bottom: var(--space-xl);
    width: 100%;
    max-width: 800px;
    margin: 0 auto;

    background: var(--ollama-surface);
    border: 1px solid var(--ollama-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-md);

    padding: var(--space-md);
    display: flex;
    align-items: center;
    gap: var(--space-md);

    transition: box-shadow var(--transition-fast);
}

.ollama-input-bar:focus-within {
    box-shadow: var(--shadow-lg);
    border-color: var(--ollama-blue);
}

@media (max-width: 768px) {
    .ollama-input-bar {
        bottom: var(--space-md);
        border-radius: var(--radius-md);
    }
}
```

#### Task 4.3.2: Web Search Toggle (Globe Icon)
- [ ] Style globe icon button
- [ ] Blue color when active
- [ ] Gray when inactive
- [ ] Smooth transition
- [ ] Touch-friendly size (44x44px min for mobile)

**Code:**
```css
.ollama-web-search {
    width: 32px;
    height: 32px;
    min-width: 32px; /* Prevent shrinking */

    display: flex;
    align-items: center;
    justify-content: center;

    border: none;
    background: transparent;
    border-radius: var(--radius-sm);

    color: var(--ollama-gray);
    cursor: pointer;

    transition: all var(--transition-fast);
}

.ollama-web-search:hover {
    background: var(--ollama-btn-hover);
}

.ollama-web-search.active {
    color: var(--ollama-blue);
    background: rgba(0, 122, 255, 0.1);
}

/* Icon size */
.ollama-web-search svg,
.ollama-web-search img {
    width: 20px;
    height: 20px;
}

/* Mobile touch target */
@media (max-width: 768px) {
    .ollama-web-search {
        width: 44px;
        height: 44px;
    }
}
```

#### Task 4.3.3: Message Input Field
- [ ] Style text input
- [ ] Flexible width (flex: 1)
- [ ] No border (borderless design)
- [ ] Placeholder styling
- [ ] Focus state

**Code:**
```css
.ollama-message-input {
    flex: 1;

    border: none;
    background: transparent;
    outline: none;

    font-size: var(--font-size-base);
    color: var(--ollama-text-primary);
    font-family: var(--font-family);

    padding: var(--space-sm) 0;
}

.ollama-message-input::placeholder {
    color: var(--ollama-placeholder);
}

/* Remove autofill background */
.ollama-message-input:-webkit-autofill {
    -webkit-box-shadow: 0 0 0 1000px var(--ollama-surface) inset;
    -webkit-text-fill-color: var(--ollama-text-primary);
}
```

#### Task 4.3.4: Model Selector Dropdown
- [ ] Style model dropdown
- [ ] Small font (13px)
- [ ] Chevron indicator
- [ ] Hover state
- [ ] Click state

**Code:**
```css
.ollama-model-selector {
    display: flex;
    align-items: center;
    gap: var(--space-xs);

    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-sm);

    font-size: var(--font-size-sm);
    color: var(--ollama-text-secondary);

    background: transparent;
    border: none;
    cursor: pointer;

    transition: background var(--transition-fast);
}

.ollama-model-selector:hover {
    background: var(--ollama-btn-hover);
}

/* Chevron icon */
.ollama-model-selector::after {
    content: '▼';
    font-size: 10px;
    margin-left: var(--space-xs);
}
```

#### Task 4.3.5: Submit Button (Three States)
- [ ] Create circular button
- [ ] State 1: Pale gray (disabled, no text entered)
- [ ] State 2: Black (active, message typed)
- [ ] State 3: Processing (green with animation)
- [ ] Smooth transitions between states

**Code:**
```css
.ollama-submit-btn {
    width: 32px;
    height: 32px;
    min-width: 32px;

    border-radius: var(--radius-full);
    border: none;

    display: flex;
    align-items: center;
    justify-content: center;

    cursor: pointer;
    transition: all var(--transition-base);

    /* Default: Disabled state (no message) */
    background: var(--ollama-btn-disabled);
    color: var(--ollama-text-tertiary);
}

/* State 2: Active (message entered) */
.ollama-submit-btn.active {
    background: var(--ollama-btn-active);
    color: white;
    cursor: pointer;
}

.ollama-submit-btn.active:hover {
    transform: scale(1.05);
    box-shadow: var(--shadow-sm);
}

/* State 3: Processing */
.ollama-submit-btn.processing {
    background: var(--ollama-green);
    color: white;
    animation: pulse 1.5s ease-in-out infinite;
    cursor: not-allowed;
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.6;
    }
}

/* Icon inside button */
.ollama-submit-btn svg {
    width: 16px;
    height: 16px;
}

/* Mobile touch target */
@media (max-width: 768px) {
    .ollama-submit-btn {
        width: 44px;
        height: 44px;
    }
}
```

**Validation:**
- [ ] Input bar appears at bottom, centered
- [ ] White background with subtle shadow
- [ ] Globe icon toggles blue on click
- [ ] Text input expands to fill space
- [ ] Model selector shows current model
- [ ] Submit button gray by default
- [ ] Submit button turns black when typing
- [ ] All components align properly

**Estimated Time:** 4-5 hours

---

### Phase 4.4: Top Navigation (Week 1, Day 4-5)

**Goal:** Implement top navigation bar with sidebar toggle and settings icon

#### Task 4.4.1: Navigation Bar Container
- [ ] Create `.ollama-top-nav` class
- [ ] Fixed positioning at top
- [ ] Full width with max-width constraint
- [ ] Flexbox for left/right alignment
- [ ] Subtle bottom border

**Code:**
```css
.ollama-top-nav {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 900;

    background: var(--ollama-surface);
    border-bottom: 1px solid var(--ollama-border-light);

    padding: var(--space-md) var(--space-xl);
}

.ollama-top-nav-inner {
    max-width: 1400px;
    margin: 0 auto;

    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Add top padding to body to account for fixed nav */
body {
    padding-top: 56px; /* Height of nav bar */
}

@media (max-width: 768px) {
    .ollama-top-nav {
        padding: var(--space-sm) var(--space-md);
    }

    body {
        padding-top: 48px;
    }
}
```

#### Task 4.4.2: Left Controls (Sidebar Toggle + New Chat)
- [ ] Style sidebar toggle button
- [ ] Style new chat button (red circle icon)
- [ ] Flexbox layout with gap
- [ ] Icon buttons with hover states

**Code:**
```css
.ollama-nav-left {
    display: flex;
    align-items: center;
    gap: var(--space-md);
}

.ollama-nav-btn {
    width: 32px;
    height: 32px;

    display: flex;
    align-items: center;
    justify-content: center;

    border: none;
    background: transparent;
    border-radius: var(--radius-sm);

    color: var(--ollama-text-secondary);
    cursor: pointer;

    transition: all var(--transition-fast);
}

.ollama-nav-btn:hover {
    background: var(--ollama-btn-hover);
    color: var(--ollama-text-primary);
}

/* New chat button - red circle */
.ollama-new-chat-btn {
    position: relative;
}

.ollama-new-chat-btn::before {
    content: '';
    position: absolute;
    width: 6px;
    height: 6px;
    background: var(--ollama-red);
    border-radius: 50%;
    top: 4px;
    right: 4px;
}

/* Mobile touch targets */
@media (max-width: 768px) {
    .ollama-nav-btn {
        width: 44px;
        height: 44px;
    }
}
```

#### Task 4.4.3: Right Controls (Cloud Status + Settings)
- [ ] Style settings gear icon
- [ ] Style cloud connectivity icon
- [ ] Online state (cloud icon)
- [ ] Offline state (cloud with slash)

**Code:**
```css
.ollama-nav-right {
    display: flex;
    align-items: center;
    gap: var(--space-md);
}

/* Cloud connectivity indicator */
.ollama-cloud-status {
    width: 32px;
    height: 32px;

    display: flex;
    align-items: center;
    justify-content: center;

    color: var(--ollama-text-tertiary);
}

.ollama-cloud-status.online {
    color: var(--ollama-blue);
}

.ollama-cloud-status.offline {
    color: var(--ollama-red);
}

/* Settings button - uses same .ollama-nav-btn styles */
```

**Validation:**
- [ ] Navigation bar fixed at top
- [ ] Sidebar toggle on left
- [ ] New chat button with red indicator
- [ ] Settings icon on right
- [ ] Cloud status shows online/offline
- [ ] All hover states work
- [ ] Body content not hidden under nav

**Estimated Time:** 3-4 hours

---

### Phase 4.5: Sidebar Styling (Week 2, Day 1-2)

**Goal:** Style conversation history sidebar to match design

#### Task 4.5.1: Sidebar Container
- [ ] Style `.ollama-sidebar` container
- [ ] Fixed position, left side
- [ ] Slide-in animation
- [ ] Right border and shadow
- [ ] Z-index above main content

**Code:**
```css
.ollama-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;

    width: 280px;

    background: var(--ollama-sidebar-bg);
    border-right: 1px solid var(--ollama-border);
    box-shadow: 2px 0 12px rgba(0, 0, 0, 0.08);

    z-index: 950;

    /* Slide in/out animation */
    transform: translateX(-100%);
    transition: transform var(--transition-base);

    overflow-y: auto;
}

.ollama-sidebar.open {
    transform: translateX(0);
}

/* Backdrop (click-away) */
.ollama-sidebar-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    background: rgba(0, 0, 0, 0.2);
    z-index: 940;

    opacity: 0;
    pointer-events: none;
    transition: opacity var(--transition-base);
}

.ollama-sidebar-backdrop.visible {
    opacity: 1;
    pointer-events: auto;
}

@media (max-width: 768px) {
    .ollama-sidebar {
        width: 85%;
        max-width: 320px;
    }
}
```

#### Task 4.5.2: Sidebar Header (New Chat Button)
- [ ] Style header section
- [ ] New chat button with red icon
- [ ] Padding and border

**Code:**
```css
.ollama-sidebar-header {
    padding: var(--space-lg);
    border-bottom: 1px solid var(--ollama-border-light);
}

.ollama-sidebar-new-chat {
    width: 100%;

    display: flex;
    align-items: center;
    gap: var(--space-md);

    padding: var(--space-md);
    border-radius: var(--radius-md);
    border: 1px solid var(--ollama-border);
    background: transparent;

    font-size: var(--font-size-base);
    color: var(--ollama-text-primary);
    cursor: pointer;

    transition: all var(--transition-fast);
}

.ollama-sidebar-new-chat:hover {
    background: var(--ollama-btn-hover);
}

.ollama-sidebar-new-chat .icon {
    width: 20px;
    height: 20px;
    color: var(--ollama-red);
}
```

#### Task 4.5.3: Conversation List Items
- [ ] Style individual conversation items
- [ ] Truncate long titles with ellipsis
- [ ] Hover and active states
- [ ] Date group headers

**Code:**
```css
.ollama-conversation-list {
    padding: var(--space-sm) 0;
}

/* Date group header */
.ollama-conversation-group {
    padding: var(--space-md) var(--space-lg);
    font-size: var(--font-size-xs);
    font-weight: 600;
    color: var(--ollama-text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Individual conversation item */
.ollama-conversation-item {
    padding: var(--space-md) var(--space-lg);

    font-size: var(--font-size-sm);
    color: var(--ollama-text-primary);

    cursor: pointer;
    transition: background var(--transition-fast);

    /* Truncate with ellipsis */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.ollama-conversation-item:hover {
    background: var(--ollama-btn-hover);
}

.ollama-conversation-item.active {
    background: rgba(0, 122, 255, 0.1);
    color: var(--ollama-blue);
    font-weight: 500;
}
```

**Validation:**
- [ ] Sidebar slides in from left
- [ ] New chat button at top
- [ ] Conversation list displays correctly
- [ ] Items truncate with "..." when too long
- [ ] Hover states work
- [ ] Click-away closes sidebar
- [ ] Backdrop appears when open

**Estimated Time:** 3-4 hours

---

### Phase 4.6: Settings Modal (Week 2, Day 2-3)

**Goal:** Style settings page as centered modal dialog

#### Task 4.6.1: Modal Overlay & Container
- [ ] Create overlay backdrop
- [ ] Center modal dialog
- [ ] Rounded corners with shadow
- [ ] macOS-style window chrome

**Code:**
```css
/* Modal overlay */
.ollama-settings-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(4px);

    display: flex;
    align-items: center;
    justify-content: center;

    z-index: 1000;
    padding: var(--space-2xl);
}

/* Modal dialog */
.ollama-settings-modal {
    width: 100%;
    max-width: 600px;
    max-height: 80vh;

    background: var(--ollama-surface);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-lg);

    overflow: hidden;
    display: flex;
    flex-direction: column;
}

@media (max-width: 768px) {
    .ollama-settings-overlay {
        padding: 0;
    }

    .ollama-settings-modal {
        max-width: 100%;
        max-height: 100vh;
        border-radius: 0;
    }
}
```

#### Task 4.6.2: Settings Header
- [ ] Title on left
- [ ] Close button (X) on right
- [ ] macOS traffic lights
- [ ] Bottom border

**Code:**
```css
.ollama-settings-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: var(--space-2xl);
    border-bottom: 1px solid var(--ollama-border-light);
}

/* macOS traffic lights */
.ollama-traffic-lights {
    display: flex;
    gap: var(--space-sm);
}

.ollama-traffic-light {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

.ollama-traffic-light.red { background: #FF5F57; }
.ollama-traffic-light.yellow { background: #FFBD2E; }
.ollama-traffic-light.green { background: #28CA42; }

/* Title */
.ollama-settings-title {
    font-size: var(--font-size-xl);
    font-weight: 600;
    color: var(--ollama-text-primary);
}

/* Close button */
.ollama-close-btn {
    width: 32px;
    height: 32px;

    display: flex;
    align-items: center;
    justify-content: center;

    border: none;
    background: transparent;
    border-radius: var(--radius-sm);

    color: var(--ollama-text-tertiary);
    cursor: pointer;

    transition: all var(--transition-fast);
}

.ollama-close-btn:hover {
    background: var(--ollama-btn-hover);
    color: var(--ollama-text-primary);
}
```

#### Task 4.6.3: User Profile Section
- [ ] Style user info (username + email)
- [ ] Three buttons (Upgrade, Manage, Sign out)
- [ ] Avatar on right
- [ ] Divider below

**Code:**
```css
.ollama-user-profile {
    display: flex;
    justify-content: space-between;
    align-items: center;

    padding: var(--space-2xl);
    border-bottom: 1px solid var(--ollama-border-light);
}

.ollama-user-info {
    flex: 1;
}

.ollama-username {
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--ollama-text-primary);
    margin-bottom: var(--space-xs);
}

.ollama-user-email {
    font-size: var(--font-size-sm);
    color: var(--ollama-text-secondary);
    margin-bottom: var(--space-lg);
}

/* Action buttons */
.ollama-user-actions {
    display: flex;
    gap: var(--space-sm);
}

.ollama-user-btn {
    padding: var(--space-sm) var(--space-lg);
    border-radius: var(--radius-sm);

    font-size: var(--font-size-sm);
    font-weight: 500;

    cursor: pointer;
    transition: all var(--transition-fast);
}

.ollama-user-btn.primary {
    background: var(--ollama-text-primary);
    color: white;
    border: none;
}

.ollama-user-btn.secondary {
    background: transparent;
    color: var(--ollama-text-primary);
    border: 1px solid var(--ollama-border);
}

.ollama-user-btn:hover {
    opacity: 0.8;
}

/* Avatar */
.ollama-user-avatar {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    background: var(--ollama-btn-hover);

    display: flex;
    align-items: center;
    justify-content: center;
}
```

#### Task 4.6.4: Settings Content (Scrollable)
- [ ] Scrollable content area
- [ ] Section spacing
- [ ] Icon + title + description layout

**Code:**
```css
.ollama-settings-content {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-2xl);
}

/* Individual setting section */
.ollama-setting {
    display: flex;
    align-items: flex-start;
    gap: var(--space-lg);

    padding: var(--space-xl) 0;
    border-bottom: 1px solid var(--ollama-border-light);
}

.ollama-setting:last-child {
    border-bottom: none;
}

/* Icon */
.ollama-setting-icon {
    width: 24px;
    height: 24px;
    color: var(--ollama-text-secondary);
    flex-shrink: 0;
}

/* Content */
.ollama-setting-content {
    flex: 1;
}

.ollama-setting-title {
    font-size: var(--font-size-base);
    font-weight: 500;
    color: var(--ollama-text-primary);
    margin-bottom: var(--space-xs);
}

.ollama-setting-description {
    font-size: var(--font-size-sm);
    color: var(--ollama-text-secondary);
    line-height: 1.5;
}

/* Control (toggle, slider, etc.) */
.ollama-setting-control {
    margin-top: var(--space-md);
}
```

#### Task 4.6.5: iOS-Style Toggle Switches
- [ ] Create custom toggle switch
- [ ] Pill shape (44x24px)
- [ ] Animated knob
- [ ] Off state (gray) → On state (blue)

**Code:**
```css
.ollama-toggle {
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
}

/* Hide default checkbox */
.ollama-toggle input {
    opacity: 0;
    width: 0;
    height: 0;
}

/* Toggle track */
.ollama-toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;

    background: var(--ollama-gray);
    border-radius: 12px;

    transition: all var(--transition-base);
}

/* Toggle knob */
.ollama-toggle-slider::before {
    position: absolute;
    content: "";
    height: 20px;
    width: 20px;
    left: 2px;
    bottom: 2px;

    background: white;
    border-radius: 50%;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);

    transition: all var(--transition-base);
}

/* Checked state */
.ollama-toggle input:checked + .ollama-toggle-slider {
    background: var(--ollama-blue);
}

.ollama-toggle input:checked + .ollama-toggle-slider::before {
    transform: translateX(20px);
}

/* Focus state */
.ollama-toggle input:focus + .ollama-toggle-slider {
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.2);
}
```

#### Task 4.6.6: Custom Slider
- [ ] Style range slider
- [ ] Value labels
- [ ] Track and thumb styling

**Code:**
```css
.ollama-slider-container {
    width: 100%;
}

.ollama-slider {
    width: 100%;
    height: 4px;
    border-radius: 2px;
    background: var(--ollama-border);
    outline: none;

    -webkit-appearance: none;
    appearance: none;
}

/* Track */
.ollama-slider::-webkit-slider-track {
    width: 100%;
    height: 4px;
    background: var(--ollama-border);
    border-radius: 2px;
}

.ollama-slider::-moz-range-track {
    width: 100%;
    height: 4px;
    background: var(--ollama-border);
    border-radius: 2px;
}

/* Thumb */
.ollama-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 16px;
    height: 16px;
    background: var(--ollama-blue);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.ollama-slider::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: var(--ollama-blue);
    border-radius: 50%;
    cursor: pointer;
    border: none;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* Value labels */
.ollama-slider-labels {
    display: flex;
    justify-content: space-between;
    margin-top: var(--space-sm);
    font-size: var(--font-size-xs);
    color: var(--ollama-text-tertiary);
}
```

**Validation:**
- [ ] Settings modal appears centered
- [ ] Close button (X) works
- [ ] User profile section displays correctly
- [ ] iOS toggles animate smoothly
- [ ] Sliders work and show values
- [ ] Content scrolls if too long
- [ ] Mobile responsive

**Estimated Time:** 5-6 hours

---

### Phase 4.7: Message Bubbles & Agent Status (Week 2, Day 3-4)

**Goal:** Style chat messages and agent thinking indicators

#### Task 4.7.1: Message Container
- [ ] Style message wrapper
- [ ] Vertical spacing between messages
- [ ] Max-width for readability

**Code:**
```css
.ollama-messages {
    display: flex;
    flex-direction: column;
    gap: var(--space-lg);
    padding: var(--space-2xl) 0;
}

.ollama-message {
    max-width: 85%;
    animation: fadeIn var(--transition-base);
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

#### Task 4.7.2: User Messages
- [ ] Style user message bubbles
- [ ] Align right
- [ ] Blue background
- [ ] White text

**Code:**
```css
.ollama-message.user {
    align-self: flex-end;
}

.ollama-message-bubble.user {
    background: var(--ollama-blue);
    color: white;

    padding: var(--space-md) var(--space-lg);
    border-radius: var(--radius-lg);
    border-bottom-right-radius: var(--space-xs);

    font-size: var(--font-size-base);
    line-height: 1.5;
    word-wrap: break-word;
}
```

#### Task 4.7.3: Assistant Messages
- [ ] Style assistant bubbles
- [ ] Align left
- [ ] Light gray background
- [ ] Dark text

**Code:**
```css
.ollama-message.assistant {
    align-self: flex-start;
}

.ollama-message-bubble.assistant {
    background: var(--ollama-surface);
    color: var(--ollama-text-primary);
    border: 1px solid var(--ollama-border);

    padding: var(--space-md) var(--space-lg);
    border-radius: var(--radius-lg);
    border-bottom-left-radius: var(--space-xs);

    font-size: var(--font-size-base);
    line-height: 1.5;
    word-wrap: break-word;
}
```

#### Task 4.7.4: Agent Status Bubble ("Thinking...")
- [ ] Style status indicator
- [ ] Yellow/amber background
- [ ] Icon on left
- [ ] Animated

**Code:**
```css
.ollama-agent-status {
    display: flex;
    align-items: center;
    gap: var(--space-md);

    padding: var(--space-md) var(--space-lg);
    border-radius: var(--radius-lg);

    background: #FFF3CD;
    border: 1px solid #FFD700;
    color: #856404;

    font-size: var(--font-size-sm);
    font-weight: 500;

    animation: slideIn var(--transition-base);
}

.ollama-agent-status .icon {
    width: 20px;
    height: 20px;
    animation: spin 2s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-16px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Different status types */
.ollama-agent-status.searching {
    /* Use search_icon.png */
}

.ollama-agent-status.analyzing {
    /* Use analyze_web_results_icon.png */
}

.ollama-agent-status.thinking {
    /* Use lightbulb_icon.png */
}
```

#### Task 4.7.5: Streaming Response Animation
- [ ] Cursor blink animation
- [ ] Typing indicator

**Code:**
```css
.ollama-typing-indicator {
    display: inline-block;
    width: 4px;
    height: 16px;
    background: var(--ollama-text-primary);
    animation: blink 1s step-end infinite;
    margin-left: 2px;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}
```

**Validation:**
- [ ] Messages display correctly
- [ ] User messages align right (blue)
- [ ] Assistant messages align left (white)
- [ ] Agent status shows with icon
- [ ] Animations smooth
- [ ] Text wraps properly

**Estimated Time:** 3-4 hours

---

### Phase 4.8: Responsive Design (Week 2, Day 4-5)

**Goal:** Ensure all components work on mobile, tablet, desktop

#### Task 4.8.1: Mobile Breakpoints
- [ ] Test on 375px (iPhone SE)
- [ ] Test on 390px (iPhone 12/13)
- [ ] Test on 428px (iPhone Pro Max)
- [ ] Adjust spacing for small screens

**Code:**
```css
/* Mobile portrait (< 480px) */
@media (max-width: 480px) {
    .ollama-chat-container {
        padding: var(--space-xl) var(--space-sm);
    }

    .ollama-input-bar {
        padding: var(--space-sm);
        gap: var(--space-sm);
    }

    .ollama-message {
        max-width: 95%;
    }

    .ollama-logo img {
        width: 48px;
        height: 48px;
    }
}
```

#### Task 4.8.2: Tablet Layout
- [ ] Test on iPad (768px)
- [ ] Test on iPad Pro (1024px)
- [ ] Adjust for landscape orientation

**Code:**
```css
/* Tablet (768px - 1024px) */
@media (min-width: 768px) and (max-width: 1024px) {
    .ollama-chat-container {
        max-width: 700px;
    }

    .ollama-sidebar {
        width: 320px;
    }
}
```

#### Task 4.8.3: Touch Targets
- [ ] Verify all interactive elements ≥ 44x44px on mobile
- [ ] Test tap/click on actual devices
- [ ] Add touch-action CSS where needed

**Code:**
```css
/* Ensure minimum touch target size on mobile */
@media (max-width: 768px) {
    .ollama-nav-btn,
    .ollama-web-search,
    .ollama-submit-btn {
        min-width: 44px;
        min-height: 44px;
    }
}
```

#### Task 4.8.4: Landscape Orientation
- [ ] Handle landscape mode on phones
- [ ] Adjust heights and padding

**Code:**
```css
/* Mobile landscape */
@media (max-height: 600px) and (orientation: landscape) {
    .ollama-logo {
        padding: var(--space-xl) 0;
    }

    .ollama-logo img {
        width: 40px;
        height: 40px;
    }

    .ollama-input-bar {
        bottom: var(--space-sm);
    }
}
```

**Validation:**
- [ ] Test on real devices (iOS, Android)
- [ ] Test with Chrome DevTools device emulation
- [ ] Verify touch targets ≥ 44px
- [ ] No horizontal scroll on any viewport
- [ ] Text remains readable at all sizes

**Estimated Time:** 3-4 hours

---

### Phase 4.9: Dark Mode (Week 3, Day 1)

**Goal:** Implement complete dark mode support

#### Task 4.9.1: Test Auto-Detection
- [ ] Verify `prefers-color-scheme` media query works
- [ ] Test on macOS (System Preferences → Appearance)
- [ ] Test on iOS (Settings → Display → Dark Mode)
- [ ] Ensure variables update correctly

#### Task 4.9.2: Manual Theme Toggle
- [ ] Implement JavaScript theme switcher
- [ ] Add classes to body: `.light-mode`, `.dark-mode`
- [ ] Persist choice to localStorage
- [ ] Wire to settings page theme selector

**JavaScript (add to Gradio custom JS):**
```javascript
function setTheme(theme) {
    document.body.classList.remove('light-mode', 'dark-mode');

    if (theme === 'light') {
        document.body.classList.add('light-mode');
    } else if (theme === 'dark') {
        document.body.classList.add('dark-mode');
    }
    // 'auto' = no class, use media query

    localStorage.setItem('theme', theme);
}

// Load theme on page load
const savedTheme = localStorage.getItem('theme') || 'auto';
if (savedTheme !== 'auto') {
    setTheme(savedTheme);
}
```

#### Task 4.9.3: Dark Mode Refinements
- [ ] Test all components in dark mode
- [ ] Adjust contrast ratios for accessibility
- [ ] Fix any hard-coded colors
- [ ] Test shadows (may need adjustment)

**Validation:**
- [ ] Auto dark mode works (detects OS setting)
- [ ] Manual toggle works (Light/Dark/Auto)
- [ ] Theme persists after page reload
- [ ] All components readable in dark mode
- [ ] WCAG AA contrast ratio met (4.5:1 for text)

**Estimated Time:** 3-4 hours

---

### Phase 4.10: Polish & Animation (Week 3, Day 2-3)

**Goal:** Add subtle animations and micro-interactions

#### Task 4.10.1: Logo Fade Animation
- [ ] Implement fade-out during processing
- [ ] Show processing icon (juggler or spinner)
- [ ] Fade logo back in on idle

**Code:**
```css
/* Already defined in Phase 4.2.3, now wire with JS */

.ollama-logo.processing {
    opacity: 0;
}

.ollama-processing-icon {
    display: none;
    animation: bounce 1s ease-in-out infinite;
}

.ollama-logo.processing + .ollama-processing-icon {
    display: flex;
}

@keyframes bounce {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-8px);
    }
}
```

**JavaScript:**
```javascript
// On message send
document.querySelector('.ollama-logo').classList.add('processing');

// On response complete
document.querySelector('.ollama-logo').classList.remove('processing');
```

#### Task 4.10.2: Toast Notifications
- [ ] Create toast notification component
- [ ] Slide up from bottom
- [ ] Auto-dismiss after 3 seconds

**Code:**
```css
.ollama-toast {
    position: fixed;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);

    padding: var(--space-md) var(--space-xl);
    border-radius: var(--radius-md);

    background: #323232;
    color: white;
    font-size: var(--font-size-sm);
    box-shadow: var(--shadow-lg);

    z-index: 2000;

    opacity: 0;
    transition: all var(--transition-base);
}

.ollama-toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}
```

#### Task 4.10.3: Button Hover Effects
- [ ] Add scale transform on hover
- [ ] Add subtle shadow on hover
- [ ] Smooth transitions

**Code:**
```css
/* Enhance existing button hover states */
.ollama-nav-btn:hover,
.ollama-submit-btn.active:hover {
    transform: scale(1.05);
}

.ollama-nav-btn:active,
.ollama-submit-btn:active {
    transform: scale(0.95);
}
```

#### Task 4.10.4: Loading States
- [ ] Skeleton screens for loading content
- [ ] Shimmer animation

**Code:**
```css
.ollama-skeleton {
    background: linear-gradient(
        90deg,
        var(--ollama-border) 0%,
        var(--ollama-btn-hover) 50%,
        var(--ollama-border) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm);
}

@keyframes shimmer {
    0% {
        background-position: -200% 0;
    }
    100% {
        background-position: 200% 0;
    }
}
```

**Validation:**
- [ ] Logo fades during processing
- [ ] Toasts appear/disappear smoothly
- [ ] Buttons feel responsive
- [ ] Loading states show progress
- [ ] All animations 60fps (no jank)

**Estimated Time:** 4-5 hours

---

### Phase 4.11: Integration & Testing (Week 3, Day 4-5)

**Goal:** Wire CSS to actual Gradio components and test thoroughly

#### Task 4.11.1: Apply Classes to Gradio Components
- [ ] Update `chat.py` to add `elem_classes`
- [ ] Update `settings.py` to add `elem_classes`
- [ ] Update `sidebar.py` to add `elem_classes`

**Example:**
```python
# ui/pages/chat.py
chatbot = gr.Chatbot(
    elem_classes=["ollama-messages"],
    # ...
)

message_input = gr.Textbox(
    elem_classes=["ollama-message-input"],
    # ...
)

submit_btn = gr.Button(
    elem_classes=["ollama-submit-btn"],
    # ...
)
```

#### Task 4.11.2: Cross-Browser Testing
- [ ] Test on Chrome (latest)
- [ ] Test on Firefox (latest)
- [ ] Test on Safari (macOS, iOS)
- [ ] Test on Edge (latest)

#### Task 4.11.3: Accessibility Testing
- [ ] Run Lighthouse audit (target: 90+)
- [ ] Test keyboard navigation (Tab, Enter, Esc)
- [ ] Test screen reader (VoiceOver on macOS)
- [ ] Verify ARIA labels
- [ ] Check color contrast ratios

#### Task 4.11.4: Performance Testing
- [ ] Measure First Contentful Paint (FCP)
- [ ] Measure Largest Contentful Paint (LCP)
- [ ] Measure Cumulative Layout Shift (CLS)
- [ ] Optimize if metrics below threshold

#### Task 4.11.5: Visual Regression Testing
- [ ] Take screenshots of all components
- [ ] Compare with design mockups
- [ ] Note differences and iterate
- [ ] Aim for >90% visual match

**Testing Checklist:**
- [ ] Desktop Chrome - Light mode
- [ ] Desktop Chrome - Dark mode
- [ ] Desktop Firefox - Light mode
- [ ] Desktop Safari - Light mode
- [ ] Mobile Safari (iOS) - Light mode
- [ ] Mobile Chrome (Android) - Light mode
- [ ] Tablet iPad - Light mode
- [ ] Lighthouse score >90
- [ ] Keyboard navigation works
- [ ] No console errors

**Estimated Time:** 6-8 hours

---

## Summary & Timeline

### Total Estimated Time: ~50-60 hours (3 weeks)

**Week 1:**
- Phase 4.1: Foundation & Variables (2-3 hours)
- Phase 4.2: Main Layout (2-3 hours)
- Phase 4.3: Chat Input Bar (4-5 hours)
- Phase 4.4: Top Navigation (3-4 hours)

**Week 2:**
- Phase 4.5: Sidebar Styling (3-4 hours)
- Phase 4.6: Settings Modal (5-6 hours)
- Phase 4.7: Message Bubbles (3-4 hours)
- Phase 4.8: Responsive Design (3-4 hours)

**Week 3:**
- Phase 4.9: Dark Mode (3-4 hours)
- Phase 4.10: Polish & Animation (4-5 hours)
- Phase 4.11: Integration & Testing (6-8 hours)

---

## Success Criteria

### Must Have (P0):
- [ ] All components match design screenshots (>90% visual match)
- [ ] Ubuntu font loads without flash (FOUT)
- [ ] Dark mode works (auto + manual toggle)
- [ ] Responsive on mobile (320px+)
- [ ] Lighthouse score >90
- [ ] Zero console errors
- [ ] All hover/active states work

### Should Have (P1):
- [ ] Smooth animations (60fps)
- [ ] Toast notifications
- [ ] Logo fade during processing
- [ ] Keyboard navigation
- [ ] Touch targets ≥44px on mobile

### Nice to Have (P2):
- [ ] Skeleton loading screens
- [ ] Advanced micro-interactions
- [ ] Scroll animations
- [ ] Haptic feedback (mobile)

---

## Rollback Plan

If Ollama design causes issues:

**Option 1: Feature Flag**
```python
# ui/mode_factory_v2.py
enable_ollama_design = os.getenv("ENABLE_OLLAMA_DESIGN", "false") == "true"

if enable_ollama_design:
    css = """
        @import url('/static/assets/css/main.css');
        @import url('/static/assets/css/ollama-design.css');
    """
else:
    css = "@import url('/static/assets/css/main.css');"
```

**Option 2: Disable CSS Import**
```python
# Remove from main.css
# @import url('ollama-design.css');
```

**Option 3: Revert to Previous Version**
```bash
git checkout main -- static/assets/css/ollama-design.css
# Or delete file entirely
rm static/assets/css/ollama-design.css
```

---

## Post-Implementation

**After Phase 4 Complete:**
1. Get user feedback (internal testing)
2. Iterate based on feedback
3. Consider merging `ollama-design.css` into `shared.css` (if stable)
4. Update documentation with implementation notes
5. Create video walkthrough of design features

**Potential Enhancements (Phase 5):**
- Animated transitions between pages
- Custom scrollbars
- Advanced theme customization
- User-uploaded avatars
- Custom font size controls

---

**End of Document**
