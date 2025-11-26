"""
Chat page - minimal chatbox interface.

NO model controls (moved to settings).
NO sidebar (separate feature - see
    docs/phase2/Feat-dev-plan-chat-history-in-sidebar-in-chatpage.md).

Identical structure for workbench and SEO coach modes - differences
controlled by config labels.
"""

import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import requests  # type: ignore[import-untyped]

from ..components.sidebar import render_sidebar


def svg_to_data_uri(svg_path: str) -> str:
    """
    Convert SVG file to base64 data URI for use in gr.Button(icon=...).

    Gradio's file serving has permission issues with static files.
    Using base64 encoding (like images) instead of URL encoding.

    Args:
        svg_path: Path like "/static/icons/svg/submit_icon_24.svg"

    Returns:
        data:image/svg+xml;base64,... string
    """
    # Remove /static/ prefix properly (not with lstrip which removes characters)
    if svg_path.startswith("/static/"):
        svg_path = svg_path[8:]  # Remove "/static/"

    svg_file = Path(__file__).parent.parent.parent / "static" / svg_path
    svg_content = svg_file.read_bytes()  # Read as bytes for base64
    # Base64 encode the SVG content (like image data URIs)
    encoded = base64.b64encode(svg_content).decode('utf-8')
    return f"data:image/svg+xml;base64,{encoded}"


# Load icons as data URIs at module level (replicating Gradio's built-in icon pattern)
SUBMIT_ICON_DATA_URI = svg_to_data_uri("/static/icons/svg/submit_icon_24.svg")
PROCESSING_ICON_DATA_URI = svg_to_data_uri("/static/icons/svg/processing_icon_24.svg")
ADD_CHAT_ICON_DATA_URI = svg_to_data_uri("/static/icons/svg/add_chat_icon_24.svg")


