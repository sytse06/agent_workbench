# UI-001: Target UX/UI Definition

## Overview
This document defines the high-level UX/UI requirements for the Agent Workbench. The design philosophy is "Ollama-Inspired": a minimal, content-focused interface with a floating chatbox, dynamic elements, and IOS-style controls.

## 1. Main Chat Interface
**Goal**: A compliant, minimal interface that prioritizes conversation.

### Layout & Visuals
- **Floating Chatbox**: The chat input area floats in the lower-middle of the screen, detached from the bottom edge.
- **Dynamic Logo**: 
    - A centralized logo is prominent in the empty state.
    - The logo fades out when processing/streaming begins.
    - Specific icons are used for different states (e.g., `juggler_icon` for processing, `cloud_on/off` for connectivity).
- **Typography**: Ubuntu font family used throughout for a modern, clean look.

### Interaction
- **Input Bar**:
    - Full-width text input.
    - **No inline model selectors** (moved to Settings to reduce clutter).
    - Submit button changes state (arrow for ready, processing icon for active).
- **Agent Transparency**: 
    - Use a "Two-Bubble" pattern:
        1.  **Status Bubble**: Shows agent's plan/actions (e.g., "Searching web...", "Reading articles...").
        2.  **Answer Bubble**: Streams the final response.

## 2. Navigation Sidebar
**Goal**: Quick access to history without cluttering the main view.

### Behavior
- **Trigger**: Top-left "Sidebar" icon (`view_sidebar_icon`) toggles the panel.
- **Animation**: Slides in from the left side (overlay on mobile, push/resize on desktop).
- **Content**:
    - **New Chat**: Prominent button at the top to clear context and reset the view.
    - **History**: List of previous conversations grouped by date (Today, Yesterday, Last 7 Days).
- **Responsiveness**:
    - **Desktop**: 300px fixed width.
    - **Mobile**: Full-screen overlay.

## 3. Settings Interface
**Goal**: A streamlined, single-view configuration page.

### Layout
- **Access**: Top-right "Gear" icon.
- **Structure**: **Single-scroll vertical layout** (replacing previous tabbed interface).
- **User Profile**: Top section displaying user status/account actions.

### Controls
- **Toggle Switches**: iOS-style rounded sliders (green active state) instead of standard checkboxes.
- **Theme**: Options for Light, Dark, and Auto (system sync).
- **Connectivity**: 
    - Visual indicators for Online/Offline status.
    - Functional degradation when offline (e.g., restricted model list).

## 4. Connectivity & Responsiveness
- **Status Indicator**: Cloud icon in the top-right header shows real-time online/offline status.
- **Mobile-First**: All layouts (chat, sidebar, settings) must adapt fluidly to mobile (<768px), tablet, and desktop breakpoints.
