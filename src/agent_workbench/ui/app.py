# Enhanced Gradio Application for Consolidated Service Integration

import uuid

import gradio as gr

from ..services.model_config_service import model_config_service


def create_workbench_app() -> gr.Blocks:
    """Create enhanced workbench interface with consolidated service integration"""

    print("=" * 80)
    print("🎯 CREATE_WORKBENCH_APP CALLED")
    print("=" * 80)

    # Import ChatService for direct calls (avoid localhost HTTP calls)
    import asyncio
    import time

    from ..models.schemas import ModelConfig
    from ..services.llm_service import ChatService

    # Get dynamic configuration from environment
    provider_choices, default_provider = (
        model_config_service.get_provider_choices_for_ui()
    )
    model_choices, default_model = model_config_service.get_model_choices_for_ui()

    print(f"🎯 Provider choices: {provider_choices}")
    print(f"🎯 Model choices: {model_choices}")

    # Get active mode for title
    import os

    active_mode = os.getenv("APP_MODE", "workbench")
    title = f"Agent Workbench - {active_mode.title()} Mode"
    print(f"🎯 Active mode: {active_mode}")

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
                # Test button to verify event system works
                with gr.Row():
                    test_btn = gr.Button("🧪 Test Event System", variant="secondary")
                    test_output = gr.Textbox(label="Test Output", scale=3)

                chatbot = gr.Chatbot(height=400, label="Enhanced Chat", type="messages")

                with gr.Row():
                    message = gr.Textbox(
                        placeholder="Enter your message (now powered by LangGraph)...",
                        label="Message",
                        scale=4,
                        lines=2,
                    )
                    send = gr.Button("Send", variant="primary", scale=1)

        def test_handler():
            """Simple test to verify Gradio events work at all."""
            print("=" * 80)
            print("🧪 TEST BUTTON CLICKED - EVENT SYSTEM WORKS!")
            print("=" * 80)
            return "✅ Event system is working! Button click detected."

        test_btn.click(fn=test_handler, outputs=test_output)

        # Direct ChatService handler (avoids localhost HTTP calls)
        async def handle_message_async(
            msg, conv_id, provider_val, model_val, temp_val, max_tokens_val, debug_val
        ):
            """Async handler that calls ChatService directly."""
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

                # Create model configuration (direct service call)
                print("🎯 DEBUG: Creating ModelConfig...")
                model_config = ModelConfig(
                    provider=selected_provider,
                    model_name=selected_model,
                    temperature=temp_val,
                    max_tokens=max_tokens_val,
                    streaming=False,
                )
                print(f"🎯 DEBUG: ModelConfig: {model_config}")

                # Initialize ChatService
                print("🎯 DEBUG: Initializing ChatService...")
                chat_service = ChatService(model_config)
                print("🎯 DEBUG: ChatService initialized")

                # Call chat completion directly
                start_time = time.time()
                print("🎯 DEBUG: Calling chat_completion...")
                response = await chat_service.chat_completion(
                    message=msg, conversation_id=None
                )
                latency_ms = (time.time() - start_time) * 1000

                print(f"🎯 DEBUG: Response received in {latency_ms:.0f}ms")
                print(f"🎯 DEBUG: Response preview: {response.reply[:100]}...")

                # Simple history format for Gradio
                history = [
                    {"role": "user", "content": msg},
                    {"role": "assistant", "content": response.reply},
                ]

                # Show success status
                success_html = f"""
                <div class='success'>
                    ✅ Direct chat successful<br>
                    <strong>Provider:</strong> {selected_provider}<br>
                    <strong>Model:</strong> {selected_model}<br>
                    <strong>Latency:</strong> {latency_ms:.0f}ms
                </div>
                """

                return "", history, success_html

            except Exception as e:
                print(f"🎯 DEBUG: Exception caught: {str(e)}")
                import traceback

                print(f"🎯 DEBUG: Traceback: {traceback.format_exc()}")

                error_msg = f"Error: {str(e)}"
                error_html = f"<div class='error'>❌ {error_msg}</div>"
                history = [
                    {"role": "user", "content": msg},
                    {"role": "assistant", "content": error_msg},
                ]
                print("🎯 DEBUG: Returning error response")
                return "", history, error_html

        def handle_message(*args):
            """Sync wrapper for Gradio that runs async handler."""
            print("=" * 80)
            print("🚨 HANDLE_MESSAGE WRAPPER CALLED")
            print(f"🚨 Args received: {len(args)} arguments")
            print(f"🚨 First arg (message): {args[0] if args else 'NO ARGS'}")
            print("=" * 80)
            try:
                result = asyncio.run(handle_message_async(*args))
                print("🚨 asyncio.run completed successfully")
                return result
            except Exception as e:
                print(f"🚨 WRAPPER EXCEPTION: {e}")
                import traceback
                print(f"🚨 Traceback:\n{traceback.format_exc()}")
                raise

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

    print("=" * 80)
    print("🎯 GRADIO APP CREATED SUCCESSFULLY")
    print("🎯 Event handlers wired to handle_message")
    print("=" * 80)

    return app


def launch_gradio_interface(host: str = "0.0.0.0", port: int = 7860) -> None:
    """Launch the Gradio interface"""
    app = create_workbench_app()
    app.launch(server_name=host, server_port=port, share=False)


if __name__ == "__main__":
    launch_gradio_interface()