def render(
    config: Dict[str, Any],
    user_state: gr.State,
    conversation_state: gr.State,
    settings_state: gr.State,
) -> Tuple[Optional[gr.BrowserState], Optional[gr.Dropdown]]:
    """
    Render chat interface with optional sidebar.

    Args:
        config: Mode configuration from mode_factory
        user_state: Shared user session state
        conversation_state: Shared conversation messages state
        settings_state: User settings (model config, theme, context)

    Phase 3: Added conversation history sidebar (feature-flagged)
    """
    print("[DEBUG chat.py] render() CALLED")
    print(f"  config['show_conv_browser']: {config.get('show_conv_browser', False)}")

    # BrowserState for conversations list (sidebar)
    # Note: Individual conversation storage removed - gr.ChatInterface manages history
    conversations_list_storage = gr.BrowserState(
        default_value=[],  # List of conversation metadata
        storage_key="agent_workbench_conversations_list",
    )

    # Render sidebar if enabled
    sidebar_visible = None
    collapse_btn = None
    conv_list = None
    clear_storage_btn = None
    sidebar_new_chat_btn = None  # New chat button inside sidebar
    if config.get("show_conv_browser", False):
        (
            sidebar_visible,
            conv_list,
            sidebar_new_chat_btn,  # Button inside sidebar
            collapse_btn,
            clear_storage_btn,
        ) = render_sidebar(config, user_state)

    # Main layout
    with gr.Row():
        # Main chat area
        with gr.Column(scale=12, elem_classes=["agent-workbench-chat-container"]):
            # Top icon bar (now inside chat container for automatic alignment)
            with gr.Row(elem_classes=["agent-workbench-top-bar"]):
                # Left side: Sidebar toggle + New chat
                with gr.Row(elem_classes=["agent-workbench-top-bar-left"]):
                    # Sidebar toggle button (always visible) - uses SVG sprite
                    _sidebar_toggle_btn = gr.HTML(  # noqa: F841
                        value=(
                            '<div class="agent-workbench-icon-btn" '
                            'id="sidebar-toggle-btn" aria-label="Toggle Sidebar">'
                            '<svg class="icon"><use href="/static/icons/sprite.svg#sidebar"/></svg>'
                            "</div>"
                        ),
                        elem_id="sidebar-toggle-container",
                    )

                    # New chat button (visible when sidebar closed) - uses SVG sprite
                    _new_chat_btn = gr.HTML(  # noqa: F841
                        value=(
                            '<div class="agent-workbench-icon-btn" '
                            'id="new-chat-btn" aria-label="New Chat">'
                            '<svg class="icon"><use href="/static/icons/sprite.svg#new-chat"/></svg>'
                            "</div>"
                        ),
                        elem_id="new-chat-container",
                        visible=True,  # Initially visible when sidebar is closed
                    )

                # Right side: Settings icon - uses SVG sprite
                with gr.Row(elem_classes=["agent-workbench-top-bar-right"]):
                    _settings_icon = gr.HTML(  # noqa: F841
                        value=(
                            '<div class="agent-workbench-icon-btn" '
                            'id="settings-icon" aria-label="Settings">'
                            '<svg class="icon"><use href="/static/icons/sprite.svg#settings"/></svg>'
                            "</div>"
                        ),
                        elem_id="settings-icon-container",
                    )
            # Main logo (shown when idle, theme-aware)
            gr.HTML(
                value=(
                    '<div class="agent-workbench-logo">'
                    '<img src="/static/icons/logo_seo_coach.png" '
                    'alt="Agent Workbench Logo" class="logo-light">'
                    '<img src="/static/icons/logo_seo_coach_inverted.png" '
                    'alt="Agent Workbench Logo" class="logo-dark">'
                    '</div>'
                ),
                elem_classes=["agent-workbench-logo-container"],
            )

            # Phase 4.3: State-dependent chat interface with gr.Blocks
            # Following skills.md Pattern 1: State-Dependent Button
            # Implements UI-005 Task 4.3.1, 4.3.3, 4.3.5

            # ===== UI COMPONENTS =====

            # Chatbot (messages display)
            chatbot = gr.Chatbot(
                type="messages",
                elem_classes=["agent-workbench-messages"],
                show_copy_button=True,
                height=600,
                label="",
                value=conversation_state.value if conversation_state.value else [],
            )

            # Input bar (Task 4.3.1: container with textbox + submit button)
            with gr.Row(elem_classes=["agent-workbench-input-bar"]):
                # Message input field (Task 4.3.3: borderless, flex: 1)
                textbox = gr.Textbox(
                    placeholder=config["labels"]["placeholder"],
                    show_label=False,
                    container=False,
                    elem_classes=["agent-workbench-message-input"],
                    scale=1,  # Takes remaining space (flex: 1)
                )

                # Submit button (Task 4.3.5: three states - disabled/active/processing)
                # Note: Icon applied via CSS background-image since gr.Button(icon=) doesn't support data URIs
                submit_btn = gr.Button(
                    value="",
                    interactive=False,  # Start disabled
                    size="sm",
                    elem_classes=["agent-workbench-submit-btn"],
                    elem_id="submit-btn",
                )

            # ===== BINDINGS =====

            def update_submit_button_state(text: str) -> gr.Button:
                """
                Update button state based on input text (Task 4.3.5 States 1-2).

                Returns new Button instance with appropriate icon and interactivity.
                State 1: Empty input - disabled (gray)
                State 2: Has input - active (black)

                Note: Processing state (State 3) handled in handle_submit generator.
                Note: Icon shown via CSS background-image.
                """
                if text.strip():
                    # State 2: Active (has text)
                    return gr.Button(
                        value="",
                        interactive=True,
                        size="sm",
                        elem_classes=["agent-workbench-submit-btn", "active"],
                        elem_id="submit-btn",
                    )
                else:
                    # State 1: Disabled (empty)
                    return gr.Button(
                        value="",
                        interactive=False,
                        size="sm",
                        elem_classes=["agent-workbench-submit-btn"],
                        elem_id="submit-btn",
                    )

            def handle_submit(
                message: str,
                history: List[Dict[str, str]],
                user_state_val: Optional[Dict[str, Any]],
                settings_val: Optional[Dict[str, Any]],
            ):
                """
                Handle message submission with processing state display.

                Generator pattern for showing intermediate states:
                1. Show processing icon (State 3)
                2. Make API call
                3. Return to disabled state (State 1)

                Yields:
                    Tuple of (chatbot, textbox, submit_btn) updates
                """
                if not message.strip():
                    return

                # State 3: Processing - show animated icon
                yield (
                    history,  # Keep current history
                    message,  # Keep message visible during processing
                    gr.Button(
                        value="",
                        interactive=False,
                        size="sm",
                        elem_classes=["agent-workbench-submit-btn", "processing"],
                        elem_id="submit-btn",
                    ),
                )

                # Get model config from settings or use defaults
                if settings_val and "model_config" in settings_val:
                    model_config = settings_val["model_config"]
                    provider = model_config.get("provider", "openrouter")
                    model_name = model_config.get("model", "openai/gpt-4o-mini")
                    temperature = model_config.get("temperature", 0.7)
                    max_tokens = model_config.get("max_tokens", 2000)
                else:
                    # Fallback to defaults
                    provider = "openrouter"
                    model_name = "openai/gpt-4o-mini"
                    temperature = 0.7
                    max_tokens = 2000

                try:
                    # Call full workflow endpoint
                    response = requests.post(
                        "http://localhost:8000/api/v1/chat/workflow",
                        json={
                            "user_message": message,
                            "workflow_mode": "workbench",
                            "llm_config": {
                                "provider": provider,
                                "model_name": model_name,
                                "temperature": temperature,
                                "max_tokens": max_tokens,
                            },
                        },
                        timeout=30,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        ai_response = result.get(
                            "assistant_response", "No response received"
                        )
                    else:
                        ai_response = (
                            f"API Error {response.status_code}: " f"{response.text}"
                        )

                except requests.exceptions.Timeout:
                    ai_response = "Request timed out after 30 seconds"
                except requests.exceptions.ConnectionError:
                    ai_response = "Connection failed - is the server running?"
                except Exception as e:
                    ai_response = f"Unexpected error: {str(e)}"

                # Update history with user message and response
                new_history = history + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": ai_response},
                ]

                # State 1: Back to disabled (empty input)
                yield (
                    new_history,  # Updated chatbot with response
                    "",  # Clear textbox
                    gr.Button(
                        value="",
                        interactive=False,
                        size="sm",
                        elem_classes=["agent-workbench-submit-btn"],
                        elem_id="submit-btn",
                    ),
                )

            # Wire button state updates (instant, no queue)
            textbox.change(
                fn=update_submit_button_state,
                inputs=[textbox],
                outputs=[submit_btn],
                queue=False,  # Instant client-side update
            )

            # Wire submit handlers (both click and Enter key)
            submit_btn.click(
                fn=handle_submit,
                inputs=[textbox, chatbot, user_state, settings_state],
                outputs=[chatbot, textbox, submit_btn],
            )

            textbox.submit(
                fn=handle_submit,
                inputs=[textbox, chatbot, user_state, settings_state],
                outputs=[chatbot, textbox, submit_btn],
            )

            # JavaScript to toggle logo/chatbot visibility (message count)
            # Logo/chatbot toggle via demo.load() in mode_factory_v2.py
            # (JavaScript in gr.HTML doesn't execute - must use
            # load event with js= parameter)

            # Note: Settings icon, sidebar toggle, and new chat clicks
            # handled via JavaScript in mode_factory_v2.py demo.load()

            # Phase 3: Wire up conversation persistence after message
            # Chatbot component updates trigger localStorage save
            if config.get("show_conv_browser", False) and (conversations_list_storage):
                print(
                    "[DEBUG chat.py] Wiring conversation persistence to "
                    "chatbot component"
                )

                # Update BrowserState after each message submission
                # When chatbot value changes, save to localStorage
                chatbot.change(
                    fn=update_conversations_list,
                    inputs=[
                        chatbot,  # Current messages from chatbot
                        conversations_list_storage,  # Existing conversations list
                        user_state,  # User session data
                    ],
                    outputs=[conversations_list_storage],  # Updated conversations list
                )

                # Also update the sidebar list display after saving
                conversations_list_storage.change(
                    fn=populate_list,
                    inputs=[user_state, conversations_list_storage],
                    outputs=[conv_list],
                )

                print(
                    "[DEBUG chat.py] ✅ Event handlers wired: "
                    "chatbot.change() → update_conversations_list → "
                    "populate_list"
                )

            # Phase 3: Wire up sidebar if enabled
            if config.get("show_conv_browser", False) and conv_list:
                # Wire Dataset.select to load conversation when clicked
                # NOTE: gr.SelectData passed automatically, not in inputs!
                conv_list.select(
                    fn=load_selected_conversation,
                    inputs=[
                        user_state,
                        conversations_list_storage,
                    ],
                    outputs=[chatbot, conversation_state],
                )

                # New Chat button inside sidebar - clear chatbot and conversation state
                if sidebar_new_chat_btn:
                    sidebar_new_chat_btn.click(
                        fn=lambda: ([], []),
                        outputs=[chatbot, conversation_state],
                    )

                # Note: The top bar new_chat_btn (gr.HTML) click
                # is handled via JavaScript

    # Return BrowserState and Dataset list for page load event in mode_factory
    # This enables conversation list population on page refresh
    if config.get("show_conv_browser", False):
        print("[DEBUG chat.py] render() RETURNING:")
        print(f"  conversations_list_storage: {conversations_list_storage}")
        print(f"  conv_list: {conv_list}")
        return conversations_list_storage, conv_list
    else:
        print("[DEBUG chat.py] render() RETURNING None, None (show_conv_browser=False)")
        return None, None


