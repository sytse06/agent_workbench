# Enhanced Gradio Application for Consolidated Service Integration

import uuid

import gradio as gr

from .components.simple_client import SimpleLangGraphClient


def create_workbench_app() -> gr.Blocks:
    """Create enhanced workbench interface with consolidated service integration"""

    client = SimpleLangGraphClient()

    with gr.Blocks(title="Agent Workbench - Enhanced") as app:
        gr.Markdown("# 🛠️ Agent Workbench - Enhanced with LangGraph")

        conversation_id = gr.State(str(uuid.uuid4()))

        with gr.Row():
            with gr.Column(scale=1):
                # Enhanced model configuration
                provider = gr.Dropdown(
                    choices=["openrouter", "ollama"],
                    value="openrouter",
                    label="Provider",
                )

                model = gr.Dropdown(
                    choices=["qwen/qwq-32b-preview", "claude-3-5-sonnet-20241022"],
                    value="qwen/qwq-32b-preview",
                    label="Model",
                )

                temperature = gr.Slider(0.0, 2.0, 0.7, label="Temperature")
                max_tokens = gr.Slider(100, 4000, 2000, label="Max Tokens")

                # NEW: Workflow monitoring
                gr.Markdown("### 🔄 Workflow Status")
                workflow_status = gr.HTML(value="<div class='info'>Ready</div>")

                # NEW: Debug mode toggle
                debug_mode = gr.Checkbox(label="Debug Mode", value=False)

            with gr.Column(scale=2):
                chatbot = gr.Chatbot(height=400, label="Enhanced Chat", type="messages")

                with gr.Row():
                    message = gr.Textbox(
                        placeholder="Enter your message (now powered by LangGraph)...",
                        label="Message",
                        scale=4,
                        lines=2,
                    )
                    send = gr.Button("Send", variant="primary", scale=1)

        # Enhanced message handler
        async def handle_enhanced_message(
            msg, conv_id, provider_val, model_val, temp_val, max_tokens_val, debug_val
        ):
            if not msg.strip():
                return "", gr.update(), "<div class='info'>Ready</div>"

            try:
                # Enhanced model config
                model_config = {
                    "provider": provider_val,
                    "model_name": model_val,
                    "temperature": temp_val,
                    "max_tokens": max_tokens_val,
                }

                # Send through consolidated service
                response = await client.send_message(
                    message=msg, conversation_id=conv_id, model_config=model_config
                )

                # Get updated history
                history = await client.get_chat_history(conv_id)

                # Show success status with workflow info
                mode = response["workflow_mode"]
                success = response["execution_successful"]
                provider_used = response.get("metadata", {}).get(
                    "provider_used", "Unknown"
                )
                success_html = f"""
                <div class='success'>
                    ✅ Workflow completed successfully<br>
                    <strong>Mode:</strong> {mode}<br>
                    <strong>Execution:</strong> {'Success' if success else 'Failed'}<br>
                    <strong>Provider:</strong> {provider_used}
                </div>
                """

                return "", history, success_html

            except Exception as e:
                error_html = f"<div class='error'>❌ Workflow failed: {str(e)}</div>"
                try:
                    history = await client.get_chat_history(conv_id)
                except Exception:
                    history = []
                history.append({"role": "user", "content": msg})
                history.append({"role": "assistant", "content": f"Error: {str(e)}"})
                return "", history, error_html

        # Wire up events
        send.click(
            fn=handle_enhanced_message,
            inputs=[
                message,
                conversation_id,
                provider,
                model,
                temperature,
                max_tokens,
                debug_mode,
            ],
            outputs=[message, chatbot, workflow_status],
        )

        message.submit(
            fn=handle_enhanced_message,
            inputs=[
                message,
                conversation_id,
                provider,
                model,
                temperature,
                max_tokens,
                debug_mode,
            ],
            outputs=[message, chatbot, workflow_status],
        )

    return app


def launch_gradio_interface(host: str = "0.0.0.0", port: int = 7860) -> None:
    """Launch the Gradio interface"""
    app = create_workbench_app()
    app.launch(server_name=host, server_port=port, share=False)


if __name__ == "__main__":
    launch_gradio_interface()
