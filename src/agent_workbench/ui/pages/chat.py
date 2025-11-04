"""
Chat page - minimal chatbox interface.

NO model controls (moved to settings).
NO sidebar (separate feature - see
    docs/phase2/Feat-dev-plan-chat-history-in-sidebar-in-chatpage.md).

Identical structure for workbench and SEO coach modes - differences
controlled by config labels.
"""

from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import requests  # type: ignore[import-untyped]

from ..components.sidebar import (
    create_sidebar_css,
    create_sidebar_javascript,
    render_sidebar,
)


def render(
    config: Dict[str, Any],
    user_state: gr.State,
    conversation_state: gr.State,
    settings_state: gr.State,
) -> None:
    """
    Render chat interface with optional sidebar.

    Args:
        config: Mode configuration from mode_factory
        user_state: Shared user session state
        conversation_state: Shared conversation messages state
        settings_state: User settings (model config, theme, context)

    Phase 3: Added conversation history sidebar (feature-flagged)
    """

    # Sidebar state and trigger (for loading conversations)
    load_conv_trigger = gr.State(None)

    # Render sidebar if enabled
    sidebar_visible = None
    conv_list_html = None
    if config.get("show_conv_browser", False):
        sidebar_visible, conv_list_html, new_chat_btn, collapse_btn = render_sidebar(
            config, user_state
        )

    # Main layout
    with gr.Row():
        # Sidebar wrapper (if enabled)
        if config.get("show_conv_browser", False):
            with gr.Column(visible=sidebar_visible, scale=2):
                pass  # Sidebar already rendered by render_sidebar

        # Main chat area
        with gr.Column(scale=8 if config.get("show_conv_browser") else 12):
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
            send.click(
                fn=handle_chat_message,
                inputs=[msg, chatbot, user_state, settings_state],
                outputs=[chatbot, msg, conversation_state],
            )

            # Event: Submit message (Enter key)
            msg.submit(
                fn=handle_chat_message,
                inputs=[msg, chatbot, user_state, settings_state],
                outputs=[chatbot, msg, conversation_state],
            )

            # Phase 3: Wire conversation loading
            if config.get("show_conv_browser", False):
                # Hidden state for conversation loading trigger
                load_conv_trigger.change(
                    fn=load_conversation_into_chat,
                    inputs=[load_conv_trigger],
                    outputs=[chatbot, conversation_state],
                )

    # Inject sidebar JavaScript and CSS (if enabled)
    if config.get("show_conv_browser", False):
        gr.HTML(create_sidebar_javascript())
        gr.HTML(create_sidebar_css())

        # Wire toggle button logic (hybrid approach)
        if collapse_btn:
            collapse_btn.click(
                fn=lambda v: not v,
                inputs=[sidebar_visible],
                outputs=[sidebar_visible],
            )

            collapse_btn.click(
                fn=None,
                js="""
                    const sb = document.querySelector('.gr-sidebar');
                    sb.classList.toggle('gr-sidebar-collapsed');
                    sb.setAttribute('aria-hidden',
                        sb.classList.contains('gr-sidebar-collapsed'));
                """,
            )


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