def populate_list(
    user_state: Optional[Dict[str, Any]],
    browser_state: List[Dict[str, Any]],
) -> gr.update:
    """
    Populate Dataset list from conversations with date categorization.

    Hybrid: API for auth users, BrowserState for guests.

    Args:
        user_state: User session data
        browser_state: Conversations from BrowserState (guests)

    Returns:
        Gradio update dict with Dataset samples

    Note:
        Dataset samples use [[item1], [item2], ...] format with:
        - Category headers marked with "📅 " prefix (non-clickable)
        - Conversation titles (no date suffix)
        - Categories: Today, This Week, Older
    """
    print("[DEBUG chat.py] populate_list CALLED!")
    print(f"  user_state: {user_state}")
    print(f"  browser_state length: {len(browser_state) if browser_state else 0}")
    if browser_state:
        sample = browser_state[:2] if len(browser_state) >= 2 else browser_state
        print(f"  browser_state sample: {sample}")

    samples = []

    # For guest users: Read from BrowserState
    if not user_state or not user_state.get("user_id"):
        # Categorize conversations by date
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)

        today_convs = []
        this_week_convs = []
        older_convs = []

        for conv in browser_state or []:
            title = conv.get("title", "Untitled")[:40]
            date_str = conv.get("updated_at", "")

            # Parse date
            try:
                conv_date = datetime.fromisoformat(date_str).date()
            except (ValueError, AttributeError):
                conv_date = None

            # Categorize by date
            if conv_date == today:
                today_convs.append([title])
            elif conv_date and conv_date >= week_ago:
                this_week_convs.append([title])
            else:
                older_convs.append([title])

        # Build samples with category headers
        if today_convs:
            samples.append(["📅 Today"])
            samples.extend(today_convs)

        if this_week_convs:
            samples.append(["📅 This Week"])
            samples.extend(this_week_convs)

        if older_convs:
            samples.append(["📅 Older"])
            samples.extend(older_convs)

        conv_count = len(today_convs) + len(this_week_convs) + len(older_convs)
        print(
            f"[populate_list] Guest: {conv_count} conversations "
            f"(Today: {len(today_convs)}, Week: {len(this_week_convs)}, "
            f"Older: {len(older_convs)})"
        )
    else:
        # For authenticated users: Fetch from API
        # TODO: Implement when needed
        print("[populate_list] Auth: API not implemented")

    print(f"[DEBUG chat.py] populate_list RETURNING {len(samples)} samples")
    if samples:
        print(f"  First 3 samples: {samples[:3]}")

    return gr.update(samples=samples)


