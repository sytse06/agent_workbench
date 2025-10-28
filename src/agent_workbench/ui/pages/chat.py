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
    config: Dict[str, Any],
    user_state: gr.State,
    conversation_state: gr.State,
    settings_state: gr.State,
) -> None:
    """
    Render chat interface.

    Args:
        config: Mode configuration from mode_factory
        user_state: Shared user session state
        conversation_state: Shared conversation messages state
        settings_state: User settings (model config, theme, context)

    Critical Pattern:
        - State passed from demo level, not created here
        - All event handlers must update conversation_state
        - NO model controls (in settings page)

    Phase 2: Now receives settings_state to use for chat
    """

    # Header with settings button
    with gr.Row():
        gr.Markdown(f"# {config['title']}")
        settings_btn = gr.Button("⚙️", size="sm")

    # Chatbox - loads from conversation_state
    chatbot = gr.Chatbot(
        value=conversation_state.value if conversation_state.value else [],
        label="",
        height=600,
        show_copy_button=True,
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
    settings_btn.click(fn=None, js="() => { window.location.href = '/settings'; }")

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


def handle_chat_message(
    message: str,
    history: List[List[str]],
    user_state: Optional[Dict[str, Any]],
    settings: Optional[Dict[str, Any]] = None,
) -> Tuple[List[List[str]], str, List[List[str]]]:
    """
    Handle chat message submission.

    Args:
        message: User input text
        history: Current chat history (Gradio format: [[user, assistant], ...])
        user_state: User session data
        settings: User settings (model config, etc.)

    Returns:
        Tuple of (updated_history, cleared_input, updated_state)

    Phase 2: Now uses settings from settings page for model configuration.
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
