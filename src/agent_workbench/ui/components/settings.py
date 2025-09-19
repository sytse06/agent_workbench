# Model Selection and Configuration Components

from typing import List

import gradio as gr


def create_model_selection_panel() -> gr.Column:
    """Create model selection panel for UI configuration"""
    with gr.Column():
        gr.Markdown("### 🧠 Model Configuration")

        provider = gr.Dropdown(
            choices=["openrouter", "ollama", "openai", "anthropic"],
            value="openrouter",
            label="Provider",
        )

        model = gr.Dropdown(
            choices=["claude-3-5-sonnet-20241022", "gpt-4", "llama3.1", "mistral-7b"],
            value="claude-3-5-sonnet-20241022",
            label="Model",
        )

        temperature = gr.Slider(
            minimum=0.0, maximum=2.0, value=0.7, step=0.1, label="Temperature"
        )

        return gr.Column([provider, model, temperature])


def create_workflow_configuration_panel(mode: str = "workbench") -> gr.Column:
    """Create workflow configuration panel based on mode"""
    with gr.Column():
        gr.Markdown("### ⚙️ Workflow Settings")

        if mode == "workbench":
            # Workbench specific settings
            max_tokens = gr.Slider(
                minimum=100, maximum=4000, value=1000, step=100, label="Max Tokens"
            )

            return gr.Column([max_tokens])
        else:
            # SEO coach specific settings
            return gr.Column([])


async def get_available_providers() -> List[str]:
    """Get list of available LLM providers"""
    return ["openrouter", "ollama", "openai", "anthropic"]


async def get_provider_models(provider: str) -> List[str]:
    """Get available models for a given provider"""
    models = {
        "openrouter": ["claude-3-5-sonnet-20241022", "gpt-4", "llama3.1"],
        "ollama": ["llama3.1", "mistral-7b", "phi3"],
        "openai": ["gpt-4", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
    }
    return models.get(provider, ["llama3.1"])
