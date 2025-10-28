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


def render(
    config: Dict[str, Any], user_state: gr.State, conversation_state: gr.State
) -> None:
    """
    Render chat interface.

    Args:
        config: Mode configuration from mode_factory
        user_state: Shared user session state
        conversation_state: Shared conversation messages state

    Critical Pattern:
        - State passed from demo level, not created here
        - All event handlers must update conversation_state
        - NO model controls (in settings page)
    """

    # Header with settings button
    with gr.Row():
        gr.Markdown(f"# {config['title']}")
        settings_btn = gr.Button("⚙️", size="sm", elem_classes="settings-button")

    # Chatbox - loads from conversation_state
    chatbot = gr.Chatbot(
        value=conversation_state.value if conversation_state.value else [],
        label="",
        height=600,
        show_copy_button=True,
        elem_classes="chatbot-container",
    )

    # Input area
    with gr.Row(elem_classes="input-row"):
        msg = gr.Textbox(
            placeholder=config["labels"]["placeholder"],
            scale=4,
            show_label=False,
            container=False,
        )
        send = gr.Button(config["labels"]["send"], scale=1, variant="primary")

    # Event: Navigate to settings
    settings_btn.click(fn=None, js="() => { window.location.href = '/settings'; }")

    # Event: Send message
    send.click(
        fn=handle_chat_message,
        inputs=[msg, chatbot, user_state],
        outputs=[chatbot, msg, conversation_state],
    )

    # Event: Submit message (Enter key)
    msg.submit(
        fn=handle_chat_message,
        inputs=[msg, chatbot, user_state],
        outputs=[chatbot, msg, conversation_state],
    )


def handle_chat_message(
    message: str, history: List[List[str]], user_state: Optional[Dict[str, Any]]
) -> Tuple[List[List[str]], str, List[List[str]]]:
    """
    Handle chat message submission.

    Args:
        message: User input text
        history: Current chat history (Gradio format: [[user, assistant], ...])
        user_state: User session data

    Returns:
        Tuple of (updated_history, cleared_input, updated_state)

    Note: This is a simple implementation that calls the existing API.
          Phase 2 will integrate with full service layer.
    """

    if not message.strip():
        return history, "", history

    try:
        # Call existing API endpoint
        response = requests.post(
            "http://localhost:8000/api/v1/chat/direct",
            json={
                "message": message,
                "provider": "openrouter",
                "model_name": "openai/gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("content", "No response received")

            # Add to history in Gradio format
            new_history = history + [[message, ai_response]]

            return (
                new_history,  # Update chatbot display
                "",  # Clear input field
                new_history,  # Update conversation_state
            )
        else:
            error_msg = f"API Error {response.status_code}: {response.text}"
            new_history = history + [[message, error_msg]]
            return new_history, "", new_history

    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds"
        new_history = history + [[message, error_msg]]
        return new_history, "", new_history

    except requests.exceptions.ConnectionError:
        error_msg = "Connection failed - is the server running?"
        new_history = history + [[message, error_msg]]
        return new_history, "", new_history

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        new_history = history + [[message, error_msg]]
        return new_history, "", new_history
