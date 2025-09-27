"""
Ultra-Simple Gradio Chat UI - Direct OpenRouter Integration
No complex workflows, no state management, just direct API calls.
"""

import gradio as gr
import requests  # type: ignore

# Hardcoded configuration for maximum reliability
PROVIDER = "openrouter"
MODEL = "openai/gpt-4o-mini"  # Fastest verified: 1.0s response time
API_URL = "http://localhost:8000/api/v1/chat/direct"
TIMEOUT = 30


def chat_handler(message, history):
    """
    Ultra-simple chat handler - direct API call to proven endpoint.

    Args:
        message: User input message
        history: Chat history (Gradio format)

    Returns:
        tuple: (empty_string, updated_history)
    """
    print(f"🎯 HANDLER CALLED: message='{message}', history_length={len(history)}")

    if not message.strip():
        print("🎯 HANDLER: Empty message, returning early")
        return "", history

    try:
        print(f"🎯 HANDLER: Making API call to {API_URL}")
        print(f"🎯 HANDLER: Payload - provider={PROVIDER}, model={MODEL}")

        # Direct call to proven working endpoint
        response = requests.post(
            API_URL,
            json={
                "message": message,
                "provider": PROVIDER,
                "model_name": MODEL,
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            timeout=TIMEOUT,
        )

        print(f"🎯 HANDLER: Response status={response.status_code}")

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("content", "No response received")
            print(f"🎯 HANDLER: AI response received: {ai_response[:50]}...")

            # Add to history in Gradio format
            history.append([message, ai_response])
            print(f"🎯 HANDLER: Updated history length={len(history)}")
            return "", history
        else:
            error_msg = f"API Error {response.status_code}: {response.text}"
            print(f"🎯 HANDLER: Error - {error_msg}")
            history.append([message, error_msg])
            return "", history

    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds"
        print(f"🎯 HANDLER: Timeout - {error_msg}")
        history.append([message, error_msg])
        return "", history

    except requests.exceptions.ConnectionError:
        error_msg = "Connection failed - is the server running?"
        print(f"🎯 HANDLER: Connection error - {error_msg}")
        history.append([message, error_msg])
        return "", history

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"🎯 HANDLER: Exception - {error_msg}")
        import traceback

        print(f"🎯 HANDLER: Traceback - {traceback.format_exc()}")
        history.append([message, error_msg])
        return "", history


def create_simple_chat_app():
    """Create the ultra-simple chat interface."""

    with gr.Blocks(
        title="Simple Chat - Direct OpenRouter", theme=gr.themes.Soft()
    ) as app:

        gr.Markdown(
            """
        # 🚀 Simple Chat - Direct OpenRouter Integration

        **Configuration:**
        - Provider: OpenRouter
        - Model: GPT-4o-mini (fastest: ~1.0s response)
        - Direct API: No complex workflows
        """
        )

        # Chat interface
        chatbot = gr.Chatbot(label="Chat", height=400, show_label=True)

        # Message input
        msg = gr.Textbox(
            placeholder="Type your message and press Enter...",
            label="Message",
            lines=2,
            max_lines=5,
        )

        # Send button
        send_btn = gr.Button("Send", variant="primary")

        # Clear button
        clear_btn = gr.Button("Clear Chat", variant="secondary")

        # Event handlers
        msg.submit(fn=chat_handler, inputs=[msg, chatbot], outputs=[msg, chatbot])

        send_btn.click(fn=chat_handler, inputs=[msg, chatbot], outputs=[msg, chatbot])

        clear_btn.click(fn=lambda: ([], ""), outputs=[chatbot, msg])

        # Status info
        gr.Markdown(
            """
        ---
        **Status:** Direct connection to `/api/v1/chat/direct`
        **Expected response time:** ~1.0 seconds
        **No complex workflows:** Just you → API → AI response
        """
        )

    return app


def launch_simple_chat(host="0.0.0.0", port=7860, share=False):
    """Launch the simple chat interface."""
    app = create_simple_chat_app()
    app.launch(server_name=host, server_port=port, share=share, show_error=True)


if __name__ == "__main__":
    launch_simple_chat()
