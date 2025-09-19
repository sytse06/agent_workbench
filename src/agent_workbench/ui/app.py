# Main Gradio Application Entry Point

import uuid

import gradio as gr

from .components.simple_client import LangGraphClient


def create_workbench_app() -> gr.Blocks:
    """Create simplified workbench interface - no dual modes"""

    client = LangGraphClient()

    with gr.Blocks(title="Agent Workbench") as app:
        gr.Markdown("# 🛠️ Agent Workbench")

        # Minimal state - just conversation ID
        conversation_id = gr.State(str(uuid.uuid4()))

        with gr.Row():
            with gr.Column(scale=1):
                # Simple model selection
                provider = gr.Dropdown(
                    choices=["openrouter", "ollama"],
                    value="openrouter",
                    label="Provider",
                )

                model = gr.Dropdown(
                    choices=["claude-3-5-sonnet-20241022", "gpt-4"],
                    value="claude-3-5-sonnet-20241022",
                    label="Model",
                )

                temperature = gr.Slider(
                    minimum=0.0, maximum=2.0, value=0.7, step=0.1, label="Temperature"
                )

            with gr.Column(scale=2):
                # Simple chat interface - no complex state management
                chatbot = gr.Chatbot(height=400, label="Chat", type="messages")

                with gr.Row():
                    message = gr.Textbox(
                        placeholder="Enter your message...",
                        label="Message",
                        scale=4,
                        lines=2,
                    )
                    send = gr.Button("Send", variant="primary", scale=1)

        # Simple event handler - no complex state sync
        async def handle_message(msg, conv_id, provider_val, model_val, temp_val):
            if not msg.strip():
                return "", gr.update()

            try:
                # Send to LangGraph
                await client.send_message(
                    message=msg,
                    conversation_id=conv_id,
                    model_config={
                        "provider": provider_val,
                        "model": model_val,
                        "temperature": temp_val,
                    },
                )

                # Get updated history from LangGraph (single source of truth)
                history = await client.get_chat_history(conv_id)

                return "", history

            except Exception as e:
                # Simple error handling
                error_history = await client.get_chat_history(conv_id)
                error_history.append({"role": "user", "content": msg})
                error_history.append(
                    {"role": "assistant", "content": f"Error: {str(e)}"}
                )
                return "", error_history

        # Wire up events
        send.click(
            fn=handle_message,
            inputs=[message, conversation_id, provider, model, temperature],
            outputs=[message, chatbot],
        )

        message.submit(
            fn=handle_message,
            inputs=[message, conversation_id, provider, model, temperature],
            outputs=[message, chatbot],
        )

    return app


def launch_gradio_interface(host: str = "0.0.0.0", port: int = 7860) -> None:
    """Launch the Gradio interface"""
    app = create_workbench_app()
    app.launch(server_name=host, server_port=port, share=False)


if __name__ == "__main__":
    launch_gradio_interface()
