"""
Chat page - minimal chatbox interface.

NO model controls (moved to settings).
NO sidebar (separate feature - see
    docs/phase2/Feat-dev-plan-chat-history-in-sidebar-in-chatpage.md).

Identical structure for workbench and SEO coach modes - differences
controlled by config labels.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import requests  # type: ignore[import-untyped]

from ..components.sidebar import render_sidebar


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

    # BrowserState for localStorage persistence (guest users only)
    # Database persistence remains primary for authenticated users
    conversation_storage = gr.BrowserState(
        default_value={},  # Empty dict as default
        storage_key="agent_workbench_conversation",
    )

    # BrowserState for conversations list (sidebar)
    conversations_list_storage = gr.BrowserState(
        default_value=[],  # List of conversation metadata
        storage_key="agent_workbench_conversations_list",
    )

    # Render sidebar if enabled
    new_chat_btn = None
    sidebar_visible = None
    collapse_btn = None
    conv_list = None
    clear_storage_btn = None
    if config.get("show_conv_browser", False):
        (
            sidebar_visible,
            conv_list,
            new_chat_btn,
            collapse_btn,
            clear_storage_btn,
        ) = render_sidebar(config, user_state)

    # Main layout
    with gr.Row():
        # Main chat area
        with gr.Column(scale=12):
            # Header with settings button
            with gr.Row():
                gr.Markdown(f"# {config['title']}")
                settings_btn = gr.Button("⚙️", size="sm")

            # Chatbot - loads from conversation_state
            chatbot = gr.Chatbot(
                value=(conversation_state.value if conversation_state.value else []),
                label="",
                height=600,
                show_copy_button=True,
                elem_id="chatbot",
                type="messages",
            )

            # Input area
            with gr.Row():
                msg = gr.Textbox(
                    placeholder=config["labels"]["placeholder"],
                    scale=4,
                    show_label=False,
                    container=False,
                )
                send = gr.Button(config["labels"]["send"], scale=1, variant="primary")

            # Event: Navigate to settings
            settings_btn.click(
                fn=None, js="() => { window.location.href = '/settings'; }"
            )

            # Event: Send message
            send_chain = (
                send.click(
                    fn=handle_chat_message,
                    inputs=[msg, chatbot, user_state, settings_state],
                    outputs=[chatbot, msg, conversation_state],
                )
                .then(
                    # For guest users: persist to BrowserState (localStorage)
                    # For authenticated users: returns empty dict (DB is primary)
                    fn=lambda conv, user: (
                        conv if (not user or not user.get("user_id")) else {}
                    ),
                    inputs=[conversation_state, user_state],
                    outputs=[conversation_storage],  # BrowserState auto-syncs
                )
                .then(
                    # Update conversations list for sidebar
                    fn=update_conversations_list,
                    inputs=[
                        conversation_state,
                        conversations_list_storage,
                        user_state,
                    ],
                    outputs=[conversations_list_storage],  # Auto-syncs
                )
            )

            # Event: Submit message (Enter key)
            submit_chain = (
                msg.submit(
                    fn=handle_chat_message,
                    inputs=[msg, chatbot, user_state, settings_state],
                    outputs=[chatbot, msg, conversation_state],
                )
                .then(
                    # For guest users: persist to BrowserState (localStorage)
                    # For authenticated users: returns empty dict (DB is primary)
                    fn=lambda conv, user: (
                        conv if (not user or not user.get("user_id")) else {}
                    ),
                    inputs=[conversation_state, user_state],
                    outputs=[conversation_storage],  # BrowserState auto-syncs
                )
                .then(
                    # Update conversations list for sidebar
                    fn=update_conversations_list,
                    inputs=[
                        conversation_state,
                        conversations_list_storage,
                        user_state,
                    ],
                    outputs=[conversations_list_storage],  # Auto-syncs
                )
            )

            # Phase 3: Wire up sidebar if enabled
            if config.get("show_conv_browser", False) and conv_list:
                # Update Dataset list AFTER conversation list is updated
                send_chain.then(
                    fn=populate_list,
                    inputs=[user_state, conversations_list_storage],
                    outputs=[conv_list],
                )

                submit_chain.then(
                    fn=populate_list,
                    inputs=[user_state, conversations_list_storage],
                    outputs=[conv_list],
                )

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

                # New Chat button - clear chatbot and conversation state
                if new_chat_btn:
                    new_chat_btn.click(
                        fn=lambda: ([], []),
                        outputs=[chatbot, conversation_state],
                    )

    # Return BrowserState and Dataset list for page load event in mode_factory
    # This enables conversation list population on page refresh
    if config.get("show_conv_browser", False):
        return conversations_list_storage, conv_list
    else:
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


def handle_chat_message(
    message: str,
    history: List[Dict[str, str]],
    user_state: Optional[Dict[str, Any]],
    settings: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, str]], str, List[Dict[str, str]]]:
    """
    Handle chat message submission.

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
