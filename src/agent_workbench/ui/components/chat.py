# Chat Interface Components

import gradio as gr


def create_simple_chat_interface() -> gr.Column:
    """Create a simple chat interface component"""
    with gr.Column():
        chatbot = gr.Chatbot(height=400, label="Chat")
        return chatbot


# Example of a more complex chat interface if needed
def create_advanced_chat_interface() -> gr.Column:
    """Create an advanced chat interface with additional features"""
    with gr.Column():
        chatbot = gr.Chatbot(height=400, label="Chat")
        # Add message history display
        message_history = gr.Textbox(label="Message History", visible=False, lines=10)
        return chatbot, message_history
