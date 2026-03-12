"""
Chat page - minimal chatbox interface.

NO model controls (moved to settings).
NO sidebar (separate feature - see
    docs/phase2/Feat-dev-plan-chat-history-in-sidebar-in-chatpage.md).

Identical structure for workbench and SEO coach modes - differences
controlled by config labels.
"""

import base64
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import gradio as gr
import httpx
import requests  # type: ignore[import-untyped]

from ..components.message_converter import (
    streaming_event_to_chat_messages,
    to_chat_message,
)
from ..components.sidebar import render_sidebar

logger = logging.getLogger(__name__)


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
    encoded = base64.b64encode(svg_content).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


# Load icons as data URIs at module level (replicating Gradio's built-in icon pattern)
SUBMIT_ICON_DATA_URI = svg_to_data_uri("/static/icons/svg/submit_icon_24.svg")
PROCESSING_ICON_DATA_URI = svg_to_data_uri("/static/icons/svg/processing_icon_24.svg")

_FILE_TYPES = [".pdf", ".docx", ".txt", ".md"]


def _extract_message(input: Union[str, dict]) -> tuple[str, list]:
    """Extract text and files from MultimodalTextbox input or plain string."""
    if isinstance(input, dict):
        return input.get("text", ""), input.get("files", [])
    return input, []


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

    Workbench mode: gr.ChatInterface with save_history=True (native Gradio sidebar)
    SEO Coach mode: custom branded UI with manual event wiring
    """
    logger.debug(
        "render() called, load_custom_js=%s", config.get("load_custom_js", False)
    )

    # Workbench: native gr.Sidebar (collapsed by default) + gr.ChatInterface
    if not config.get("load_custom_js"):
        conv_storage = gr.BrowserState(
            default_value=[],
            storage_key="wb_conversations",
        )

        with gr.Sidebar(open=False, label="Conversations"):
            new_chat_btn = gr.Button("New Chat", size="sm", variant="secondary")
            conv_dataset = gr.Dataset(
                components=[gr.Textbox(visible=False)],
                samples=[],
                show_label=False,
                type="index",
            )

        pending_files_wb = gr.State([])
        conv_id_state_wb = gr.State(None)

        with gr.Group(
            visible=False, elem_classes=["aw-approval-bar"]
        ) as approval_group_wb:
            with gr.Row():
                approval_filename_wb = gr.Markdown("")
                approve_btn_wb = gr.Button(
                    config["labels"].get("file_approve", "Confirm"),
                    variant="primary",
                    size="sm",
                )
                cancel_btn_wb = gr.Button(
                    config["labels"].get("file_cancel", "Remove"), size="sm"
                )

        chat_iface = gr.ChatInterface(
            fn=handle_chat_interface_message,
            additional_inputs=[
                user_state,
                settings_state,
                pending_files_wb,
                conv_id_state_wb,
            ],
            additional_outputs=[conv_id_state_wb],
            save_history=False,
            title="Agent Workbench Chat",
            textbox=gr.MultimodalTextbox(
                placeholder=config["labels"]["placeholder"],
                file_types=_FILE_TYPES,
                file_count="multiple",
            ),
        )

        def on_wb_input_change(input_val: Union[str, dict], pending: list) -> tuple:
            _, files = _extract_message(input_val)
            if files and files != pending:
                if len(files) == 1:
                    f = files[0]
                    label = (
                        os.path.basename(f)
                        if isinstance(f, str)
                        else f.get("orig_name", f.get("name", "unknown"))
                    )
                else:
                    label = f"{len(files)} files"
                return gr.Group(visible=True), pending, f"**{label}**"
            if not files and pending:
                return gr.Group(visible=False), [], ""
            return gr.Group(visible=False), pending, ""

        chat_iface.textbox.change(
            fn=on_wb_input_change,
            inputs=[chat_iface.textbox, pending_files_wb],
            outputs=[approval_group_wb, pending_files_wb, approval_filename_wb],
            queue=False,
        )

        approve_btn_wb.click(
            fn=lambda inp, _p: (gr.Group(visible=False), _extract_message(inp)[1]),
            inputs=[chat_iface.textbox, pending_files_wb],
            outputs=[approval_group_wb, pending_files_wb],
        )

        cancel_btn_wb.click(
            fn=lambda: (gr.Group(visible=False), []),
            outputs=[approval_group_wb, pending_files_wb],
        )

        # Save conversation after each message
        chat_iface.chatbot.change(
            fn=update_conversations_list,
            inputs=[chat_iface.chatbot, conv_storage, user_state],
            outputs=[conv_storage],
        )

        # Update sidebar list when storage changes
        conv_storage.change(
            fn=populate_list,
            inputs=[user_state, conv_storage],
            outputs=[conv_dataset],
        )

        # Load selected conversation into chatbot
        conv_dataset.select(
            fn=load_selected_conversation,
            inputs=[user_state, conv_storage],
            outputs=[chat_iface.chatbot, conversation_state],
        )

        # New chat clears the chatbot and state
        new_chat_btn.click(
            fn=lambda: ([], [], None),
            outputs=[chat_iface.chatbot, conversation_state, conv_id_state_wb],
        )

        # Return storage + dataset so mode_factory wires the page-load event
        return conv_storage, conv_dataset

    # SEO Coach: custom branded UI
    # BrowserState for conversations list (sidebar)
    conversations_list_storage = gr.BrowserState(
        default_value=[],  # List of conversation metadata
        storage_key="agent_workbench_conversations_list",
    )

    # Sidebar component references (initialized outside, rendered inside Row)
    sidebar_visible = None
    sidebar_col = None
    collapse_btn = None
    conv_list = None
    clear_storage_btn = None
    sidebar_new_chat_btn = None  # New chat button inside sidebar

    # Main layout - two-column structure (sidebar + chat)
    with gr.Row():
        # Sidebar column (hidden by default, slides in from left)
        if config.get("show_conv_browser", False):
            (
                sidebar_visible,
                sidebar_col,
                conv_list,
                sidebar_new_chat_btn,
                collapse_btn,
                clear_storage_btn,
            ) = render_sidebar(config, user_state)

        # Main chat area (scale=4 to allow sidebar push behavior)
        with gr.Column(
            scale=4, elem_id="aw-main", elem_classes=["agent-workbench-chat-container"]
        ):
            # Custom icon bar + logo: SEO Coach only
            # Workbench uses plain Gradio — no icon bar, no branded logo
            if config.get("load_custom_js"):
                with gr.Row(
                    elem_id="aw-top-bar", elem_classes=["agent-workbench-top-bar"]
                ):
                    # Left side: Sidebar toggle + New chat icon
                    with gr.Row(elem_classes=["agent-workbench-top-bar-left"]):
                        _sidebar_toggle_btn = gr.HTML(  # noqa: F841
                            value=(
                                '<div class="agent-workbench-icon-btn" '
                                'id="sidebar-toggle-btn" aria-label="Toggle Sidebar">'
                                '<svg class="icon">'
                                '<use href="/static/icons/sprite.svg#sidebar"/>'
                                "</svg>"
                                "</div>"
                            ),
                            elem_id="sidebar-toggle-container",
                        )

                        _new_chat_btn = gr.HTML(  # noqa: F841
                            value=(
                                '<div class="agent-workbench-icon-btn" '
                                'id="new-chat-btn" aria-label="New Chat">'
                                '<svg class="icon">'
                                '<use href="/static/icons/sprite.svg#new-chat"/>'
                                "</svg>"
                                "</div>"
                            ),
                            elem_id="new-chat-container",
                            visible=True,
                        )

                    # Right side: Settings icon
                    with gr.Row(elem_classes=["agent-workbench-top-bar-right"]):
                        _settings_icon = gr.HTML(  # noqa: F841
                            value=(
                                '<div class="agent-workbench-icon-btn" '
                                'id="settings-icon" aria-label="Settings">'
                                '<svg class="icon">'
                                '<use href="/static/icons/sprite.svg#settings"/>'
                                "</svg>"
                                "</div>"
                            ),
                            elem_id="settings-icon-container",
                        )

                # Branded logo (shown when idle, theme-aware)
                gr.HTML(
                    value=(
                        '<div class="agent-workbench-logo">'
                        '<img src="/static/icons/logo_seo_coach.png" '
                        'alt="Agent Workbench Logo" class="logo-light">'
                        '<img src="/static/icons/logo_seo_coach_inverted.png" '
                        'alt="Agent Workbench Logo" class="logo-dark">'
                        "</div>"
                    ),
                    elem_classes=["agent-workbench-logo-container"],
                )

            # Phase 4.3: State-dependent chat interface with gr.Blocks
            # Following skills.md Pattern 1: State-Dependent Button
            # Implements UI-005 Task 4.3.1, 4.3.3, 4.3.5

            # ===== UI COMPONENTS =====

            # Chatbot (messages display)
            chatbot = gr.Chatbot(
                elem_classes=["agent-workbench-messages"],
                buttons=["copy"],
                height=600,
                label="",
                value=conversation_state.value if conversation_state.value else [],
            )

            # File upload state + approval bar
            pending_files_seo = gr.State([])

            with gr.Group(
                visible=False, elem_classes=["aw-approval-bar"]
            ) as approval_group_seo:
                with gr.Row():
                    approval_filename_seo = gr.Markdown("")
                    approve_btn_seo = gr.Button(
                        config["labels"].get("file_approve", "Confirm"),
                        variant="primary",
                        size="sm",
                    )
                    cancel_btn_seo = gr.Button(
                        config["labels"].get("file_cancel", "Remove"), size="sm"
                    )

            # Input bar (Task 4.3.1: container with textbox + submit button)
            with gr.Row(
                elem_id="aw-input-bar", elem_classes=["agent-workbench-input-bar"]
            ):
                # Message input field — MultimodalTextbox for file upload + drag-and-drop  # noqa: E501
                textbox = gr.MultimodalTextbox(
                    placeholder=config["labels"]["placeholder"],
                    show_label=False,
                    container=False,
                    elem_classes=["agent-workbench-message-input"],
                    scale=1,
                    file_types=_FILE_TYPES,
                    file_count="multiple",
                    submit_btn=False,  # external custom submit button used instead
                )

                # Submit button (Task 4.3.5: three states - disabled/active/processing)
                # Icon applied via CSS background-image
                # (gr.Button icon= doesn't support data URIs)
                submit_btn = gr.Button(
                    value="",
                    interactive=False,  # Start disabled
                    size="sm",
                    elem_classes=["agent-workbench-submit-btn"],
                    elem_id="submit-btn",
                )

            # ===== BINDINGS =====

            _disabled_btn = gr.Button(
                value="",
                interactive=False,
                size="sm",
                elem_classes=["agent-workbench-submit-btn"],
                elem_id="submit-btn",
            )

            def on_seo_input_change(
                input_val: Union[str, dict, None], pending: list
            ) -> tuple:
                """Combined handler: updates submit button state + shows approval bar.

                State 1: Empty input — button disabled, approval bar hidden.
                State 2: Has text — button active.
                File detected: approval bar shown with filename.
                File removed: approval bar hidden, pending cleared.
                """
                if input_val is None:
                    return _disabled_btn, gr.Group(visible=False), pending, ""
                text, files = _extract_message(input_val)

                btn = (
                    gr.Button(
                        value="",
                        interactive=True,
                        size="sm",
                        elem_classes=["agent-workbench-submit-btn", "active"],
                        elem_id="submit-btn",
                    )
                    if text.strip()
                    else gr.Button(
                        value="",
                        interactive=False,
                        size="sm",
                        elem_classes=["agent-workbench-submit-btn"],
                        elem_id="submit-btn",
                    )
                )

                if files and files != pending:
                    if len(files) == 1:
                        f = files[0]
                        label = (
                            os.path.basename(f)
                            if isinstance(f, str)
                            else f.get("orig_name", f.get("name", "unknown"))
                        )
                    else:
                        label = f"{len(files)} files"
                    return btn, gr.Group(visible=True), pending, f"**{label}**"
                if not files and pending:
                    return btn, gr.Group(visible=False), [], ""
                return btn, gr.Group(visible=False), pending, ""

            def handle_submit(
                message: Union[str, dict],
                history: List[gr.ChatMessage],
                user_state_val: Optional[Dict[str, Any]],
                settings_val: Optional[Dict[str, Any]],
                pending_files: Optional[list] = None,
            ):
                """Handle message submission with processing state display.

                Accepts str (legacy) or dict (gr.MultimodalTextbox).
                Generator: yields (chatbot, textbox, submit_btn, pending_files).
                """
                text, msg_files = _extract_message(message)
                if not text.strip():
                    return

                effective_files = pending_files if pending_files else msg_files

                # State 3: Processing - show animated icon
                yield (
                    history,  # Keep current history
                    message,  # Keep original value visible during processing
                    gr.Button(
                        value="",
                        interactive=False,
                        size="sm",
                        elem_classes=["agent-workbench-submit-btn", "processing"],
                        elem_id="submit-btn",
                    ),
                    [],  # pending_files unchanged during processing
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

                payload = {
                    "user_message": text,
                    "workflow_mode": "seo_coach",
                    "llm_config": {
                        "provider": provider,
                        "model_name": model_name,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                    "pending_files": effective_files or [],
                }

                # Streaming: build up the assistant message token by token
                user_msg = to_chat_message({"role": "user", "content": text})
                answer_content = ""
                thinking_content = ""

                try:
                    with requests.post(
                        "http://localhost:8000/api/v1/chat/workflow/stream",
                        json=payload,
                        stream=True,
                        timeout=60,
                    ) as resp:
                        if resp.status_code != 200:
                            answer_content = (
                                f"API Error {resp.status_code}: {resp.text}"
                            )
                        else:
                            for line in resp.iter_lines():
                                if not line:
                                    continue
                                raw = (
                                    line.decode("utf-8")
                                    if isinstance(line, bytes)
                                    else line
                                )
                                if not raw.startswith("data: "):
                                    continue
                                try:
                                    event = json.loads(raw[6:])
                                except json.JSONDecodeError:
                                    continue

                                event_type = event.get("type")
                                if event_type in (
                                    "thinking_chunk",
                                    "answer_chunk",
                                    "processing_file",
                                ):
                                    if event_type == "thinking_chunk":
                                        thinking_content += event.get("content", "")
                                    elif event_type == "answer_chunk":
                                        answer_content += event.get("content", "")
                                    msgs = streaming_event_to_chat_messages(
                                        event,
                                        thinking_content,
                                        answer_content,
                                        locale="nl",
                                    )
                                    if msgs:
                                        if event_type == "processing_file":
                                            new_history = history + msgs
                                        else:
                                            new_history = history + [user_msg] + msgs
                                        yield (
                                            new_history,
                                            message,
                                            gr.Button(
                                                value="",
                                                interactive=False,
                                                size="sm",
                                                elem_classes=[
                                                    "agent-workbench-submit-btn",
                                                    "processing",
                                                ],
                                                elem_id="submit-btn",
                                            ),
                                            [],
                                        )

                except requests.exceptions.Timeout:
                    answer_content = "Verzoek verlopen na 60 seconden"
                except requests.exceptions.ConnectionError:
                    answer_content = "Verbinding mislukt - draait de server?"
                except Exception as e:
                    answer_content = f"Onverwachte fout: {str(e)}"

                # Build final history entry
                final_assistant: List[gr.ChatMessage] = []
                if thinking_content:
                    final_assistant.append(
                        gr.ChatMessage(
                            role="assistant",
                            content=thinking_content,
                            metadata={"title": "Redenering", "status": "done"},
                        )
                    )
                final_assistant.append(
                    gr.ChatMessage(
                        role="assistant",
                        content=answer_content or "Geen antwoord ontvangen",
                    )
                )
                new_history = history + [user_msg] + final_assistant

                # State 1: Back to disabled — clear textbox + pending files
                yield (
                    new_history,
                    {"text": "", "files": []},
                    gr.Button(
                        value="",
                        interactive=False,
                        size="sm",
                        elem_classes=["agent-workbench-submit-btn"],
                        elem_id="submit-btn",
                    ),
                    [],
                )

            # Wire combined input change handler (button state + approval bar)
            textbox.change(
                fn=on_seo_input_change,
                inputs=[textbox, pending_files_seo],
                outputs=[
                    submit_btn,
                    approval_group_seo,
                    pending_files_seo,
                    approval_filename_seo,
                ],
                queue=False,
            )

            # Wire approval bar buttons
            approve_btn_seo.click(
                fn=lambda inp, _p: (gr.Group(visible=False), _extract_message(inp)[1]),
                inputs=[textbox, pending_files_seo],
                outputs=[approval_group_seo, pending_files_seo],
            )

            cancel_btn_seo.click(
                fn=lambda: (gr.Group(visible=False), []),
                outputs=[approval_group_seo, pending_files_seo],
            )

            # Wire submit handlers (both click and Enter key)
            submit_btn.click(
                fn=handle_submit,
                inputs=[
                    textbox,
                    chatbot,
                    user_state,
                    settings_state,
                    pending_files_seo,
                ],
                outputs=[chatbot, textbox, submit_btn, pending_files_seo],
            )

            textbox.submit(
                fn=handle_submit,
                inputs=[
                    textbox,
                    chatbot,
                    user_state,
                    settings_state,
                    pending_files_seo,
                ],
                outputs=[chatbot, textbox, submit_btn, pending_files_seo],
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
                logger.debug("Wiring conversation persistence to chatbot component")

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

                logger.debug(
                    "Event handlers wired: chatbot.change"
                    " -> update_conversations_list -> populate_list"
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
        logger.debug("render() returning conversations_list_storage and conv_list")
        return conversations_list_storage, conv_list
    else:
        logger.debug("render() returning None, None (show_conv_browser=False)")
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
    logger.debug(
        "populate_list: user_state=%s, browser_state length=%d",
        user_state,
        len(browser_state) if browser_state else 0,
    )

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
        logger.debug(
            "populate_list guest: %d conversations (Today: %d, Week: %d, Older: %d)",
            conv_count,
            len(today_convs),
            len(this_week_convs),
            len(older_convs),
        )
    else:
        # For authenticated users: Fetch from API
        # TODO: Implement when needed
        logger.debug("populate_list: auth user — API not yet implemented")

    logger.debug("populate_list returning %d samples", len(samples))

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

    logger.debug(
        "load_selected_conversation: clicked='%s', user_state=%s, storage=%d items",
        clicked_text,
        user_state,
        len(browser_state) if browser_state else 0,
    )

    # Ignore category header clicks
    if clicked_text.startswith("📅"):
        logger.debug("load_selected_conversation: header clicked, ignoring")
        return [], []

    # For guest users: Load from BrowserState by title match
    if not user_state or not user_state.get("user_id"):
        for conv in browser_state or []:
            conv_title = conv.get("title", "Untitled")[:40]
            if conv_title == clicked_text:
                messages = conv.get("messages", [])
                msg_count = len(messages)
                logger.debug(
                    "load_selected_conversation: found '%s' with %d messages",
                    conv_title,
                    msg_count,
                )
                return messages, messages

        logger.debug(
            "load_selected_conversation: no match found for '%s'", clicked_text
        )
        return [], []

    # For authenticated users: Fetch from API
    # TODO: Implement API fetching when needed
    logger.debug("load_selected_conversation: auth user — API not yet implemented")
    return [], []


def _content_to_str(content: Any) -> str:
    """Normalize Gradio 6 message content to plain string.

    In Gradio 6, content can be a list of content parts (multimodal format)
    instead of a plain string. Extract text parts into a single string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        ]
        return " ".join(p for p in parts if p)
    return str(content) if content is not None else ""


