# Enhanced Gradio Application for Consolidated Service Integration

import uuid

import gradio as gr

from .components.simple_client import SimpleLangGraphClient
from ..services.model_config_service import model_config_service


def create_workbench_app() -> gr.Blocks:
    """Create enhanced workbench interface with consolidated service integration"""

    client = SimpleLangGraphClient()

    # Get dynamic configuration from environment
    provider_choices, default_provider = model_config_service.get_provider_choices_for_ui()
    model_choices, default_model = model_config_service.get_model_choices_for_ui()

    # Get active mode for title
    import os
    active_mode = os.getenv("APP_MODE", "workbench")
    title = f"Agent Workbench - {active_mode.title()} Mode"

    with gr.Blocks(title=title) as app:
        gr.Markdown(f"# 🛠️ Agent Workbench - {active_mode.title()} Mode")

        conversation_id = gr.State(str(uuid.uuid4()))

        with gr.Row():
            with gr.Column(scale=1):
                # Dynamic model configuration from .env
                provider = gr.Dropdown(
                    choices=provider_choices,
                    value=default_provider,
                    label="Provider",
                )

                model = gr.Dropdown(
                    choices=model_choices,
                    value=default_model,
                    label="Model Configuration",
                )

                temperature = gr.Slider(
                    0.0, 2.0,
                    model_config_service.default_temperature,
                    label="Temperature"
                )
                max_tokens = gr.Slider(
                    100, 4000,
                    model_config_service.default_max_tokens,
                    label="Max Tokens"
                )

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
                # Parse model selection to get provider and model name
                selected_provider, selected_model = model_config_service.parse_model_selection(model_val)

                # Enhanced model config
                model_config = {
                    "provider": selected_provider,
                    "model_name": selected_model,
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
