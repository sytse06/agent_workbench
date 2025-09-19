# Error Handling Components for UI

from typing import Any, Dict

import gradio as gr


def create_error_display() -> gr.Column:
    """Create error display component"""
    with gr.Column():
        error_message = gr.Textbox(
            label="Error Details", visible=False, interactive=False, lines=3
        )
        return error_message


def format_error_message(error: Exception) -> str:
    """Format error message for display"""
    return f"❌ Error: {str(error)}"


def show_error(error_message: str) -> gr.update:
    """Show error in UI"""
    return gr.update(value=error_message, visible=True, interactive=True)


def hide_error() -> gr.update:
    """Hide error in UI"""
    return gr.update(value="", visible=False)


def create_error_handling_context() -> Dict[str, Any]:
    """Create error handling context for UI components"""
    return {"error_display": None, "last_error": None}


# Example usage in a component
async def handle_component_error(func, *args, **kwargs):
    """Generic error handling wrapper for UI components"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        error_msg = format_error_message(e)
        # In a real implementation, this would update the UI
        print(f"Component error: {error_msg}")
        raise e