def load_selected_conversation(
    evt: gr.SelectData,
    user_state: Optional[Dict[str, Any]],
    browser_state: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Load selected conversation from Dataset list by title matching.

    Hybrid: API for authenticated users, BrowserState for guests.

    Args:
        evt: SelectData event containing .index and .value of clicked item
        user_state: User session data
        browser_state: Conversations list from BrowserState (guests)

    Returns:
        Tuple of (chatbot_messages, conversation_state)

    Note:
        Category headers (starting with "📅") are ignored.
        Conversations are matched by title to handle categorized list.
    """
    # Extract clicked text from SelectData
    selected_value = evt.value
    if isinstance(selected_value, list) and len(selected_value) > 0:
        clicked_text = str(selected_value[0])
    else:
        clicked_text = str(selected_value) if selected_value else ""

    print("[load_selected_conversation] CALLED!")
    print(f"  - clicked_text: '{clicked_text}'")
    print(f"  - user_state: {user_state}")
    print(f"  - browser_state length: {len(browser_state) if browser_state else 0}")

    # Ignore category header clicks
    if clicked_text.startswith("📅"):
        print("[load_selected_conversation] Header clicked, ignoring")
        return [], []

    # For guest users: Load from BrowserState by title match
    if not user_state or not user_state.get("user_id"):
        for conv in browser_state or []:
            conv_title = conv.get("title", "Untitled")[:40]
            if conv_title == clicked_text:
                messages = conv.get("messages", [])
                msg_count = len(messages)
                print(
                    f"[load_selected_conversation] Found conversation: "
                    f"'{conv_title}' with {msg_count} messages"
                )
                return messages, messages

        print(f"[load_selected_conversation] No match found for '{clicked_text}'")
        return [], []

    # For authenticated users: Fetch from API
    # TODO: Implement API fetching when needed
    print("[load_selected_conversation] API fetching not yet implemented")
    return [], []


def update_conversations_list(
    conv_state: List[Dict[str, str]],
    conv_list: List[Dict[str, Any]],
    user_state: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Update conversations list with current conversation metadata.

    For guest users only - authenticated users use database.

    Args:
        conv_state: Current conversation messages
        conv_list: Existing conversations list from localStorage
        user_state: User session data

    Returns:
        Updated conversations list (for guests) or empty list (for auth users)
    """
    # Debug logging
    print("[update_conversations_list] Called with:")
    print(f"  - conv_state length: {len(conv_state) if conv_state else 0}")
    print(f"  - conv_list length: {len(conv_list) if conv_list else 0}")
    print(f"  - user_state: {user_state}")

    # Authenticated users use database - return empty list
    if user_state and user_state.get("user_id"):
        print("[update_conversations_list] Auth user - returning empty")
        return []

    # Guest users: update localStorage list
    if not conv_state or len(conv_state) == 0:
        print("[update_conversations_list] Empty conv_state - returning existing")
        return conv_list if conv_list else []

    # Extract first user message as title
    first_user_msg = next(
        (msg["content"] for msg in conv_state if msg.get("role") == "user"),
        "Untitled",
    )
    title = first_user_msg[:50]

    # Generate stable conversation ID from FIRST message only
    # This ensures the ID stays the same as conversation grows
    conv_id = str(abs(hash(first_user_msg)))
    timestamp = datetime.now().isoformat()

    # Debug: Print extracted info
    print("[update_conversations_list] Extracted:")
    print(f"  - first_user_msg: '{first_user_msg}'")
    print(f"  - generated ID: {conv_id}")
    print(f"  - existing IDs in list: {[c.get('id') for c in (conv_list or [])]}")

    # Get last message for preview
    preview = ""
    if len(conv_state) > 0:
        preview = conv_state[-1].get("content", "")[:100]

    # Remove existing entry with same ID
    updated_list = [c for c in (conv_list or []) if c.get("id") != conv_id]

    # Add new entry at the beginning
    new_entry = {
        "id": conv_id,
        "title": title,
        "updated_at": timestamp,
        "preview": preview,
        "messages": conv_state,
    }
    updated_list.insert(0, new_entry)

    # Keep only last 20 conversations
    result = updated_list[:20]

    # Debug logging
    print("[update_conversations_list] Created new entry:")
    print(f"  - id: {conv_id}")
    print(f"  - title: {title}")
    print(f"  - Returning list with {len(result)} conversations")

    return result


def load_conversation_into_chat(
    conv_data: Optional[Dict[str, Any]],
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """
    Load conversation from sidebar click into chatbot.

    Args:
        conv_data: Conversation data with messages

    Returns:
        Tuple of (chatbot_history, conversation_state)
    """
    if not conv_data:
        return [], []

    messages = conv_data.get("messages", [])

    # Convert to chatbot format (user, assistant pairs)
    chatbot_history: List[Tuple[str, str]] = []
    for i in range(0, len(messages), 2):
        if i + 1 < len(messages):
            user_msg = messages[i]["content"]
            assistant_msg = messages[i + 1]["content"]
            chatbot_history.append((user_msg, assistant_msg))

    return chatbot_history, chatbot_history


def handle_chat_interface_message(
    message: str,
    history: List[Dict[str, str]],
    user_state: Optional[Dict[str, Any]],
    settings: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Handle chat message submission for gr.ChatInterface.

    Args:
        message: User input text
        history: Current chat history (messages format)
        user_state: User session data (from additional_inputs)
        settings: User settings (model config, etc.)

    Returns:
        Assistant's response text only (ChatInterface manages history)

    Note:
        gr.ChatInterface automatically adds user message to history and
        appends the returned response, so we only return assistant text.
    """

    if not message.strip():
        return "Please enter a message."

    # Get model config from settings or use defaults
    if settings and "model_config" in settings:
        model_config = settings["model_config"]
        provider = model_config.get("provider", "openrouter")
        model_name = model_config.get("model", "openai/gpt-4o-mini")
        temperature = model_config.get("temperature", 0.7)
        max_tokens = model_config.get("max_tokens", 2000)
    else:
        # Fallback to defaults
        provider = "openrouter"
        model_name = "openai/gpt-4o-mini"
        temperature = 0.7
        max_tokens = 2000

    try:
        # Call full workflow endpoint for database persistence
        response = requests.post(
            "http://localhost:8000/api/v1/chat/workflow",
            json={
                "user_message": message,
                "workflow_mode": "workbench",
                "llm_config": {
                    "provider": provider,
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            },
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("assistant_response", "No response received")
            return ai_response
        else:
            return f"API Error {response.status_code}: {response.text}"

    except requests.exceptions.Timeout:
        return "Request timed out after 30 seconds"

    except requests.exceptions.ConnectionError:
        return "Connection failed - is the server running?"

    except Exception as e:
        return f"Unexpected error: {str(e)}"


def handle_chat_message(
    message: str,
    history: List[Dict[str, str]],
    user_state: Optional[Dict[str, Any]],
    settings: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, str]], str, List[Dict[str, str]]]:
    """
    Handle chat message submission (legacy handler - kept for compatibility).

    Args:
        message: User input text
        history: Current chat history (Gradio messages format with 'role' and 'content')
        user_state: User session data
        settings: User settings (model config, etc.)

    Returns:
        Tuple of (updated_history, cleared_input, updated_state)

    Phase 2: Now uses settings from settings page for model configuration.
    Updated for Gradio 5.x messages format (type="messages").
    """

    if not message.strip():
        return history, "", history

    # Get model config from settings or use defaults
    if settings and "model_config" in settings:
        model_config = settings["model_config"]
        provider = model_config.get("provider", "openrouter")
        model_name = model_config.get("model", "openai/gpt-5-mini")
        temperature = model_config.get("temperature", 0.7)
        max_tokens = model_config.get("max_tokens", 2000)
    else:
        # Fallback to defaults
        provider = "openrouter"
        model_name = "openai/gpt-5-mini"
        temperature = 0.7
        max_tokens = 2000

    try:
        # Call full workflow endpoint for database persistence
        response = requests.post(
            "http://localhost:8000/api/v1/chat/workflow",
            json={
                "user_message": message,
                "workflow_mode": "workbench",
                "llm_config": {
                    "provider": provider,
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            },
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("assistant_response", "No response received")

            # Add to history in Gradio messages format (type="messages")
            new_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": ai_response},
            ]

            return (
                new_history,  # Update chatbot display
                "",  # Clear input field
                new_history,  # Update conversation_state
            )
        else:
            error_msg = f"API Error {response.status_code}: {response.text}"
            new_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": error_msg},
            ]
            return new_history, "", new_history

    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds"
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_msg},
        ]
        return new_history, "", new_history

    except requests.exceptions.ConnectionError:
        error_msg = "Connection failed - is the server running?"
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_msg},
        ]
        return new_history, "", new_history

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_msg},
        ]
        return new_history, "", new_history
