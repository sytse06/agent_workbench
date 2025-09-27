# Enhanced Gradio Application for Consolidated Service Integration

import uuid

import gradio as gr

from ..services.model_config_service import model_config_service


def create_workbench_app() -> gr.Blocks:
    """Create enhanced workbench interface with consolidated service integration"""

    # Get dynamic configuration from environment
    provider_choices, default_provider = (
        model_config_service.get_provider_choices_for_ui()
    )
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
                    0.0,
                    2.0,
                    model_config_service.default_temperature,
                    label="Temperature",
                )
                max_tokens = gr.Slider(
                    100,
                    4000,
                    model_config_service.default_max_tokens,
                    label="Max Tokens",
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

        # Simple working handler using direct API call (FIXED for Gradio compatibility)
        def handle_message(
            msg, conv_id, provider_val, model_val, temp_val, max_tokens_val, debug_val
        ):
            print(f"🎯 DEBUG: handle_message called with msg='{msg}'")

            if not msg.strip():
                print("🎯 DEBUG: Empty message, returning early")
                return "", [], "<div class='info'>Ready</div>"

            try:
                print(f"🎯 DEBUG: Processing message, model_val='{model_val}'")

                # Parse model selection to get provider and model name
                selected_provider, selected_model = (
                    model_config_service.parse_model_selection(model_val)
                )
                print(
                    f"🎯 DEBUG: Parsed provider='{selected_provider}', "
                    f"model='{selected_model}'"
                )

                # Use requests instead of httpx for simplicity
                import requests  # type: ignore

                print("🎯 DEBUG: Making direct API call...")

                # Prepare request payload
                payload = {
                    "message": msg,
                    "provider": selected_provider,
                    "model_name": selected_model,
                    "temperature": temp_val,
                    "max_tokens": max_tokens_val,
                }
                print(f"🎯 DEBUG: Request payload: {payload}")

                # Make synchronous API call
                response = requests.post(
                    "http://localhost:8000/api/v1/chat/direct",
                    json=payload,
                    timeout=30,  # 30 second timeout
                )

                print(f"🎯 DEBUG: Response status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    content_preview = result.get("content", "")[:50]
                    print(f"🎯 DEBUG: Response received: {content_preview}...")

                    # Simple history format for Gradio
                    history = [
                        {"role": "user", "content": msg},
                        {
                            "role": "assistant",
                            "content": result.get("content", "No response"),
                        },
                    ]

                    # Show success status
                    success_html = f"""
                    <div class='success'>
                        ✅ Direct chat successful<br>
                        <strong>Provider:</strong> {selected_provider}<br>
                        <strong>Model:</strong> {selected_model}<br>
                        <strong>Latency:</strong> {result.get('latency_ms', 0):.0f}ms
                    </div>
                    """

                    return "", history, success_html
                else:
                    error_msg = f"API Error {response.status_code}: {response.text}"
                    print(f"🎯 DEBUG: Error: {error_msg}")
                    history = [
                        {"role": "user", "content": msg},
                        {"role": "assistant", "content": error_msg},
                    ]
                    error_html = f"<div class='error'>❌ API Error: {error_msg}</div>"
                    return "", history, error_html

            except Exception as e:
                print(f"🎯 DEBUG: Exception caught: {str(e)}")
                import traceback

                print(f"🎯 DEBUG: Traceback: {traceback.format_exc()}")

                error_msg = f"Connection Error: {str(e)}"
                error_html = f"<div class='error'>❌ Connection failed: {str(e)}</div>"
                history = [
                    {"role": "user", "content": msg},
                    {"role": "assistant", "content": error_msg},
                ]
                print("🎯 DEBUG: Returning error response")
                return "", history, error_html

        # Wire up events to use FastAPI consolidated service
        send.click(
            fn=handle_message,
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
            fn=handle_message,
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