def update_conversations_list(
    conv_state: List[Dict[str, Any]],
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
    logger.debug(
        "update_conversations_list: conv_state=%d, conv_list=%d, user_state=%s",
        len(conv_state) if conv_state else 0,
        len(conv_list) if conv_list else 0,
        user_state,
    )

    # Authenticated users use database - return empty list
    if user_state and user_state.get("user_id"):
        logger.debug("update_conversations_list: auth user — returning empty")
        return []

    # Guest users: update localStorage list
    if not conv_state or len(conv_state) == 0:
        logger.debug("update_conversations_list: empty conv_state — returning existing")
        return conv_list if conv_list else []

    # Extract first user message as title
    # _content_to_str handles Gradio 6's list format for multimodal content
    first_user_msg = _content_to_str(
        next(
            (msg["content"] for msg in conv_state if msg.get("role") == "user"),
            "Untitled",
        )
    )
    title = first_user_msg[:50]

    # Generate stable conversation ID from FIRST message only
    # This ensures the ID stays the same as conversation grows
    conv_id = str(abs(hash(first_user_msg)))
    timestamp = datetime.now().isoformat()

    logger.debug(
        "update_conversations_list: title='%s', id=%s, existing=%s",
        first_user_msg,
        conv_id,
        [c.get("id") for c in (conv_list or [])],
    )

    # Get last message for preview
    preview = ""
    if len(conv_state) > 0:
        preview = _content_to_str(conv_state[-1].get("content", ""))[:100]

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

    logger.debug(
        "update_conversations_list: saved '%s' (id=%s), returning %d conversations",
        title,
        conv_id,
        len(result),
    )

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


async def handle_chat_interface_message(
    message: Union[str, dict],
    history: List[Dict[str, Any]],
    user_state: Optional[Dict[str, Any]],
    settings: Optional[Dict[str, Any]] = None,
    pending_files: Optional[list] = None,
    conv_id: Optional[str] = None,
):
    """Handle chat message submission for gr.ChatInterface (async streaming).

    Async generator: yields (List[gr.ChatMessage], conv_id_update) tuples.
    gr.ChatInterface replaces its last yield each time.
    """
    text, msg_files = _extract_message(message)
    if not text.strip():
        yield [
            gr.ChatMessage(role="assistant", content="Please enter a message.")
        ], gr.update()
        return

    effective_files = pending_files if pending_files else msg_files

    if settings and "model_config" in settings:
        model_config = settings["model_config"]
        provider = model_config.get("provider", "openrouter")
        model_name = model_config.get("model", "openai/gpt-4o-mini")
        temperature = model_config.get("temperature", 0.7)
        max_tokens = model_config.get("max_tokens", 2000)
    else:
        provider = "openrouter"
        model_name = "openai/gpt-4o-mini"
        temperature = 0.7
        max_tokens = 2000

    payload = {
        "user_message": text,
        "workflow_mode": "workbench",
        "llm_config": {
            "provider": provider,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        "pending_files": effective_files or [],
    }
    if conv_id:
        payload["conversation_id"] = conv_id

    thinking_content = ""
    answer_content = ""
    current_conv_id = conv_id
    last_msgs: list = []

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "http://localhost:8000/api/v1/chat/workflow/stream",
                json=payload,
                timeout=60,
            ) as response:
                if response.status_code != 200:
                    body = await response.aread()
                    error_text = body.decode()
                    yield [
                        gr.ChatMessage(
                            role="assistant",
                            content=(f"API Error {response.status_code}: {error_text}"),
                        )
                    ], gr.update()
                    return
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if not line.startswith("data: "):
                        continue
                    try:
                        event = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue

                    event_type = event.get("type")
                    if event_type in (
                        "thinking_chunk",
                        "answer_chunk",
                        "processing_file",
                    ):
                        if event_type == "thinking_chunk":
                            thinking_content += event.get("content", "")
                        elif event_type == "answer_chunk":
                            answer_content += event.get("content", "")
                        msgs = streaming_event_to_chat_messages(
                            event,
                            thinking_content,
                            answer_content,
                            locale="en",
                        )
                        if msgs:
                            last_msgs = msgs
                            yield msgs, gr.update()
                    elif event_type == "done":
                        resp = event.get("response", {})
                        if isinstance(resp, dict):
                            current_conv_id = (
                                resp.get("conversation_id") or current_conv_id
                            )
                        # Yield last messages again to update conv_id state.
                        # gr.ChatInterface replaces (not appends) on each yield,
                        # so re-yielding last_msgs causes no visual duplication.
                        yield last_msgs, current_conv_id

    except httpx.TimeoutException:
        yield [
            gr.ChatMessage(
                role="assistant", content="Request timed out after 60 seconds"
            )
        ], gr.update()
    except httpx.ConnectError:
        yield [
            gr.ChatMessage(
                role="assistant", content="Connection failed - is the server running?"
            )
        ], gr.update()
    except Exception as e:
        yield [
            gr.ChatMessage(role="assistant", content=f"Unexpected error: {str(e)}")
        ], gr.update()


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
