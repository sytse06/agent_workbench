# UI-001: Target User Experience & Interface Behavior

## Status

**Status**: Draft
**Date**: October 15, 2025
**Author**: my cousing
**Related Doc**: `UI-001-pwa-app-user-settings.md`

## 1. Introduction

This document defines the target user experience (UX) and interface (UI) behaviors for the Agent Workbench PWA. It complements the technical specifications in `UI-001-pwa-app-user-settings.md` by providing concrete guidance on the remaining "loose ends" related to user-facing interactions.

## 2. Main Interface & Navigation

The application will feature a minimal, content-focused design consistent with an Ollama-style interface. See @/designs/screenshots for examples.

![Example_main_screen.png](/Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/design/screenshots/Example_main_screen.png)

**Main View & Dynamic Logo**:

- The primary view is a floating chatbox centered on the screen. When the chat is idle, the main logo (`logo.png`) is displayed prominently above the chat history.
- **Dynamic Behavior**: As soon as the assistant starts processing the query, the central logo fades out and a waiting symbol is displayed. This could be the juggler_icon.png which is throwing circus balls in the air or a dynamic version of the planner_review_icon.png. Via streaming agents actions are visible and the tokens come streaming in. Icons such as analyze_web_results_icon.png, lightbulb_icon.png, search_icon.png can be used for this.

  ![Scherm­afbeelding 2025-10-20 om 11.16.34.png](/Users/sytsevanderschaaf/Desktop/Scherm­afbeelding%202025-10-20%20om%2011.16.34.png)

- The logo reappears when the user starts a new conversation by clicking on the chat_add_icon.png (left top corner).

**Chat Input Bar**: The text input area at the bottom contains several integrated controls:

- **Type in chat and submit message**: An up-arrow icon (↑) on the right serves as the submit button. It is pale when no text is entered and becomes black with arrow in it when message is typed.
- **Web Search**: A globe icon (🌐) on the left, which can be toggled to allow the agent to access the internet for its response.
- **Model Selector**: The name of the currently selected model (e.g., "gpt-oss:20b") is displayed. Tapping it opens a dropdown to switch models.
- **File Upload/Submit**: Files can be drag and dropped in the chatbox. A file symbol and the filename is visible above the chat text.
- **Submit query**: In the right corner a submit button is visible (arrow_up_in_circle_icon.png). When a query is submitted a processing icon is visible when the answer is processed (processing_icon.png). When the answer is finished the submit icon is greyed out.

**Chat History Panel**:

![Example_expanded_sidebar_left.png](/Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/design/screenshots/Example_expanded_sidebar_left.png)

- **Trigger**: A left sidebar icon is located in the top-left corner of the screen (view_sidebar_icon.png). Next to that is an icon to start a new chat (chat_add_icon.png).
- **Action 1**: Tapping this sidebar slider icon slides the chat history panel in from the left. The panel contains a list of previous conversations and a prominent "New Chat" button at the top. Tapping the sidebar icon again  will close it and will show the icon for new chat next to it.
- **Action 2**: When the button for a new chat is clicked the chatbox will be cleared and the user can type a new message. When the left sidebar is visible a new chat button is visible with on the left the new chat button.

**Settings Access**:

- **Trigger**: A gear icon (⚙️) is located in the top-right corner of the screen.
- **Action**: Tapping the gear icon navigates the user to the dedicated `/settings` page.

![Example_settings_screen.png](/Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/design/screenshots/Example_settings_screen.png)

## 3. Logging in

    The login is located in the settings page. In the top of the settings page users see their login name and registered email address. They have the option to sign in or sign out and manage their account.

- **Trigger**: A gear icon (⚙️) is located in the top-right corner of the screen.

- **Action**: When signing in users see their login name and registered email address at the top of the settings page.

![Example_login.png](/Users/sytsevanderschaaf/Documents/Dev/Projects/agent_workbench/design/screenshots/Example_login.png)

To ensure users are aware of the application's connectivity status, a clear visual indicator will be implemented.

- **Visual Indicator**:
  - A small icon in the top right corner will be persistently displayed in the main header, to the left of the settings (gear) icon (cloud_on_icon.png).
  - **Online State**: The icon will be a simple cloud (☁️) when online.
  - **Offline State**: The icon will be a cloud with a slash through it (cloud_off_icon.png). This state is active when the browser detects it is offline OR when "Airplane mode" is enabled in the settings.
- **Graceful Degradation**: When the app is in an offline state:
  - The model selector in the chat input will be disabled and filtered, showing only locally available models.
  - Any UI elements related to cloud-based services (e.g., "Upgrade" button, websearch, API key inputs in settings) will be grayed out and disabled.
  - **User Feedback**: If a user attempts an action that requires an internet connection (like selecting a disabled cloud model), a toast notification will appear at the bottom of the screen with the message: "This feature requires an internet connection."

## 4. Responsive Layouts

The PWA must be fully responsive and functional across desktop, tablet, and mobile devices.

- **Main Chat Interface**:
  - **Desktop/Tablet (Landscape)**: The chat history panel is hidden by default and must be opened via the top-left view_sidebar_icon.png.
  - **Mobile/Tablet (Portrait)**: The chat history panel is hidden by default and must be opened via the top-left view_sidebar_icon.png.
- **Settings Page**:
  - **Desktop**: The settings page is horizontally scrollable.
  - **Mobile**: The settings page is horizontally scrollable.

## 5. User Feedback & Notifications

The interface will provide clear, non-intrusive feedback for user actions.

- **Saving Settings**:
  - **On Success**: When settings are saved successfully, a temporary toast notification appears with the message: "Settings saved."
  - **On Error**: If saving fails, a toast notification appears with the message: "Error: Could not save settings."
- **Security Confirmation**:
  - **Trigger**: When a user toggles an option in the Advanced settings.
  - **UI**: A modal dialog will appear, requiring confirmation.
  - **Content**:
    - **Title**: "Security Warning"
    - **Body**: "Enabling this feature will allow other devices on your local network to access Ollama. Are you sure you want to proceed?"
    - **Actions**: "Cancel" and "Confirm" buttons.

## 6. PWA-Specific UX Flows

- **Application Installation Prompt**:
  - **Strategy**: A "gentle" prompt will be used to encourage installation without being intrusive.
  - **Trigger**: The installation prompt (e.g., a banner or a small "Install" button appearing in the header) will only be shown after the user has demonstrated engagement, such as after sending 3-5 messages.
- **Share Target Flow**:
  - **Initial State**: When a user shares content (a URL, text, or file) to the app, they are redirected to the main chat interface (`/`). A new conversation is created.
  - **Pre-filled Message**: The chat input box is pre-filled with the shared content and automatically sent.
    - **URL**: `Shared URL: [the shared url]`
    - **Text**: `Shared Text: "[the shared text]"`
    - **File**: `Processing shared file: [filename]`
  - **Loading State**: While the agent processes this initial message, the chat input is disabled, and a "Thinking..." indicator is shown. This prevents the user from sending a follow-up message before the initial context is established.

## 7. Agent Feedback & Loading States

To manage user expectations during long wait times for agentic responses, a combination of transparency and immediate feedback will be used.

- **Initial Feedback**: The moment a user sends a query:
  
  - The submit button (↑ arrow_up_in_circle_icon.png) transforms into a "Generating" button (processing_icon.png).
  - A new message bubble appears instantly with a "Thinking..." status.

- **Agentic Transparency (The "Work")**:
  
  - This "Thinking..." bubble will update in real-time to show the agent's high-level plan or current action. This makes the wait feel productive.
  - The status updates should be visually distinct from the final answer (e.g., have a different background color or a preceding icon).
  - **Example Statuses**:
    - `[Agent] 🔍 Searching the web for "PWA best practices"...`
    - `[Agent] 📚 Reading 3 articles...`
    - `[Agent] ✨ Compiling the answer...`

  ![Scherm­afbeelding 2025-10-20 om 11.16.34.png](/Users/sytsevanderschaaf/Desktop/Scherm­afbeelding%202025-10-20%20om%2011.16.34.png)

- **Streaming Response (The "Answer")**:
  
  - Once the agent begins formulating its final response, a *new*, separate message bubble will appear.
  - This new bubble will stream the answer token-by-token, providing immediate progress to the user.
  - The "Show Work" bubble remains above the final answer, and could be made collapsible for a cleaner view after the fact.

## 8. Font

In the @/design/assets directory you find the type font we are going to use in the webapp. This will be the Ubuntu type font.

## 9. Theming & Appearance

The application will provide users with control over its visual theme.

- **Location**: The theme setting is located in the "Account" tab of the settings page.
- **UI Control**: A segmented control or button group will provide three options:
  - **Light**: Forces the application into light mode.
  - **Dark**: Forces the application into dark mode.
  - **Auto**: Automatically syncs with the user's operating system theme preference.
- **Behavior**:
  - The "Auto" setting is the default for all new users.
  - The selected theme is applied instantly across the entire application.
  - The choice is saved and persists across sessions and devices for the logged-in user.
